# frozen_string_literal: true

# Agent Name: ruby-engine-context
#
# Part of the scjson project.
# Developed by Softoboros Technology Inc.
# Licensed under the BSD 1-Clause License.

require 'json'
require 'set'
require_relative '../../scjson'

module Scjson
  module Engine
    #
    # Minimal document context and transition logic to support
    # deterministic trace emission for simple charts. This is an
    # iterative scaffold toward full SCXML semantics.
    #
    class DocumentContext
      # @return [Hash{String=>Object}] Canonical scjson root map
      attr_reader :root
      # @return [Array<String>] Active state configuration
      attr_reader :configuration

      ##
      # Load a document and create a context.
      #
      # @param input_path [String] Path to SCXML or SCJSON document
      # @param xml [Boolean] Treat the input as SCXML when true
      # @return [DocumentContext]
      def self.from_file(input_path, xml: false)
        data = File.read(input_path)
        json = xml ? Scjson.xml_to_json(data) : data
        new(JSON.parse(json))
      end

      ##
      # Construct a context from a canonical scjson object.
      #
      # @param root [Hash] Canonical scjson root map
      def initialize(root)
        @root = root
        @states = {}
        @parent = {}
        index_states(@root)
        @configuration = initial_configuration
      end

      ##
      # Compute the set of leaf state IDs for filtering.
      #
      # @return [Array<String>] Sorted list of leaf state IDs
      def leaf_state_ids
        leaves = []
        @states.each do |id, node|
          has_children = node.key?('state') || node.key?('parallel')
          leaves << id unless has_children
        end
        leaves.sort
      end

      ##
      # Produce the initialization trace snapshot (step 0).
      #
      # @return [Hash] Trace record for initialization step
      def trace_init
        {
          'event' => nil,
          'firedTransitions' => [],
          'enteredStates' => @configuration.dup,
          'exitedStates' => [],
          'configuration' => @configuration.dup,
          'actionLog' => [],
          'datamodelDelta' => {}
        }
      end

      ##
      # Process one external event and emit a trace step.
      #
      # @param name [String] Event name
      # @param data [Object] Event payload (unused in scaffold)
    # @return [Hash] Trace record for this step
      def trace_step(name:, data: nil)
        event_obj = { 'name' => name, 'data' => data }
        fired = []
        exited = []
        entered = []
        action_log = []
        datamodel_delta = {}

        @data ||= {}
        @internal_queue ||= []
        @current_event_name = name
        @current_event_data = data

        # First, process one external-event transition (if any)
        process_event = lambda do |ev_name, ev_data|
          @current_event_name = ev_name
          @current_event_data = ev_data
          loop do
            tx = find_enabled_transition_for_event(ev_name)
            break unless tx
            src, t = tx
            tr_entered, tr_exited, tr_fired, tr_actions, tr_delta = apply_transition(src, t, cause: ev_name)
            entered.concat(tr_entered)
            exited.concat(tr_exited)
            fired.concat(tr_fired)
            action_log.concat(tr_actions)
            datamodel_delta.merge!(tr_delta)
            # After a transition, process eventless transitions to quiescence
            0.upto(100) do
              tx2 = find_enabled_eventless_transition
              break unless tx2
              src2, t2 = tx2
              e2, x2, f2, a2, d2 = apply_transition(src2, t2, cause: nil)
              entered.concat(e2)
              exited.concat(x2)
              fired.concat(f2)
              action_log.concat(a2)
              datamodel_delta.merge!(d2)
            end
          end
        end

        process_event.call(name, data)

        # Then process internal events, FIFO
        0.upto(100) do
          break if @internal_queue.empty?
          ev = @internal_queue.shift
          if ev.is_a?(Hash)
            process_event.call(ev['name'], ev['data'])
          else
            process_event.call(ev.to_s, nil)
          end
        end

        {
          'event' => event_obj,
          'firedTransitions' => fired,
          'enteredStates' => entered,
          'exitedStates' => exited,
          'configuration' => @configuration.dup,
          'actionLog' => action_log,
          'datamodelDelta' => datamodel_delta
        }
      end

      private

      def wrap_list(value)
        return [] if value.nil?
        value.is_a?(Array) ? value : [value]
      end

      # Find the first enabled transition in document order matching the event name.
      def find_enabled_transition_for_event(name)
        @configuration.each do |sid|
          node = @states[sid]
          next unless node
          wrap_list(node['transition']).each do |t|
            next unless t.is_a?(Hash)
            tokens = parse_event_tokens(t['event'])
            if (tokens.include?(name) || tokens.include?('*')) && cond_true?(t['cond'])
              return [sid, t]
            end
          end
        end
        nil
      end

      # Find the first enabled eventless transition from the active configuration.
      def find_enabled_eventless_transition
        @configuration.each do |sid|
          node = @states[sid]
          next unless node
          wrap_list(node['transition']).each do |t|
            next unless t.is_a?(Hash)
            ev = t['event']
            if (ev.nil? || (ev.is_a?(String) && ev.strip.empty?)) && cond_true?(t['cond'])
              return [sid, t]
            end
          end
        end
        nil
      end

      # Apply a transition: update configuration and compute deltas.
      def apply_transition(source_id, transition_map, cause:)
        targets = wrap_list(transition_map['target']).map(&:to_s)
        actions = []
        delta = {}

        # Compute exit and entry sets using a basic LCA approach per target
        exit_order = []
        entry_order = []

        # Exit chain: from source up to (but not including) the shallowest LCA among targets
        lcas = targets.map { |tid| lca(source_id, tid) }
        # choose the highest (closest to root) LCA to be safe across multiple targets
        chosen_lca = choose_shallowest_ancestor(lcas)
        exit_chain = path_up_exclusive(source_id, chosen_lca)
        exit_order.concat(exit_chain) # deep -> shallow

        # Entry chains: for each target, from LCA down to target (excluding LCA)
        targets.each do |tid|
          chain = path_down_from_lca(chosen_lca, tid)
          entry_order.concat(chain)
        end

        # Execute onexit in deep->shallow order
        exit_order.each do |sid|
          a, d = run_onexit(sid)
          actions.concat(a)
          delta.merge!(d)
        end

        # Update configuration: remove exited leaves and add targets (leaf-level model)
        new_config = @configuration.dup
        exit_order.each { |sid| new_config.delete(sid) }
        # Ensure source is removed even if not in exit_order due to missing ids
        new_config.delete(source_id)
        targets.each { |tid| new_config << tid unless new_config.include?(tid) }
        @configuration = new_config

        # Execute transition actions (between exit and entry)
        ta, td = run_actions_from_map(transition_map)
        actions.concat(ta)
        delta.merge!(td)

        # Execute onentry in shallow->deep order along each entry chain
        entry_order.each do |sid|
          a, d = run_onentry(sid)
          actions.concat(a)
          delta.merge!(d)
        end

        fired = [{
          'source' => source_id,
          'targets' => targets,
          'event' => cause,
          'cond' => nil
        }]
        [entry_order, exit_order, fired, actions, delta]
      end

      # Ancestor chain from a state up to root (inclusive), leaf->root
      def ancestors(id)
        chain = []
        cur = id
        while cur
          chain << cur
          cur = @parent[cur]
        end
        chain
      end

      # Lowest common ancestor (by id), returns nil if only the root matches
      def lca(a, b)
        return nil if a.nil? || b.nil?
        aa = ancestors(a)
        ab = ancestors(b)
        set = aa.to_set
        ab.each do |x|
          return x if set.include?(x)
        end
        nil
      end

      # Choose the shallowest ancestor (closest to root) from a list
      def choose_shallowest_ancestor(list)
        # Compute depth by walking to root; pick one with max depth index reversed (shallowest)
        return nil if list.nil? || list.empty?
        # If all nil, return nil
        found = list.compact
        return nil if found.empty?
        # Shallowest: minimal depth
        found.min_by { |x| ancestors(x).length }
      end

      # Path from a node up to (but not including) the stop node
      def path_up_exclusive(from_id, stop_id)
        out = []
        cur = from_id
        while cur && cur != stop_id
          out << cur
          cur = @parent[cur]
        end
        out
      end

      # Path from LCA down to target, excluding LCA, shallow->deep
      def path_down_from_lca(lca_id, target_id)
        return [target_id] if lca_id.nil?
        chain = ancestors(target_id) # leaf->root
        idx = chain.index(lca_id)
        if idx.nil?
          # lca not on path; fallback to just the target
          return [target_id]
        end
        # chain[0..idx-1] are below LCA in leaf->... order; reverse to get shallow->deep
        below = chain[0...idx]
        below.reverse
      end

      # Execute onexit actions for a state.
      def run_onexit(state_id)
        node = @states[state_id]
        return [[], {}] unless node
        actions = []
        delta = {}
        wrap_list(node['onexit']).each do |blk|
          next unless blk.is_a?(Hash)
          a, d = run_actions_from_map(blk)
          actions.concat(a)
          delta.merge!(d)
        end
        [actions, delta]
      end

      # Execute onentry actions for a state.
      def run_onentry(state_id)
        node = @states[state_id]
        return [[], {}] unless node
        actions = []
        delta = {}
        wrap_list(node['onentry']).each do |blk|
          next unless blk.is_a?(Hash)
          a, d = run_actions_from_map(blk)
          actions.concat(a)
          delta.merge!(d)
        end
        [actions, delta]
      end

      # Execute actions defined in a map: log, assign, raise, if/elseif/else.
      def run_actions_from_map(map)
        actions = []
        delta = {}
        # log
        wrap_list(map['log']).each do |log|
          label = log.is_a?(Hash) ? log['label'] : nil
          expr = log.is_a?(Hash) ? log['expr'] : nil
          val = eval_expr(expr)
          actions << format_log(label, val)
        end
        # assign
        wrap_list(map['assign']).each do |as|
          loc = as.is_a?(Hash) ? as['location'] : nil
          expr = as.is_a?(Hash) ? as['expr'] : nil
          next unless loc
          val = eval_assign_expr(loc, expr)
          @data[loc] = val
          delta[loc] = val
        end
        # raise
        wrap_list(map['raise']).each do |rz|
          ev = rz.is_a?(Hash) ? (rz['event'] || rz['name']) : rz
          @internal_queue << ev.to_s if ev
        end
        wrap_list(map['raise_value']).each do |rz|
          ev = rz.is_a?(Hash) ? (rz['event'] || rz['name']) : rz
          @internal_queue << ev.to_s if ev
        end
        # foreach
        wrap_list(map['foreach']).each do |fe|
          next unless fe.is_a?(Hash)
          array_expr = fe['array']
          item_name = (fe['item'] || 'item').to_s
          index_name = (fe['index'] || 'index').to_s
          ary = eval_expr(array_expr)
          # Normalize ary to an array
          if ary.nil?
            ary = []
          elsif ary.is_a?(Hash)
            ary = ary.values
          elsif !ary.is_a?(Array) && ary.respond_to?(:to_a)
            ary = ary.to_a
          elsif !ary.is_a?(Array)
            ary = [ary]
          end
          had_item = @data.key?(item_name)
          had_index = @data.key?(index_name)
          old_item = @data[item_name]
          old_index = @data[index_name]
          ary.each_with_index do |elem, idx|
            @data[item_name] = elem
            @data[index_name] = idx
            a, d = run_actions_from_map(fe)
            actions.concat(a)
            delta.merge!(d)
          end
          if had_item
            @data[item_name] = old_item
          else
            @data.delete(item_name)
          end
          if had_index
            @data[index_name] = old_index
          else
            @data.delete(index_name)
          end
        end
        # if / elseif / else
        wrap_list(map['if_value']).each do |iff|
          next unless iff.is_a?(Hash)
          if cond_true?(iff['cond'])
            a, d = run_actions_from_map(iff)
            actions.concat(a)
            delta.merge!(d)
          else
            taken = false
            wrap_list(iff['elseif']).each do |eif|
              next unless eif.is_a?(Hash)
              if cond_true?(eif['cond'])
                a, d = run_actions_from_map(eif)
                actions.concat(a)
                delta.merge!(d)
                taken = true
                break
              end
            end
            unless taken
              wrap_list(iff['else_value']).each do |els|
                next unless els.is_a?(Hash)
                a, d = run_actions_from_map(els)
                actions.concat(a)
                delta.merge!(d)
              end
            end
          end
        end
        [actions, delta]
      end

      def format_log(label, value)
        lbl = label ? label.to_s : 'log'
        val = value.nil? ? '' : value.to_s
        "#{lbl}:#{val}"
      end

      # Very small expression handler for demo purposes.
      def eval_expr(expr)
        return nil if expr.nil?
        s = expr.to_s.strip
        # quoted string (single or double)
        if (m = s.match(/^\s*['\"](.*)['\"]\s*$/))
          return m[1]
        end
        # boolean literals
        return true if s.downcase == 'true'
        return false if s.downcase == 'false'
        # integer or float
        if s.match?(/^[-+]?\d+(?:\.\d+)?$/)
          return s.include?('.') ? s.to_f : s.to_i
        end
        # variable reference
        if (m = s.match(/^\s*([a-zA-Z_][\w]*(?:\.[A-Za-z0-9_\[\]']+)*)\s*$/))
          return resolve_path(m[1])
        end
        # pattern: <var> ... + <number>
        if (m = s.match(/([a-zA-Z_][\w]*).*?\+\s*([-+]?\d+)/))
          base = (@data || {})[m[1]]
          base = 0 unless base.is_a?(Numeric)
          return base + m[2].to_i
        end
        # fallback: return as-is
        s
      end

      def eval_assign_expr(location, expr)
        val = eval_expr(expr)
        # If val is a string equal to location or empty due to parsing limits, default to increment when reasonable
        if val.is_a?(String) && val.strip.empty?
          base = (@data || {})[location]
          base = 0 unless base.is_a?(Numeric)
          return base + 1
        end
        val
      end

      # Evaluate a condition into boolean truthiness.
      def cond_true?(expr)
        return true if expr.nil? || expr.to_s.strip.empty?
        s = expr.to_s.strip
        # logical and/or (left-associative, naive split)
        if (i = s.index(' and '))
          left = s[0...i]
          right = s[(i + 5)..-1]
          return cond_true?(left) && cond_true?(right)
        end
        if (i = s.index(' or '))
          left = s[0...i]
          right = s[(i + 4)..-1]
          return cond_true?(left) || cond_true?(right)
        end
        # unary not
        if s.start_with?('!')
          return !cond_true?(s[1..-1])
        end
        if s.downcase.start_with?('not ')
          return !cond_true?(s[4..-1])
        end
        # equality/inequality
        if (m = s.match(/^([a-zA-Z_][\w]*)\s*(==|!=)\s*(['\"]?)(.+?)\3$/))
          lhs = (@data || {})[m[1]]
          rhs_raw = m[4]
          rhs = (rhs_raw =~ /^[-+]?\d+(?:\.\d+)?$/) ? (rhs_raw.include?('.') ? rhs_raw.to_f : rhs_raw.to_i) : rhs_raw
          return (lhs == rhs) if m[2] == '=='
          return (lhs != rhs)
        end
        # numeric comparison
        if (m = s.match(/^([a-zA-Z_][\w]*)\s*(>=|<=|>|<)\s*([-+]?\d+(?:\.\d+)?)$/))
          lhs = (@data || {})[m[1]]
          rhs = m[3].include?('.') ? m[3].to_f : m[3].to_i
          return false unless lhs.is_a?(Numeric)
          case m[2]
          when '>' then return lhs > rhs
          when '<' then return lhs < rhs
          when '>=' then return lhs >= rhs
          when '<=' then return lhs <= rhs
          end
        end
        # direct variable truthiness
        val = eval_expr(s)
        !!val && val != 0 && val != ''
      end

      # Resolve a dotted path from @data or _event context.
      def resolve_path(path)
        tokens = path.split('.')
        return nil if tokens.empty?
        if tokens[0] == '_event'
          cur = { 'name' => @current_event_name, 'data' => @current_event_data }
          tokens = tokens[1..-1]
        else
          cur = @data || {}
        end
        tokens.each do |tk|
          key = tk
          if cur.is_a?(Array)
            if key =~ /^\d+$/
              idx = key.to_i
              cur = cur[idx]
            else
              return nil
            end
          elsif cur.is_a?(Hash)
            # support string/symbol access
            cur = cur[key] || cur[key.to_sym]
          else
            return nil
          end
          break if cur.nil?
        end
        cur
      end

      def parse_event_tokens(str)
        return [] if str.nil?
        return [] unless str.is_a?(String)
        str.split(/\s+/)
      end

      def index_states(node, parent_id = nil)
        return unless node.is_a?(Hash)
        # Record this node if it looks like a state (has an id)
        sid = node['id']
        if sid
          @states[sid] = node
          @parent[sid] = parent_id if parent_id
        end
        # Recurse into known containers
        wrap_list(node['state']).each { |child| index_states(child, sid) }
        wrap_list(node['parallel']).each { |child| index_states(child, sid) }
      end

      def initial_configuration
        # Prefer explicit initial on root
        tokens = wrap_list(@root['initial']).map(&:to_s)
        return tokens unless tokens.empty?
        # Else first child state id
        first_state = wrap_list(@root['state']).find { |s| s.is_a?(Hash) && s['id'] }
        first_state ? [first_state['id'].to_s] : []
      end
    end
  end
end
