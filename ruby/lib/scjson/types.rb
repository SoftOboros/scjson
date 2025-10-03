# frozen_string_literal: true
#
# Agent Name: ruby-props
#
# Part of the scjson project.
# Developed by Softoboros Technology Inc.
# Licensed under the BSD 1-Clause License.

require 'json'

# Canonical Ruby representations of the scjson schema.
module Scjson
  module Types
    # The assign type that allows for precise manipulation of the datamodel     location.      Types are:     replacechildren (default),     firstchild, lastchild,     previoussibling, nextsibling,     replace, delete,     addattribute
    module AssignTypeDatatypeProps
      REPLACECHILDREN = 'replacechildren'.freeze
      FIRSTCHILD = 'firstchild'.freeze
      LASTCHILD = 'lastchild'.freeze
      PREVIOUSSIBLING = 'previoussibling'.freeze
      NEXTSIBLING = 'nextsibling'.freeze
      REPLACE = 'replace'.freeze
      DELETE = 'delete'.freeze
      ADDATTRIBUTE = 'addattribute'.freeze
      DEFAULT = REPLACECHILDREN
      VALUES = [REPLACECHILDREN, FIRSTCHILD, LASTCHILD, PREVIOUSSIBLING, NEXTSIBLING, REPLACE, DELETE, ADDATTRIBUTE].freeze

      module_function

      # @return [Array<String>] All legal enumeration values.
      def values
        VALUES
      end

      # @return [String] Schema-defined default enumeration value.
      def default
        DEFAULT
      end

      # Coerce arbitrary input into a valid enumeration value.
      # @param value [Object, nil] Raw value to coerce.
      # @param allow_nil [Boolean] When true, allow nil to pass-through.
      # @return [String, nil]
      def coerce(value, allow_nil: false)
        return nil if allow_nil && value.nil?
        return DEFAULT if value.nil?

        candidate = value.to_s
        return candidate if VALUES.include?(candidate)

        raise ArgumentError, "Unsupported value '#{value}' for AssignTypeDatatypeProps"
      end
    end

    # The binding type in use for the SCXML document.
    module BindingDatatypeProps
      EARLY = 'early'.freeze
      LATE = 'late'.freeze
      DEFAULT = EARLY
      VALUES = [EARLY, LATE].freeze

      module_function

      # @return [Array<String>] All legal enumeration values.
      def values
        VALUES
      end

      # @return [String] Schema-defined default enumeration value.
      def default
        DEFAULT
      end

      # Coerce arbitrary input into a valid enumeration value.
      # @param value [Object, nil] Raw value to coerce.
      # @param allow_nil [Boolean] When true, allow nil to pass-through.
      # @return [String, nil]
      def coerce(value, allow_nil: false)
        return nil if allow_nil && value.nil?
        return DEFAULT if value.nil?

        candidate = value.to_s
        return candidate if VALUES.include?(candidate)

        raise ArgumentError, "Unsupported value '#{value}' for BindingDatatypeProps"
      end
    end

    # Boolean: true or false only
    module BooleanDatatypeProps
      TRUE = 'true'.freeze
      FALSE = 'false'.freeze
      DEFAULT = TRUE
      VALUES = [TRUE, FALSE].freeze

      module_function

      # @return [Array<String>] All legal enumeration values.
      def values
        VALUES
      end

      # @return [String] Schema-defined default enumeration value.
      def default
        DEFAULT
      end

      # Coerce arbitrary input into a valid enumeration value.
      # @param value [Object, nil] Raw value to coerce.
      # @param allow_nil [Boolean] When true, allow nil to pass-through.
      # @return [String, nil]
      def coerce(value, allow_nil: false)
        return nil if allow_nil && value.nil?
        return DEFAULT if value.nil?

        candidate = value.to_s
        return candidate if VALUES.include?(candidate)

        raise ArgumentError, "Unsupported value '#{value}' for BooleanDatatypeProps"
      end
    end

    # Describes the processor execution mode for this document, being either "lax" or     "strict".
    module ExmodeDatatypeProps
      LAX = 'lax'.freeze
      STRICT = 'strict'.freeze
      DEFAULT = LAX
      VALUES = [LAX, STRICT].freeze

      module_function

      # @return [Array<String>] All legal enumeration values.
      def values
        VALUES
      end

      # @return [String] Schema-defined default enumeration value.
      def default
        DEFAULT
      end

      # Coerce arbitrary input into a valid enumeration value.
      # @param value [Object, nil] Raw value to coerce.
      # @param allow_nil [Boolean] When true, allow nil to pass-through.
      # @return [String, nil]
      def coerce(value, allow_nil: false)
        return nil if allow_nil && value.nil?
        return DEFAULT if value.nil?

        candidate = value.to_s
        return candidate if VALUES.include?(candidate)

        raise ArgumentError, "Unsupported value '#{value}' for ExmodeDatatypeProps"
      end
    end

    # type of `<history>` state: `shallow` or `deep`.
    module HistoryTypeDatatypeProps
      SHALLOW = 'shallow'.freeze
      DEEP = 'deep'.freeze
      DEFAULT = SHALLOW
      VALUES = [SHALLOW, DEEP].freeze

      module_function

      # @return [Array<String>] All legal enumeration values.
      def values
        VALUES
      end

      # @return [String] Schema-defined default enumeration value.
      def default
        DEFAULT
      end

      # Coerce arbitrary input into a valid enumeration value.
      # @param value [Object, nil] Raw value to coerce.
      # @param allow_nil [Boolean] When true, allow nil to pass-through.
      # @return [String, nil]
      def coerce(value, allow_nil: false)
        return nil if allow_nil && value.nil?
        return DEFAULT if value.nil?

        candidate = value.to_s
        return candidate if VALUES.include?(candidate)

        raise ArgumentError, "Unsupported value '#{value}' for HistoryTypeDatatypeProps"
      end
    end

    # The type of the transition i.e. internal or external.
    module TransitionTypeDatatypeProps
      INTERNAL = 'internal'.freeze
      EXTERNAL = 'external'.freeze
      DEFAULT = INTERNAL
      VALUES = [INTERNAL, EXTERNAL].freeze

      module_function

      # @return [Array<String>] All legal enumeration values.
      def values
        VALUES
      end

      # @return [String] Schema-defined default enumeration value.
      def default
        DEFAULT
      end

      # Coerce arbitrary input into a valid enumeration value.
      # @param value [Object, nil] Raw value to coerce.
      # @param allow_nil [Boolean] When true, allow nil to pass-through.
      # @return [String, nil]
      def coerce(value, allow_nil: false)
        return nil if allow_nil && value.nil?
        return DEFAULT if value.nil?

        candidate = value.to_s
        return candidate if VALUES.include?(candidate)

        raise ArgumentError, "Unsupported value '#{value}' for TransitionTypeDatatypeProps"
      end
    end


    # update a datamodel location with an expression or value.
    class AssignProps
      attr_accessor :location, :expr, :type_value, :attr, :other_attributes, :content
      # Instantiate a new AssignProps object.
      # @param kwargs [Hash] Optional keyword overrides.
      def initialize(**kwargs)
        @location = kwargs.fetch(:location, '')
        @expr = kwargs.fetch(:expr, nil)
        @type_value = kwargs.fetch(:type_value, AssignTypeDatatypeProps::REPLACECHILDREN)
        @attr = kwargs.fetch(:attr, nil)
        @other_attributes = kwargs.fetch(:other_attributes, {})
        @content = kwargs.fetch(:content, [])
      end

      # Build an instance from a Hash representation.
      # @param data [Hash] Canonical hash representation.
      # @return [AssignProps]
      def self.from_hash(data)
        raise ArgumentError, 'Expected Hash' unless data.is_a?(Hash)

        normalized = data.transform_keys(&:to_s)
        kwargs = {}
        kwargs[:location] = normalized.fetch('location', '')
        kwargs[:expr] = normalized.fetch('expr', nil)
        kwargs[:type_value] = AssignTypeDatatypeProps.coerce(normalized.fetch('type_value', AssignTypeDatatypeProps::REPLACECHILDREN))
        kwargs[:attr] = normalized.fetch('attr', nil)
        kwargs[:other_attributes] = normalized.fetch('other_attributes', {})
        kwargs[:content] = Array(normalized.fetch('content', []))
        new(**kwargs)
      end

      # Deserialize an instance from a JSON payload.
      # @param json [String] JSON document to decode.
      # @return [AssignProps]
      def self.from_json(json)
        parsed = JSON.parse(json)
        from_hash(parsed)
      end

      # Convert the object to a Hash suitable for JSON serialization.
      # @return [Hash]
      def to_hash
        {
          'location' => @location,
          'expr' => @expr,
          'type_value' => @type_value,
          'attr' => @attr,
          'other_attributes' => @other_attributes,
          'content' => @content
        }
      end

      # Serialize the object to JSON.
      # @param opts [Array] JSON generation options.
      # @return [String]
      def to_json(*opts)
        JSON.generate(to_hash, *opts)
      end
    end

    # Collection alias for AssignProps values.
    AssignArray = ::Array

    # cancel a pending `<send>` operation.
    class CancelProps
      attr_accessor :other_element, :sendid, :sendidexpr, :other_attributes
      # Instantiate a new CancelProps object.
      # @param kwargs [Hash] Optional keyword overrides.
      def initialize(**kwargs)
        @other_element = kwargs.fetch(:other_element, [])
        @sendid = kwargs.fetch(:sendid, nil)
        @sendidexpr = kwargs.fetch(:sendidexpr, nil)
        @other_attributes = kwargs.fetch(:other_attributes, {})
      end

      # Build an instance from a Hash representation.
      # @param data [Hash] Canonical hash representation.
      # @return [CancelProps]
      def self.from_hash(data)
        raise ArgumentError, 'Expected Hash' unless data.is_a?(Hash)

        normalized = data.transform_keys(&:to_s)
        kwargs = {}
        kwargs[:other_element] = Array(normalized.fetch('other_element', []))
        kwargs[:sendid] = normalized.fetch('sendid', nil)
        kwargs[:sendidexpr] = normalized.fetch('sendidexpr', nil)
        kwargs[:other_attributes] = normalized.fetch('other_attributes', {})
        new(**kwargs)
      end

      # Deserialize an instance from a JSON payload.
      # @param json [String] JSON document to decode.
      # @return [CancelProps]
      def self.from_json(json)
        parsed = JSON.parse(json)
        from_hash(parsed)
      end

      # Convert the object to a Hash suitable for JSON serialization.
      # @return [Hash]
      def to_hash
        {
          'other_element' => @other_element,
          'sendid' => @sendid,
          'sendidexpr' => @sendidexpr,
          'other_attributes' => @other_attributes
        }
      end

      # Serialize the object to JSON.
      # @param opts [Array] JSON generation options.
      # @return [String]
      def to_json(*opts)
        JSON.generate(to_hash, *opts)
      end
    end

    # Collection alias for CancelProps values.
    CancelArray = ::Array

    # Structured type for scjson elements.
    class ContentProps
      attr_accessor :content, :expr, :other_attributes
      # Instantiate a new ContentProps object.
      # @param kwargs [Hash] Optional keyword overrides.
      def initialize(**kwargs)
        @content = kwargs.fetch(:content, nil)
        @expr = kwargs.fetch(:expr, nil)
        @other_attributes = kwargs.fetch(:other_attributes, {})
      end

      # Build an instance from a Hash representation.
      # @param data [Hash] Canonical hash representation.
      # @return [ContentProps]
      def self.from_hash(data)
        raise ArgumentError, 'Expected Hash' unless data.is_a?(Hash)

        normalized = data.transform_keys(&:to_s)
        kwargs = {}
        kwargs[:content] = begin
          value = normalized.fetch('content', nil)
          value.nil? ? nil : Array(value).map { |item| ScxmlProps.from_hash(item) }
        end
        kwargs[:expr] = normalized.fetch('expr', nil)
        kwargs[:other_attributes] = normalized.fetch('other_attributes', {})
        new(**kwargs)
      end

      # Deserialize an instance from a JSON payload.
      # @param json [String] JSON document to decode.
      # @return [ContentProps]
      def self.from_json(json)
        parsed = JSON.parse(json)
        from_hash(parsed)
      end

      # Convert the object to a Hash suitable for JSON serialization.
      # @return [Hash]
      def to_hash
        {
          'content' => (@content || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'expr' => @expr,
          'other_attributes' => @other_attributes
        }
      end

      # Serialize the object to JSON.
      # @param opts [Array] JSON generation options.
      # @return [String]
      def to_json(*opts)
        JSON.generate(to_hash, *opts)
      end
    end

    # Collection alias for ContentProps values.
    ContentArray = ::Array

    # represents a single datamodel variable.
    class DataProps
      attr_accessor :id, :src, :expr, :other_attributes, :content
      # Instantiate a new DataProps object.
      # @param kwargs [Hash] Optional keyword overrides.
      def initialize(**kwargs)
        @id = kwargs.fetch(:id, '')
        @src = kwargs.fetch(:src, nil)
        @expr = kwargs.fetch(:expr, nil)
        @other_attributes = kwargs.fetch(:other_attributes, {})
        @content = kwargs.fetch(:content, [])
      end

      # Build an instance from a Hash representation.
      # @param data [Hash] Canonical hash representation.
      # @return [DataProps]
      def self.from_hash(data)
        raise ArgumentError, 'Expected Hash' unless data.is_a?(Hash)

        normalized = data.transform_keys(&:to_s)
        kwargs = {}
        kwargs[:id] = normalized.fetch('id', '')
        kwargs[:src] = normalized.fetch('src', nil)
        kwargs[:expr] = normalized.fetch('expr', nil)
        kwargs[:other_attributes] = normalized.fetch('other_attributes', {})
        kwargs[:content] = Array(normalized.fetch('content', []))
        new(**kwargs)
      end

      # Deserialize an instance from a JSON payload.
      # @param json [String] JSON document to decode.
      # @return [DataProps]
      def self.from_json(json)
        parsed = JSON.parse(json)
        from_hash(parsed)
      end

      # Convert the object to a Hash suitable for JSON serialization.
      # @return [Hash]
      def to_hash
        {
          'id' => @id,
          'src' => @src,
          'expr' => @expr,
          'other_attributes' => @other_attributes,
          'content' => @content
        }
      end

      # Serialize the object to JSON.
      # @param opts [Array] JSON generation options.
      # @return [String]
      def to_json(*opts)
        JSON.generate(to_hash, *opts)
      end
    end

    # Collection alias for DataProps values.
    DataArray = ::Array

    # container for one or more `<data>` elements.
    class DatamodelProps
      attr_accessor :data, :other_element, :other_attributes
      # Instantiate a new DatamodelProps object.
      # @param kwargs [Hash] Optional keyword overrides.
      def initialize(**kwargs)
        @data = kwargs.fetch(:data, [])
        @other_element = kwargs.fetch(:other_element, [])
        @other_attributes = kwargs.fetch(:other_attributes, {})
      end

      # Build an instance from a Hash representation.
      # @param data [Hash] Canonical hash representation.
      # @return [DatamodelProps]
      def self.from_hash(data)
        raise ArgumentError, 'Expected Hash' unless data.is_a?(Hash)

        normalized = data.transform_keys(&:to_s)
        kwargs = {}
        kwargs[:data] = Array(normalized.fetch('data', [])).map { |item| DataProps.from_hash(item) }
        kwargs[:other_element] = Array(normalized.fetch('other_element', []))
        kwargs[:other_attributes] = normalized.fetch('other_attributes', {})
        new(**kwargs)
      end

      # Deserialize an instance from a JSON payload.
      # @param json [String] JSON document to decode.
      # @return [DatamodelProps]
      def self.from_json(json)
        parsed = JSON.parse(json)
        from_hash(parsed)
      end

      # Convert the object to a Hash suitable for JSON serialization.
      # @return [Hash]
      def to_hash
        {
          'data' => (@data || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'other_element' => @other_element,
          'other_attributes' => @other_attributes
        }
      end

      # Serialize the object to JSON.
      # @param opts [Array] JSON generation options.
      # @return [String]
      def to_json(*opts)
        JSON.generate(to_hash, *opts)
      end
    end

    # Collection alias for DatamodelProps values.
    DatamodelArray = ::Array

    # Structured type for scjson elements.
    class DonedataProps
      attr_accessor :content, :param, :other_attributes
      # Instantiate a new DonedataProps object.
      # @param kwargs [Hash] Optional keyword overrides.
      def initialize(**kwargs)
        @content = kwargs.fetch(:content, nil)
        @param = kwargs.fetch(:param, [])
        @other_attributes = kwargs.fetch(:other_attributes, {})
      end

      # Build an instance from a Hash representation.
      # @param data [Hash] Canonical hash representation.
      # @return [DonedataProps]
      def self.from_hash(data)
        raise ArgumentError, 'Expected Hash' unless data.is_a?(Hash)

        normalized = data.transform_keys(&:to_s)
        kwargs = {}
        kwargs[:content] = normalized.key?('content') && normalized['content'] ? ContentProps.from_hash(normalized['content']) : nil
        kwargs[:param] = Array(normalized.fetch('param', [])).map { |item| ParamProps.from_hash(item) }
        kwargs[:other_attributes] = normalized.fetch('other_attributes', {})
        new(**kwargs)
      end

      # Deserialize an instance from a JSON payload.
      # @param json [String] JSON document to decode.
      # @return [DonedataProps]
      def self.from_json(json)
        parsed = JSON.parse(json)
        from_hash(parsed)
      end

      # Convert the object to a Hash suitable for JSON serialization.
      # @return [Hash]
      def to_hash
        {
          'content' => @content&.to_hash,
          'param' => (@param || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'other_attributes' => @other_attributes
        }
      end

      # Serialize the object to JSON.
      # @param opts [Array] JSON generation options.
      # @return [String]
      def to_json(*opts)
        JSON.generate(to_hash, *opts)
      end
    end

    # Collection alias for DonedataProps values.
    DonedataArray = ::Array

    # fallback branch for `<if>` conditions.
    class ElseProps
      attr_accessor :other_attributes
      # Instantiate a new ElseProps object.
      # @param kwargs [Hash] Optional keyword overrides.
      def initialize(**kwargs)
        @other_attributes = kwargs.fetch(:other_attributes, {})
      end

      # Build an instance from a Hash representation.
      # @param data [Hash] Canonical hash representation.
      # @return [ElseProps]
      def self.from_hash(data)
        raise ArgumentError, 'Expected Hash' unless data.is_a?(Hash)

        normalized = data.transform_keys(&:to_s)
        kwargs = {}
        kwargs[:other_attributes] = normalized.fetch('other_attributes', {})
        new(**kwargs)
      end

      # Deserialize an instance from a JSON payload.
      # @param json [String] JSON document to decode.
      # @return [ElseProps]
      def self.from_json(json)
        parsed = JSON.parse(json)
        from_hash(parsed)
      end

      # Convert the object to a Hash suitable for JSON serialization.
      # @return [Hash]
      def to_hash
        {
          'other_attributes' => @other_attributes
        }
      end

      # Serialize the object to JSON.
      # @param opts [Array] JSON generation options.
      # @return [String]
      def to_json(*opts)
        JSON.generate(to_hash, *opts)
      end
    end

    # conditional branch following an `<if>`.
    class ElseifProps
      attr_accessor :cond, :other_attributes
      # Instantiate a new ElseifProps object.
      # @param kwargs [Hash] Optional keyword overrides.
      def initialize(**kwargs)
        @cond = kwargs.fetch(:cond, '')
        @other_attributes = kwargs.fetch(:other_attributes, {})
      end

      # Build an instance from a Hash representation.
      # @param data [Hash] Canonical hash representation.
      # @return [ElseifProps]
      def self.from_hash(data)
        raise ArgumentError, 'Expected Hash' unless data.is_a?(Hash)

        normalized = data.transform_keys(&:to_s)
        kwargs = {}
        kwargs[:cond] = normalized.fetch('cond', '')
        kwargs[:other_attributes] = normalized.fetch('other_attributes', {})
        new(**kwargs)
      end

      # Deserialize an instance from a JSON payload.
      # @param json [String] JSON document to decode.
      # @return [ElseifProps]
      def self.from_json(json)
        parsed = JSON.parse(json)
        from_hash(parsed)
      end

      # Convert the object to a Hash suitable for JSON serialization.
      # @return [Hash]
      def to_hash
        {
          'cond' => @cond,
          'other_attributes' => @other_attributes
        }
      end

      # Serialize the object to JSON.
      # @param opts [Array] JSON generation options.
      # @return [String]
      def to_json(*opts)
        JSON.generate(to_hash, *opts)
      end
    end

    # Structured type for scjson elements.
    class FinalProps
      attr_accessor :onentry, :onexit, :donedata, :other_element, :id, :other_attributes
      # Instantiate a new FinalProps object.
      # @param kwargs [Hash] Optional keyword overrides.
      def initialize(**kwargs)
        @onentry = kwargs.fetch(:onentry, [])
        @onexit = kwargs.fetch(:onexit, [])
        @donedata = kwargs.fetch(:donedata, [])
        @other_element = kwargs.fetch(:other_element, [])
        @id = kwargs.fetch(:id, nil)
        @other_attributes = kwargs.fetch(:other_attributes, {})
      end

      # Build an instance from a Hash representation.
      # @param data [Hash] Canonical hash representation.
      # @return [FinalProps]
      def self.from_hash(data)
        raise ArgumentError, 'Expected Hash' unless data.is_a?(Hash)

        normalized = data.transform_keys(&:to_s)
        kwargs = {}
        kwargs[:onentry] = Array(normalized.fetch('onentry', [])).map { |item| OnentryProps.from_hash(item) }
        kwargs[:onexit] = Array(normalized.fetch('onexit', [])).map { |item| OnexitProps.from_hash(item) }
        kwargs[:donedata] = Array(normalized.fetch('donedata', [])).map { |item| DonedataProps.from_hash(item) }
        kwargs[:other_element] = Array(normalized.fetch('other_element', []))
        kwargs[:id] = normalized.fetch('id', nil)
        kwargs[:other_attributes] = normalized.fetch('other_attributes', {})
        new(**kwargs)
      end

      # Deserialize an instance from a JSON payload.
      # @param json [String] JSON document to decode.
      # @return [FinalProps]
      def self.from_json(json)
        parsed = JSON.parse(json)
        from_hash(parsed)
      end

      # Convert the object to a Hash suitable for JSON serialization.
      # @return [Hash]
      def to_hash
        {
          'onentry' => (@onentry || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'onexit' => (@onexit || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'donedata' => (@donedata || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'other_element' => @other_element,
          'id' => @id,
          'other_attributes' => @other_attributes
        }
      end

      # Serialize the object to JSON.
      # @param opts [Array] JSON generation options.
      # @return [String]
      def to_json(*opts)
        JSON.generate(to_hash, *opts)
      end
    end

    # Collection alias for FinalProps values.
    FinalArray = ::Array

    # Structured type for scjson elements.
    class FinalizeProps
      attr_accessor :other_element, :raise_value, :if_value, :foreach, :send, :script, :assign, :log, :cancel, :other_attributes
      # Instantiate a new FinalizeProps object.
      # @param kwargs [Hash] Optional keyword overrides.
      def initialize(**kwargs)
        @other_element = kwargs.fetch(:other_element, [])
        @raise_value = kwargs.fetch(:raise_value, [])
        @if_value = kwargs.fetch(:if_value, [])
        @foreach = kwargs.fetch(:foreach, [])
        @send = kwargs.fetch(:send, [])
        @script = kwargs.fetch(:script, [])
        @assign = kwargs.fetch(:assign, [])
        @log = kwargs.fetch(:log, [])
        @cancel = kwargs.fetch(:cancel, [])
        @other_attributes = kwargs.fetch(:other_attributes, {})
      end

      # Build an instance from a Hash representation.
      # @param data [Hash] Canonical hash representation.
      # @return [FinalizeProps]
      def self.from_hash(data)
        raise ArgumentError, 'Expected Hash' unless data.is_a?(Hash)

        normalized = data.transform_keys(&:to_s)
        kwargs = {}
        kwargs[:other_element] = Array(normalized.fetch('other_element', []))
        kwargs[:raise_value] = Array(normalized.fetch('raise_value', [])).map { |item| RaiseProps.from_hash(item) }
        kwargs[:if_value] = Array(normalized.fetch('if_value', [])).map { |item| IfProps.from_hash(item) }
        kwargs[:foreach] = Array(normalized.fetch('foreach', [])).map { |item| ForeachProps.from_hash(item) }
        kwargs[:send] = Array(normalized.fetch('send', [])).map { |item| SendProps.from_hash(item) }
        kwargs[:script] = Array(normalized.fetch('script', [])).map { |item| ScriptProps.from_hash(item) }
        kwargs[:assign] = Array(normalized.fetch('assign', [])).map { |item| AssignProps.from_hash(item) }
        kwargs[:log] = Array(normalized.fetch('log', [])).map { |item| LogProps.from_hash(item) }
        kwargs[:cancel] = Array(normalized.fetch('cancel', [])).map { |item| CancelProps.from_hash(item) }
        kwargs[:other_attributes] = normalized.fetch('other_attributes', {})
        new(**kwargs)
      end

      # Deserialize an instance from a JSON payload.
      # @param json [String] JSON document to decode.
      # @return [FinalizeProps]
      def self.from_json(json)
        parsed = JSON.parse(json)
        from_hash(parsed)
      end

      # Convert the object to a Hash suitable for JSON serialization.
      # @return [Hash]
      def to_hash
        {
          'other_element' => @other_element,
          'raise_value' => (@raise_value || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'if_value' => (@if_value || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'foreach' => (@foreach || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'send' => (@send || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'script' => (@script || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'assign' => (@assign || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'log' => (@log || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'cancel' => (@cancel || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'other_attributes' => @other_attributes
        }
      end

      # Serialize the object to JSON.
      # @param opts [Array] JSON generation options.
      # @return [String]
      def to_json(*opts)
        JSON.generate(to_hash, *opts)
      end
    end

    # Collection alias for FinalizeProps values.
    FinalizeArray = ::Array

    # Structured type for scjson elements.
    class ForeachProps
      attr_accessor :other_element, :raise_value, :if_value, :foreach, :send, :script, :assign, :log, :cancel, :array, :item, :index, :other_attributes
      # Instantiate a new ForeachProps object.
      # @param kwargs [Hash] Optional keyword overrides.
      def initialize(**kwargs)
        @other_element = kwargs.fetch(:other_element, [])
        @raise_value = kwargs.fetch(:raise_value, [])
        @if_value = kwargs.fetch(:if_value, [])
        @foreach = kwargs.fetch(:foreach, [])
        @send = kwargs.fetch(:send, [])
        @script = kwargs.fetch(:script, [])
        @assign = kwargs.fetch(:assign, [])
        @log = kwargs.fetch(:log, [])
        @cancel = kwargs.fetch(:cancel, [])
        @array = kwargs.fetch(:array, '')
        @item = kwargs.fetch(:item, '')
        @index = kwargs.fetch(:index, nil)
        @other_attributes = kwargs.fetch(:other_attributes, {})
      end

      # Build an instance from a Hash representation.
      # @param data [Hash] Canonical hash representation.
      # @return [ForeachProps]
      def self.from_hash(data)
        raise ArgumentError, 'Expected Hash' unless data.is_a?(Hash)

        normalized = data.transform_keys(&:to_s)
        kwargs = {}
        kwargs[:other_element] = Array(normalized.fetch('other_element', []))
        kwargs[:raise_value] = Array(normalized.fetch('raise_value', [])).map { |item| RaiseProps.from_hash(item) }
        kwargs[:if_value] = Array(normalized.fetch('if_value', [])).map { |item| IfProps.from_hash(item) }
        kwargs[:foreach] = Array(normalized.fetch('foreach', [])).map { |item| ForeachProps.from_hash(item) }
        kwargs[:send] = Array(normalized.fetch('send', [])).map { |item| SendProps.from_hash(item) }
        kwargs[:script] = Array(normalized.fetch('script', [])).map { |item| ScriptProps.from_hash(item) }
        kwargs[:assign] = Array(normalized.fetch('assign', [])).map { |item| AssignProps.from_hash(item) }
        kwargs[:log] = Array(normalized.fetch('log', [])).map { |item| LogProps.from_hash(item) }
        kwargs[:cancel] = Array(normalized.fetch('cancel', [])).map { |item| CancelProps.from_hash(item) }
        kwargs[:array] = normalized.fetch('array', '')
        kwargs[:item] = normalized.fetch('item', '')
        kwargs[:index] = normalized.fetch('index', nil)
        kwargs[:other_attributes] = normalized.fetch('other_attributes', {})
        new(**kwargs)
      end

      # Deserialize an instance from a JSON payload.
      # @param json [String] JSON document to decode.
      # @return [ForeachProps]
      def self.from_json(json)
        parsed = JSON.parse(json)
        from_hash(parsed)
      end

      # Convert the object to a Hash suitable for JSON serialization.
      # @return [Hash]
      def to_hash
        {
          'other_element' => @other_element,
          'raise_value' => (@raise_value || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'if_value' => (@if_value || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'foreach' => (@foreach || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'send' => (@send || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'script' => (@script || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'assign' => (@assign || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'log' => (@log || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'cancel' => (@cancel || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'array' => @array,
          'item' => @item,
          'index' => @index,
          'other_attributes' => @other_attributes
        }
      end

      # Serialize the object to JSON.
      # @param opts [Array] JSON generation options.
      # @return [String]
      def to_json(*opts)
        JSON.generate(to_hash, *opts)
      end
    end

    # Collection alias for ForeachProps values.
    ForeachArray = ::Array

    # Structured type for scjson elements.
    class HistoryProps
      attr_accessor :other_element, :transition, :id, :type_value, :other_attributes
      # Instantiate a new HistoryProps object.
      # @param kwargs [Hash] Optional keyword overrides.
      def initialize(**kwargs)
        @other_element = kwargs.fetch(:other_element, [])
        @transition = kwargs.fetch(:transition, TransitionProps.new)
        @id = kwargs.fetch(:id, nil)
        @type_value = kwargs.fetch(:type_value, nil)
        @other_attributes = kwargs.fetch(:other_attributes, {})
      end

      # Build an instance from a Hash representation.
      # @param data [Hash] Canonical hash representation.
      # @return [HistoryProps]
      def self.from_hash(data)
        raise ArgumentError, 'Expected Hash' unless data.is_a?(Hash)

        normalized = data.transform_keys(&:to_s)
        kwargs = {}
        kwargs[:other_element] = Array(normalized.fetch('other_element', []))
        kwargs[:transition] = normalized.key?('transition') && normalized['transition'] ? TransitionProps.from_hash(normalized['transition']) : TransitionProps.new
        kwargs[:id] = normalized.fetch('id', nil)
        kwargs[:type_value] = normalized.key?('type_value') ? HistoryTypeDatatypeProps.coerce(normalized['type_value'], allow_nil: true) : nil
        kwargs[:other_attributes] = normalized.fetch('other_attributes', {})
        new(**kwargs)
      end

      # Deserialize an instance from a JSON payload.
      # @param json [String] JSON document to decode.
      # @return [HistoryProps]
      def self.from_json(json)
        parsed = JSON.parse(json)
        from_hash(parsed)
      end

      # Convert the object to a Hash suitable for JSON serialization.
      # @return [Hash]
      def to_hash
        {
          'other_element' => @other_element,
          'transition' => @transition&.to_hash,
          'id' => @id,
          'type_value' => @type_value,
          'other_attributes' => @other_attributes
        }
      end

      # Serialize the object to JSON.
      # @param opts [Array] JSON generation options.
      # @return [String]
      def to_json(*opts)
        JSON.generate(to_hash, *opts)
      end
    end

    # Collection alias for HistoryProps values.
    HistoryArray = ::Array

    # Structured type for scjson elements.
    class IfProps
      attr_accessor :other_element, :raise_value, :if_value, :foreach, :send, :script, :assign, :log, :cancel, :elseif, :else_value, :cond, :other_attributes
      # Instantiate a new IfProps object.
      # @param kwargs [Hash] Optional keyword overrides.
      def initialize(**kwargs)
        @other_element = kwargs.fetch(:other_element, [])
        @raise_value = kwargs.fetch(:raise_value, [])
        @if_value = kwargs.fetch(:if_value, [])
        @foreach = kwargs.fetch(:foreach, [])
        @send = kwargs.fetch(:send, [])
        @script = kwargs.fetch(:script, [])
        @assign = kwargs.fetch(:assign, [])
        @log = kwargs.fetch(:log, [])
        @cancel = kwargs.fetch(:cancel, [])
        @elseif = kwargs.fetch(:elseif, nil)
        @else_value = kwargs.fetch(:else_value, nil)
        @cond = kwargs.fetch(:cond, '')
        @other_attributes = kwargs.fetch(:other_attributes, {})
      end

      # Build an instance from a Hash representation.
      # @param data [Hash] Canonical hash representation.
      # @return [IfProps]
      def self.from_hash(data)
        raise ArgumentError, 'Expected Hash' unless data.is_a?(Hash)

        normalized = data.transform_keys(&:to_s)
        kwargs = {}
        kwargs[:other_element] = Array(normalized.fetch('other_element', []))
        kwargs[:raise_value] = Array(normalized.fetch('raise_value', [])).map { |item| RaiseProps.from_hash(item) }
        kwargs[:if_value] = Array(normalized.fetch('if_value', [])).map { |item| IfProps.from_hash(item) }
        kwargs[:foreach] = Array(normalized.fetch('foreach', [])).map { |item| ForeachProps.from_hash(item) }
        kwargs[:send] = Array(normalized.fetch('send', [])).map { |item| SendProps.from_hash(item) }
        kwargs[:script] = Array(normalized.fetch('script', [])).map { |item| ScriptProps.from_hash(item) }
        kwargs[:assign] = Array(normalized.fetch('assign', [])).map { |item| AssignProps.from_hash(item) }
        kwargs[:log] = Array(normalized.fetch('log', [])).map { |item| LogProps.from_hash(item) }
        kwargs[:cancel] = Array(normalized.fetch('cancel', [])).map { |item| CancelProps.from_hash(item) }
        kwargs[:elseif] = normalized.key?('elseif') && normalized['elseif'] ? ElseifProps.from_hash(normalized['elseif']) : nil
        kwargs[:else_value] = normalized.key?('else_value') && normalized['else_value'] ? ElseProps.from_hash(normalized['else_value']) : nil
        kwargs[:cond] = normalized.fetch('cond', '')
        kwargs[:other_attributes] = normalized.fetch('other_attributes', {})
        new(**kwargs)
      end

      # Deserialize an instance from a JSON payload.
      # @param json [String] JSON document to decode.
      # @return [IfProps]
      def self.from_json(json)
        parsed = JSON.parse(json)
        from_hash(parsed)
      end

      # Convert the object to a Hash suitable for JSON serialization.
      # @return [Hash]
      def to_hash
        {
          'other_element' => @other_element,
          'raise_value' => (@raise_value || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'if_value' => (@if_value || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'foreach' => (@foreach || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'send' => (@send || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'script' => (@script || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'assign' => (@assign || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'log' => (@log || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'cancel' => (@cancel || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'elseif' => @elseif&.to_hash,
          'else_value' => @else_value&.to_hash,
          'cond' => @cond,
          'other_attributes' => @other_attributes
        }
      end

      # Serialize the object to JSON.
      # @param opts [Array] JSON generation options.
      # @return [String]
      def to_json(*opts)
        JSON.generate(to_hash, *opts)
      end
    end

    # Collection alias for IfProps values.
    IfArray = ::Array

    # Structured type for scjson elements.
    class InitialProps
      attr_accessor :other_element, :transition, :other_attributes
      # Instantiate a new InitialProps object.
      # @param kwargs [Hash] Optional keyword overrides.
      def initialize(**kwargs)
        @other_element = kwargs.fetch(:other_element, [])
        @transition = kwargs.fetch(:transition, TransitionProps.new)
        @other_attributes = kwargs.fetch(:other_attributes, {})
      end

      # Build an instance from a Hash representation.
      # @param data [Hash] Canonical hash representation.
      # @return [InitialProps]
      def self.from_hash(data)
        raise ArgumentError, 'Expected Hash' unless data.is_a?(Hash)

        normalized = data.transform_keys(&:to_s)
        kwargs = {}
        kwargs[:other_element] = Array(normalized.fetch('other_element', []))
        kwargs[:transition] = normalized.key?('transition') && normalized['transition'] ? TransitionProps.from_hash(normalized['transition']) : TransitionProps.new
        kwargs[:other_attributes] = normalized.fetch('other_attributes', {})
        new(**kwargs)
      end

      # Deserialize an instance from a JSON payload.
      # @param json [String] JSON document to decode.
      # @return [InitialProps]
      def self.from_json(json)
        parsed = JSON.parse(json)
        from_hash(parsed)
      end

      # Convert the object to a Hash suitable for JSON serialization.
      # @return [Hash]
      def to_hash
        {
          'other_element' => @other_element,
          'transition' => @transition&.to_hash,
          'other_attributes' => @other_attributes
        }
      end

      # Serialize the object to JSON.
      # @param opts [Array] JSON generation options.
      # @return [String]
      def to_json(*opts)
        JSON.generate(to_hash, *opts)
      end
    end

    # Collection alias for InitialProps values.
    InitialArray = ::Array

    # Structured type for scjson elements.
    class InvokeProps
      attr_accessor :content, :param, :finalize, :other_element, :type_value, :typeexpr, :src, :srcexpr, :id, :idlocation, :namelist, :autoforward, :other_attributes
      # Instantiate a new InvokeProps object.
      # @param kwargs [Hash] Optional keyword overrides.
      def initialize(**kwargs)
        @content = kwargs.fetch(:content, [])
        @param = kwargs.fetch(:param, [])
        @finalize = kwargs.fetch(:finalize, [])
        @other_element = kwargs.fetch(:other_element, [])
        @type_value = kwargs.fetch(:type_value, 'scxml')
        @typeexpr = kwargs.fetch(:typeexpr, nil)
        @src = kwargs.fetch(:src, nil)
        @srcexpr = kwargs.fetch(:srcexpr, nil)
        @id = kwargs.fetch(:id, nil)
        @idlocation = kwargs.fetch(:idlocation, nil)
        @namelist = kwargs.fetch(:namelist, nil)
        @autoforward = kwargs.fetch(:autoforward, BooleanDatatypeProps::FALSE)
        @other_attributes = kwargs.fetch(:other_attributes, {})
      end

      # Build an instance from a Hash representation.
      # @param data [Hash] Canonical hash representation.
      # @return [InvokeProps]
      def self.from_hash(data)
        raise ArgumentError, 'Expected Hash' unless data.is_a?(Hash)

        normalized = data.transform_keys(&:to_s)
        kwargs = {}
        kwargs[:content] = Array(normalized.fetch('content', [])).map { |item| ContentProps.from_hash(item) }
        kwargs[:param] = Array(normalized.fetch('param', [])).map { |item| ParamProps.from_hash(item) }
        kwargs[:finalize] = Array(normalized.fetch('finalize', [])).map { |item| FinalizeProps.from_hash(item) }
        kwargs[:other_element] = Array(normalized.fetch('other_element', []))
        kwargs[:type_value] = normalized.fetch('type_value', 'scxml')
        kwargs[:typeexpr] = normalized.fetch('typeexpr', nil)
        kwargs[:src] = normalized.fetch('src', nil)
        kwargs[:srcexpr] = normalized.fetch('srcexpr', nil)
        kwargs[:id] = normalized.fetch('id', nil)
        kwargs[:idlocation] = normalized.fetch('idlocation', nil)
        kwargs[:namelist] = normalized.fetch('namelist', nil)
        kwargs[:autoforward] = BooleanDatatypeProps.coerce(normalized.fetch('autoforward', BooleanDatatypeProps::FALSE))
        kwargs[:other_attributes] = normalized.fetch('other_attributes', {})
        new(**kwargs)
      end

      # Deserialize an instance from a JSON payload.
      # @param json [String] JSON document to decode.
      # @return [InvokeProps]
      def self.from_json(json)
        parsed = JSON.parse(json)
        from_hash(parsed)
      end

      # Convert the object to a Hash suitable for JSON serialization.
      # @return [Hash]
      def to_hash
        {
          'content' => (@content || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'param' => (@param || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'finalize' => (@finalize || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'other_element' => @other_element,
          'type_value' => @type_value,
          'typeexpr' => @typeexpr,
          'src' => @src,
          'srcexpr' => @srcexpr,
          'id' => @id,
          'idlocation' => @idlocation,
          'namelist' => @namelist,
          'autoforward' => @autoforward,
          'other_attributes' => @other_attributes
        }
      end

      # Serialize the object to JSON.
      # @param opts [Array] JSON generation options.
      # @return [String]
      def to_json(*opts)
        JSON.generate(to_hash, *opts)
      end
    end

    # Collection alias for InvokeProps values.
    InvokeArray = ::Array

    # diagnostic output statement.
    class LogProps
      attr_accessor :other_element, :label, :expr, :other_attributes
      # Instantiate a new LogProps object.
      # @param kwargs [Hash] Optional keyword overrides.
      def initialize(**kwargs)
        @other_element = kwargs.fetch(:other_element, [])
        @label = kwargs.fetch(:label, nil)
        @expr = kwargs.fetch(:expr, nil)
        @other_attributes = kwargs.fetch(:other_attributes, {})
      end

      # Build an instance from a Hash representation.
      # @param data [Hash] Canonical hash representation.
      # @return [LogProps]
      def self.from_hash(data)
        raise ArgumentError, 'Expected Hash' unless data.is_a?(Hash)

        normalized = data.transform_keys(&:to_s)
        kwargs = {}
        kwargs[:other_element] = Array(normalized.fetch('other_element', []))
        kwargs[:label] = normalized.fetch('label', nil)
        kwargs[:expr] = normalized.fetch('expr', nil)
        kwargs[:other_attributes] = normalized.fetch('other_attributes', {})
        new(**kwargs)
      end

      # Deserialize an instance from a JSON payload.
      # @param json [String] JSON document to decode.
      # @return [LogProps]
      def self.from_json(json)
        parsed = JSON.parse(json)
        from_hash(parsed)
      end

      # Convert the object to a Hash suitable for JSON serialization.
      # @return [Hash]
      def to_hash
        {
          'other_element' => @other_element,
          'label' => @label,
          'expr' => @expr,
          'other_attributes' => @other_attributes
        }
      end

      # Serialize the object to JSON.
      # @param opts [Array] JSON generation options.
      # @return [String]
      def to_json(*opts)
        JSON.generate(to_hash, *opts)
      end
    end

    # Collection alias for LogProps values.
    LogArray = ::Array

    # Structured type for scjson elements.
    class OnentryProps
      attr_accessor :other_element, :raise_value, :if_value, :foreach, :send, :script, :assign, :log, :cancel, :other_attributes
      # Instantiate a new OnentryProps object.
      # @param kwargs [Hash] Optional keyword overrides.
      def initialize(**kwargs)
        @other_element = kwargs.fetch(:other_element, [])
        @raise_value = kwargs.fetch(:raise_value, [])
        @if_value = kwargs.fetch(:if_value, [])
        @foreach = kwargs.fetch(:foreach, [])
        @send = kwargs.fetch(:send, [])
        @script = kwargs.fetch(:script, [])
        @assign = kwargs.fetch(:assign, [])
        @log = kwargs.fetch(:log, [])
        @cancel = kwargs.fetch(:cancel, [])
        @other_attributes = kwargs.fetch(:other_attributes, {})
      end

      # Build an instance from a Hash representation.
      # @param data [Hash] Canonical hash representation.
      # @return [OnentryProps]
      def self.from_hash(data)
        raise ArgumentError, 'Expected Hash' unless data.is_a?(Hash)

        normalized = data.transform_keys(&:to_s)
        kwargs = {}
        kwargs[:other_element] = Array(normalized.fetch('other_element', []))
        kwargs[:raise_value] = Array(normalized.fetch('raise_value', [])).map { |item| RaiseProps.from_hash(item) }
        kwargs[:if_value] = Array(normalized.fetch('if_value', [])).map { |item| IfProps.from_hash(item) }
        kwargs[:foreach] = Array(normalized.fetch('foreach', [])).map { |item| ForeachProps.from_hash(item) }
        kwargs[:send] = Array(normalized.fetch('send', [])).map { |item| SendProps.from_hash(item) }
        kwargs[:script] = Array(normalized.fetch('script', [])).map { |item| ScriptProps.from_hash(item) }
        kwargs[:assign] = Array(normalized.fetch('assign', [])).map { |item| AssignProps.from_hash(item) }
        kwargs[:log] = Array(normalized.fetch('log', [])).map { |item| LogProps.from_hash(item) }
        kwargs[:cancel] = Array(normalized.fetch('cancel', [])).map { |item| CancelProps.from_hash(item) }
        kwargs[:other_attributes] = normalized.fetch('other_attributes', {})
        new(**kwargs)
      end

      # Deserialize an instance from a JSON payload.
      # @param json [String] JSON document to decode.
      # @return [OnentryProps]
      def self.from_json(json)
        parsed = JSON.parse(json)
        from_hash(parsed)
      end

      # Convert the object to a Hash suitable for JSON serialization.
      # @return [Hash]
      def to_hash
        {
          'other_element' => @other_element,
          'raise_value' => (@raise_value || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'if_value' => (@if_value || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'foreach' => (@foreach || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'send' => (@send || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'script' => (@script || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'assign' => (@assign || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'log' => (@log || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'cancel' => (@cancel || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'other_attributes' => @other_attributes
        }
      end

      # Serialize the object to JSON.
      # @param opts [Array] JSON generation options.
      # @return [String]
      def to_json(*opts)
        JSON.generate(to_hash, *opts)
      end
    end

    # Collection alias for OnentryProps values.
    OnentryArray = ::Array

    # Structured type for scjson elements.
    class OnexitProps
      attr_accessor :other_element, :raise_value, :if_value, :foreach, :send, :script, :assign, :log, :cancel, :other_attributes
      # Instantiate a new OnexitProps object.
      # @param kwargs [Hash] Optional keyword overrides.
      def initialize(**kwargs)
        @other_element = kwargs.fetch(:other_element, [])
        @raise_value = kwargs.fetch(:raise_value, [])
        @if_value = kwargs.fetch(:if_value, [])
        @foreach = kwargs.fetch(:foreach, [])
        @send = kwargs.fetch(:send, [])
        @script = kwargs.fetch(:script, [])
        @assign = kwargs.fetch(:assign, [])
        @log = kwargs.fetch(:log, [])
        @cancel = kwargs.fetch(:cancel, [])
        @other_attributes = kwargs.fetch(:other_attributes, {})
      end

      # Build an instance from a Hash representation.
      # @param data [Hash] Canonical hash representation.
      # @return [OnexitProps]
      def self.from_hash(data)
        raise ArgumentError, 'Expected Hash' unless data.is_a?(Hash)

        normalized = data.transform_keys(&:to_s)
        kwargs = {}
        kwargs[:other_element] = Array(normalized.fetch('other_element', []))
        kwargs[:raise_value] = Array(normalized.fetch('raise_value', [])).map { |item| RaiseProps.from_hash(item) }
        kwargs[:if_value] = Array(normalized.fetch('if_value', [])).map { |item| IfProps.from_hash(item) }
        kwargs[:foreach] = Array(normalized.fetch('foreach', [])).map { |item| ForeachProps.from_hash(item) }
        kwargs[:send] = Array(normalized.fetch('send', [])).map { |item| SendProps.from_hash(item) }
        kwargs[:script] = Array(normalized.fetch('script', [])).map { |item| ScriptProps.from_hash(item) }
        kwargs[:assign] = Array(normalized.fetch('assign', [])).map { |item| AssignProps.from_hash(item) }
        kwargs[:log] = Array(normalized.fetch('log', [])).map { |item| LogProps.from_hash(item) }
        kwargs[:cancel] = Array(normalized.fetch('cancel', [])).map { |item| CancelProps.from_hash(item) }
        kwargs[:other_attributes] = normalized.fetch('other_attributes', {})
        new(**kwargs)
      end

      # Deserialize an instance from a JSON payload.
      # @param json [String] JSON document to decode.
      # @return [OnexitProps]
      def self.from_json(json)
        parsed = JSON.parse(json)
        from_hash(parsed)
      end

      # Convert the object to a Hash suitable for JSON serialization.
      # @return [Hash]
      def to_hash
        {
          'other_element' => @other_element,
          'raise_value' => (@raise_value || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'if_value' => (@if_value || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'foreach' => (@foreach || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'send' => (@send || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'script' => (@script || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'assign' => (@assign || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'log' => (@log || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'cancel' => (@cancel || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'other_attributes' => @other_attributes
        }
      end

      # Serialize the object to JSON.
      # @param opts [Array] JSON generation options.
      # @return [String]
      def to_json(*opts)
        JSON.generate(to_hash, *opts)
      end
    end

    # Collection alias for OnexitProps values.
    OnexitArray = ::Array

    # Structured type for scjson elements.
    class ParallelProps
      attr_accessor :onentry, :onexit, :transition, :state, :parallel, :history, :datamodel, :invoke, :other_element, :id, :other_attributes
      # Instantiate a new ParallelProps object.
      # @param kwargs [Hash] Optional keyword overrides.
      def initialize(**kwargs)
        @onentry = kwargs.fetch(:onentry, [])
        @onexit = kwargs.fetch(:onexit, [])
        @transition = kwargs.fetch(:transition, [])
        @state = kwargs.fetch(:state, [])
        @parallel = kwargs.fetch(:parallel, [])
        @history = kwargs.fetch(:history, [])
        @datamodel = kwargs.fetch(:datamodel, [])
        @invoke = kwargs.fetch(:invoke, [])
        @other_element = kwargs.fetch(:other_element, [])
        @id = kwargs.fetch(:id, nil)
        @other_attributes = kwargs.fetch(:other_attributes, {})
      end

      # Build an instance from a Hash representation.
      # @param data [Hash] Canonical hash representation.
      # @return [ParallelProps]
      def self.from_hash(data)
        raise ArgumentError, 'Expected Hash' unless data.is_a?(Hash)

        normalized = data.transform_keys(&:to_s)
        kwargs = {}
        kwargs[:onentry] = Array(normalized.fetch('onentry', [])).map { |item| OnentryProps.from_hash(item) }
        kwargs[:onexit] = Array(normalized.fetch('onexit', [])).map { |item| OnexitProps.from_hash(item) }
        kwargs[:transition] = Array(normalized.fetch('transition', [])).map { |item| TransitionProps.from_hash(item) }
        kwargs[:state] = Array(normalized.fetch('state', [])).map { |item| StateProps.from_hash(item) }
        kwargs[:parallel] = Array(normalized.fetch('parallel', [])).map { |item| ParallelProps.from_hash(item) }
        kwargs[:history] = Array(normalized.fetch('history', [])).map { |item| HistoryProps.from_hash(item) }
        kwargs[:datamodel] = Array(normalized.fetch('datamodel', [])).map { |item| DatamodelProps.from_hash(item) }
        kwargs[:invoke] = Array(normalized.fetch('invoke', [])).map { |item| InvokeProps.from_hash(item) }
        kwargs[:other_element] = Array(normalized.fetch('other_element', []))
        kwargs[:id] = normalized.fetch('id', nil)
        kwargs[:other_attributes] = normalized.fetch('other_attributes', {})
        new(**kwargs)
      end

      # Deserialize an instance from a JSON payload.
      # @param json [String] JSON document to decode.
      # @return [ParallelProps]
      def self.from_json(json)
        parsed = JSON.parse(json)
        from_hash(parsed)
      end

      # Convert the object to a Hash suitable for JSON serialization.
      # @return [Hash]
      def to_hash
        {
          'onentry' => (@onentry || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'onexit' => (@onexit || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'transition' => (@transition || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'state' => (@state || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'parallel' => (@parallel || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'history' => (@history || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'datamodel' => (@datamodel || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'invoke' => (@invoke || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'other_element' => @other_element,
          'id' => @id,
          'other_attributes' => @other_attributes
        }
      end

      # Serialize the object to JSON.
      # @param opts [Array] JSON generation options.
      # @return [String]
      def to_json(*opts)
        JSON.generate(to_hash, *opts)
      end
    end

    # Collection alias for ParallelProps values.
    ParallelArray = ::Array

    # parameter passed to `<invoke>` or `<send>`.
    class ParamProps
      attr_accessor :other_element, :name, :expr, :location, :other_attributes
      # Instantiate a new ParamProps object.
      # @param kwargs [Hash] Optional keyword overrides.
      def initialize(**kwargs)
        @other_element = kwargs.fetch(:other_element, [])
        @name = kwargs.fetch(:name, '')
        @expr = kwargs.fetch(:expr, nil)
        @location = kwargs.fetch(:location, nil)
        @other_attributes = kwargs.fetch(:other_attributes, {})
      end

      # Build an instance from a Hash representation.
      # @param data [Hash] Canonical hash representation.
      # @return [ParamProps]
      def self.from_hash(data)
        raise ArgumentError, 'Expected Hash' unless data.is_a?(Hash)

        normalized = data.transform_keys(&:to_s)
        kwargs = {}
        kwargs[:other_element] = Array(normalized.fetch('other_element', []))
        kwargs[:name] = normalized.fetch('name', '')
        kwargs[:expr] = normalized.fetch('expr', nil)
        kwargs[:location] = normalized.fetch('location', nil)
        kwargs[:other_attributes] = normalized.fetch('other_attributes', {})
        new(**kwargs)
      end

      # Deserialize an instance from a JSON payload.
      # @param json [String] JSON document to decode.
      # @return [ParamProps]
      def self.from_json(json)
        parsed = JSON.parse(json)
        from_hash(parsed)
      end

      # Convert the object to a Hash suitable for JSON serialization.
      # @return [Hash]
      def to_hash
        {
          'other_element' => @other_element,
          'name' => @name,
          'expr' => @expr,
          'location' => @location,
          'other_attributes' => @other_attributes
        }
      end

      # Serialize the object to JSON.
      # @param opts [Array] JSON generation options.
      # @return [String]
      def to_json(*opts)
        JSON.generate(to_hash, *opts)
      end
    end

    # Collection alias for ParamProps values.
    ParamArray = ::Array

    # raise an internal event.
    class RaiseProps
      attr_accessor :event, :other_attributes
      # Instantiate a new RaiseProps object.
      # @param kwargs [Hash] Optional keyword overrides.
      def initialize(**kwargs)
        @event = kwargs.fetch(:event, '')
        @other_attributes = kwargs.fetch(:other_attributes, {})
      end

      # Build an instance from a Hash representation.
      # @param data [Hash] Canonical hash representation.
      # @return [RaiseProps]
      def self.from_hash(data)
        raise ArgumentError, 'Expected Hash' unless data.is_a?(Hash)

        normalized = data.transform_keys(&:to_s)
        kwargs = {}
        kwargs[:event] = normalized.fetch('event', '')
        kwargs[:other_attributes] = normalized.fetch('other_attributes', {})
        new(**kwargs)
      end

      # Deserialize an instance from a JSON payload.
      # @param json [String] JSON document to decode.
      # @return [RaiseProps]
      def self.from_json(json)
        parsed = JSON.parse(json)
        from_hash(parsed)
      end

      # Convert the object to a Hash suitable for JSON serialization.
      # @return [Hash]
      def to_hash
        {
          'event' => @event,
          'other_attributes' => @other_attributes
        }
      end

      # Serialize the object to JSON.
      # @param opts [Array] JSON generation options.
      # @return [String]
      def to_json(*opts)
        JSON.generate(to_hash, *opts)
      end
    end

    # Collection alias for RaiseProps values.
    RaiseArray = ::Array

    # inline executable script.
    class ScriptProps
      attr_accessor :src, :other_attributes, :content
      # Instantiate a new ScriptProps object.
      # @param kwargs [Hash] Optional keyword overrides.
      def initialize(**kwargs)
        @src = kwargs.fetch(:src, nil)
        @other_attributes = kwargs.fetch(:other_attributes, {})
        @content = kwargs.fetch(:content, [])
      end

      # Build an instance from a Hash representation.
      # @param data [Hash] Canonical hash representation.
      # @return [ScriptProps]
      def self.from_hash(data)
        raise ArgumentError, 'Expected Hash' unless data.is_a?(Hash)

        normalized = data.transform_keys(&:to_s)
        kwargs = {}
        kwargs[:src] = normalized.fetch('src', nil)
        kwargs[:other_attributes] = normalized.fetch('other_attributes', {})
        kwargs[:content] = Array(normalized.fetch('content', []))
        new(**kwargs)
      end

      # Deserialize an instance from a JSON payload.
      # @param json [String] JSON document to decode.
      # @return [ScriptProps]
      def self.from_json(json)
        parsed = JSON.parse(json)
        from_hash(parsed)
      end

      # Convert the object to a Hash suitable for JSON serialization.
      # @return [Hash]
      def to_hash
        {
          'src' => @src,
          'other_attributes' => @other_attributes,
          'content' => @content
        }
      end

      # Serialize the object to JSON.
      # @param opts [Array] JSON generation options.
      # @return [String]
      def to_json(*opts)
        JSON.generate(to_hash, *opts)
      end
    end

    # Collection alias for ScriptProps values.
    ScriptArray = ::Array

    # Structured type for scjson elements.
    class ScxmlProps
      attr_accessor :state, :parallel, :final, :datamodel, :script, :other_element, :initial, :name, :version, :datamodel_attribute, :binding, :exmode, :other_attributes
      # Instantiate a new ScxmlProps object.
      # @param kwargs [Hash] Optional keyword overrides.
      def initialize(**kwargs)
        @state = kwargs.fetch(:state, [])
        @parallel = kwargs.fetch(:parallel, [])
        @final = kwargs.fetch(:final, [])
        @datamodel = kwargs.fetch(:datamodel, [])
        @script = kwargs.fetch(:script, [])
        @other_element = kwargs.fetch(:other_element, [])
        @initial = kwargs.fetch(:initial, [])
        @name = kwargs.fetch(:name, nil)
        @version = kwargs.fetch(:version, '1.0')
        @datamodel_attribute = kwargs.fetch(:datamodel_attribute, 'null')
        @binding = kwargs.fetch(:binding, nil)
        @exmode = kwargs.fetch(:exmode, nil)
        @other_attributes = kwargs.fetch(:other_attributes, {})
      end

      # Build an instance from a Hash representation.
      # @param data [Hash] Canonical hash representation.
      # @return [ScxmlProps]
      def self.from_hash(data)
        raise ArgumentError, 'Expected Hash' unless data.is_a?(Hash)

        normalized = data.transform_keys(&:to_s)
        kwargs = {}
        kwargs[:state] = Array(normalized.fetch('state', [])).map { |item| StateProps.from_hash(item) }
        kwargs[:parallel] = Array(normalized.fetch('parallel', [])).map { |item| ParallelProps.from_hash(item) }
        kwargs[:final] = Array(normalized.fetch('final', [])).map { |item| FinalProps.from_hash(item) }
        kwargs[:datamodel] = Array(normalized.fetch('datamodel', [])).map { |item| DatamodelProps.from_hash(item) }
        kwargs[:script] = Array(normalized.fetch('script', [])).map { |item| ScriptProps.from_hash(item) }
        kwargs[:other_element] = Array(normalized.fetch('other_element', []))
        kwargs[:initial] = Array(normalized.fetch('initial', []))
        kwargs[:name] = normalized.fetch('name', nil)
        kwargs[:version] = normalized.fetch('version', nil)
        kwargs[:datamodel_attribute] = normalized.fetch('datamodel_attribute', 'null')
        kwargs[:binding] = normalized.key?('binding') ? BindingDatatypeProps.coerce(normalized['binding'], allow_nil: true) : nil
        kwargs[:exmode] = normalized.key?('exmode') ? ExmodeDatatypeProps.coerce(normalized['exmode'], allow_nil: true) : nil
        kwargs[:other_attributes] = normalized.fetch('other_attributes', {})
        new(**kwargs)
      end

      # Deserialize an instance from a JSON payload.
      # @param json [String] JSON document to decode.
      # @return [ScxmlProps]
      def self.from_json(json)
        parsed = JSON.parse(json)
        from_hash(parsed)
      end

      # Convert the object to a Hash suitable for JSON serialization.
      # @return [Hash]
      def to_hash
        {
          'state' => (@state || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'parallel' => (@parallel || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'final' => (@final || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'datamodel' => (@datamodel || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'script' => (@script || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'other_element' => @other_element,
          'initial' => @initial,
          'name' => @name,
          'version' => @version,
          'datamodel_attribute' => @datamodel_attribute,
          'binding' => @binding,
          'exmode' => @exmode,
          'other_attributes' => @other_attributes
        }
      end

      # Serialize the object to JSON.
      # @param opts [Array] JSON generation options.
      # @return [String]
      def to_json(*opts)
        JSON.generate(to_hash, *opts)
      end
    end

    # Structured type for scjson elements.
    class SendProps
      attr_accessor :content, :param, :other_element, :event, :eventexpr, :target, :targetexpr, :type_value, :typeexpr, :id, :idlocation, :delay, :delayexpr, :namelist, :other_attributes
      # Instantiate a new SendProps object.
      # @param kwargs [Hash] Optional keyword overrides.
      def initialize(**kwargs)
        @content = kwargs.fetch(:content, [])
        @param = kwargs.fetch(:param, [])
        @other_element = kwargs.fetch(:other_element, [])
        @event = kwargs.fetch(:event, nil)
        @eventexpr = kwargs.fetch(:eventexpr, nil)
        @target = kwargs.fetch(:target, nil)
        @targetexpr = kwargs.fetch(:targetexpr, nil)
        @type_value = kwargs.fetch(:type_value, 'scxml')
        @typeexpr = kwargs.fetch(:typeexpr, nil)
        @id = kwargs.fetch(:id, nil)
        @idlocation = kwargs.fetch(:idlocation, nil)
        @delay = kwargs.fetch(:delay, '0s')
        @delayexpr = kwargs.fetch(:delayexpr, nil)
        @namelist = kwargs.fetch(:namelist, nil)
        @other_attributes = kwargs.fetch(:other_attributes, {})
      end

      # Build an instance from a Hash representation.
      # @param data [Hash] Canonical hash representation.
      # @return [SendProps]
      def self.from_hash(data)
        raise ArgumentError, 'Expected Hash' unless data.is_a?(Hash)

        normalized = data.transform_keys(&:to_s)
        kwargs = {}
        kwargs[:content] = Array(normalized.fetch('content', [])).map { |item| ContentProps.from_hash(item) }
        kwargs[:param] = Array(normalized.fetch('param', [])).map { |item| ParamProps.from_hash(item) }
        kwargs[:other_element] = Array(normalized.fetch('other_element', []))
        kwargs[:event] = normalized.fetch('event', nil)
        kwargs[:eventexpr] = normalized.fetch('eventexpr', nil)
        kwargs[:target] = normalized.fetch('target', nil)
        kwargs[:targetexpr] = normalized.fetch('targetexpr', nil)
        kwargs[:type_value] = normalized.fetch('type_value', 'scxml')
        kwargs[:typeexpr] = normalized.fetch('typeexpr', nil)
        kwargs[:id] = normalized.fetch('id', nil)
        kwargs[:idlocation] = normalized.fetch('idlocation', nil)
        kwargs[:delay] = normalized.fetch('delay', '0s')
        kwargs[:delayexpr] = normalized.fetch('delayexpr', nil)
        kwargs[:namelist] = normalized.fetch('namelist', nil)
        kwargs[:other_attributes] = normalized.fetch('other_attributes', {})
        new(**kwargs)
      end

      # Deserialize an instance from a JSON payload.
      # @param json [String] JSON document to decode.
      # @return [SendProps]
      def self.from_json(json)
        parsed = JSON.parse(json)
        from_hash(parsed)
      end

      # Convert the object to a Hash suitable for JSON serialization.
      # @return [Hash]
      def to_hash
        {
          'content' => (@content || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'param' => (@param || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'other_element' => @other_element,
          'event' => @event,
          'eventexpr' => @eventexpr,
          'target' => @target,
          'targetexpr' => @targetexpr,
          'type_value' => @type_value,
          'typeexpr' => @typeexpr,
          'id' => @id,
          'idlocation' => @idlocation,
          'delay' => @delay,
          'delayexpr' => @delayexpr,
          'namelist' => @namelist,
          'other_attributes' => @other_attributes
        }
      end

      # Serialize the object to JSON.
      # @param opts [Array] JSON generation options.
      # @return [String]
      def to_json(*opts)
        JSON.generate(to_hash, *opts)
      end
    end

    # Collection alias for SendProps values.
    SendArray = ::Array

    # Structured type for scjson elements.
    class StateProps
      attr_accessor :onentry, :onexit, :transition, :initial, :state, :parallel, :final, :history, :datamodel, :invoke, :other_element, :id, :initial_attribute, :other_attributes
      # Instantiate a new StateProps object.
      # @param kwargs [Hash] Optional keyword overrides.
      def initialize(**kwargs)
        @onentry = kwargs.fetch(:onentry, [])
        @onexit = kwargs.fetch(:onexit, [])
        @transition = kwargs.fetch(:transition, [])
        @initial = kwargs.fetch(:initial, [])
        @state = kwargs.fetch(:state, [])
        @parallel = kwargs.fetch(:parallel, [])
        @final = kwargs.fetch(:final, [])
        @history = kwargs.fetch(:history, [])
        @datamodel = kwargs.fetch(:datamodel, [])
        @invoke = kwargs.fetch(:invoke, [])
        @other_element = kwargs.fetch(:other_element, [])
        @id = kwargs.fetch(:id, nil)
        @initial_attribute = kwargs.fetch(:initial_attribute, [])
        @other_attributes = kwargs.fetch(:other_attributes, {})
      end

      # Build an instance from a Hash representation.
      # @param data [Hash] Canonical hash representation.
      # @return [StateProps]
      def self.from_hash(data)
        raise ArgumentError, 'Expected Hash' unless data.is_a?(Hash)

        normalized = data.transform_keys(&:to_s)
        kwargs = {}
        kwargs[:onentry] = Array(normalized.fetch('onentry', [])).map { |item| OnentryProps.from_hash(item) }
        kwargs[:onexit] = Array(normalized.fetch('onexit', [])).map { |item| OnexitProps.from_hash(item) }
        kwargs[:transition] = Array(normalized.fetch('transition', [])).map { |item| TransitionProps.from_hash(item) }
        kwargs[:initial] = Array(normalized.fetch('initial', [])).map { |item| InitialProps.from_hash(item) }
        kwargs[:state] = Array(normalized.fetch('state', [])).map { |item| StateProps.from_hash(item) }
        kwargs[:parallel] = Array(normalized.fetch('parallel', [])).map { |item| ParallelProps.from_hash(item) }
        kwargs[:final] = Array(normalized.fetch('final', [])).map { |item| FinalProps.from_hash(item) }
        kwargs[:history] = Array(normalized.fetch('history', [])).map { |item| HistoryProps.from_hash(item) }
        kwargs[:datamodel] = Array(normalized.fetch('datamodel', [])).map { |item| DatamodelProps.from_hash(item) }
        kwargs[:invoke] = Array(normalized.fetch('invoke', [])).map { |item| InvokeProps.from_hash(item) }
        kwargs[:other_element] = Array(normalized.fetch('other_element', []))
        kwargs[:id] = normalized.fetch('id', nil)
        kwargs[:initial_attribute] = Array(normalized.fetch('initial_attribute', []))
        kwargs[:other_attributes] = normalized.fetch('other_attributes', {})
        new(**kwargs)
      end

      # Deserialize an instance from a JSON payload.
      # @param json [String] JSON document to decode.
      # @return [StateProps]
      def self.from_json(json)
        parsed = JSON.parse(json)
        from_hash(parsed)
      end

      # Convert the object to a Hash suitable for JSON serialization.
      # @return [Hash]
      def to_hash
        {
          'onentry' => (@onentry || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'onexit' => (@onexit || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'transition' => (@transition || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'initial' => (@initial || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'state' => (@state || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'parallel' => (@parallel || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'final' => (@final || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'history' => (@history || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'datamodel' => (@datamodel || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'invoke' => (@invoke || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'other_element' => @other_element,
          'id' => @id,
          'initial_attribute' => @initial_attribute,
          'other_attributes' => @other_attributes
        }
      end

      # Serialize the object to JSON.
      # @param opts [Array] JSON generation options.
      # @return [String]
      def to_json(*opts)
        JSON.generate(to_hash, *opts)
      end
    end

    # Collection alias for StateProps values.
    StateArray = ::Array

    # Structured type for scjson elements.
    class TransitionProps
      attr_accessor :other_element, :raise_value, :if_value, :foreach, :send, :script, :assign, :log, :cancel, :event, :cond, :target, :type_value, :other_attributes
      # Instantiate a new TransitionProps object.
      # @param kwargs [Hash] Optional keyword overrides.
      def initialize(**kwargs)
        @other_element = kwargs.fetch(:other_element, [])
        @raise_value = kwargs.fetch(:raise_value, [])
        @if_value = kwargs.fetch(:if_value, [])
        @foreach = kwargs.fetch(:foreach, [])
        @send = kwargs.fetch(:send, [])
        @script = kwargs.fetch(:script, [])
        @assign = kwargs.fetch(:assign, [])
        @log = kwargs.fetch(:log, [])
        @cancel = kwargs.fetch(:cancel, [])
        @event = kwargs.fetch(:event, nil)
        @cond = kwargs.fetch(:cond, nil)
        @target = kwargs.fetch(:target, [])
        @type_value = kwargs.fetch(:type_value, nil)
        @other_attributes = kwargs.fetch(:other_attributes, {})
      end

      # Build an instance from a Hash representation.
      # @param data [Hash] Canonical hash representation.
      # @return [TransitionProps]
      def self.from_hash(data)
        raise ArgumentError, 'Expected Hash' unless data.is_a?(Hash)

        normalized = data.transform_keys(&:to_s)
        kwargs = {}
        kwargs[:other_element] = Array(normalized.fetch('other_element', []))
        kwargs[:raise_value] = Array(normalized.fetch('raise_value', [])).map { |item| RaiseProps.from_hash(item) }
        kwargs[:if_value] = Array(normalized.fetch('if_value', [])).map { |item| IfProps.from_hash(item) }
        kwargs[:foreach] = Array(normalized.fetch('foreach', [])).map { |item| ForeachProps.from_hash(item) }
        kwargs[:send] = Array(normalized.fetch('send', [])).map { |item| SendProps.from_hash(item) }
        kwargs[:script] = Array(normalized.fetch('script', [])).map { |item| ScriptProps.from_hash(item) }
        kwargs[:assign] = Array(normalized.fetch('assign', [])).map { |item| AssignProps.from_hash(item) }
        kwargs[:log] = Array(normalized.fetch('log', [])).map { |item| LogProps.from_hash(item) }
        kwargs[:cancel] = Array(normalized.fetch('cancel', [])).map { |item| CancelProps.from_hash(item) }
        kwargs[:event] = normalized.fetch('event', nil)
        kwargs[:cond] = normalized.fetch('cond', nil)
        kwargs[:target] = Array(normalized.fetch('target', []))
        kwargs[:type_value] = normalized.key?('type_value') ? TransitionTypeDatatypeProps.coerce(normalized['type_value'], allow_nil: true) : nil
        kwargs[:other_attributes] = normalized.fetch('other_attributes', {})
        new(**kwargs)
      end

      # Deserialize an instance from a JSON payload.
      # @param json [String] JSON document to decode.
      # @return [TransitionProps]
      def self.from_json(json)
        parsed = JSON.parse(json)
        from_hash(parsed)
      end

      # Convert the object to a Hash suitable for JSON serialization.
      # @return [Hash]
      def to_hash
        {
          'other_element' => @other_element,
          'raise_value' => (@raise_value || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'if_value' => (@if_value || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'foreach' => (@foreach || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'send' => (@send || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'script' => (@script || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'assign' => (@assign || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'log' => (@log || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'cancel' => (@cancel || []).map { |item| item.respond_to?(:to_hash) ? item.to_hash : item },
          'event' => @event,
          'cond' => @cond,
          'target' => @target,
          'type_value' => @type_value,
          'other_attributes' => @other_attributes
        }
      end

      # Serialize the object to JSON.
      # @param opts [Array] JSON generation options.
      # @return [String]
      def to_json(*opts)
        JSON.generate(to_hash, *opts)
      end
    end

    # Collection alias for TransitionProps values.
    TransitionArray = ::Array

  end
end

