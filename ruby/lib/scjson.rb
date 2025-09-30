# frozen_string_literal: true

# Agent Name: ruby-scjson
#
# Part of the scjson project.
# Developed by Softoboros Technology Inc.
# Licensed under the BSD 1-Clause License.

require 'json'
require 'nokogiri'

require_relative 'scjson/version'

# Canonical SCXML <-> scjson conversion for the Ruby agent.
module Scjson
  XMLNS = 'http://www.w3.org/2005/07/scxml'.freeze

  ATTRIBUTE_MAP = {
    'datamodel' => 'datamodel_attribute',
    'initial' => 'initial_attribute',
    'type' => 'type_value',
    'raise' => 'raise_value'
  }.freeze

  COLLAPSE_ATTRS = %w[expr cond event target delay location name src id].freeze

  SCXML_ELEMENTS = %w[
    scxml state parallel final history transition invoke finalize datamodel data
    onentry onexit log send cancel raise assign script foreach param if elseif
    else content donedata initial
  ].freeze

  STRUCTURAL_FIELDS = %w[
    state parallel final history transition invoke finalize datamodel data
    onentry onexit log send cancel raise assign script foreach param if_value
    elseif else_value raise_value content donedata initial
  ].freeze

  module_function

  ##
  # Convert an SCXML document to its canonical scjson form.
  #
  # @param [String] xml_str SCXML source document.
  # @param [Boolean] omit_empty Remove empty containers when true.
  # @return [String] Canonical scjson output.
  def xml_to_json(xml_str, omit_empty = true)
    doc = Nokogiri::XML(xml_str) { |cfg| cfg.strict.nonet }
    root = locate_root(doc)
    raise ArgumentError, 'Document missing <scxml> root element' unless root

    map = element_to_hash(root)
    collapse_whitespace(map)
    remove_empty(map) if omit_empty
    JSON.pretty_generate(map)
  end

  ##
  # Convert a canonical scjson document back to SCXML.
  #
  # @param [String] json_str Canonical scjson input.
  # @return [String] XML document encoded as UTF-8.
  def json_to_xml(json_str)
    data = JSON.parse(json_str)
    remove_empty(data)
    doc = Nokogiri::XML::Document.new
    doc.encoding = 'utf-8'
    root = build_element(doc, 'scxml', data)
    doc.root = root
    doc.to_xml
  end

  # ----------------------------
  # Conversion helpers
  # ----------------------------

  def locate_root(doc)
    doc.at_xpath('/*[local-name()="scxml"]')
  end
  private_class_method :locate_root

  def local_name(node)
    (node.name || '').split(':').last
  end
  private_class_method :local_name

  def append_child(hash, key, value)
    if hash.key?(key)
      existing = hash[key]
      if existing.is_a?(Array)
        existing << value
      else
        hash[key] = [existing, value]
      end
    else
      hash[key] = [value]
    end
  end
  private_class_method :append_child

  def wrap_list(value)
    return [] if value.nil?
    value.is_a?(Array) ? value : [value]
  end
  private_class_method :wrap_list

  def any_element_to_hash(node)
    result = { 'qname' => node.name }
    text = node.text
    result['text'] = text.to_s if text
    unless node.attribute_nodes.empty?
      attrs = {}
      node.attribute_nodes.each do |attr|
        attrs[attr.name] = attr.value
      end
      result['attributes'] = attrs unless attrs.empty?
    end
    unless node.element_children.empty?
      children = node.element_children.map { |child| any_element_to_hash(child) }
      result['children'] = children unless children.empty?
    end
    result
  end
  private_class_method :any_element_to_hash

  def element_to_hash(node)
    map = {}
    local = local_name(node)

    node.attribute_nodes.each do |attr|
      name = local_name(attr)
      value = attr.value
      if local == 'transition' && name == 'target'
        map['target'] = value.split(/\s+/)
      elsif name == 'initial'
        tokens = value.split(/\s+/)
        key = local == 'scxml' ? 'initial' : 'initial_attribute'
        map[key] = tokens
      elsif name == 'version'
        number = begin
          Float(value)
        rescue StandardError
          nil
        end
        map['version'] = number ? number : value
      elsif name == 'datamodel'
        map['datamodel_attribute'] = value
      elsif name == 'type'
        map['type_value'] = value
      elsif name == 'raise'
        map['raise_value'] = value
      elsif local == 'send' && name == 'delay'
        map['delay'] = value
      elsif local == 'send' && name == 'event'
        map['event'] = value
      elsif name == 'xmlns'
        next
      else
        map[name] = value
      end
    end

    if local == 'assign'
      map['type_value'] ||= 'replacechildren'
    end
    if local == 'send'
      map['type_value'] ||= 'scxml'
      map['delay'] ||= '0s'
    end
    if local == 'invoke'
      map['type_value'] ||= 'scxml'
      map['autoforward'] ||= 'false'
    end
    if local == 'assign' && map.key?('id')
      (map['other_attributes'] ||= {})['id'] = map.delete('id')
    end
    if map.key?('intial')
      (map['other_attributes'] ||= {})['intial'] = map.delete('intial')
    end

    text_items = []
    node.children.each do |child|
      if child.element?
        child_local = local_name(child)
        if SCXML_ELEMENTS.include?(child_local)
          key = case child_local
                when 'if' then 'if_value'
                when 'else' then 'else_value'
                when 'raise' then 'raise_value'
                else child_local
                end
          child_map = element_to_hash(child)
          target_key = if child_local == 'scxml' && local != 'scxml'
                         'content'
                       elsif local == 'content' && child_local == 'scxml'
                         'content'
                       else
                         key
                       end
          if %w[initial history].include?(local) && child_local == 'transition'
            map[target_key] = child_map
          else
            append_child(map, target_key, child_map)
          end
        else
          append_child(map, 'content', any_element_to_hash(child))
        end
      elsif child.text?
        value = child.text
        text_items << value if value && !value.strip.empty?
      end
    end

    text_items.each { |text| append_child(map, 'content', text) }

    if local == 'scxml'
      map['version'] ||= 1.0
      map['datamodel_attribute'] ||= 'null'
    elsif local == 'donedata'
      content = map['content']
      if content.is_a?(Array) && content.length == 1
        map['content'] = content.first
      end
    end

    map
  end
  private_class_method :element_to_hash

  def collapse_whitespace(value)
    case value
    when Array
      value.each { |item| collapse_whitespace(item) }
    when Hash
      value.each do |key, val|
        if (key.end_with?('_attribute') || COLLAPSE_ATTRS.include?(key)) && val.is_a?(String)
          value[key] = val.tr("\n\r\t", ' ')
        else
          collapse_whitespace(val)
        end
      end
    end
  end
  private_class_method :collapse_whitespace

  PRESERVE_EMPTY_KEYS = %w[expr cond event target id name label text].freeze

  ALWAYS_KEEP_KEYS = %w[else_value else final onentry].freeze

  def remove_empty(value, key = nil)
    case value
    when Hash
      value.keys.each do |key|
        remove = remove_empty(value[key], key)
        value.delete(key) if remove
      end
      value.empty? && !ALWAYS_KEEP_KEYS.include?(key)
    when Array
      value.reject! { |item| remove_empty(item, key) }
      value.empty? && !ALWAYS_KEEP_KEYS.include?(key)
    when NilClass
      true
    when String
      if value.empty?
        preserve_empty_string?(key) ? false : true
      else
        false
      end
    else
      false
    end
  end
  private_class_method :remove_empty

  def preserve_empty_string?(key)
    return false if key.nil?

    key.end_with?('_attribute') ||
      key.end_with?('_value') ||
      PRESERVE_EMPTY_KEYS.include?(key)
  end
  private_class_method :preserve_empty_string?

  def join_tokens(value)
    case value
    when Array
      return unless value.all? { |item| item.is_a?(String) || item.is_a?(Numeric) }
      value.map(&:to_s).join(' ')
    when String
      value
    when Numeric
      value.to_s
    else
      nil
    end
  end
  private_class_method :join_tokens

  def scxml_like?(hash)
    return false unless hash.is_a?(Hash)

    hash.key?('state') || hash.key?('parallel') || hash.key?('final') ||
      hash.key?('datamodel') || hash.key?('datamodel_attribute') || hash.key?('version')
  end
  private_class_method :scxml_like?

  def build_element(doc, name, map)
    if map.is_a?(Array) && map.length == 1
      return build_element(doc, name, map.first)
    end

    if map.is_a?(String)
      element = Nokogiri::XML::Element.new(name, doc)
      element.content = map
      return element
    end

    raise ArgumentError, 'Expected object for element construction' unless map.is_a?(Hash)

    element_name = map['qname'] || name
    element = Nokogiri::XML::Element.new(element_name, doc)

    if name == 'scxml'
      element['xmlns'] ||= XMLNS
    elsif !element_name.include?(':') && !SCXML_ELEMENTS.include?(element_name)
      element['xmlns'] ||= ''
    end

    if map['text']
      element.add_child(Nokogiri::XML::Text.new(map['text'], doc))
    end

    if map['attributes'].is_a?(Hash)
      map['attributes'].each do |attr_name, attr_value|
        element[attr_name] = attr_value if attr_value
      end
    end

    map.each do |key, value|
      next if %w[qname text attributes].include?(key)

      case key
      when 'content'
        handle_content_nodes(doc, element, value, element_name)
      when 'children'
        wrap_list(value).each do |child_map|
          next unless child_map.is_a?(Hash)
          child_name = child_map['qname'] || 'content'
          element.add_child(build_element(doc, child_name, child_map))
        end
      when 'other_attributes'
        next unless value.is_a?(Hash)
        value.each do |attr_name, attr_value|
          element[attr_name] = join_tokens(attr_value) || attr_value.to_s
        end
      when ->(k) { k.end_with?('_attribute') }
        attr_name = key.sub(/_attribute\z/, '')
        joined = join_tokens(value)
        element[attr_name] = joined if joined
      when 'datamodel_attribute'
        joined = join_tokens(value)
        element['datamodel'] = joined if joined
      when 'type_value'
        joined = join_tokens(value)
        element['type'] = joined if joined
      when 'target'
        joined = join_tokens(value)
        element['target'] = joined if joined
      when 'delay', 'event'
        joined = join_tokens(value)
        element[key] = joined if joined
      when 'initial'
        joined = join_tokens(value)
        if joined
          element['initial'] = joined
        else
          wrap_list(value).each do |child|
            element.add_child(build_element(doc, 'initial', child))
          end
          next
        end
      when 'version'
        element['version'] = value.to_s
      else
        child_name = case key
                      when 'if_value' then 'if'
                      when 'else_value' then 'else'
                      when 'raise_value' then 'raise'
                      else key
                      end

        if STRUCTURAL_FIELDS.include?(key) || %w[if_value else_value raise_value].include?(key)
          wrap_list(value).each do |child|
            element.add_child(build_element(doc, child_name, child))
          end
        elsif value.is_a?(Array) && value.all? { |item| !item.is_a?(Hash) }
          element[key] = join_tokens(value)
        elsif value.is_a?(Hash)
          element.add_child(build_element(doc, child_name, value))
        elsif !value.nil?
          element[key] = value.to_s
        end
      end
    end

    element
  end
  private_class_method :build_element

  def handle_content_nodes(doc, element, value, parent_name)
    items = wrap_list(value)
    items.each do |item|
      if item.is_a?(String)
        if parent_name == 'script'
          element.add_child(Nokogiri::XML::Text.new(item, doc))
        elsif parent_name == 'data'
          element.add_child(Nokogiri::XML::Text.new(item, doc))
        else
          content_element = Nokogiri::XML::Element.new('content', doc)
          content_element.add_child(Nokogiri::XML::Text.new(item, doc))
          element.add_child(content_element)
        end
        next
      end

      next unless item.is_a?(Hash)

      if parent_name == 'send' && item.keys == ['content']
        wrap_list(item['content']).each do |inner|
          content_element = Nokogiri::XML::Element.new('content', doc)
          if inner.is_a?(String)
            content_element.add_child(Nokogiri::XML::Text.new(inner, doc))
          elsif inner.is_a?(Hash)
            content_element.add_child(build_element(doc, 'content', inner))
          end
          element.add_child(content_element)
        end
        next
      end

      if parent_name == 'donedata' && item.keys == ['content']
        content_element = Nokogiri::XML::Element.new('content', doc)
        wrap_list(item['content']).each do |inner|
          if inner.is_a?(String)
            content_element.add_child(Nokogiri::XML::Text.new(inner, doc))
          elsif inner.is_a?(Hash)
            content_element.add_child(build_element(doc, 'content', inner))
          end
        end
        element.add_child(content_element)
        next
      end

      if item.key?('qname')
        child = build_element(doc, item['qname'], item)
        element.add_child(child)
        next
      end

      child_name = if scxml_like?(item)
                     'scxml'
                   elsif parent_name == 'script'
                     'content'
                   else
                     'content'
                   end

      if parent_name == 'data' && child_name == 'content'
        element.add_child(Nokogiri::XML::Text.new(item['content'].to_s, doc))
      else
        child_element = build_element(doc, child_name, item)
        element.add_child(child_element)
      end
    end
  end
  private_class_method :handle_content_nodes
end
