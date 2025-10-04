/**
 * Agent Name: js-scion-harness
 *
 * Part of the scjson project.
 * Developed by Softoboros Technology Inc.
 * Licensed under the BSD 1-Clause License.
 */

import { spawn } from 'node:child_process';
import { createInterface } from 'node:readline';
import { resolve } from 'node:path';

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

async function main() {
  const argv = process.argv.slice(2);
  const { pass, norm } = parseArgs(argv);
  const runner = resolve(__dirname, '../../tools/scion-runner/scion-trace.cjs');
  const runPipe = (cmd: string, args: string[]) => new Promise<number>((resolve) => {
    const proc = spawn(cmd, args, { stdio: ['inherit', 'pipe', 'inherit'] });
    const rl = createInterface({ input: proc.stdout });
    let failed = false;
    rl.on('line', (line) => {
      const s = line.trim();
      if (!s) return;
      try {
        const obj = JSON.parse(s);
        const normed = normalizeStep(obj, norm);
        process.stdout.write(JSON.stringify(normed) + '\n');
      } catch (e) {
        failed = true;
        process.stderr.write(String(e) + '\n');
        process.stdout.write(line + '\n');
      }
    });
    proc.on('close', (code) => resolve(code ?? (failed ? 1 : 0)));
  });
  const code = await runPipe('node', [runner, ...pass]);
  if (code !== 0) {
    await runPipe('python', ['-m', 'scjson.cli', 'engine-trace', ...pass]);
  }
}

void main();
