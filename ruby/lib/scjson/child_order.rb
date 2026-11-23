# frozen_string_literal: true

# Capture and replay authored SCXML child sequences alongside grouped SCJSON fields.
# Agent Name: scjson-converter-parity
# Part of the scjson project. Licensed under the BSD 1-Clause License.

module Scjson
  module ChildOrder
    ACTIONS = %w[raise if foreach send script assign log cancel elseif else].freeze
    ACTION_FIELDS = { 'if' => 'if_value', 'else' => 'else_value', 'raise' => 'raise_value' }.freeze
    EXECUTABLE = %w[transition onentry onexit finalize foreach if].freeze
    STRUCTURAL = %w[state parallel final].freeze
    FIELDS = %w[execution_order state_order region_order].freeze
    module_function

    def spec(owner)
      return ['execution_order', ACTIONS] if EXECUTABLE.include?(owner)
      return ['state_order', STRUCTURAL] if %w[scxml state].include?(owner)
      return ['region_order', %w[state parallel]] if owner == 'parallel'
    end

    def extension_kind(qname)
      raise ArgumentError, 'ordered extension requires a qname' unless qname.is_a?(String) && !qname.empty?
      qname.start_with?('{') ? qname : "{}#{qname}"
    end

    def check_markers(owner, order)
      saw_else = false
      order.each do |kind|
        next unless %w[elseif else].include?(kind)
        raise ArgumentError, 'invalid conditional marker sequence' if owner != 'if' || saw_else
        saw_else = kind == 'else'
      end
    end

    # Return ordered children for each group of XML slots owned by this parent.
    def slots(owner, map)
      field, kinds = spec(owner)
      misplaced = (map.keys & FIELDS) - [field]
      raise ArgumentError, "#{misplaced.first} is invalid on #{owner}" unless misplaced.empty?
      return {} unless field
      explicit = map.key?(field)
      if !explicit && field == 'execution_order'
        %w[elseif else].each do |kind|
          field_name = ACTION_FIELDS.fetch(kind, kind)
          next unless map.key?(field_name)
          value = map[field_name]
          check_markers(owner, [kind] * (value.is_a?(Array) ? value.length : 1))
        end
        return {}
      end

      groups = {}
      slots = {}
      kinds.each do |kind|
        key = ACTION_FIELDS.fetch(kind, kind)
        next unless map.key?(key)
        if explicit && field != 'execution_order' && !map[key].is_a?(Array)
          raise ArgumentError, "#{field} requires child arrays"
        end
        values = map[key].is_a?(Array) ? map[key] : [map[key]]
        raise ArgumentError, "#{field} requires child objects" unless values.all? { |v| v.is_a?(Hash) }
        groups[kind] = values.map { |value| [kind, value] }
        slots[key] = values.length
      end
      if field == 'execution_order' && map.key?('other_element')
        extensions = map['other_element']
        extensions = [extensions] unless extensions.is_a?(Array)
        extensions.each do |child|
          raise ArgumentError, 'expected an extension object' unless child.is_a?(Hash)
          kind = extension_kind(child['qname'])
          (groups[kind] ||= []) << [child['qname'], child]
        end
        slots['other_element'] = extensions.length
      end
      order = explicit ? map[field] : groups.flat_map { |kind, values| [kind] * values.length }
      raise ArgumentError, "#{field} must be an array" unless order.is_a?(Array)
      check_markers(owner, order) if field == 'execution_order'
      indices = Hash.new(0)
      sequence = order.map do |kind|
        index = indices[kind]
        indices[kind] += 1
        groups.fetch(kind, [])[index] || (raise ArgumentError, "#{field} references an absent child: #{kind}")
      end
      raise ArgumentError, "#{field} omits a child" unless sequence.length == slots.values.sum

      offset = 0
      map.keys.each_with_object({}) do |key, result|
        next unless slots.key?(key)
        result[key] = sequence.slice(offset, slots[key])
        offset += slots[key]
      end
    end
  end
end
