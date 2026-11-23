# frozen_string_literal: true

# Verify that one event is consumed once even when a new state accepts it.
# Agent Name: ruby-engine-tests
# Part of the scjson project. Licensed under the BSD 1-Clause License.

require_relative '../lib/scjson/engine'
require 'timeout'

RSpec.describe Scjson::Engine::DocumentContext do
  def fixture(name)
    File.expand_path("../../tests/exec/#{name}.scxml", __dir__)
  end

  it 'tests ECMAScript properties separately from Python collection values' do
    [[3, [1, 2, 3], 'fail'], [0, [42], 'pass'], ['01', [42, 43], 'fail'],
     ['length', [], 'pass'], ['map', [], 'pass'], ['x', { 'x' => nil }, 'pass']].each do |key, data, expected|
      machine = described_class.from_file(fixture('membership'), xml: true)
      expect(machine.trace_step(name: 'check', data: { 'val' => key, 'arr' => data })['configuration']).to eq([expected])
    end
    python = File.read(fixture('membership')).sub('datamodel="ecmascript"', 'datamodel="python"')
    machine = described_class.new(JSON.parse(Scjson.xml_to_json(python)))
    expect(machine.trace_step(name: 'check', data: { 'val' => 3, 'arr' => [1, 2, 3] })['configuration']).to eq(['pass'])
  end

  it 'recognizes the case-sensitive active-state predicate' do
    xml = File.read(fixture('in_predicate'))
    [["In('s0')", 's1'], ["In('s1')", 's0'], ["in('s0')", 's0']].each do |guard, target|
      machine = described_class.new(JSON.parse(Scjson.xml_to_json(xml.sub("In('s0')", guard))))
      expect(machine.trace_step(name: 'go')['configuration']).to eq([target])
    end
  end

  it 'emits parallel completion after both direct regions reach final' do
    xml = File.read(fixture('conflict_parallel')).sub('event="tick"', 'event="left"').sub('event="tick"', 'event="right"')
    machine = described_class.new(JSON.parse(Scjson.xml_to_json(xml)))
    expect(machine.trace_init['configuration']).to eq(%w[LReady RReady])
    expect(machine.trace_step(name: 'left')['configuration']).to match_array(%w[LF RReady])
    expect(machine.trace_step(name: 'right')['configuration']).to eq(['done'])
  end

  it 'stabilizes eventless transitions and waits for the next named event' do
    machine = described_class.new({
      'initial_attribute' => 'a',
      'state' => [
        { 'id' => 'a', 'transition' => [{ 'event' => 'go', 'target' => 'b' }] },
        { 'id' => 'b', 'transition' => [{ 'target' => 'c' }] },
        { 'id' => 'c', 'transition' => [{ 'event' => 'go', 'target' => 'd' }] },
        { 'id' => 'd' }
      ]
    })

    expect(machine.trace_step(name: 'go', data: nil).fetch('configuration')).to eq(['c'])
    expect(machine.trace_step(name: 'go', data: nil).fetch('configuration')).to eq(['d'])
  end

  it 'restores the remembered child without entering the default sibling' do
    chart = File.expand_path('../../tests/exec/history_reentry.scxml', __dir__)
    machine = described_class.from_file(chart, xml: true)
    states = Timeout.timeout(5) do
      %w[start flip toR back].map do |event|
        machine.trace_step(name: event, data: nil).fetch('configuration')
      end
    end
    expect(states).to eq([['LA'], ['LB'], ['R'], ['LB']])
  end
end
