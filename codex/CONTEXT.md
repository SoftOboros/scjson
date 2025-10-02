# Python Engine — Context Snapshot (2025-10-02)

This file captures the current runtime/CLI/test context so work can continue smoothly after a cold restart. It points to the right files, summarizes behaviors that matter for compatibility, and includes reproducible commands used during development.

## Overview
- Canonical reference: scion-core (Node) via `tools/scion-runner/scion-trace.cjs`
- Python runtime core: `py/scjson/context.py` (DocumentContext)
- Invoke subsystem: `py/scjson/invoke.py`
- Events/queue: `py/scjson/events.py`
- CLI: `py/scjson/cli.py` (`engine-trace`, `engine-verify`)
- Trace compare: `py/exec_compare.py` (leaf-only + step-0 normalization)
- Tests: `py/tests/*` (engine core in `py/tests/test_engine.py`)
- Docs/TODO: `docs/TODO-ENGINE-PY.md`, detailed design: `py/scjson/ENGINE.md`

Environment constraints
- Python is preconfigured; do not run pip/poetry
- JavaScript CLI entry is `js/dist/index.js`; run `npm run build` before using Node CLI in uber tests

Recent highlights (landed)
- Exec compare normalization: strips step-0 `datamodelDelta` and `firedTransitions`; `--keep-step0-states` optionally keeps step-0 `enteredStates`/`exitedStates`.
- Error semantics: generic `error` alias emitted alongside `error.execution` (not for `error.communication`) to support charts listening to `error.*`.
- Assign semantics: assigning to a non-existent location enqueues `error.execution` and does not create variables (enables W3C test401).
- Event matching: transitions support space-separated names, wildcard `*`, and prefix patterns like `error.*`.
- Invoke src failure (scxml/scjson child): emits `error.communication`.
- Invoke lifecycle: macrostep-end start; parent↔child sends via `#_parent`, `#_child`/`#_invokedChild`, explicit `#_<invokeId>`; finalize runs in invoking state and sets `_event`.
- Timers: deterministic delayed `<send>` via `DocumentContext.advance_time`, with support for mid-sequence time-advance control tokens.

Stable semantics (previously landed)
- Macrostep/microstep, entry/exit sets via LCA
- Parallel done ordering + region completion
- History: shallow + deep (deep restores exact descendant leaves)
- Executable content: assign, log, raise, if/elseif/else, foreach, send, cancel, script(no-op warning)
- Error events: `error.execution` push-front; external sends produce `error.communication`

Where to look (file pointers)
- Engine core: `py/scjson/context.py`
  - Transition selection with multi-event + wildcard: `_select_transition`
  - Execute transitions: `_fire_transition`, `_run_actions`, `_iter_actions`
  - History, entry/exit: `_enter_state`, `_exit_state`, `_enter_history`, `_handle_entered_final`
  - Error helper: `_emit_error`
  - Assign/send/cancel: `_do_assign`, `_do_send`, `_do_cancel`
  - Invoke lifecycle: `_start_invocations_for_state`, `_start_invocations_for_active_states`, `_on_invoke_done`, `_cancel_invocations_for_state`
  - Expressions: `_scope_env`, `_evaluate_expr` (safe eval by default; `allow_unsafe_eval` opt-out)
  - Timers: `_schedule_event`, `_release_delayed_events`, `advance_time`
- Invokers: `py/scjson/invoke.py`
  - Handlers: mock:immediate, mock:record, mock:deferred, scxml/scjson child
  - Bubbling child events with SCXML Event I/O metadata (`origintype`, `invokeid`)
- CLI: `py/scjson/cli.py` (`engine-trace`, `engine-verify`) with `--xml`, `--lax/--strict`, `--unsafe-eval`, `--max-steps`, `--advance-time`
- Compare: `py/exec_compare.py` (leaf-only normalization, step-0 noise stripping, optional strip of step-0 states)
- Events: `py/scjson/events.py` (Event carries `origin`, `origintype`, `invokeid`)
 - Wrapper for tests expecting path: `py/py/exec_compare.py`

## Repro Commands
Unit tests (Python)
- `PYTHONPATH=py pytest -q py/tests`
- Single test: `PYTHONPATH=py pytest -q py/tests/test_engine.py::test_name`
 - Parameterized smoke over tutorial charts (one test per chart):
   - All: `PYTHONPATH=py pytest -q -k "uber_test and executes_chart"`
   - Filter by name: `PYTHONPATH=py pytest -q -k "executes_chart and history_shallow.scxml"`

Engine outcome (W3C charts)
- `PYTHONPATH=py python -m scjson.cli engine-verify -I tutorial/Tests/python/W3C/Mandatory/Auto/test253.scxml --xml --advance-time 3`
- Same for: 338, 422, 554 → current outcome: pass
- 401 (generic error precedence) now passes due to invalid-assign + alias semantics:
  - `PYTHONPATH=py python -m scjson.cli engine-verify -I tutorial/Tests/python/W3C/Mandatory/Auto/test401.scxml --xml`

Trace compare vs reference
- Primary: `python py/exec_compare.py <chart.scxml> --events <events.jsonl>`
- Defaults: reference runner `node tools/scion-runner/scion-trace.cjs` when available
- Optional: `--keep-step0-states` to preserve step-0 `enteredStates`/`exitedStates`
- Env override: `SCJSON_REF_ENGINE_CMD` to supply a reference command

Node runner setup (if needed)
- The repo includes `tools/scion-runner/scion-trace.cjs` and `node_modules`.
- Use directly: `node tools/scion-runner/scion-trace.cjs --help`

## Current Status & Checks
Engine unit suite
- Status: green (Python tests pass)
- Focused checks include: deep history, parallel finalize ordering, send content normalization, error event priority, invoke finalize scope, explicit `#_<invokeId>` targeting, event pattern matching, CLI control-token handling, and vector time-advance injection.

W3C/Tutorial highlights
- Mandatory W3C: 253/338/422/554 pass with `--advance-time 3`
- Mandatory W3C: 401 now passes (invalid assign → `error.execution` + `error` alias ensures generic error precedence)
- Python datamodel tutorial charts discovered: 208
- Ad-hoc sample of 50 python-datamodel charts: no failures constructing traces (`DocumentContext.from_xml_file(...).trace_step()`)

Skip list maintenance
- `py/uber_test.py::ENGINE_KNOWN_UNSUPPORTED` no longer includes W3C test401
- Remaining entries are Optional tests unrelated to current scope (HTTP processors, etc.)

## Behavioral Notes
Step-0 trace normalization
- Engines differ on initial transition visibility; normalization strips step-0 datamodelDelta and firedTransitions by default
- Optionally strip step-0 entered/exited lists as well to reduce diff noise

Event matching
- Accepts space-separated event names, wildcard `*`, and prefix `error.*`

Error events ordering
- `error.execution` is push-front; also emits generic `error` (not push-front by default unless explicitly needed to preserve onentry ordering semantics)
- `error.communication` does not emit alias to avoid interleaving with explicit events

Invoke
- Finalize runs in invoking state with `_event` dict (`name`, `data`, `invokeid`, and any origin/origintype)
- Done ordering defaults to id-specific then generic; preference adjusted when children emit events during init to preserve observed ordering
- Macrostep-end start: only for states still active at end of step

## What Changed This Session
- engine-trace: accepts `{"advance_time": N}` control tokens in events JSONL; advances mock clock without emitting a step.
- vector_gen: injects `advance_time` control tokens between stimuli when timers are pending after a step.
- Tests: added CLI control-token test; added curated sweep_corpus charts and advanced exec_compare tests.
- Wrapper: added `py/py/exec_compare.py` for tests invoking that path.
- uber_test: parameterized per-chart tests for faster feedback; `python py/uber_test.py --python-smoke` prints per-chart progress and status.
- Docs: `docs/ENGINE-PY.md` updated with control tokens, vector time-advance injection, and invoke/finalize semantics.
 - Engine ordering: added explicit `ordering` policy with `scion` mode. In `scion` mode child→parent emissions enqueue normally while `done.invoke` is pushed to the front (generic before id‑specific) to align with SCION microstep behavior.

## Next Steps (Suggested)
- Optional: mark parameterized uber tests `@pytest.mark.slow` to exclude from default runs; prefer targeted `-k` filters for iteration.
- Broaden curated corpus; evolve vector heuristics for deeper coverage.

## Quick Resumption Checklist
- Run unit suite: `PYTHONPATH=py pytest -q py/tests`
- Verify W3C quick set: 253/338/422/554/401 with `engine-verify`
- For diffs against reference, use `py/exec_compare.py` with or without `--keep-step0-states`
- When editing invoke/child behavior, retest:
  - `py/tests/test_engine.py::test_invoke_*`
  - child bubbling and finalize ordering tests
 - Python smoke with progress:
   - `python py/uber_test.py --python-smoke`
   - `python py/uber_test.py --python-smoke --chart tutorial/Tests/python/W3C/Mandatory/Auto/test253.scxml`

Fast Grep
- `rg -n "_emit_error|_select_transition|finalize|#_parent|invokeid|error\.execution|error\.communication" py` to jump into relevant code
 - `rg -n "advance_time|control token|advance-time" py`
