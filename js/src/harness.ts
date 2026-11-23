#!/usr/bin/env node
/**
 * Agent Name: js-scion-harness
 *
 * Part of the scjson project.
 * Developed by Softoboros Technology Inc.
 * Licensed under the BSD 1-Clause License.
 */

import { jsonToXml } from './converters.js';

type NormFlags = {
  leafOnly: boolean;
  omitDelta: boolean;
  omitTransitions: boolean;
  stripStep0Noise: boolean;
  stripStep0States: boolean;
};

function parseArgs(argv: string[]): { pass: string[]; norm: NormFlags } {
  const norm: NormFlags = {
    leafOnly: false,
    omitDelta: false,
    omitTransitions: false,
    stripStep0Noise: false,
    stripStep0States: false,
  };
  const pass: string[] = [];
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    switch (a) {
      case '--leaf-only':
        norm.leafOnly = true;
        break;
      case '--omit-delta':
        norm.omitDelta = true;
        break;
      case '--omit-transitions':
        norm.omitTransitions = true;
        break;
      case '--strip-step0-noise':
        norm.stripStep0Noise = true;
        break;
      case '--strip-step0-states':
        norm.stripStep0States = true;
        break;
      default:
        pass.push(a);
        break;
    }
  }
  return { pass, norm };
}

function normalizeStep(obj: any, norm: NormFlags): any {
  if (!obj || typeof obj !== 'object') return obj;
  const out: any = { ...obj };
  const step = typeof out.step === 'number' ? out.step : -1;
  if (norm.omitDelta) out.datamodelDelta = {};
  if (norm.omitTransitions) out.firedTransitions = [];
  if (step === 0 && norm.stripStep0Noise) {
    out.datamodelDelta = {};
    out.firedTransitions = [];
  }
  if (step === 0 && norm.stripStep0States) {
    out.enteredStates = [];
    out.exitedStates = [];
  }
  return out;
}

const { pass, norm } = parseArgs(process.argv.slice(2));
// The build stages the repository's canonical runner beside this entry point.
require('./scion-trace.cjs').runCli(pass, {
  convertJson(text: string): string {
    const chart = jsonToXml(text);
    if (!chart.valid) throw new Error('Invalid SCJSON: ' + JSON.stringify(chart.errors));
    return chart.result;
  },
  normalize: (frame: unknown) => normalizeStep(frame, norm),
});
