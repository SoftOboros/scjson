# frozen_string_literal: true

# Agent Name: ruby-cli
#
# Part of the scjson project.
# Developed by Softoboros Technology Inc.
# Licensed under the BSD 1-Clause License.

require 'pathname'
require 'optparse'
require 'fileutils'
require_relative '../scjson'

module Scjson
  # Display program header.
  def self.splash
    puts "scjson #{VERSION} - SCXML <-> scjson converter"
  end

  # Command line interface for scjson conversions.
  def self.main(argv = ARGV)
    options = { recursive: false, verify: false, keep_empty: false }
    cmd = argv.shift
    if cmd.nil? || %w[-h --help].include?(cmd)
      puts(help_text)
      return
    end
    parser = OptionParser.new do |opts|
      opts.banner = ''
      opts.on('-o', '--output PATH', 'output file or directory') { |v| options[:output] = v }
      opts.on('-r', '--recursive', 'recurse into directories') { options[:recursive] = true }
      opts.on('-v', '--verify', 'verify conversion without writing output') { options[:verify] = true }
      opts.on('--keep-empty', 'keep null or empty items when producing JSON') { options[:keep_empty] = true }
    end
    path = argv.shift
    parser.parse!(argv)
    unless path
      puts(help_text)
      return
    end
    splash
    case cmd
    when 'json'
      handle_json(Pathname.new(path), options)
    when 'xml'
      handle_xml(Pathname.new(path), options)
    when 'validate'
      validate(Pathname.new(path), options[:recursive])
    else
      puts(help_text)
    end
  end

  def self.help_text
    'scjson - SCXML <-> scjson converter and validator'
  end

  def self.handle_json(path, opt)
    if path.directory?
      out_dir = opt[:output] ? Pathname.new(opt[:output]) : path
      pattern = opt[:recursive] ? '**/*.scxml' : '*.scxml'
      Dir.glob(path.join(pattern).to_s).each do |src|
        rel = Pathname.new(src).relative_path_from(path)
        dest = out_dir.join(rel).sub_ext('.scjson')
        convert_scxml_file(src, dest, opt[:verify], opt[:keep_empty])
      end
    else
      dest = if opt[:output]
               p = Pathname.new(opt[:output])
               p.directory? ? p.join(path.basename.sub_ext('.scjson')) : p
             else
               path.sub_ext('.scjson')
             end
      convert_scxml_file(path, dest, opt[:verify], opt[:keep_empty])
    end
  end

  def self.handle_xml(path, opt)
    if path.directory?
      out_dir = opt[:output] ? Pathname.new(opt[:output]) : path
      pattern = opt[:recursive] ? '**/*.scjson' : '*.scjson'
      Dir.glob(path.join(pattern).to_s).each do |src|
        rel = Pathname.new(src).relative_path_from(path)
        dest = out_dir.join(rel).sub_ext('.scxml')
        convert_scjson_file(src, dest, opt[:verify])
      end
    else
      dest = if opt[:output]
               p = Pathname.new(opt[:output])
               p.directory? ? p.join(path.basename.sub_ext('.scxml')) : p
             else
               path.sub_ext('.scxml')
             end
      convert_scjson_file(path, dest, opt[:verify])
    end
  end

  def self.convert_scxml_file(src, dest, verify, keep_empty)
    xml_str = File.read(src)
    begin
      json_str = Scjson.xml_to_json(xml_str, !keep_empty)
      if verify
        Scjson.json_to_xml(json_str)
        puts "Verified #{src}"
      else
        FileUtils.mkdir_p(dest.dirname)
        File.write(dest, json_str)
        puts "Wrote #{dest}"
      end
    rescue StandardError => e
      warn "Failed to convert #{src}: #{e}"
    end
  end

  def self.convert_scjson_file(src, dest, verify)
    json_str = File.read(src)
    begin
      xml_str = Scjson.json_to_xml(json_str)
      if verify
        Scjson.xml_to_json(xml_str)
        puts "Verified #{src}"
      else
        FileUtils.mkdir_p(dest.dirname)
        File.write(dest, xml_str)
        puts "Wrote #{dest}"
      end
    rescue StandardError => e
      warn "Failed to convert #{src}: #{e}"
    end
  end

  def self.validate(path, recursive)
    success = true
    if path.directory?
      pattern = recursive ? '**/*' : '*'
      Dir.glob(path.join(pattern).to_s).each do |f|
        next unless File.file?(f)
        next unless f.end_with?('.scxml', '.scjson')
        success &= validate_file(f)
      end
    else
      success &= validate_file(path.to_s)
    end
    exit(1) unless success
  end

  def self.validate_file(src)
    begin
      data = File.read(src)
      if src.end_with?('.scxml')
        json = Scjson.xml_to_json(data)
        Scjson.json_to_xml(json)
      elsif src.end_with?('.scjson')
        xml = Scjson.json_to_xml(data)
        Scjson.xml_to_json(xml)
      else
        return true
      end
      true
    rescue StandardError => e
      warn "Validation failed for #{src}: #{e}"
      false
    end
  end
end
