<p align="center"><img src="../scjson.png" alt="scjson logo" width="200"/></p>

Agent Name: ruby-engine-todo

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

# Ruby Execution Engine — Checklist Plan

This checklist tracks work to deliver a Ruby execution engine with full [SCION](https://www.npmjs.com/package/scion)-compatible behavior and cross-language parity with the Python engine. The plan also covers packaging, documentation, and integration into the existing validation harness.

## Scope & Goals
- [ ] Implement SCXML execution algorithm (macro/microstep), event processing, transition selection, conflict resolution, configuration management.
- [ ] Achieve full SCION-compatible semantics for Ruby, matching traces on a shared corpus (normalization allowed where appropriate).
- [ ] Mirror Python engine capabilities first (single document), then extend to full SCION-equivalent behavior for multiple documents (invoke/finalize, child machines, done events).
- [ ] Keep the validation pipeline the same as Python: use the Python harness to evaluate Ruby engine execution vs SCION and/or Python.
- [ ] Convert test docs currently tailored for JS and Python into Ruby test vector extensions (in-repo only; do not edit tutorial content).
- [ ] Provide a dedicated Ruby engine user guide (like Python’s), with deeper details and runnable examples.
- [ ] Highlight the Ruby engine in the top of the README and mention SCXML/SCML execution in description, package metadata, and search terms.
- [ ] Enhance RubyGems documentation support and add RubyGems package details to the bottom section of the README.
- [ ] Bump project version to 0.3.4 as part of the release including the Ruby engine.

## Reference Semantics
- [ ] Use [SCION](https://www.npmjs.com/package/scion) (Node) as behavioral reference.
- [ ] Compare Ruby engine traces against SCION and Python traces via the Python harness tools.
- [ ] Document any implementation-defined ordering or known deltas and provide normalization flags consistent with Python.

## Roadmap (Iterations)

1) Bootstrap & Parity with Python (single document)
- [x] Define Ruby runtime core (document context, configuration, event queue, selection/conflict rules — basic, single-transition).
- [x] Implement eventless transitions to quiescence (basic macrostep; bounded).
- [x] Implement LCA-based exit/entry ordering for single-transition microsteps (basic; leaves-only configuration).
- [x] Transition condition evaluation (basic: literals, variables, ==/!=, numeric comparisons).
- [ ] Implement full macrostep loop and complete conflict resolution to match Python.
- [x] Executable content Phase 1 (subset): log, assign (literals and +N increments), raise, if/elseif/else, foreach.
- [ ] Event I/O: internal queue, error events; timers via mock clock (advance_time control token accepted in event streams to match Python’s deterministic traces).
- [x] CLI: `scjson engine-trace` in Ruby, emitting deterministic JSONL traces (same schema as Python).
- [x] Integrate with `py/exec_compare.py` as a “secondary” engine under test (use `--secondary "ruby/bin/scjson engine-trace"`).

2) Multi-document & Invoke/Finalize
- [ ] Implement `<invoke>` lifecycle, `<finalize>`, `done.invoke`/`done.invoke.<id>` events.
- [ ] Support child machines (`scxml`/`scjson` inline and file: URIs); `#_parent` and `#_child`/`#_<id>` targets.
- [ ] Parallel completion, history (shallow/deep), and final states semantics.
- [ ] Error handling and ordering consistent with SCION; adopt Python’s normalization knobs where helpful.

3) Validation Harness Integration
- [ ] Wire Ruby CLI into `py/exec_compare.py` and `py/exec_sweep.py` (command string + cwd assumptions documented).
- [ ] Normalize traces with leaf-only/omit-delta/step-0 controls mirroring Python flags.
- [ ] CI target to run a subset of charts on every PR against SCION and Python.

4) Documentation & Examples
- [x] Create `docs/ENGINE-RB.md` (user guide) mirroring `docs/ENGINE-PY.md` structure.
- [x] Add `ruby/ENGINE-RB-DETAILS.md` (architecture & in-depth reference) analogous to `py/ENGINE-PY-DETAILS.md`.
- [ ] Port JS/Python example event streams into Ruby-focused examples (without changing `tutorial/`).
- [ ] Add troubleshooting and normalization guidance (step-0, timers, expression limitations).

5) Packaging & Release
- [x] Enhance RubyGems doc support: README sections, YARD/RDoc hooks, homepage and source links, extended summary/description.
- [ ] Update gem metadata keywords (search terms): "scxml", "statecharts", "state-machine", "scjson", "scml", "execution".
- [x] README updates: highlight Ruby engine at the top; add RubyGems package details at bottom.
- [x] Version bump to 0.3.4 across repo (Python and Ruby packages updated).

## Test Vectors & Corpora
- [ ] Convert JS/Python test docs into Ruby vector extensions hosted in-repo (e.g., `tests/exec/*.events.jsonl` variants if Ruby requires timing tokens). Do not modify `tutorial/` content.
- [ ] Ensure the Python harness can select Ruby as target via `-l ruby` and aggregate coverage in `uber_out/`.
- [ ] Add a small Ruby-specific corpus to exercise multi-document (invoke/finalize) semantics.

## Acceptance Criteria
- [ ] Ruby engine traces match SCION on the canonical corpus (after normalization) and match Python on shared subsets.
- [ ] CI job runs `exec_compare` for Ruby vs SCION and reports zero mismatches on the acceptance suite.
- [ ] `docs/ENGINE-RB.md` and `ruby/ENGINE-RB-DETAILS.md` are published with runnable examples.
- [ ] README highlights Ruby engine; RubyGems links and metadata are updated.
- [ ] Repository version is bumped to 0.3.4 and released artifacts are tagged.

## Immediate Next Steps
- [x] Draft trace schema parity doc for Ruby (reuse Python schema and flags).
- [x] Add a Ruby CLI stub command `engine-trace` that prints a static trace line to validate harness wiring, then iterate.
- [x] Add harness integration to `py/exec_compare.py` to invoke the Ruby CLI and parse trace output (via `--secondary`).
- [ ] Prepare initial Ruby examples and corresponding `.events.jsonl` streams (with `advance_time` if timers are used).
 - [x] Implement timers: `<send delay>` with `advance_time` control token to flush scheduled events deterministically.

## Risks & Mitigations
- [ ] Expression evaluation differences across languages: constrain to cross-engine subset; provide optional Ruby-only mode flagged in docs.
- [ ] Timer and event ordering nuances: retain Python normalization switches; test with advance_time controls.
- [ ] Multi-document finalize ordering differences: document policy and, if necessary, adopt SCION ordering strictly in a “scion mode”.

## Status Snapshot — 2025-10-03
- Converter CLI and schema types exist in `ruby/lib/scjson`.
- Engine trace CLI stub added (`scjson engine-trace`); harness can call Ruby via `--secondary`.
- Documentation skeletons added (`docs/ENGINE-RB.md`, `ruby/ENGINE-RB-DETAILS.md`).
 - Timers supported (delayed send + `advance_time`), internal events, and basic conditions.

---

Back to
- Python Engine User Guide: `docs/ENGINE-PY.md`
- Compatibility Matrix: `docs/COMPATIBILITY.md`
- Project overview: `README.md`
