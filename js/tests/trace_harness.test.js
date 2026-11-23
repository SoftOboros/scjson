/**
 * Regression tests for the packaged SCION CLI and its browser declarations.
 * Agent Name: scion-release-tests
 * Part of the scjson project. Developed by Softoboros Technology Inc.
 * Licensed under the BSD 1-Clause License.
 */
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const { xmlToJson } = require('../dist/converters.js');

const bin = path.resolve(__dirname, '../dist/harness.js');
const chart = '<scxml xmlns="http://www.w3.org/2005/07/scxml" version="1.0" initial="idle">' +
  '<state id="idle"><transition event="go" target="done"/></state><final id="done"/></scxml>';
let dir;
beforeAll(() => {
  dir = fs.mkdtempSync(path.join(os.tmpdir(), 'scjson-reference-'));
  fs.writeFileSync(path.join(dir, 'chart.scxml'), chart);
  const converted = xmlToJson(chart);
  expect(converted.valid).toBe(true);
  fs.writeFileSync(path.join(dir, 'chart.scjson'), converted.result);
  fs.writeFileSync(path.join(dir, 'events.jsonl'), '{"event":"go","data":{"order":7}}\n');
});
afterAll(() => fs.rmSync(dir, { recursive: true, force: true }));

function trace(...args) {
  return spawnSync(process.execPath, [bin, ...args], { cwd: dir, encoding: 'utf8' });
}

test.each(['chart.scxml', 'chart.scjson'])('executes %s and observes the transition', source => {
  const result = trace('-I', source, '-e', 'events.jsonl');
  expect(result.stderr).toBe('');
  expect(result.status).toBe(0);
  const [boot, event] = result.stdout.trim().split('\n').map(JSON.parse);
  expect(boot).toMatchObject({ step: 0, event: null, configuration: ['idle'] });
  expect(event).toMatchObject({ step: 1, event: { name: 'go', data: { order: 7 } },
    configuration: ['done'], firedTransitions: [{ source: 'idle', targets: ['done'], event: 'go' }] });
});

test('writes normalized frames to the output selected by comparison tools', () => {
  const result = trace('-I', 'chart.scxml', '-e', 'events.jsonl', '-o', 'frames.jsonl', '--xml', '--omit-transitions');
  expect(result.status).toBe(0);
  expect(result.stdout).toBe('');
  const frames = fs.readFileSync(path.join(dir, 'frames.jsonl'), 'utf8').trim().split('\n').map(JSON.parse);
  expect(frames.map(frame => frame.configuration)).toEqual([['idle'], ['done']]);
  expect(frames[1].firedTransitions).toEqual([]);
});

test('a failed trace preserves a previous output and returns an error', () => {
  const file = path.join(dir, 'existing.jsonl');
  fs.writeFileSync(file, 'previous trace\n');
  const result = trace('-I', 'missing.scxml', '-o', file);
  expect(result.status).not.toBe(0);
  expect(result.stderr).toContain('missing.scxml');
  expect(result.stdout).toBe('');
  expect(fs.readFileSync(file, 'utf8')).toBe('previous trace\n');
});

test('rejects invalid saved SCJSON before producing a frame', () => {
  fs.writeFileSync(path.join(dir, 'invalid.scjson'), JSON.stringify({ state: 'invalid' }));
  const result = trace('-I', 'invalid.scjson');
  expect(result.status).not.toBe(0);
  expect(result.stderr).toContain('Invalid SCJSON');
  expect(result.stdout).toBe('');
});

test('stages the canonical runner and ships the browser types selected for each module format', () => {
  expect(fs.readFileSync(path.join(__dirname, '../dist/scion-trace.cjs')))
    .toEqual(fs.readFileSync(path.join(__dirname, '../../tools/scion-runner/scion-trace.cjs')));
  const browser = require('../package.json').exports['./browser'];
  for (const [mode, extension] of [['import', '.d.mts'], ['require', '.d.cts']]) {
    expect(browser[mode].types.endsWith(extension)).toBe(true);
    expect(fs.existsSync(path.join(__dirname, '..', browser[mode].types))).toBe(true);
  }
});
