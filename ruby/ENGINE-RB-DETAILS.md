<p align="center"><img src="../scjson.png" alt="scjson logo" width="200"/></p>

Agent Name: ruby-engine-details

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

# Ruby Engine — Architecture & Details

This document outlines the architecture, design goals, and implementation notes for the Ruby execution engine. It tracks parity with the Python reference where appropriate while following Ruby idioms.

## Goals

- Execute SCXML/SCJSON with SCION‑compatible semantics
- Deterministic JSONL trace output (schema matching Python)
- Lax/strict modes analogous to Python
- Support for multi‑document invoke/finalize lifecycle

## Components

- `Scjson::Engine` – public entry point for tracing execution (`engine.rb`)
- CLI: `scjson engine-trace` – wrapper around `Scjson::Engine.trace`
- Future: core runtime (document context, activation/configuration, event queue)

## Trace Schema

Each trace line is a JSON object with fields:

- `step` – integer step number (0 is initialization)
- `event` – `{ "name": string, "data": any } | null`
- `configuration` – `[string]` current active configuration
- `enteredStates` / `exitedStates` – `[string]` deltas for the step
- `firedTransitions` – `[object]` transitions taken this step
- `actionLog` – `[object]` executed actions (order preserved)
- `datamodelDelta` – `{string: any}` datamodel changes (normalized keys)

## Execution Algorithm (preview)

1. Initialization (step 0): compute initial configuration
2. Process events: macrostep loop to quiescence, microsteps per transition set
3. Timers: support `advance_time` tokens in event streams for determinism

## Parity With Python

- Flags: `--leaf-only`, `--omit-delta`, `--omit-actions`, `--omit-transitions`, `--advance-time`, `--ordering`
- Normalization: step‑0 noise stripping handled in compare tooling
- Coverage & vectors: reuse Python generator and harness

## Status

The initial implementation provides a contract‑level CLI (`engine-trace`) that prints a well‑formed trace with step 0 and one line per input event. The core runtime will replace the stub to achieve SCION‑compatible behavior.

See also
- User guide: `docs/ENGINE-RB.md`
- Checklist plan: `docs/TODO-ENGINE-RUBY.md`
