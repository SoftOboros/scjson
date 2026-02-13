<p align="center"><img src="../scjson.png" alt="scjson logo" width="200"/></p>

# Python Engine — User Guide

This guide explains how to use the Python execution engine and the companion tools to trace charts, compare against a reference engine, generate test vectors, and sweep corpora. It is a user‑facing companion to the development checklist in `docs/TODO-ENGINE-PY.md`.

Looking for deeper implementation details? See the architecture reference at `py/ENGINE-PY-DETAILS.md`.

For cross-language parity and [SCION](https://www.npmjs.com/package/scion) comparison details, see `docs/COMPATIBILITY.md`.

## Navigation

- This page: User Guide
  - [Overview](#overview)
  - [Quick Start](#quick-start)
  - [Event Streams](#event-streams-eventsjsonl)
- [Vector Generation](#vector-generation)
  - [Time Control](#time-control)
- Architecture & in-depth reference: `py/ENGINE-PY-DETAILS.md`
- Compatibility Matrix: `docs/COMPATIBILITY.md`

## Overview

The Python engine executes SCXML/SCJSON statecharts and can emit deterministic JSONL traces of execution. A set of CLI utilities help you:

- Run the Python engine and collect traces
- Compare Python traces against a reference engine ([SCION](https://www.npmjs.com/package/scion)/Node)
- Generate input event vectors to improve coverage
- Sweep folders of charts, auto‑generate vectors, and aggregate coverage

Key components (paths relative to repo root):

- `py/scjson/cli.py` – main CLI, including `engine-trace`
- `py/exec_compare.py` – compare Python vs reference (and optional secondary)
- `py/exec_sweep.py` – sweep a directory and compare all charts
- `py/vector_gen.py` – event vector generator with coverage heuristics

Traces are line‑delimited JSON objects with fields: `event`, `firedTransitions`, `enteredStates`, `exitedStates`, `configuration`, `actionLog`, `datamodelDelta`.

## Quick Start

1) Engine trace (Python only)

```bash
python -m scjson.cli engine-trace -I tests/exec/toggle.scxml \
  -e tests/exec/toggle.events.jsonl -o toggle.python.trace.jsonl --xml \
  --leaf-only --omit-delta
```

Notes:
- `-I` points at the input chart; add `--xml` for SCXML input, omit for SCJSON.
- `-e` supplies a JSONL events file (see “Event Streams”).
- Normalization flags reduce noise and keep traces deterministic.

2) Compare against reference engine

```bash
python py/exec_compare.py tests/exec/toggle.scxml \
  --events tests/exec/toggle.events.jsonl \
  --reference "node tools/scion-runner/scion-trace.cjs" \
  --leaf-only --omit-delta
```

If you omit `--events`, you can ask the tool to generate vectors:

```bash
python py/exec_compare.py tests/exec/toggle.scxml \
  --generate-vectors --gen-depth 2 --gen-variants-per-event 3
```

3) Sweep a directory of charts

```bash
python py/exec_sweep.py tutorial \
  --glob "**/*.scxml" \
  --reference "node tools/scion-runner/scion-trace.cjs" \
  --generate-vectors --gen-depth 2 --gen-variants-per-event 3 \
  --workdir uber_out/sweep
```

When `--workdir` is provided and vectors are generated, a `coverage-summary.json` is written with aggregated coverage across charts.

---

Back to
- Architecture & reference: `py/ENGINE-PY-DETAILS.md`
- Compatibility Matrix: `docs/COMPATIBILITY.md`

## Event Streams (.events.jsonl)

Event streams are newline‑delimited JSON objects, one per event:

```json
{"event": "start"}
{"event": "go", "data": {"flag": true}}
```

Accepted keys:
- `event` (or `name`) – string event name
- `data` – optional payload (object, number, string, etc.)

Control tokens:
- `advance_time` – number of seconds to advance the Python engine's mock clock
  before the next external event is processed. This is ignored by reference
  engines that only consume `event`/`name`, but lets the Python engine flush
  delayed `<send>` timers between stimuli to better match engines that do not
  model time explicitly.

## Time Control

By default, the CLI emits a synthetic step whenever an `{"advance_time": N}`
control token is processed so that due timers are visible even when no
subsequent external events occur. Disable this behavior with
`--no-emit-time-steps` when strict parity with tools that do not emit such
steps is desired.

Example:

```bash
python -m scjson.cli engine-trace -I chart.scxml --xml \
  -e stream.events.jsonl --leaf-only --omit-delta
```

Notes:
- The synthetic step sets `event` to `null` and otherwise follows the same
  normalization rules (`--leaf-only`, `--omit-*`).
- Use `--no-emit-time-steps` to suppress these steps if comparing against tools
  that do not emit them.

## Vector Generation

`py/vector_gen.py` generates compact event sequences to explore a chart’s behavior. It extracts an event alphabet and uses coverage‑guided search with payload heuristics.

Core features:
- Alphabet extraction from transition `event` tokens (skips wildcards/prefix patterns)
- Payload heuristics from `cond` expressions on `_event.data.*`:
  - Truthiness / negation (True/False)
  - Equality/inequality and numeric thresholds
  - Membership tests (including reversed forms and datamodel containers)
  - Chained/split numeric ranges
- Payload fusion:
  - Merge non‑conflicting per‑condition hints for richer payloads
  - One‑hot “branch flipping” variants (positive for one condition, negatives for others)
- Auto‑advance detection: if the chart schedules delayed sends during init, the generator recommends and applies a small initial time advance

CLI usage:

```bash
python py/vector_gen.py path/to/chart.scxml --xml \
  --out ./vectors --max-depth 2 --limit 1 \
  --variants-per-event 3 --advance-time 0 \
  # use --no-auto-advance to disable delayed-send detection
```

Outputs written alongside the chart’s base name:
- `<name>.events.jsonl` – generated event sequence
- `<name>.coverage.json` – coverage summary for the sequence
- `<name>.vector.json` – metadata including `advanceTime`, `sequenceLength`, and hint counts

`exec_compare` and `exec_sweep` adopt the recommended `advanceTime` from `.vector.json` when you use `--generate-vectors` and do not pass an explicit `--advance-time`.

The number of candidate payload variants per event is capped by `--variants-per-event`.

Mid-sequence time advance injection
- When the chart schedules delayed `<send>` events after initialization, the
  generator now injects control tokens (`{"advance_time": N}`) between external
  stimuli in `<name>.events.jsonl` so those timers are released before the next
  event. The `engine-trace` CLI understands these tokens and advances the
  interpreter’s mock clock without emitting a trace step; the [SCION](https://www.npmjs.com/package/scion) reference
  runner ignores them (it only looks at `event`/`name`).

This behavior improves cross-engine parity when the reference does not model
time, while keeping the event stream format backward compatible.

## Normalization and Flags

These flags appear on `engine-trace`, `exec_compare`, and `exec_sweep` to keep output reproducible and focus comparisons:

- `--leaf-only` – restricts `configuration`, `enteredStates`, and `exitedStates` to leaf states
- `--omit-delta` – clears `datamodelDelta` (step 0 is still normalized)
- `--omit-actions` – clears `actionLog`
- `--omit-transitions` – clears `firedTransitions`
- `--advance-time <seconds>` – advances mock time before event processing (and propagates to child invocations)

Step‑0 normalization: both Python and reference traces get `datamodelDelta` and `firedTransitions` cleared at step 0. Leaf‑only state filtering further reduces step‑0 variance.

## Reference Engine ([SCION](https://www.npmjs.com/package/scion))

The default reference is the [SCION](https://www.npmjs.com/package/scion) Node implementation; a helper script is included. `exec_compare` and `exec_sweep` automatically use it when present.

Setup once:

```bash
cd tools/scion-runner
npm install
```

Point `exec_compare`/`exec_sweep` at it explicitly with:

```bash
--reference "node tools/scion-runner/scion-trace.cjs"
```

Alternatively set `SCJSON_REF_ENGINE_CMD` in your environment. When other engines are added, they should default to comparing back to [SCION](https://www.npmjs.com/package/scion) as the reference.

## Examples

Trace and compare with generated vectors:

```bash
python py/exec_compare.py tests/exec/toggle.scxml \
  --generate-vectors --gen-depth 2 --gen-variants-per-event 2 \
  --reference "node tools/scion-runner/scion-trace.cjs"
```

Sweep a folder and write coverage summary:

```bash
python py/exec_sweep.py tutorial \
  --glob "**/*.scxml" --generate-vectors \
  --gen-depth 2 --gen-variants-per-event 3 \
  --workdir uber_out/sweep \
  --reference "node tools/scion-runner/scion-trace.cjs"
```

Generate vectors only (no compare):

```bash
python py/vector_gen.py examples/demo.scxml --xml \
  --out ./vectors --max-depth 2 --variants-per-event 3
```

## Coverage

Coverage is a simple aggregate of unique:
- Entered state IDs
- Fired transitions (by source and targets)
- `done.*` events
- `error*` events

`exec_sweep` aggregates coverage for generated vectors and writes a `coverage-summary.json` when `--workdir` is provided. Per‑chart coverage sidecars are written by `vector_gen.py`.

## Troubleshooting

- If `engine-trace` is unavailable, `exec_compare` falls back to an inline Python runner.
- For SCXML inputs that schedule delayed sends during init, use `--advance-time` (or rely on generator auto‑detection) so those timers are flushed before the first external event.
- If Node is unavailable, you can still run `exec_sweep` by using the Python engine as the reference: `--reference "$(python -c 'import sys;print(sys.executable)') -m scjson.cli engine-trace"`.

## More Details

For design notes, implementation status, and known limitations, see: `py/scjson/ENGINE.md` and `docs/TODO-ENGINE-PY.md`.
