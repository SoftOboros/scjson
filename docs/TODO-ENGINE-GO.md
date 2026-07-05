<p align="center"><img src="../scjson.png" alt="scjson logo" width="200"/></p>

Agent Name: go-engine-todo

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

# Go Execution Engine — Checklist Plan

This checklist tracks work to deliver a Go execution engine with full
[SCION](https://www.npmjs.com/package/scion)-compatible behavior and
cross-language parity with the Python engine. It is the EXEC-G work package
named in `docs/concepts/SCJSON-EXEC-00-CONCEPTS.md` Section 5. That document
is authoritative for trace schema, event-stream format, and frozen execution
invariants (EXEC-INV-1..7) — this checklist does not restate them.

## Starting Point

- Go currently ships a converter-only CLI: `json`, `xml`, `validate`
  (`go/main.go:123`, `go/main.go:199`, `go/main.go:272`), backed by
  `go/converter.go`, tested via standard `go test` in `go/cli_test.go`.
- No execution/trace code exists yet (`engine-trace`, `advance_time`,
  microstep/macrostep are all absent from `go/`).
- `py/uber_test.py` already has a `LANG_CMDS["go"]` entry
  (`py/uber_test.py:76-95`) pointing at a built `go/scjson` binary, so the
  compatibility harness can pick up an engine subcommand once it exists
  without further wiring changes.

## Scope & Goals
- [ ] Implement the SCXML execution algorithm (macro/microstep), event
  processing, transition selection, conflict resolution, and configuration
  management in Go.
- [ ] Achieve SCION-compatible semantics per EXEC-INV-1..7, matching traces on
  the shared tutorial corpus (harness normalization permitted per Section 3
  "Harness Normalization").
- [ ] Mirror the Python engine first for a single document, then extend to
  multi-document behavior (invoke/finalize, child machines, done events).
- [ ] Reuse the existing Python harness (`py/exec_compare.py`,
  `py/uber_test.py`) to evaluate the Go engine against SCION and/or Python —
  do not build a parallel comparison tool.
- [ ] Add a dedicated `docs/ENGINE-GO.md` user guide and a
  `go/ENGINE-GO-DETAILS.md` architecture reference, mirroring the Python and
  Ruby pairs (`docs/ENGINE-PY.md`/`py/ENGINE-PY-DETAILS.md`,
  `docs/ENGINE-RB.md`/`ruby/ENGINE-RB-DETAILS.md`).
- [ ] Update `docs/COMPATIBILITY.md`'s Go row only after the acceptance
  criteria below are met; do not hand-edit the status tier before then.

## Reference Semantics
- [ ] Use SCION (Node) as the behavioral reference, exactly as Python and
  Ruby do.
- [ ] Compare Go engine traces against SCION and Python traces via the
  existing Python harness tooling — no bespoke Go-side comparator.
- [ ] Any Go-specific ordering delta or implementation-defined behavior MUST
  be documented in `docs/ENGINE-GO.md`, not silently normalized away.

## Roadmap (Iterations)

1) Bootstrap & Parity with Python (single document)
- [ ] Define the Go runtime core (document context, configuration, event
  queue, selection/conflict rules — single-transition case).
- [ ] Implement eventless transitions to quiescence (bounded macrostep).
- [ ] Implement LCA-based exit/entry ordering for single-transition
  microsteps (leaves-only configuration).
- [ ] Transition condition evaluation (literals, variables, comparisons).
- [ ] Executable content subset: `log`, `assign`, `raise`,
  `if`/`elseif`/`else`, `foreach`.
- [ ] Event I/O: internal queue, error events, timers via mock clock
  (`advance_time` control token accepted in event streams per EXEC-INV-2).
- [ ] Add `engine-trace` subcommand to the existing `go/main.go` CLI app,
  emitting the Section 3 trace record schema as JSONL.
- [ ] Integrate with `py/exec_compare.py` as a secondary engine under test
  (`--secondary "go/scjson engine-trace"`, matching the `LANG_CMDS["go"]`
  binary path already assumed by the harness).

2) Multi-document & Invoke/Finalize
- [ ] Implement `<invoke>` lifecycle, `<finalize>`, and
  `done.invoke`/`done.invoke.<id>` events per EXEC-INV-4.
- [ ] Support child machines (inline and `src`-file forms); `#_parent`,
  `#_child`/`#_invokedChild`, `#_<id>` targets; `autoforward`.
- [ ] Parallel completion, history (shallow/deep) targets, final-state
  semantics; enqueue `done.state.<id>` events.
- [ ] Error handling and ordering consistent with the ordering modes in
  EXEC-INV-5 (`tolerant`, `strict`, `scion`); this depends on EXEC-D settling
  invoke/finalize ordering policy before Go asserts its own.

3) Validation Harness Integration
- [ ] Wire the Go CLI into `py/exec_compare.py` and `py/exec_sweep.py`
  (command string + cwd assumptions documented, reusing the existing
  `LANG_CMDS["go"]` entry rather than adding a parallel path).
- [ ] Normalize traces with the same leaf-only/omit-delta/step-0 controls
  Python and Ruby use.
- [ ] Add a CI target running a subset of charts against SCION and Python.

4) Documentation & Examples
- [ ] Create `docs/ENGINE-GO.md` (user guide) mirroring
  `docs/ENGINE-PY.md`/`docs/ENGINE-RB.md` structure.
- [ ] Add `go/ENGINE-GO-DETAILS.md` (architecture reference).
- [ ] Port example event streams into Go-focused examples without changing
  `tutorial/` content: membership, invoke_inline, invoke_timer,
  parallel_invoke.

5) Packaging & Release
- [ ] Update `go/README.md` to describe the engine alongside the existing
  converter usage.
- [ ] Confirm `go install github.com/softoboros/scjson/go@latest` still
  builds the combined converter+engine binary.
- [ ] Version bump coordinated with the project's next minor release once
  EXEC-G lands.

## Test Vectors & Corpora
- [ ] Convert existing JS/Python/Ruby test event streams into Go vector
  extensions hosted in-repo (e.g. `tests/exec/*.events.jsonl` variants if Go
  requires timing tokens). Do not modify `tutorial/` content.
- [ ] Ensure the Python harness can select Go via `-l go` and aggregate
  coverage in `uber_out/`.

## Acceptance Criteria
- [ ] Go engine traces match SCION on the canonical corpus (after
  normalization) and match Python on shared subsets.
- [ ] CI job runs `exec_compare` for Go vs SCION and reports zero mismatches
  on the acceptance suite.
- [ ] `docs/ENGINE-GO.md` and `go/ENGINE-GO-DETAILS.md` are published with
  runnable examples.
- [ ] `docs/COMPATIBILITY.md` Go row is updated to reflect engine parity
  status separately from converter status.

## Immediate Next Steps
- [ ] Draft trace schema parity notes for Go (reuse the Section 3 schema and
  flags from `SCJSON-EXEC-00-CONCEPTS.md` — do not redefine).
- [ ] Add an `engine-trace` CLI stub that prints a static trace line to
  validate harness wiring, then iterate.
- [ ] Add harness integration to `py/exec_compare.py` to invoke the Go CLI
  and parse trace output.

## Risks & Mitigations
- [ ] Expression evaluation differences across languages: constrain to the
  cross-engine subset already documented for Python/Ruby.
- [ ] Timer and event ordering nuances: reuse Python's normalization
  switches; test with `advance_time` controls.
- [ ] Multi-document finalize ordering differences: wait on EXEC-D before
  committing to Go-specific ordering guarantees.

## Status Snapshot — 2026-07-05
- Converter CLI (`json`/`xml`/`validate`) exists and is tested
  (`go/cli_test.go`); no engine/trace code exists yet.
- This checklist is newly drafted; no roadmap items are checked.
- Depends on EXEC-D (invoke/finalize ordering concepts) before Section 2 of
  the roadmap can commit to ordering behavior.

---

Back to
- Execution Concepts: `docs/concepts/SCJSON-EXEC-00-CONCEPTS.md`
- Compatibility Matrix: `docs/COMPATIBILITY.md`
- Project overview: `README.md`
