# frozen_string_literal: true

# Agent Name: ruby-cli-tests
#
# Part of the scjson project.
# Developed by Softoboros Technology Inc.
# Licensed under the BSD 1-Clause License.

require 'open3'
require 'tmpdir'
require 'fileutils'
require 'json'

RSpec.describe 'scjson CLI' do
  def create_scxml
    '<scxml xmlns="http://www.w3.org/2005/07/scxml"/>'
  end

  def create_scjson
    JSON.pretty_generate({ version: 1.0, datamodel_attribute: 'null' })
  end

  let(:cli_path) { File.expand_path('../bin/scjson', __dir__) }

  it 'shows help' do
    stdout, stderr, status = Open3.capture3('ruby', cli_path, '--help')
    expect(status.success?).to be(true)
    expect(stderr).not_to match(/Failed to convert/)
    expect(stdout).to match(/scjson/)
  end

  it 'single json conversion' do
    Dir.mktmpdir do |dir|
      xml_path = File.join(dir, 'sample.scxml')
      File.write(xml_path, create_scxml)
      system('ruby', cli_path, 'json', xml_path)
      out_path = File.join(dir, 'sample.scjson')
      expect(File.exist?(out_path)).to be(true)
      data = JSON.parse(File.read(out_path))
      expect(data['version']).to eq(1.0)
    end
  end

  it 'directory json conversion' do
    Dir.mktmpdir do |dir|
      src = File.join(dir, 'src')
      Dir.mkdir(src)
      %w[a b].each { |n| File.write(File.join(src, "#{n}.scxml"), create_scxml) }
      system('ruby', cli_path, 'json', src)
      %w[a b].each do |n|
        expect(File.exist?(File.join(src, "#{n}.scjson"))).to be(true)
      end
    end
  end

  it 'single xml conversion' do
    Dir.mktmpdir do |dir|
      json_path = File.join(dir, 'sample.scjson')
      File.write(json_path, create_scjson)
      system('ruby', cli_path, 'xml', json_path)
      out_path = File.join(dir, 'sample.scxml')
      expect(File.exist?(out_path)).to be(true)
      data = File.read(out_path)
      expect(data).to include('scxml')
    end
  end

  it 'preserves unresolved XInclude elements as extension elements' do
    Dir.mktmpdir do |dir|
      xml_path = File.join(dir, 'xinclude.scxml')
      json_path = File.join(dir, 'xinclude.scjson')
      out_xml_path = File.join(dir, 'xinclude.out.scxml')
      File.write(
        xml_path,
        '<scxml xmlns="http://www.w3.org/2005/07/scxml" xmlns:xi="http://www.w3.org/2001/XInclude">' \
          '<xi:include href="child.xml"/>' \
          '</scxml>'
      )

      expect(system('ruby', cli_path, 'json', xml_path, '-o', json_path)).to be(true)
      data = JSON.parse(File.read(json_path))
      include_node = data.fetch('other_element').first
      expect(include_node['qname']).to eq('{http://www.w3.org/2001/XInclude}include')
      expect(include_node.fetch('attributes').fetch('href')).to eq('child.xml')

      expect(system('ruby', cli_path, 'xml', json_path, '-o', out_xml_path)).to be(true)
      xml = File.read(out_xml_path)
      expect(xml).to include('<xi:include')
      expect(xml).to include('href="child.xml"')
      expect(xml).to include('xmlns:xi="http://www.w3.org/2001/XInclude"')
    end
  end

  it 'promotes and emits help_text comments' do
    Dir.mktmpdir do |dir|
      xml_path = File.join(dir, 'comments.scxml')
      json_path = File.join(dir, 'comments.scjson')
      out_xml_path = File.join(dir, 'comments.out.scxml')
      File.write(
        xml_path,
        '<scxml xmlns="http://www.w3.org/2005/07/scxml" initial="idle">' \
          '<!-- state help -->' \
          '<state id="idle">' \
          '<!-- transition help -->' \
          '<transition event="go" target="done"/>' \
          '</state>' \
          '<final id="done"/>' \
          '</scxml>'
      )

      expect(system('ruby', cli_path, 'json', xml_path, '-o', json_path)).to be(true)
      data = JSON.parse(File.read(json_path))
      state = data.fetch('state').first
      expect(state.fetch('help_text')).to eq(['state help'])
      expect(state.fetch('transition').first.fetch('help_text')).to eq(['transition help'])

      expect(system('ruby', cli_path, 'xml', json_path, '-o', out_xml_path)).to be(true)
      xml = File.read(out_xml_path)
      expect(xml).to include('<!--state help-->')
      expect(xml).to include('<!--transition help-->')
    end
  end

  it 'directory xml conversion' do
    Dir.mktmpdir do |dir|
      src = File.join(dir, 'jsons')
      Dir.mkdir(src)
      %w[x y].each { |n| File.write(File.join(src, "#{n}.scjson"), create_scjson) }
      system('ruby', cli_path, 'xml', src)
      %w[x y].each do |n|
        expect(File.exist?(File.join(src, "#{n}.scxml"))).to be(true)
      end
    end
  end

  def build_dataset(base)
    d1 = File.join(base, 'level1')
    d2 = File.join(d1, 'level2')
    FileUtils.mkdir_p(d2)
    %w[a b].each do |n|
      File.write(File.join(d1, "#{n}.scxml"), create_scxml)
      File.write(File.join(d2, "#{n}.scxml"), create_scxml)
    end
  end

  it 'recursive conversion' do
    Dir.mktmpdir do |dataset|
      build_dataset(dataset)
      scjson_dir = File.join(dataset, 'outjson')
      scxml_dir = File.join(dataset, 'outxml')
      system('ruby', cli_path, 'json', dataset, '-o', scjson_dir, '-r')
      system('ruby', cli_path, 'xml', scjson_dir, '-o', scxml_dir, '-r')
      json_files = Dir.glob('**/*.scjson', base: scjson_dir)
      xml_files = Dir.glob('**/*.scxml', base: scxml_dir)
      expect(json_files).not_to be_empty
      expect(xml_files).not_to be_empty
      expect(xml_files.length).to be <= json_files.length
    end
  end

  it 'recursive validation' do
    Dir.mktmpdir do |dataset|
      build_dataset(dataset)
      scjson_dir = File.join(dataset, 'outjson')
      scxml_dir = File.join(dataset, 'outxml')
      system('ruby', cli_path, 'json', dataset, '-o', scjson_dir, '-r')
      system('ruby', cli_path, 'xml', scjson_dir, '-o', scxml_dir, '-r')
      File.write(File.join(scjson_dir, 'corrupt.scjson'), 'bad')
      _, stderr, status = Open3.capture3('ruby', cli_path, 'validate', dataset, '-r')
      expect(status.success?).to be(false)
      expect(stderr).to match(/Validation failed/)
    end
  end

  it 'recursive verify' do
    Dir.mktmpdir do |dataset|
      build_dataset(dataset)
      scjson_dir = File.join(dataset, 'outjson')
      scxml_dir = File.join(dataset, 'outxml')
      system('ruby', cli_path, 'json', dataset, '-o', scjson_dir, '-r')
      system('ruby', cli_path, 'xml', scjson_dir, '-o', scxml_dir, '-r')
      system('ruby', cli_path, 'json', scxml_dir, '-r', '-v')
      system('ruby', cli_path, 'xml', scjson_dir, '-r', '-v')
    end
  end
end
