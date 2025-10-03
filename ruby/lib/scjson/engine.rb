# frozen_string_literal: true

# Agent Name: ruby-engine
#
# Part of the scjson project.
# Developed by Softoboros Technology Inc.
# Licensed under the BSD 1-Clause License.

require 'json'
require_relative 'engine/context'

module Scjson
  #
  # Engine interface to emit standardized JSONL execution traces.
  #
  # This is a contract-level stub that preserves the CLI and trace schema
  # while the full runtime is being implemented. It mirrors Python flags and
  # behavior where appropriate, following Ruby idioms.
  #
  module Engine
    module_function

    ##
    # Emit a standardized JSONL trace for the given document and event stream.
    #
    # @param input_path [String] Path to SCXML or SCJSON document.
    # @param events_path [String, nil] Path to JSONL event stream (reads STDIN when nil).
    # @param out_path [String, nil] Destination file for trace (writes STDOUT when nil).
    # @param xml [Boolean] When true, treat the input as SCXML (placeholder for future).
    # @param leaf_only [Boolean] Restrict states to leaves (placeholder; no-op in stub).
    # @param omit_actions [Boolean] Omit actionLog entries.
    # @param omit_delta [Boolean] Omit datamodelDelta entries.
    # @param omit_transitions [Boolean] Omit firedTransitions entries.
    # @param advance_time [Float] Advance engine time before processing events (no-op in stub).
    # @param ordering [String] Ordering policy (tolerant|strict|scion); placeholder in stub.
    # @param max_steps [Integer, nil] Limit processed steps (nil = unlimited).
    # @return [void]
    def trace(input_path:,
              events_path: nil,
              out_path: nil,
              xml: false,
              leaf_only: false,
              omit_actions: false,
              omit_delta: false,
              omit_transitions: false,
              advance_time: 0.0,
              ordering: 'tolerant',
              max_steps: nil,
              strip_step0_noise: false,
              strip_step0_states: false,
              keep_cond: false)
      sink = out_path ? File.open(out_path, 'w', encoding: 'utf-8') : $stdout
      begin
        ctx = DocumentContext.from_file(input_path, xml: xml)
        leaves = leaf_only ? ctx.leaf_state_ids : nil
        # Step 0 snapshot
        init = ctx.trace_init
        if leaf_only && leaves
          %w[configuration enteredStates exitedStates].each do |k|
            init[k] = (init[k] || []).select { |sid| leaves.include?(sid) }
          end
        end
        init['actionLog'] = [] if omit_actions
        init['datamodelDelta'] = {} if omit_delta
        init['firedTransitions'] = [] if omit_transitions
        if strip_step0_noise
          init['datamodelDelta'] = {}
          init['firedTransitions'] = []
        end
        if strip_step0_states
          init['enteredStates'] = []
          init['exitedStates'] = []
        end
        sink.write(JSON.generate({ step: 0 }.merge(init)) + "\n")

        # Stream of events: from file or STDIN
        stream = events_path ? File.open(events_path, 'r', encoding: 'utf-8') : $stdin
        # Apply global advance_time before first event if provided
        if advance_time && advance_time.to_f > 0
          begin
            ctx.advance_time(advance_time.to_f)
          rescue StandardError
            # ignore
          end
        end
        step_no = 1
        stream.each_line do |line|
          line = line.strip
          next if line.empty?
          begin
            msg = JSON.parse(line)
          rescue StandardError
            next
          end
          # Control token: advance_time -> skip trace emission, but flush timers
          if msg.is_a?(Hash) && msg.key?('advance_time')
            begin
              adv = msg['advance_time']
              ctx.advance_time(adv.to_f)
            rescue StandardError
              # ignore malformed
            end
            next
          end
          break if max_steps && step_no > max_steps
          evt_name = (msg.is_a?(Hash) && (msg['event'] || msg['name']))
          next unless evt_name
          evt_data = msg.is_a?(Hash) ? msg['data'] : nil
          rec = ctx.trace_step(name: evt_name.to_s, data: evt_data)
          if leaf_only && leaves
            %w[configuration enteredStates exitedStates].each do |k|
              rec[k] = (rec[k] || []).select { |sid| leaves.include?(sid) }
            end
          end
          rec['actionLog'] = [] if omit_actions
          # sort datamodelDelta keys for deterministic output
          unless omit_delta
            if rec['datamodelDelta'].is_a?(Hash)
              dm = rec['datamodelDelta']
              rec['datamodelDelta'] = dm.keys.sort.each_with_object({}) { |k, h| h[k] = dm[k] }
            end
          else
            rec['datamodelDelta'] = {}
          end
          # scrub cond in firedTransitions unless requested
          unless keep_cond
            if rec['firedTransitions'].is_a?(Array)
              rec['firedTransitions'] = rec['firedTransitions'].map do |ft|
                if ft.is_a?(Hash)
                  ft['cond'] = nil
                end
                ft
              end
            end
          end
          rec['firedTransitions'] = [] if omit_transitions
          sink.write(JSON.generate({ step: step_no }.merge(rec)) + "\n")
          step_no += 1
        end
      ensure
        sink.close if sink && sink != $stdout
      end
    end
  end
end
