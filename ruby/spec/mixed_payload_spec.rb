# frozen_string_literal: true

# Verify that Ruby transmits all SCXML content alternatives and preserves order metadata.
# Part of the scjson project. Licensed under the BSD 1-Clause License.

require_relative '../lib/scjson/types'
require_relative '../lib/scjson'

RSpec.describe Scjson::Types::ContentProps do
  it 'retains mixed text, markup and nested charts from a sparse SCJSON document' do
    wire = JSON.parse(File.read(File.expand_path('../../rust/tests/fixtures/ordered-mixed-payload.scjson', __dir__)))
    encoded = JSON.parse(Scjson::Types::ScxmlProps.from_hash(wire).to_json)
    path = ['state', 0, 'onentry', 0, 'send', 0, 'content', 0, 'content']
    expect(encoded.dig(*path)).to eq(wire.dig(*path))
    expect(encoded.dig('state', 0, 'onentry', 0, 'execution_order')).to eq(%w[assign send])
  end

  it 'distinguishes an absent order from an explicit empty list' do
    expect(Scjson::Types::OnentryProps.from_hash({}).to_hash).not_to have_key('execution_order')
    expect(Scjson::Types::OnentryProps.from_hash({ 'execution_order' => [] }).to_hash.fetch('execution_order')).to eq([])
  end

  it 'retains a single elseif object and a sequence of elseif objects' do
    [{ 'cond' => 'a' }, [{ 'cond' => 'a' }, { 'cond' => 'b' }]].each do |markers|
      expect(Scjson::Types::IfProps.from_hash({ 'cond' => 'false', 'elseif' => markers }).to_hash.fetch('elseif')).to eq(markers)
    end
  end
end

RSpec.describe 'native converter child order' do
  it 'preserves mixed states, regions, actions, repeated logs and a namespaced extension' do
    source = <<~XML
      <scxml xmlns="#{Scjson::XMLNS}" xmlns:x="urn:example"><final/><parallel id="p">
        <parallel/><state id="s"><onentry><if cond="a"><log label="a"/><elseif cond="b"/>
        <x:note/><else/><log label="b"/></if></onentry></state>
      </parallel><state/></scxml>
    XML
    wire = JSON.parse(Scjson.xml_to_json(source))
    expect(wire['state_order']).to eq(%w[final parallel state])
    expect(wire['parallel'][0]['region_order']).to eq(%w[parallel state])
    branch = wire.dig('parallel', 0, 'state', 0, 'onentry', 0, 'if_value', 0)
    expect(branch['execution_order']).to eq(%w[log elseif {urn:example}note else log])
    expect(branch['elseif']).to eq('cond' => 'b')
    branch.replace(branch.sort.to_h)
    output = Scjson.json_to_xml(JSON.generate(wire))
    expect(JSON.parse(Scjson.xml_to_json(output))).to eq(wire)
    wire.delete('state_order')
    expect(JSON.parse(Scjson.xml_to_json(Scjson.json_to_xml(wire.to_json)))['state_order']).to eq(%w[state parallel final])
  end

  it 'refuses invalid references and misplaced branch markers' do
    [nil, [], ['unknown'], %w[log log]].each do |order|
      wire = { state: [{ onentry: [{ log: [{}], execution_order: order }] }] }
      expect { Scjson.json_to_xml(wire.to_json) }.to raise_error(ArgumentError)
    end
    ['<else/>', '<if cond="a"><else/><elseif cond="b"/></if>'].each do |body|
      xml = "<scxml><state><onentry>#{body}</onentry></state></scxml>"
      expect { Scjson.xml_to_json(xml) }.to raise_error(ArgumentError)
    end
  end
end
