# frozen_string_literal: true

# Agent Name: ruby-scjson
#
# Part of the scjson project.
# Developed by Softoboros Technology Inc.
# Licensed under the BSD 1-Clause License.

require 'json'
begin
  require 'nokogiri'
  NOKOGIRI_AVAILABLE = true
rescue LoadError
  NOKOGIRI_AVAILABLE = false
end
require 'shellwords'

require_relative 'scjson/version'
require_relative 'scjson/types'

# Canonical SCXML <-> scjson conversion for the Ruby agent.
module Scjson
  XMLNS = 'http://www.w3.org/2005/07/scxml'.freeze
  XINCLUDE_NS = 'http://www.w3.org/2001/XInclude'.freeze
  XINCLUDE_CLARK_INCLUDE = "{#{XINCLUDE_NS}}include".freeze

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

  SOURCE_BODY_TAGS = %w[script data].freeze

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
    if NOKOGIRI_AVAILABLE
      doc = Nokogiri::XML(xml_str) { |cfg| cfg.strict.nonet }
      root = locate_root(doc)
      raise ArgumentError, 'Document missing <scxml> root element' unless root

      map = element_to_hash(root)
      attach_root_sibling_comments(doc, root, map)
      collapse_whitespace(map)
      remove_empty(map) if omit_empty
      return JSON.pretty_generate(map)
    end
    # Fallback: use Python CLI converter when Nokogiri is unavailable.
    begin
      require 'tmpdir'
      Dir.mktmpdir('scjson-rb-xml2json') do |dir|
        in_path = File.join(dir, 'in.scxml')
        out_path = File.join(dir, 'out.scjson')
        File.write(in_path, xml_str)
        py_candidates = [ENV['PYTHON'], 'python3', 'python'].compact.uniq
        ok = false
        py_candidates.each do |py|
          # Try package entrypoint; add repo-local 'py' to PYTHONPATH for import
          repo_py = File.expand_path('../../py', __dir__)
          env = {}
          current_pp = ENV['PYTHONPATH']
          env['PYTHONPATH'] = current_pp ? (repo_py + File::PATH_SEPARATOR + current_pp) : repo_py
          cmd = [py, '-m', 'scjson.cli', 'json', in_path, '-o', out_path]
          ok = system(env, *cmd, out: File::NULL, err: File::NULL) && File.file?(out_path)
          break if ok
        end
        raise 'python converter failed' unless ok
        return File.read(out_path)
      end
    rescue StandardError => e
      raise LoadError, "SCXML->JSON conversion unavailable: Nokogiri missing and external converter failed (#{e})"
    end
  end

  ##
  # Convert a canonical scjson document back to SCXML.
  #
  # @param [String] json_str Canonical scjson input.
  # @return [String] XML document encoded as UTF-8.
  def json_to_xml(json_str)
    if NOKOGIRI_AVAILABLE
      data = JSON.parse(json_str)
      remove_empty(data)
      doc = Nokogiri::XML::Document.new
      doc.encoding = 'utf-8'
      root = build_element(doc, 'scxml', data)
      doc.root = root
      add_preceding_help_text_comments(doc, root, data)
      return doc.to_xml
    end
    # Fallback: use Python CLI converter when Nokogiri is unavailable.
    begin
      require 'tmpdir'
      Dir.mktmpdir('scjson-rb-json2xml') do |dir|
        in_path = File.join(dir, 'in.scjson')
        out_path = File.join(dir, 'out.scxml')
        File.write(in_path, json_str)
        py_candidates = [ENV['PYTHON'], 'python3', 'python'].compact.uniq
        ok = false
        py_candidates.each do |py|
          repo_py = File.expand_path('../../py', __dir__)
          env = {}
          current_pp = ENV['PYTHONPATH']
          env['PYTHONPATH'] = current_pp ? (repo_py + File::PATH_SEPARATOR + current_pp) : repo_py
          cmd = [py, '-m', 'scjson.cli', 'xml', in_path, '-o', out_path]
          ok = system(env, *cmd, out: File::NULL, err: File::NULL) && File.file?(out_path)
          break if ok
        end
        raise 'python converter failed' unless ok
        return File.read(out_path)
      end
    rescue StandardError => e
      raise LoadError, "JSON->SCXML conversion unavailable: Nokogiri missing and external converter failed (#{e})"
    end
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

  def scxml_element?(node)
    ns = node.namespace&.href
    SCXML_ELEMENTS.include?(local_name(node)) && (ns.nil? || ns.empty? || ns == XMLNS)
  end
  private_class_method :scxml_element?

  def extension_element?(node)
    ns = node.namespace&.href
    !ns.nil? && !ns.empty? && ns != XMLNS
  end
  private_class_method :extension_element?

  def comment_node?(node)
    node.respond_to?(:comment?) && node.comment?
  end
  private_class_method :comment_node?

  def processing_instruction_node?(node)
    node.respond_to?(:processing_instruction?) && node.processing_instruction?
  end
  private_class_method :processing_instruction_node?

  def clark_name(node)
    ns = node.namespace&.href
    return node.name if ns.nil? || ns.empty?

    "{#{ns}}#{local_name(node)}"
  end
  private_class_method :clark_name

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

  def repair_comment_text(raw)
    text = raw.to_s
    return text.strip unless text.include?("\n")

    lines = text.lines.map { |line| line.chomp("\n") }
    lines.shift while !lines.empty? && lines.first.strip.empty?
    lines.pop while !lines.empty? && lines.last.strip.empty?
    return '' if lines.empty?

    indents = lines.map do |line|
      next if line.strip.empty?

      line.length - line.sub(/\A[ \t]+/, '').length
    end.compact
    common = indents.empty? ? 0 : indents.min
    lines = lines.map { |line| line.length >= common ? line[common, line.length] : line } if common.positive?
    lines.join("\n")
  end
  private_class_method :repair_comment_text

  def emit_safe_comment_text(text)
    safe = text.to_s.gsub('--', '- -')
    safe = "#{safe} " if safe.end_with?('-')
    safe
  end
  private_class_method :emit_safe_comment_text

  def append_help_text(map, comments, prepend: false)
    repaired = comments.map(&:to_s)
    return if repaired.empty?

    existing = map['help_text']
    if existing
      existing = wrap_list(existing)
      map['help_text'] = prepend ? repaired + existing : existing + repaired
    else
      map['help_text'] = repaired
    end
  end
  private_class_method :append_help_text

  def add_preceding_help_text_comments(doc, element, map)
    return unless map.is_a?(Hash)

    wrap_list(map['help_text']).each do |text|
      element.add_previous_sibling(Nokogiri::XML::Comment.new(doc, emit_safe_comment_text(text)))
    end
  end
  private_class_method :add_preceding_help_text_comments

  def add_child_element(doc, parent, child_name, child_map)
    child = build_element(doc, child_name, child_map)
    if child_map.is_a?(Hash)
      wrap_list(child_map['help_text']).each do |text|
        parent.add_child(Nokogiri::XML::Comment.new(doc, emit_safe_comment_text(text)))
      end
    end
    parent.add_child(child)
  end
  private_class_method :add_child_element

  def attach_root_sibling_comments(doc, root, map)
    comments = []
    doc.children.each do |child|
      next if child.equal?(root)
      next unless comment_node?(child)

      comments << repair_comment_text(child.text || '')
    end
    append_help_text(map, comments) unless comments.empty?
  end
  private_class_method :attach_root_sibling_comments

  def any_element_to_hash(node)
    result = { 'qname' => clark_name(node) }
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

  def element_to_hash(node, inside_source_body = false, inside_extension = false)
    map = {}
    local = local_name(node)
    elem_in_source = inside_source_body || SOURCE_BODY_TAGS.include?(local)
    elem_in_extension = inside_extension || (!SCXML_ELEMENTS.include?(local) && local != 'scxml')

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
    pending_comments = []
    node.children.each do |child|
      if comment_node?(child)
        pending_comments << repair_comment_text(child.text || '')
      elsif processing_instruction_node?(child)
        next
      elsif child.element?
        child_local = local_name(child)
        if scxml_element?(child)
          key = case child_local
                when 'if' then 'if_value'
                when 'else' then 'else_value'
                when 'raise' then 'raise_value'
                else child_local
                end
          child_map = element_to_hash(child, elem_in_source || local == 'content', elem_in_extension)
          target_eligible = SCXML_ELEMENTS.include?(child_local) && !elem_in_source && !elem_in_extension
          if !pending_comments.empty? && local == 'content' && child_local == 'scxml'
            # Comments inside an inline <content> payload are payload-local,
            # not authoring metadata for the nested machine.
          elsif !pending_comments.empty? && target_eligible
            append_help_text(child_map, pending_comments, prepend: true)
          elsif !pending_comments.empty? && SCXML_ELEMENTS.include?(local) && !elem_in_source && !elem_in_extension
            append_help_text(map, pending_comments)
          end
          pending_comments = []
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
          if !pending_comments.empty? && SCXML_ELEMENTS.include?(local) && !elem_in_source && !elem_in_extension
            append_help_text(map, pending_comments)
          end
          pending_comments = []
          target_key = extension_element?(child) ? 'other_element' : 'content'
          append_child(map, target_key, any_element_to_hash(child))
        end
      elsif child.text?
        value = child.text
        if value && !value.strip.empty? && !pending_comments.empty?
          append_help_text(map, pending_comments) if SCXML_ELEMENTS.include?(local) && !elem_in_source && !elem_in_extension
          pending_comments = []
        end
        text_items << value if value && !value.strip.empty?
      end
    end

    if !pending_comments.empty? && SCXML_ELEMENTS.include?(local) && !elem_in_source && !elem_in_extension
      append_help_text(map, pending_comments)
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
    attrs = map['attributes'].is_a?(Hash) ? map['attributes'].dup : {}
    if element_name == XINCLUDE_CLARK_INCLUDE
      element_name = 'xi:include'
      attrs['xmlns:xi'] ||= XINCLUDE_NS
    end
    element = Nokogiri::XML::Element.new(element_name, doc)

    if name == 'scxml'
      element['xmlns'] ||= XMLNS
    elsif !element_name.include?(':') && !SCXML_ELEMENTS.include?(element_name)
      element['xmlns'] ||= ''
    end

    if map['text']
      element.add_child(Nokogiri::XML::Text.new(map['text'], doc))
    end

    attrs.each do |attr_name, attr_value|
      element[attr_name] = attr_value if attr_value
    end

    map.each do |key, value|
      next if %w[qname text attributes help_text].include?(key)

      case key
      when 'content'
        handle_content_nodes(doc, element, value, element_name)
      when 'other_element'
        wrap_list(value).each do |child_map|
          next unless child_map.is_a?(Hash)

          child_name = child_map['qname'] || 'content'
          add_child_element(doc, element, child_name, child_map)
        end
      when 'children'
        wrap_list(value).each do |child_map|
          next unless child_map.is_a?(Hash)
          child_name = child_map['qname'] || 'content'
          add_child_element(doc, element, child_name, child_map)
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
            add_child_element(doc, element, 'initial', child)
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
            add_child_element(doc, element, child_name, child)
          end
        elsif value.is_a?(Array) && value.all? { |item| !item.is_a?(Hash) }
          element[key] = join_tokens(value)
        elsif value.is_a?(Hash)
          add_child_element(doc, element, child_name, value)
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

      if parent_name == 'send' && (item.keys - ['help_text']) == ['content']
        wrap_list(item['help_text']).each do |text|
          element.add_child(Nokogiri::XML::Comment.new(doc, emit_safe_comment_text(text)))
        end
        wrap_list(item['content']).each do |inner|
          content_element = Nokogiri::XML::Element.new('content', doc)
          if inner.is_a?(String)
            content_element.add_child(Nokogiri::XML::Text.new(inner, doc))
          elsif inner.is_a?(Hash)
            add_child_element(doc, content_element, 'content', inner)
          end
          element.add_child(content_element)
        end
        next
      end

      if parent_name == 'donedata' && (item.keys - ['help_text']) == ['content']
        wrap_list(item['help_text']).each do |text|
          element.add_child(Nokogiri::XML::Comment.new(doc, emit_safe_comment_text(text)))
        end
        content_element = Nokogiri::XML::Element.new('content', doc)
        wrap_list(item['content']).each do |inner|
          if inner.is_a?(String)
            content_element.add_child(Nokogiri::XML::Text.new(inner, doc))
          elsif inner.is_a?(Hash)
            add_child_element(doc, content_element, 'content', inner)
          end
        end
        element.add_child(content_element)
        next
      end

      if item.key?('qname')
        add_child_element(doc, element, item['qname'], item)
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
        add_child_element(doc, element, child_name, item)
      end
    end
  end
  private_class_method :handle_content_nodes
end
