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
require_relative 'engine'

module Scjson
  ##
  # Display the CLI program header.
  #
  # @return [void]
  def self.splash
    puts "scjson #{VERSION} - SCXML/SCML execution, SCXML <-> scjson converter & validator"
  end

  ##
  # Command line interface for scjson conversions.
  #
  # @param [Array<String>] argv Command line arguments provided by the user.
  # @return [void]
  def self.main(argv = ARGV)
    options = { recursive: false, verify: false, keep_empty: false }
    cmd = argv.shift
    if cmd.nil? || %w[-h --help].include?(cmd)
      puts(help_text)
      return
    end
    if cmd == 'engine-trace'
      return engine_trace(argv)
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

  ##
  # Render the help text describing CLI usage.
  #
  # @return [String] A one-line summary of the CLI purpose.
  def self.help_text
    'scjson - SCXML <-> scjson converter, validator, and engine trace'
  end

  ##
  # Convert SCXML inputs to scjson outputs.
  #
  # Handles both file and directory inputs, preserving relative paths when
  # writing to directories.
  #
  # @param [Pathname] path Source file or directory.
  # @param [Hash] opt Options hash controlling output and recursion behaviour.
  # @return [void]
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

  ##
  # Convert scjson inputs to SCXML outputs.
  #
  # Handles both file and directory inputs.
  #
  # @param [Pathname] path Source file or directory.
  # @param [Hash] opt Options hash controlling output and recursion behaviour.
  # @return [void]
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

  ##
  # Convert a single SCXML document to scjson.
  #
  # @param [String, Pathname] src Input SCXML file path.
  # @param [Pathname] dest Target path for scjson output.
  # @param [Boolean] verify When true, only validate round-tripping without writing.
  # @param [Boolean] keep_empty When true, retain empty containers in JSON output.
  # @return [void]
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

  ##
  # Convert a single scjson document to SCXML.
  #
  # @param [String, Pathname] src Input scjson file path.
  # @param [Pathname] dest Target SCXML file path.
  # @param [Boolean] verify When true, only validate round-tripping without writing.
  # @return [void]
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

  ##
  # Validate a file or directory tree of SCXML and scjson documents.
  #
  # @param [Pathname] path File or directory to validate.
  # @param [Boolean] recursive When true, traverse subdirectories.
  # @return [void]
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

  ##
  # Validate a single SCXML or scjson document by round-tripping.
  #
  # @param [String] src Path to the document to validate.
  # @return [Boolean] True when the document validates successfully.
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

  ##
  # Emit a standardized JSONL execution trace for a document.
  #
  # Mirrors the Python CLI flags where appropriate, using Ruby idioms.
  #
  # @param [Array<String>] argv Command line arguments following 'engine-trace'.
  # @return [void]
  def self.engine_trace(argv)
    input = nil
    events = nil
    out = nil
    is_xml = false
    leaf_only = false
    omit_actions = false
    omit_delta = false
    omit_transitions = false
    advance_time = 0.0
    ordering = 'tolerant'
    max_steps = nil
    strip_step0_noise = false
    strip_step0_states = false
    keep_cond = false

    parser = OptionParser.new do |opts|
      opts.banner = 'scjson engine-trace [options]'
      opts.on('-I', '--input PATH', 'SCJSON/SCXML document') { |v| input = v }
      opts.on('-e', '--events PATH', 'JSONL stream of events') { |v| events = v }
      opts.on('-o', '--out PATH', 'Destination trace file (stdout by default)') { |v| out = v }
      opts.on('--xml', 'Treat input as SCXML') { is_xml = true }
      opts.on('--leaf-only', 'Restrict configuration/entered/exited to leaf states') { leaf_only = true }
      opts.on('--omit-actions', 'Omit actionLog entries from the trace') { omit_actions = true }
      opts.on('--omit-delta', 'Omit datamodelDelta entries from the trace') { omit_delta = true }
      opts.on('--omit-transitions', 'Omit firedTransitions entries from the trace') { omit_transitions = true }
      opts.on('--advance-time N', Float, 'Advance time by N seconds before processing events') { |v| advance_time = v }
      opts.on('--ordering MODE', ['tolerant', 'strict', 'scion'], 'Ordering policy (tolerant|strict|scion)') { |v| ordering = v }
      opts.on('--max-steps N', Integer, 'Maximum steps to process') { |v| max_steps = v }
      opts.on('--strip-step0-noise', 'Clear datamodelDelta and firedTransitions at step 0') { strip_step0_noise = true }
      opts.on('--strip-step0-states', 'Clear enteredStates and exitedStates at step 0') { strip_step0_states = true }
      opts.on('--keep-cond', 'Keep transition cond fields (default scrubs cond)') { keep_cond = true }
      opts.on('-h', '--help', 'Show help') do
        puts opts
        return
      end
    end

    begin
      parser.parse!(argv)
    rescue OptionParser::ParseError => e
      warn e.message
      puts parser
      return
    end
    unless input
      warn 'Missing required --input'
      puts parser
      return
    end

    Scjson::Engine.trace(
      input_path: input,
      events_path: events,
      out_path: out,
      xml: is_xml,
      leaf_only: leaf_only,
      omit_actions: omit_actions,
      omit_delta: omit_delta,
      omit_transitions: omit_transitions,
      advance_time: advance_time,
      ordering: ordering,
      max_steps: max_steps,
      strip_step0_noise: strip_step0_noise,
      strip_step0_states: strip_step0_states,
      keep_cond: keep_cond
    )
  end
end
