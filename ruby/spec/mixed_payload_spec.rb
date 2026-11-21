# frozen_string_literal: true

# Verify that Ruby transmits all SCXML content alternatives and preserves order metadata.
# Part of the scjson project. Licensed under the BSD 1-Clause License.

require_relative '../lib/scjson/types'

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
