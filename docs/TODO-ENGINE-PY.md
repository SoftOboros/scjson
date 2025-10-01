Agent Name: python-engine-todo

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

# Python Execution Engine — Checklist Plan

This checklist tracks work to take the current Python runtime (DocumentContext + Activation/Event modules) to a feature‑complete SCXML execution engine validated against a canonical reference engine.

## Scope & Goals
- [ ] Implement SCXML execution algorithm (macrostep/microstep), event processing, transition selection, conflict resolution, configuration management.
- [ ] Support compound, parallel, final, and history states (shallow/deep) with correct completion semantics.
- [ ] Implement executable content: assign, log, raise, if/elseif/else, foreach, script, send/cancel, invoke/finalize, param/content.
- [x] Provide a CLI to run a chart against an event script and emit a deterministic JSON trace for comparison. (`scjson engine-trace`)
- [ ] Validate behavior across a stock corpus by comparing traces against a canonical engine.

## Reference Semantics
- [x] Decide canonical reference engine.
  - [x] Use scion-core (Node.js) as the canonical reference for behavior.
  - [x] Document rationale and guidance for scion compatibility in repo docs.
- [ ] Provide comparison against Apache Commons SCXML 0.x as historical reference when needed (build/run optional).

## Roadmap (Iterations)

1) Core Algorithm & Trace
- [x] Make `scjson.context` the single runtime source (retire/repurpose `engine.py`).
- [x] Implement macrostep loop (process eventless transitions until quiescence).
- [x] Deterministic transition selection (document order, ancestor checks, conflict resolution).
- [x] Define standardized JSON trace schema (event, firedTransitions, enteredStates, exitedStates, configuration, actionLog, datamodelDelta).
- [x] Add CLI: `scjson engine-trace -I path.[scxml|scjson] [--xml] -e events.jsonl`.

2) Compound, Parallel, Final, History
- [x] Compute exit/entry sets via LCA; correct ancestor/descendant handling.
- [ ] Parallel completion: parent final when all regions complete; propagate finalization.
- [x] History: shallow with default transition fallback.
- [ ] History: deep (restore deep descendants).
- [x] Parallel: initial entry enters all child regions.

3) Executable Content Phase 1
- [x] Implement assign, log, raise within onentry/onexit/transition bodies.
- [ ] Implement if/elseif/else.
- [ ] Implement foreach.
- [ ] Replace `eval` with safe expression evaluator/sandbox; document trust model and add `--unsafe-eval` for trusted runs.

4) Events, Timers, and External I/O
- [x] Basic internal `EventQueue` for external/internal events.
- [ ] `<send>` (delay, target), `<cancel>` by ID; external sinks.
- [ ] Emit error events (`error.execution`, `error.communication`, …) into trace.
- [ ] Timers with mock clock for deterministic tests.

5) Invoke / Finalize
- [ ] `<invoke>` lifecycle with `autoforward`.
- [ ] `<param>` and `<finalize>` handling.
- [ ] Pluggable InvokeRegistry with test/mocked invokers.

6) Robustness & Performance
- [ ] Lax vs strict execution modes; unknown element/attribute behavior.
- [ ] Snapshot sizing/log filters; reproducible ordering for sets.
- [ ] Update `ENGINE.md` to match implementation and trace schema.

## Test Strategy

Reference Engine Runner
- [ ] Implement Java runner wrapper (preferred):
  - [ ] Load SCXML with Commons SCXML2, consume JSONL events on stdin, emit standardized trace on stdout.
  - [ ] Package as Maven exec target or fat‑jar under `java/runner`.
- [x] Implement Node runner wrapper (fallback, if Java runner not feasible): thin `scion-core` script emitting the same trace format (see `tools/scion-runner/scion-trace.cjs`).

Artifacts & Datasets
- [ ] Use tutorial submodule + permissible W3C tests as stock corpus.
- [x] Add `tests/exec/` with curated charts and JSONL event scripts.

Trace Schema (per line JSON)
- [x] `step`: integer.
- [x] `event`: `{ name, data } | null`.
- [x] `firedTransitions`: `[{ source, targets:[...], event, cond }]`.
- [x] `enteredStates`: `[stateId]`.
- [x] `exitedStates`: `[stateId]`.
- [x] `configuration`: `[stateId]` (sorted).
- [x] `actionLog`: `[string]` (optional; stable order).
- [x] `datamodelDelta`: `{ key: newValue }` (optional; only changed keys).

Harness Logic
- [x] Python runner produces `py.trace.jsonl`.
- [x] Reference runner produces `ref.trace.jsonl`.
- [x] Normalizer for ordering and simple type normalization.
- [x] Step-by-step diff and summary (first differing step, mismatch counts).
- [ ] Report totals similar to `uber_test` (files and item mismatches).

CLI Additions (Python)
- [x] Implement `scjson engine-trace`.
- [x] Inputs: `--xml`, `-I/--input`, `-e/--events`, `-o/--out`.
- [ ] Options: `--lax/--strict`, `--unsafe-eval` (default off), `--max-steps`.

Comparison Tooling
- [x] Add `py/exec_compare.py` (or integrate into `uber_test.py`) to drive both runners and diff traces with CI‑friendly exit codes.
- [x] Support optional secondary comparisons (e.g., Scion vs Apache Commons) via CLI/env overrides.

## Milestones & Deliverables
- [ ] M1: Core trace + macrostep + CLI; trace unit tests; 10 simple charts pass vs chosen runner.
- [ ] M2: Parallel + finalization + shallow history; expanded corpus; runner usage docs.
- [ ] M3: Safe expression evaluator; exec content conformance; increased coverage.
- [ ] M4: send/cancel/timers with mock clock; error events; trace schema stabilized.
- [ ] M5: invoke/finalize with mocks; CI job for full corpus diff.

## Risks & Mitigations
- [ ] Decide on reference engine if Maven hoops block Java; switch to a free alternative with comparable authority (e.g., scion-core).
- [ ] Constrain expression features to cross‑engine subset or inject via event data; provide Python‑only mode for advanced expressions.
- [ ] Enforce deterministic ordering where SCXML permits implementation choice.

## Acceptance Criteria
- [ ] Python traces match reference traces for the selected corpus (configuration, fired transitions, entry/exit actions).
- [ ] CI job executes the harness and reports zero mismatches.
- [ ] Documentation (`ENGINE.md`, this TODO, CLI help) is updated.

## Immediate Next Steps
- [x] Add `engine-trace` subcommand emitting the standardized trace.
- [x] Draft Java (or Node) runner that emits the same trace format.
- [x] Create `tests/exec/` with 5–10 seed charts and event scripts; add a minimal `exec_compare.py` to run both and diff.

### Notes
- As of Sept 2025, Apache Commons SCXML is considered deprecated/legacy; scion-core is the authoritative implementation for behavioral compatibility.
- Historical Commons SCXML builds (0.x) may be kept for reference but are not required for CI.
