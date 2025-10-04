<p align="center"><img src="../scjson.png" alt="scjson logo" width="200"/></p>

Agent Name: ruby-engine-guide

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

# Ruby Engine — User Guide

This guide explains how to use the Ruby execution engine interface to emit deterministic JSONL traces and how to compare behavior against the reference engine ([SCION](https://www.npmjs.com/package/scion)) and the Python engine. It mirrors the Python guide where appropriate, while following Ruby conventions.

Looking for deeper implementation details? See the architecture reference at `ruby/ENGINE-RB-DETAILS.md`.

For cross-language parity and SCION comparison details, see `docs/COMPATIBILITY.md`.

## Navigation

- This page: User Guide
  - Overview
  - Quick Start
  - Event Streams (.events.jsonl)
- Architecture & in‑depth reference: `ruby/ENGINE-RB-DETAILS.md`
- Compatibility Matrix: `docs/COMPATIBILITY.md`

## Overview

The Ruby engine interface is being developed to execute SCXML/SCJSON statecharts and emit deterministic JSONL traces of execution. A set of CLI utilities and the existing Python harness help you:

- Run the Ruby engine and collect traces
- Compare Ruby traces against a reference engine (SCION/Node) and Python
- Reuse existing event vectors and control tokens for deterministic runs

Key components (paths relative to repo root):

- `ruby/lib/scjson/cli.rb` – Ruby CLI, including `engine-trace`
- `ruby/lib/scjson/engine.rb` – engine trace interface (stub; expands over time)
  - Normalization flags: `--leaf-only`, `--omit-actions`, `--omit-delta`, `--omit-transitions`, `--strip-step0-noise`, `--strip-step0-states`, `--keep-cond`
  - Ordering: `--ordering tolerant|strict|scion` (affects done.invoke event ordering)
- `py/exec_compare.py` – compare traces vs reference and optional secondary (use for Ruby)

Traces are line‑delimited JSON objects with fields: `event`, `firedTransitions`, `enteredStates`, `exitedStates`, `configuration`, `actionLog`, `datamodelDelta`, `step`.

## Quick Start

1) Engine trace (Ruby; SCXML input)

```bash
ruby/bin/scjson engine-trace -I tests/exec/toggle.scxml \
  -e tests/exec/toggle.events.jsonl -o toggle.ruby.trace.jsonl --xml \
  --leaf-only --omit-delta --strip-step0-noise --strip-step0-states
```

Notes:
- `-I` points at the input chart; add `--xml` for SCXML input, omit for SCJSON.
- `-e` supplies a JSONL events file (see “Event Streams”).
- Normalization flags reduce noise and keep traces deterministic.

2) Compare against reference engine with Ruby as secondary

```bash
python py/exec_compare.py tests/exec/toggle.scxml \
  --events tests/exec/toggle.events.jsonl \
  --reference "node tools/scion-runner/scion-trace.cjs" \
  --secondary "ruby/bin/scjson engine-trace" \
  --leaf-only --omit-delta
```

3) Sweep a directory of charts (Ruby as secondary)

```bash
python py/exec_sweep.py tutorial \
  --glob "**/*.scxml" \
  --reference "node tools/scion-runner/scion-trace.cjs" \
  --workdir uber_out/sweep \
  --secondary "ruby/bin/scjson engine-trace"
```

When using generated vectors, the Python harness writes a `coverage-summary.json` with aggregated coverage across charts.

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
- `advance_time` – number of seconds to advance the engine’s clock before the next external event is processed. No trace step is emitted for this control token. This mirrors Python’s behavior to keep traces comparable.
  - Ruby CLI also supports `--advance-time N` to apply an initial time advance before the first event.

## CI Notes — Converter Fallback

- Ruby’s SCXML↔scjson converter uses Nokogiri when available. Some CI environments do not install Ruby gems (Nokogiri requires native extensions). To keep the engine harness usable in those environments, the Ruby converter transparently falls back to the Python CLI for conversion:
  - SCXML→scjson: `python -m scjson.cli json <in.scxml> -o <out.scjson>`
  - scjson→SCXML: `python -m scjson.cli xml <in.scjson> -o <out.scxml>`
- This fallback is only about file format conversion; execution/tracing is still performed by the Ruby engine. Using the Python converter keeps the canonical JSON identical across languages and avoids CI‑only variance.
- If preferred, pre‑convert charts up front and run the Ruby engine on scjson inputs to bypass XML parsing entirely:
  - `python -m scjson.cli json chart.scxml -o chart.scjson`
  - `ruby/bin/scjson engine-trace -I chart.scjson -e chart.events.jsonl`

Documentation coverage
- Conversion and documentation build checks run earlier in the CI pipeline; by the time the Ruby engine harness executes, the docs and converters have already been validated. The Nokogiri fallback simply removes the need for a Ruby‑native XML stack in later stages.

## Troubleshooting

- Known differences in CI runs
  - Some charts have intentional, documented differences between engines (e.g., ECMA `in` semantics, history reentry nuances). Use the known‑diffs list to keep CI green while still reporting these cases:
    - File: `scripts/ci_ruby_known_diffs.txt`
    - Harness: `bash scripts/ci_ruby_harness.sh --list scripts/ci_ruby_charts.txt --known scripts/ci_ruby_known_diffs.txt`

- Normalization profile for comparisons
  - Use the SCION profile to align output fields and ordering across engines:
    - `python py/exec_compare.py <chart> --events <events> --reference "node tools/scion-runner/scion-trace.cjs" --norm scion`
  - `--norm scion` sets: leaf‑only, omit‑delta, omit‑transitions, strip‑step0‑states, and ordering=scion.

- Pre‑convert SCXML to scjson for Ruby execution
  - To avoid XML parser differences or Nokogiri setup on your machine, pre‑convert once and run Ruby on scjson:
    - `python -m scjson.cli json chart.scxml -o chart.scjson`
    - `ruby/bin/scjson engine-trace -I chart.scjson -e chart.events.jsonl`

- Nokogiri dependency (local development)
  - Ruby’s SCXML↔scjson converter uses the Nokogiri gem for XML parsing when running from source. If the gem is not installed, the Ruby CLI falls back to the Python converter transparently (see “CI Notes”).
  - For best local performance and to keep everything in Ruby, install Nokogiri (and system build deps) in your environment. Otherwise the Python fallback will be used for conversion while execution remains in Ruby.

---

Back to
- Architecture & reference: `ruby/ENGINE-RB-DETAILS.md`
- Compatibility Matrix: `docs/COMPATIBILITY.md`
- Project overview: `README.md`
