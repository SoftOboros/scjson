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
      def self.from_file(input_path, xml: false, parent_link: nil, child_invoke_id: nil)
        data = File.read(input_path)
        json = xml ? Scjson.xml_to_json(data) : data
        new(
          JSON.parse(json),
          parent_link: parent_link,
          child_invoke_id: child_invoke_id,
          base_dir: File.dirname(File.expand_path(input_path))
        )
      end

      ##
      # Construct a context from a canonical scjson object.
      #
      # @param root [Hash] Canonical scjson root map
      def initialize(root, parent_link: nil, child_invoke_id: nil, base_dir: nil)
        @root = root
        @states = {}
        @parent = {}
        @parent_link = parent_link
        @child_invoke_id = child_invoke_id
        @base_dir = base_dir
        @tag_type = {}
        @history_shallow = {}
        @history_deep = {}
        index_states(@root)
        @configuration = initial_configuration
        @time = 0.0
        @timers = [] # array of {time: Float, name: String, data: Object}
        @invocations = {} # id => {state: sid, node: inv_map, status: 'active'|'done'|'canceled'}
        @invocations_by_state = Hash.new { |h, k| h[k] = [] }
        @invoke_seq = 0
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
          # Special internal control: invocation completion
          if ev_name == '__invoke_complete'
            iid = ev_data.is_a?(Hash) ? ev_data['invokeid'] : nil
            if iid
              a, d = finalize_invoke(iid, completed: true)
              action_log.concat(a)
              datamodel_delta.merge!(d)
              # enqueue done.invoke events
              @internal_queue << ({ 'name' => 'done.invoke', 'data' => { 'invokeid' => iid } })
              @internal_queue << ({ 'name' => "done.invoke.#{iid}", 'data' => nil })
            end
            return
          end
          loop do
            tx_set = select_transitions_for_event(ev_name)
            break if tx_set.empty?
            e1, x1, f1, a1, d1 = apply_transition_set(tx_set, cause: ev_name)
            entered.concat(e1)
            exited.concat(x1)
            fired.concat(f1)
            action_log.concat(a1)
            datamodel_delta.merge!(d1)
            # After a set, enqueue done.state events if any states completed
            enqueue_done_events
            # After a set, process eventless transitions to quiescence
            0.upto(100) do
              tx0 = select_transitions_for_event(nil)
              break if tx0.empty?
              e2, x2, f2, a2, d2 = apply_transition_set(tx0, cause: nil)
              entered.concat(e2)
              exited.concat(x2)
              fired.concat(f2)
              action_log.concat(a2)
              datamodel_delta.merge!(d2)
              enqueue_done_events
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

      # Select a non-conflicting set of transitions for the given event name (or nil for eventless).
      def select_transitions_for_event(name)
        candidates = []
        # For each active leaf, walk up ancestry and pick the first enabled transition
        @configuration.each do |sid|
          chain = ancestors(sid)
          chain.each do |nid|
            node = @states[nid]
            next unless node
            t = wrap_list(node['transition']).find do |tm|
              next false unless tm.is_a?(Hash)
              if name.nil?
                ev = tm['event']
                (ev.nil? || (ev.is_a?(String) && ev.strip.empty?)) && cond_true?(tm['cond'])
              else
                tokens = parse_event_tokens(tm['event'])
                (tokens.include?(name) || tokens.include?('*')) && cond_true?(tm['cond'])
              end
            end
            if t
              candidates << [nid, t]
              break
            end
          end
        end
        # Resolve conflicts: prefer deeper (descendant) sources; drop ancestors
        selected = []
        candidates.each do |src, t|
          drop = false
          selected.reject! do |(s2, _)|
            if is_ancestor?(src, s2)
              false # keep deeper s2, keep existing
            elsif is_ancestor?(s2, src)
              # remove ancestor already selected
              true
            else
              false
            end
          end
          # If any selected is ancestor of src, then skip adding src (deeper already present?)
          drop = selected.any? { |(s2, _)| is_ancestor?(s2, src) }
          selected << [src, t] unless drop
        end
        selected
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

      # Apply a set of non-conflicting transitions in one microstep.
      def apply_transition_set(tx_set, cause:)
        actions = []
        delta = {}
        fired = []
        exit_set = []
        entry_sequences = []

        # Compute exit and entry sequences per transition
        tx_set.each do |source_id, transition_map|
          targets = wrap_list(transition_map['target']).map(&:to_s)
          lcas = targets.map { |tid| lca(source_id, tid) }
          chosen_lca = choose_shallowest_ancestor(lcas)
          exit_chain = path_up_exclusive(source_id, chosen_lca)
          exit_set.concat(exit_chain)
          seq = []
          targets.each do |tid|
            if @tag_type[tid] == :history
              parent_id = @parent[tid]
              node = @states[tid]
              deep = (node && node['type_value'].to_s.downcase == 'deep')
              remembered = deep ? (@history_deep[parent_id] || []) : (@history_shallow[parent_id] || [])
              if remembered.empty?
                # Fallback to parent's defaults
                if deep
                  remembered = initial_leaves_for_id(parent_id)
                else
                  parent = @states[parent_id]
                  remembered = initial_child_ids_for(parent)
                end
              end
              remembered.each do |rid|
                seq.concat(path_down_from_lca(chosen_lca, rid))
              end
            else
              seq.concat(path_down_from_lca(chosen_lca, tid))
            end
          end
          entry_sequences << seq
          fired << { 'source' => source_id, 'targets' => targets, 'event' => cause, 'cond' => nil }
        end

        # Deduplicate exit set, deep->shallow
        exit_order = exit_set.uniq
        # Execute onexit
        exit_order.each do |sid|
          a, d = run_onexit(sid)
          actions.concat(a)
          delta.merge!(d)
        end

        # Update configuration: remove exit leaves; we'll add entered leaves after expansion
        new_config = @configuration.dup
        exit_order.each { |sid| new_config.delete(sid) }

        # Record history for parents being exited based on previous configuration
        record_history_for_exits(exit_order, @configuration)

        # Transition bodies
        tx_set.each do |_, tmap|
          a, d = run_actions_from_map(tmap)
          actions.concat(a)
          delta.merge!(d)
        end

        # Entry: shallow->deep for each sequence in given order; then expand to initial leaves
        entered = []
        entered_leaves = []
        entry_sequences.each do |seq|
          seq.each do |sid|
            a, d = run_onentry(sid)
            actions.concat(a)
            delta.merge!(d)
            entered << sid
          end
          # Expand descendants when last target is a non-history composite
          target_id = seq.last
          if target_id && @tag_type[target_id] != :history
            leaves, bundle = enter_descendants(target_id)
            entered.concat(bundle[:entered])
            actions.concat(bundle[:actions])
            delta.merge!(bundle[:delta])
            entered_leaves.concat(leaves)
          else
            # If history (deep): remembered leaves were appended as part of seq; if shallow: enter_descendants handled per remembered child in seq
            # For shallow we should expand each remembered child; this happens implicitly since seq contains those child ids
            # and we will expand below by calling enter_descendants on each non-history id in the sequence
          end
          # Expand descendants for any non-history ids in the sequence (covers shallow history children)
          seq.each do |sid|
            next if @tag_type[sid] == :history
            leaves, bundle = enter_descendants(sid)
            entered.concat(bundle[:entered])
            actions.concat(bundle[:actions])
            delta.merge!(bundle[:delta])
            entered_leaves.concat(leaves)
          end
        end

        # Merge entered leaves into configuration
        entered_leaves.each { |leaf| new_config << leaf unless new_config.include?(leaf) }
        @configuration = new_config

        # After finishing entry, schedule invocations for entered states (including leaves)
        schedule_invocations_for_entered((entered + entered_leaves).uniq)

        [entered, exit_order, fired, actions, delta]
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

      def is_ancestor?(a, b)
        return false if a.nil? || b.nil?
        cur = b
        while cur
          return true if cur == a
          cur = @parent[cur]
        end
        false
      end

      # ---- Entry helpers for composite states ----
      def enter_descendants(state_id)
        entered = []
        actions = []
        delta = {}
        leaves = []
        node = @states[state_id]
        return [[], { entered: [], actions: [], delta: {} }] unless node
        if composite?(node)
          initial_child_ids_for(node).each do |cid|
            a, d = run_onentry(cid)
            actions.concat(a)
            delta.merge!(d)
            entered << cid
            sub_leaves, sub = enter_descendants(cid)
            actions.concat(sub[:actions])
            delta.merge!(sub[:delta])
            entered.concat(sub[:entered])
            leaves.concat(sub_leaves)
          end
        else
          leaves << state_id
        end
        [leaves, { entered: entered, actions: actions, delta: delta }]
      end

      def composite?(node)
        node.is_a?(Hash) && (node.key?('state') || node.key?('parallel'))
      end

      def initial_child_ids_for(node)
        # parallel: initial for each region
        if node.key?('parallel')
          ids = []
          wrap_list(node['parallel']).each do |p|
            wrap_list(p['state']).each do |s|
              sid = s['id']
              ids.concat(initial_leaves_for_id(sid.to_s)) if sid
            end
          end
          return ids.uniq
        end
        # state: choose initial children or first
        if node.key?('state')
          initial_tokens = wrap_list(node['initial_attribute']).map(&:to_s)
          if !initial_tokens.empty?
            return initial_tokens
          end
          if node.key?('initial') && node['initial'].is_a?(Hash)
            return wrap_list(node['initial']['transition']).flat_map { |t| wrap_list(t['target']).map(&:to_s) }
          end
          first = wrap_list(node['state']).map { |s| s['id'] }.compact.map(&:to_s).first
          return first ? [first] : []
        end
        []
      end

      def initial_leaves_for_id(state_id)
        node = @states[state_id]
        return [] unless node
        return [state_id] unless composite?(node)
        leaves = []
        if node.key?('parallel')
          wrap_list(node['parallel']).each do |p|
            wrap_list(p['state']).each do |s|
              sid = s['id']
              leaves.concat(initial_leaves_for_id(sid.to_s)) if sid
            end
          end
          return leaves
        end
        initial_child_ids_for(node).each do |cid|
          leaves.concat(initial_leaves_for_id(cid))
        end
        leaves
      end

      # ---- Invoke / Finalize ----
      def schedule_invocations_for_entered(state_ids)
        state_ids.each do |sid|
          node = @states[sid]
          next unless node
          wrap_list(node['invoke']).each do |inv|
            next unless inv.is_a?(Hash)
            iid = (inv['id'] && inv['id'].to_s)
            unless iid && !iid.empty?
              @invoke_seq += 1
              iid = "i#{@invoke_seq}"
            end
            rec = { state: sid, node: inv, status: 'active' }
            # Try to build a child context for inline content or src
            child_ctx = build_child_context(inv, iid)
            rec[:ctx] = child_ctx if child_ctx
            @invocations[iid] = rec
            @invocations_by_state[sid] << iid unless @invocations_by_state[sid].include?(iid)
            # For now, treat as immediate completion after child init/quiescence
            if child_ctx
              0.upto(100) do
                tx0 = child_ctx.select_transitions_for_event(nil)
                break if tx0.empty?
                child_ctx.apply_transition_set(tx0, cause: nil)
              end
            end
            @internal_queue << ({ 'name' => '__invoke_complete', 'data' => { 'invokeid' => iid } })
          end
        end
      end

      def finalize_invoke(invoke_id, completed:)
        rec = @invocations[invoke_id]
        return [[], {}] unless rec
        # run finalize actions
        actions = []
        delta = {}
        inv_node = rec[:node]
        wrap_list(inv_node['finalize']).each do |fin|
          a, d = run_actions_from_map(fin) if fin.is_a?(Hash)
          if a
            actions.concat(a)
          end
          if d
            delta.merge!(d)
          end
        end
        rec[:status] = completed ? 'done' : 'canceled'
        # remove mapping from state
        sid = rec[:state]
        if sid && @invocations_by_state[sid]
          @invocations_by_state[sid].delete(invoke_id)
        end
        [actions, delta]
      end

      def cancel_invocations_for_state(state_id)
        actions = []
        delta = {}
        ids = (@invocations_by_state[state_id] || []).dup
        ids.each do |iid|
          rec = @invocations[iid]
          next unless rec && rec[:status] == 'active'
          a, d = finalize_invoke(iid, completed: false)
          actions.concat(a)
          delta.merge!(d)
        end
        [actions, delta]
      end

      # Route a send to a specific child invocation by id
      def route_to_child(invoke_id, name, data, delay)
        rec = @invocations[invoke_id]
        return false unless rec
        ctx = rec[:ctx]
        return false unless ctx
        if delay && delay > 0
          ctx.schedule_internal_event(name, data, delay)
        else
          ctx.trace_step(name: name, data: data)
        end
        true
      end

      # Parent accepts events from a child context
      def enqueue_from_child(name, data, invoke_id)
        @internal_queue << ({ 'name' => name.to_s, 'data' => data, 'invokeid' => invoke_id })
      end

      # Build a child context from an <invoke> map if inline content or src is present
      def build_child_context(inv, iid)
        # Inline content: looks like scjson root
        content = inv['content']
        if content
          root = if content.is_a?(Hash)
                   content
                 elsif content.is_a?(Array)
                   content.find { |x| x.is_a?(Hash) && (x.key?('state') || x.key?('parallel') || x.key?('final')) }
                 else
                   nil
                 end
          if root
            begin
              return DocumentContext.new(root, parent_link: self, child_invoke_id: iid, base_dir: @base_dir)
            rescue StandardError
              return nil
            end
          end
        end
        # External src file reference
        src = inv['src']
        if src && src.is_a?(String)
          path = src
          if @base_dir && !(path.start_with?('/') || path =~ /^[A-Za-z]:\\/)
            path = File.expand_path(File.join(@base_dir, path))
          end
          begin
            if File.file?(path)
              is_xml = File.extname(path).downcase == '.scxml'
              return DocumentContext.from_file(path, xml: is_xml, parent_link: self, child_invoke_id: iid)
            end
          rescue StandardError
            return nil
          end
        end
        nil
      end

      # Record history for parents of exiting states using the previous configuration
      def record_history_for_exits(exit_order, prev_config)
        parents = exit_order.map { |sid| @parent[sid] }.compact.uniq
        parents.each do |pid|
          # Deep history: all leaves under pid in prev_config
          deep = prev_config.select { |leaf| is_ancestor?(pid, leaf) }
          @history_deep[pid] = deep.dup
          # Shallow history: nearest child under pid for each leaf
          shallow = []
          prev_config.each do |leaf|
            next unless is_ancestor?(pid, leaf)
            chain = ancestors(leaf)
            idx = chain.index(pid)
            next unless idx && idx > 0
            near = chain[idx - 1]
            shallow << near if near
          end
          @history_shallow[pid] = shallow.uniq
        end
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
        # Cancel active invocations for this state and run their finalize
        a2, d2 = cancel_invocations_for_state(state_id)
        actions.concat(a2)
        delta.merge!(d2)
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
        # send
        wrap_list(map['send']).each do |sd|
          next unless sd.is_a?(Hash)
          ev_name = sd['event'] || sd['name']
          delay = parse_delay(sd['delay'] || '0s')
          target = sd['target']
          data_payload = nil
          if sd['content']
            data_payload = sd['content']
          end
          if ev_name
            if target.nil? || target == '#_internal' || target == 'internal'
              schedule_internal_event(ev_name.to_s, data_payload, delay)
            elsif target == '#_parent'
              if @parent_link
                @parent_link.enqueue_from_child(ev_name.to_s, data_payload, @child_invoke_id)
              else
                schedule_internal_event('error.communication', { 'detail' => 'no parent for #_parent', 'event' => ev_name.to_s }, 0.0)
              end
            elsif target.to_s.start_with?('#_')
              iid = target.to_s.sub(/^#_/, '')
              unless route_to_child(iid, ev_name.to_s, data_payload, delay)
                schedule_internal_event('error.communication', { 'detail' => 'unknown child', 'target' => target, 'event' => ev_name.to_s }, 0.0)
              end
            else
              # unsupported external targets -> error.communication
              schedule_internal_event('error.communication', { 'detail' => 'unsupported target', 'target' => target, 'event' => ev_name.to_s }, 0.0)
            end
          end
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

      # Timers and scheduling
      def schedule_internal_event(name, data, delay)
        if delay.nil? || delay <= 0
          @internal_queue << ({ 'name' => name, 'data' => data })
        else
          @timers << { time: (@time + delay.to_f), name: name, data: data }
          @timers.sort_by! { |t| t[:time] }
        end
      end

      def advance_time(seconds)
        return if seconds.nil? || seconds.to_f <= 0
        @time += seconds.to_f
        flush_timers
      end

      def flush_timers
        while !@timers.empty? && @timers.first[:time] <= @time
          t = @timers.shift
          @internal_queue << ({ 'name' => t[:name], 'data' => t[:data] })
        end
      end

      def parse_delay(str)
        return 0.0 if str.nil?
        return str if str.is_a?(Numeric)
        s = str.to_s.strip
        return 0.0 if s.empty?
        if (m = s.match(/^([-+]?\d+(?:\.\d+)?)\s*(ms|s)?$/i))
          val = m[1].to_f
          unit = (m[2] || 's').downcase
          return unit == 'ms' ? (val / 1000.0) : val
        end
        0.0
      end

      def parse_event_tokens(str)
        return [] if str.nil?
        return [] unless str.is_a?(String)
        str.split(/\s+/)
      end

      # ---- Completion (done.state.*) ----
      def enqueue_done_events
        done_ids = compute_done_states
        done_ids.each do |sid|
          @internal_queue << ({ 'name' => "done.state.#{sid}", 'data' => nil })
        end
      end

      def compute_done_states
        # Identify composite state completion and parallel completion
        finals = @configuration.select { |sid| @tag_type[sid] == :final }
        done = []
        # State is done if one of its direct 'final' children is active
        @states.each do |sid, node|
          next unless node.is_a?(Hash)
          # only consider composite states
          if node.key?('state') || node.key?('parallel')
            # direct final children ids
            direct_finals = wrap_list(node['final']).map { |f| f.is_a?(Hash) ? f['id'] : nil }.compact.map(&:to_s)
            if !direct_finals.empty? && (finals & direct_finals).any?
              done << sid
              next
            end
            # parallel: all regions have a final descendant
            if node.key?('parallel')
              region_ids = wrap_list(node['parallel']).flat_map { |p| wrap_list(p['state']).map { |s| s['id'] }.compact.map(&:to_s) }
              if !region_ids.empty?
                all_done = region_ids.all? do |rid|
                  finals.any? { |fid| is_ancestor?(rid, fid) }
                end
                done << sid if all_done
              end
            end
          end
        end
        done.uniq
      end

      def index_states(node, parent_id = nil, tag = nil)
        return unless node.is_a?(Hash)
        # Record this node if it looks like a state (has an id)
        sid = node['id']
        if sid
          @states[sid] = node
          @parent[sid] = parent_id if parent_id
          @tag_type[sid] = tag || :state
        end
        # Recurse into known containers
        wrap_list(node['state']).each { |child| index_states(child, sid, :state) }
        wrap_list(node['parallel']).each { |child| index_states(child, sid, :parallel) }
        wrap_list(node['history']).each { |child| index_states(child, sid, :history) }
        wrap_list(node['final']).each { |child| index_states(child, sid, :final) }
      end

      def initial_configuration
        # Prefer explicit initial on root
        tokens = wrap_list(@root['initial']).map(&:to_s)
        leaves = []
        unless tokens.empty?
          tokens.each do |tid|
            leaves.concat(initial_leaves_for_token(tid))
          end
          return leaves.uniq
        end
        # Else first child state id -> expand to leaves
        first_state = wrap_list(@root['state']).find { |s| s.is_a?(Hash) && s['id'] }
        if first_state && first_state['id']
          return initial_leaves_for_token(first_state['id'].to_s)
        end
        []
      end

      def initial_leaves_for_token(token)
        # History tokens fallback to parent's defaults
        if @tag_type[token] == :history
          parent_id = @parent[token]
          return [] unless parent_id
          node = @states[token]
          deep = (node && node['type_value'].to_s.downcase == 'deep')
          if deep
            return initial_leaves_for_id(parent_id)
          else
            parent = @states[parent_id]
            return initial_child_ids_for(parent).flat_map { |cid| initial_leaves_for_id(cid) }
          end
        end
        initial_leaves_for_id(token)
      end
    end
  end
end
