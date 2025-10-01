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
  - [x] Document rationale and guidance for scion compatibility in repo docs. (`py/scjson/ENGINE.md`)
- [ ] Provide comparison against Apache Commons SCXML 0.x as historical reference when needed (optional, for historical parity).

## Roadmap (Iterations)

1) Core Algorithm & Trace
- [x] Make `scjson.context` the single runtime source (retire/repurpose `engine.py`).
- [x] Implement macrostep loop (process eventless transitions until quiescence).
- [x] Deterministic transition selection (document order, ancestor checks, conflict resolution).
- [x] Define standardized JSON trace schema (event, firedTransitions, enteredStates, exitedStates, configuration, actionLog, datamodelDelta).
- [x] Add CLI: `scjson engine-trace -I path.[scxml|scjson] [--xml] -e events.jsonl`.

2) Compound, Parallel, Final, History
- [x] Compute exit/entry sets via LCA; correct ancestor/descendant handling.
- [x] Parallel completion: parent final when all regions complete; propagate finalization.
- [x] History: shallow with default transition fallback.
 - [x] History: deep (restore deep descendants).
- [x] Parallel: initial entry enters all child regions.

3) Executable Content Phase 1
- [x] Implement assign, log, raise within onentry/onexit/transition bodies.
- [x] Implement if/elseif/else.
- [x] Implement foreach.
- [x] Replace `eval` with safe expression evaluator/sandbox; document trust model and add `--unsafe-eval` for trusted runs.

4) Events, Timers, and External I/O
- [x] Basic internal `EventQueue` for external/internal events.
- [x] `<send>` (delay, target), `<cancel>` by ID; external sinks.
 - [x] Emit error events (`error.execution`, `error.communication`, …) into trace.
- [x] Timers with mock clock for deterministic tests. (Delayed `<send>` scheduling uses `DocumentContext.advance_time` for deterministic control.)

5) Invoke / Finalize
 - [x] Add scaffolding: InvokeRegistry + mock handler; start/cancel on state entry/exit; `<finalize>` executes on completion/cancel; emits `done.invoke` and `done.invoke.<id>`.
 - [x] Implement basic `<invoke>` lifecycle with `autoforward` and child bubbling.
 - [x] Support child `<send target="#_parent">` and parent `<send target="#_child">`.
 - [x] Handle inline `<invoke><content>` SCXML and file: URIs, type URI normalization.
 - [x] Complete `<param>`/`<content>` mapping and `_event` exposure for finalize (tests added).
 - [x] Expand registry: `mock:immediate`, `mock:record`, `mock:deferred`, `scxml`/`scjson` child; tests for ordering and concurrency.

6) Robustness & Performance
- [ ] Lax vs strict execution modes; unknown element/attribute behavior.
- [ ] Snapshot sizing/log filters; reproducible ordering for sets.
 - [x] Update `ENGINE.md` to match implementation and trace schema.

## Status Snapshot — 2025-09-30
- Engine executes `if`/`elseif`/`else`, `foreach`, `<send>` (immediate + delayed), `<cancel>`, and transition bodies in authoring order.
- Parallel completion: emits `done.state.<regionId>` events per region and `done.state.<parallelId>` when all regions are final. Compound states emit `done.state.<parentId>` with `<donedata>` payload.
- History: shallow and deep restore supported. Default history transition actions execute when no snapshot exists.
- Delayed `<send>` tasks schedule against `DocumentContext` and are advanced deterministically with `advance_time`; external targets enqueue `error.communication` and are skipped.
- Error events: non-boolean/failed `cond`, `<foreach>` array errors, and `<assign>` evaluation failures enqueue `error.execution`.
  - Engine-generated error events are prioritized to the front of the queue so they are processed before subsequently enqueued normal events.
- Tutorial sweep (`py/uber_test.py::test_python_engine_executes_python_charts`) honors `ENGINE_KNOWN_UNSUPPORTED` and is being reduced as features land.
- Textual `<send><content>` blocks are normalized during JSON ingestion; location attributes receive autogenerated IDs before Pydantic validation.
- Integration tests cover textual, expression, and nested markup payloads emitted by `<send>`.
- Documentation in `py/scjson/ENGINE.md` describes done events, history semantics, transition-body ordering, and error events.

## Test Strategy

Reference Engine Runner
- [ ] Implement Java runner wrapper (preferred):
  - [ ] Load SCXML with Commons SCXML2, consume JSONL events on stdin, emit standardized trace on stdout.
  - [ ] Package as Maven exec target or fat‑jar under `java/runner`.
- [x] Implement Node runner wrapper (fallback, if Java runner not feasible): thin `scion-core` script emitting the same trace format (see `tools/scion-runner/scion-trace.cjs`).

Artifacts & Datasets
- [ ] Use tutorial submodule + permissible W3C tests as stock corpus.
- [x] Add `tests/exec/` with curated charts and JSONL event scripts.
- [x] `py/uber_test.py` sweeps tutorial Python charts with skip-aware `ENGINE_KNOWN_UNSUPPORTED` handling and aggregated failure output.

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
- [x] Report totals similar to `uber_test` (files and item mismatches).

CLI Additions (Python)
- [x] Implement `scjson engine-trace`.
- [x] Inputs: `--xml`, `-I/--input`, `-e/--events`, `-o/--out`.
 - [x] Options:
  - [x] `--lax/--strict`
  - [x] `--unsafe-eval` (default off)
  - [x] `--max-steps`

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
 - [x] Update `py/scjson/ENGINE.md` with current limitations (skip list, `<script>` noop, external send targets) and safe-eval guidance.
 - [x] Add focused unit tests covering delayed `<send>` scheduling/cancellation via `DocumentContext.advance_time`.
- [x] Add integration coverage for normalized `<send><content>` payloads to ensure parity with scion-core. (`py/tests/test_engine.py::test_send_content_*`)
- [x] Add focused tests for deep history across parallel and donedata precedence (content dominates params).
- [x] Add ordering tests for `error.execution` and `error.communication` vs normal events; prioritize error events in the queue.
- [ ] Review `ENGINE_KNOWN_UNSUPPORTED` in `py/uber_test.py:44-58` and plan removals as features land.

### Notes
- As of Sept 2025, Apache Commons SCXML is considered deprecated/legacy; scion-core is the authoritative implementation for behavioral compatibility.
- Historical Commons SCXML builds (0.x) may be kept for reference but are not required for CI.
- External send targets (e.g., `#_scxml_*`, HTTP processors) now enqueue `error.communication` and are skipped; `<script>` actions still emit warnings and are no-ops.
- Tutorial sweep guardrails live in `py/uber_test.py::ENGINE_KNOWN_UNSUPPORTED`; revisit after expanding coverage.
