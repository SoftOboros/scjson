# Python Engine Convergence — Expanded Context Snapshot (2025-10-02)

This expanded snapshot is designed to fast‑track resumption after a cold restart. It captures what matters right now: where things live, what changed, how to reproduce, and what to do next.

## Quick Resume
- Run unit tests: `PYTHONPATH=py pytest -q py/tests`
- Enable slow smoke explicitly: `PYTHONPATH=py pytest -q -m slow -k "uber_test and executes_chart"`
- Parameterized smoke (one test per tutorial chart):
  - All: `PYTHONPATH=py pytest -q -k "uber_test and executes_chart"`
  - Filter by name: `PYTHONPATH=py pytest -q -k "executes_chart and parallel_invoke_complete.scxml"`
- CLI smoke with progress output:
  - All: `python py/uber_test.py --python-smoke`
  - Single chart: `python py/uber_test.py --python-smoke --chart tutorial/Tests/python/W3C/Mandatory/Auto/test253.scxml`
- Verify W3C outcomes (advance timers):
  - `PYTHONPATH=py python -m scjson.cli engine-verify -I tutorial/Tests/python/W3C/Mandatory/Auto/test253.scxml --xml --advance-time 3`
  - Repeat for 338, 422, 554 → expected: pass
  - 401 (generic error precedence): `--xml` (no advance) → expected: pass
- Compare traces vs reference (leaf-only + step-0 normalization):
  - `python py/exec_compare.py <chart.scxml> --events <events.jsonl>`
  - Optional: `--keep-step0-states` to preserve step-0 entered/exited

## Repo Pointers (What/Where)
- Engine core: `py/scjson/context.py`
  - Macro/Microstep, transition selection: `_select_transition`
  - Entry/Exit & History: `_enter_state`, `_exit_state`, `_enter_history`, `_handle_entered_final`
  - Exec content: `_run_actions`, `_iter_actions`, `_build_action_sequence`
  - Send/Cancel: `_do_send`, `_do_cancel`, timers: `_schedule_event`, `_release_delayed_events`, `advance_time`
  - Expressions & scope: `_scope_env`, `_evaluate_expr` (safe eval by default)
  - Invoke lifecycle: `_start_invocations_for_state`, `_start_invocations_for_active_states`, `_on_invoke_done`, `_cancel_invocations_for_state`
  - Error helper: `_emit_error` (specific + generic alias for `error.execution`)
- Invoke subsystem: `py/scjson/invoke.py` (mock:immediate, mock:record, mock:deferred, scxml/scjson child)
- Events/queue: `py/scjson/events.py` (`Event` includes `origin`, `origintype`, `invokeid`)
- CLI: `py/scjson/cli.py` (`engine-trace`, `engine-verify`)
- Trace compare tool: `py/exec_compare.py`
- Exec compare wrapper for tests: `py/py/exec_compare.py`
- Design/Docs: `py/scjson/ENGINE.md`, `docs/TODO-ENGINE-PY.md`
- Tutorial/Corpus: `tutorial/` (W3C + examples), skip list: `py/uber_test.py::ENGINE_KNOWN_UNSUPPORTED`

## Behavioral Snapshot (Implemented)
- Execution + Structure
  - Macrostep loop with eventless transitions until quiescence
  - Deterministic transition selection (document order)
  - Entry/exit sets via LCA; parallel emits region done and parent done
  - Shallow and deep history (deep restores exact descendant leaves)
  - Exec content: assign, log, raise, if/elseif/else, foreach, send (immediate + delayed), cancel, script(no-op)
- Expressions & Errors
  - Safe eval by default; `--unsafe-eval` optional
  - `error.execution` when cond/foreach/assign exprs fail or cond non-boolean (push-front)
  - Generic `error` alias emitted for `error.execution` (not for `error.communication`) to support charts listening to `error.*`
  - Assign to invalid location: enqueue `error.execution` (no variable creation); alias prioritized for onentry ordering
- Sends & Timers
  - Internal: `#_internal`/`_internal` enqueue into the engine queue
  - External: unsupported targets raise `error.communication` and are skipped
  - Deterministic delayed sends: `advance_time(seconds)` releases in order
  - Control tokens: `engine-trace` accepts event-stream lines like `{"advance_time": N}` to advance time without emitting a step (used by vector generation)
- Invoke
  - Macrostep-end start for states entered and not exited during the step
  - Parent↔Child: `#_parent` bubbling; parent `#_child`/`#_invokedChild` and explicit `#_<invokeId>`
  - Autoforward external events to active invocations (skips canceled)
  - Finalize runs in invoking state; `_event` maps include `name`, `data`, `invokeid`, optional `origin`/`origintype`
  - Done ordering: id-specific then generic by default, with preferences to preserve ordering when child emits during init
  - Child scxml/scjson start failure surfaces `error.communication`
- Event Matching
  - Space-separated event lists
  - Wildcard `*` and prefix patterns like `error.*`

## Trace Normalization
- Leaf-only comparison (config/entered/exited limited to leaf states)
- Step-0 noise stripping by default: `datamodelDelta` and `firedTransitions`
- Optional: strip step-0 `enteredStates`/`exitedStates` unless `--keep-step0-states` is provided

## Current Status
- Unit suite (Python): green → `PYTHONPATH=py pytest -q py/tests`
- W3C mandatory quick set outcomes (with `--advance-time 3` where applicable):
  - 253: pass; 338: pass; 422: pass; 554: pass
  - 401: pass (generic error precedence via invalid-assign + alias)
- Tutorial python-datamodel charts discovered: 208
- Ad-hoc sample of 50 charts: no failures to construct a step via `trace_step()`

## Diff (Since Prior Snapshot)
- engine-trace: supports `{"advance_time": N}` control tokens within events JSONL
- vector_gen: injects mid-sequence `advance_time` tokens when timers are pending after a step
- Added curated `tests/sweep_corpus/*` and advanced exec_compare tests
- Added shim `py/py/exec_compare.py` for test path stability
- uber_test: parameterized per-chart tests; CLI smoke mode with per-chart progress
- Docs updated: control tokens, vector injection, invoke/finalize semantics

## Reproduction Recipes
Unit tests
- All Python tests: `PYTHONPATH=py pytest -q py/tests`
- Single test: `PYTHONPATH=py pytest -q py/tests/test_engine.py::test_invoke_generic_done_event`

Engine outcome
- `PYTHONPATH=py python -m scjson.cli engine-verify -I tutorial/Tests/python/W3C/Mandatory/Auto/test253.scxml --xml --advance-time 3`
- 401: `PYTHONPATH=py python -m scjson.cli engine-verify -I tutorial/Tests/python/W3C/Mandatory/Auto/test401.scxml --xml`

Trace compare
- Primary: `python py/exec_compare.py <chart.scxml> --events <events.jsonl>`
- Optional: `--keep-step0-states` to retain step-0 `enteredStates`/`exitedStates`
- Reference fallback is auto-resolved to `node tools/scion-runner/scion-trace.cjs`; override via `SCJSON_REF_ENGINE_CMD`

Uber harness (cross‑lang conversion)
- Path: `py/uber_test.py`
- Python engine smoke (parameterized): `PYTHONPATH=py pytest -q -k "uber_test and executes_chart"`
- CLI smoke with progress: `python py/uber_test.py --python-smoke [--chart <path>]`

## Known Differences & Notes
- Initialization visibility varies across engines; step-0 normalization mitigates diffs
- Invoke IDs differ; not behaviorally relevant
- External processors (HTTP) remain unsupported; tests that rely on them are left in `ENGINE_KNOWN_UNSUPPORTED`

## Next Steps
- Broader tutorial sweep and incremental skip‑list reductions
- Validate more charts with exec_compare and adjust normalization only if required
- Consider marking parameterized smoke as `@pytest.mark.slow` and using `-k` filters by default

## Handy Greps
- Jump to key spots:
  - `rg -n "_emit_error|_select_transition|finalize|#_parent|invokeid|error\.execution|error\.communication" py`
  - `rg -n "engine-verify|engine-trace" py/scjson/cli.py`  
  - `rg -n "InvokeRegistry|SCXMLChildHandler|send\(\)" py/scjson/invoke.py`
  - `rg -n "advance_time|control token|advance-time" py`
