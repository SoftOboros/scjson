# frozen_string_literal: true

# Agent Name: ruby-scjson
#
# Part of the scjson project.
# Developed by Softoboros Technology Inc.
# Licensed under the BSD 1-Clause License.

require 'nokogiri'
require_relative 'scjson/version'
require 'json'

# Minimal SCXML ↔ scjson conversion utilities.
module Scjson
  XMLNS = 'http://www.w3.org/2005/07/scxml'

  # Convert an SCXML string to a scjson string.
  # @param xml_str [String] XML document
  # @param omit_empty [Boolean] remove empty values when true
  # @return [String] scjson representation
  def self.xml_to_json(xml_str, omit_empty = true)
    doc = Nokogiri::XML(xml_str)
    root = doc.at_xpath('/scxml')
    obj = {}
    root&.attribute_nodes&.each do |attr|
      next if attr.name == 'xmlns'
      obj[attr.name] = attr.value
    end
    obj['version'] ||= 1.0
    obj['datamodel_attribute'] ||= 'null'
    if omit_empty
      obj.delete_if { |_, v| v.nil? || (v.respond_to?(:empty?) && v.empty?) }
    end
    JSON.pretty_generate(obj)
  end

  # Convert a scjson string to an SCXML string.
  # @param json_str [String] scjson document
  # @return [String] XML representation
  def self.json_to_xml(json_str)
    obj = JSON.parse(json_str)
    attrs = obj.dup
    if attrs.key?('datamodel_attribute')
      attrs['datamodel'] = attrs.delete('datamodel_attribute')
    end
    attrs['xmlns'] ||= XMLNS
    builder = Nokogiri::XML::Builder.new do |xml|
      xml.scxml(attrs)
    end
    builder.to_xml
  end
end
