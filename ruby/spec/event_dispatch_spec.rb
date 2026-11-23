# frozen_string_literal: true

# Verify that one event is consumed once even when a new state accepts it.
# Agent Name: ruby-engine-tests
# Part of the scjson project. Licensed under the BSD 1-Clause License.

require_relative '../lib/scjson/engine'
require 'timeout'

RSpec.describe Scjson::Engine::DocumentContext do
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
