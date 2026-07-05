<p align="center"><img src="../scjson.png" alt="scjson logo" width="200"/></p>

Agent Name: swift-engine-todo

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

# Swift Execution Engine — Checklist Plan

This checklist tracks work to deliver a Swift execution engine with full
[SCION](https://www.npmjs.com/package/scion)-compatible behavior and
cross-language parity with the Python engine. It is the EXEC-H work package
named in `docs/concepts/SCJSON-EXEC-00-CONCEPTS.md` Section 5. That document
is authoritative for trace schema, event-stream format, and frozen execution
invariants (EXEC-INV-1..7) — this checklist does not restate them.

## Starting Point

Unlike Go/C#/Lua, the Swift implementation is not a plain subdirectory —
`swift` is itself a nested git submodule pointing at
`https://github.com/SoftOboros/scjson-swift.git` (`.gitmodules`), and it was
**not checked out** in the working tree used to draft this checklist
(`git ls-tree HEAD swift` shows only the gitlink, commit
`38b5c24d3c7777d9c7287b9020d4e0885685a29c`). Every claim below about current
Swift converter state is therefore inferred from the harness, not from
reading `swift/` source directly, and MUST be verified once the submodule is
initialized.

- `py/uber_test.py` has a `LANG_CMDS["swift"]` entry (`py/uber_test.py:76-95`)
  pointing at `swift/.build/x86_64-unknown-linux-gnu/debug/scjson-swift`,
  implying a Swift Package Manager build (`swift build`) producing a
  `scjson-swift` executable — this is the only concrete fact available
  without the submodule checked out.
- `docs/COMPATIBILITY.md` rates Swift **Beta** ("CLI stabilised; parity audit
  in progress"), consistent with Go/C#.
- No execution/trace code is assumed to exist yet; this MUST be confirmed
  once the submodule is initialized, before Section 1 work below begins.

## Scope & Goals
- [ ] Initialize the nested submodule locally
  (`git submodule update --init swift` from the scjson repo root) and
  confirm the "Starting Point" claims above against the actual source tree
  before scheduling further work.
- [ ] Implement the SCXML execution algorithm (macro/microstep), event
  processing, transition selection, conflict resolution, and configuration
  management in Swift.
- [ ] Achieve SCION-compatible semantics per EXEC-INV-1..7, matching traces on
  the shared tutorial corpus (harness normalization permitted per Section 3
  "Harness Normalization").
- [ ] Mirror the Python engine first for a single document, then extend to
  multi-document behavior (invoke/finalize, child machines, done events).
- [ ] Reuse the existing Python harness (`py/exec_compare.py`,
  `py/uber_test.py`) to evaluate the Swift engine against SCION and/or
  Python.
- [ ] Add a dedicated `docs/ENGINE-SWIFT.md` user guide and a
  `swift/ENGINE-SWIFT-DETAILS.md` architecture reference (in the
  `scjson-swift` submodule repo), mirroring the Python and Ruby pairs.
- [ ] Update `docs/COMPATIBILITY.md`'s Swift row only after the acceptance
  criteria below are met; do not hand-edit the status tier before then.

## Reference Semantics
- [ ] Use SCION (Node) as the behavioral reference, exactly as Python and
  Ruby do.
- [ ] Compare Swift engine traces against SCION and Python traces via the
  existing Python harness tooling — no bespoke Swift-side comparator.
- [ ] Any Swift-specific ordering delta or implementation-defined behavior
  MUST be documented in `docs/ENGINE-SWIFT.md`, not silently normalized away.

## Roadmap (Iterations)

0) Submodule Initialization & Fact-Check
- [ ] Run `git submodule update --init swift` and confirm current CLI
  commands, test framework, and package layout in `scjson-swift` before
  trusting any inference in this document's "Starting Point" section.
- [ ] Amend this checklist's "Starting Point" section with verified facts
  (file paths, line numbers) in the same change that does the fact-check —
  do not leave inferred claims uncorrected once verification is possible.

1) Bootstrap & Parity with Python (single document)
- [ ] Define the Swift runtime core (document context, configuration, event
  queue, selection/conflict rules — single-transition case).
- [ ] Implement eventless transitions to quiescence (bounded macrostep).
- [ ] Implement LCA-based exit/entry ordering for single-transition
  microsteps (leaves-only configuration).
- [ ] Transition condition evaluation (literals, variables, comparisons).
- [ ] Executable content subset: `log`, `assign`, `raise`,
  `if`/`elseif`/`else`, `foreach`.
- [ ] Event I/O: internal queue, error events, timers via mock clock
  (`advance_time` control token accepted in event streams per EXEC-INV-2).
- [ ] Add an `engine-trace` subcommand to the Swift CLI, emitting the
  Section 3 trace record schema as JSONL.
- [ ] Integrate with `py/exec_compare.py` as a secondary engine under test
  (`--secondary` pointing at the built `scjson-swift` binary, matching the
  existing `LANG_CMDS["swift"]` path).

2) Multi-document & Invoke/Finalize
- [ ] Implement `<invoke>` lifecycle, `<finalize>`, and
  `done.invoke`/`done.invoke.<id>` events per EXEC-INV-4.
- [ ] Support child machines (inline and `src`-file forms); `#_parent`,
  `#_child`/`#_invokedChild`, `#_<id>` targets; `autoforward`.
- [ ] Parallel completion, history (shallow/deep) targets, final-state
  semantics; enqueue `done.state.<id>` events.
- [ ] Error handling and ordering consistent with the ordering modes in
  EXEC-INV-5 (`tolerant`, `strict`, `scion`); this depends on EXEC-D settling
  invoke/finalize ordering policy before Swift asserts its own.

3) Validation Harness Integration
- [ ] Wire the Swift CLI into `py/exec_compare.py` and `py/exec_sweep.py`,
  reusing the existing `LANG_CMDS["swift"]` entry rather than adding a
  parallel path.
- [ ] Normalize traces with the same leaf-only/omit-delta/step-0 controls
  Python and Ruby use.
- [ ] Add a CI target running a subset of charts against SCION and Python.
  Note the harness currently assumes a Linux build path
  (`x86_64-unknown-linux-gnu`); confirm CI runner architecture matches or
  parameterize the path.

4) Documentation & Examples
- [ ] Create `docs/ENGINE-SWIFT.md` (user guide) mirroring
  `docs/ENGINE-PY.md`/`docs/ENGINE-RB.md` structure.
- [ ] Add `swift/ENGINE-SWIFT-DETAILS.md` (architecture reference) in the
  `scjson-swift` submodule.
- [ ] Port example event streams into Swift-focused examples without
  changing `tutorial/` content: membership, invoke_inline, invoke_timer,
  parallel_invoke.

5) Packaging & Release
- [ ] Update the Swift package's own README to describe the engine
  alongside the existing converter usage.
- [ ] Confirm `swift build` still produces the combined converter+engine
  executable at the path the harness expects.
- [ ] Version bump coordinated with the project's next minor release once
  EXEC-H lands.

## Test Vectors & Corpora
- [ ] Convert existing JS/Python/Ruby test event streams into Swift vector
  extensions hosted in-repo. Do not modify `tutorial/` content.
- [ ] Ensure the Python harness can select Swift via `-l swift` (note the
  existing typo'd alias `"swfit"` at `py/uber_test.py:98-110` also resolves
  to `"swift"` — leave it unless a separate CONV-family cleanup removes it)
  and aggregate coverage in `uber_out/`.

## Acceptance Criteria
- [ ] Swift engine traces match SCION on the canonical corpus (after
  normalization) and match Python on shared subsets.
- [ ] CI job runs `exec_compare` for Swift vs SCION and reports zero
  mismatches on the acceptance suite.
- [ ] `docs/ENGINE-SWIFT.md` and `swift/ENGINE-SWIFT-DETAILS.md` are
  published with runnable examples.
- [ ] `docs/COMPATIBILITY.md` Swift row is updated to reflect engine parity
  status separately from converter status.

## Immediate Next Steps
- [ ] Initialize the `swift` submodule and fact-check this document's
  "Starting Point" section (Roadmap step 0) — this MUST happen before any
  other item on this checklist is scheduled.
- [ ] Draft trace schema parity notes for Swift (reuse the Section 3 schema
  and flags from `SCJSON-EXEC-00-CONCEPTS.md` — do not redefine).
- [ ] Add an `engine-trace` CLI stub that prints a static trace line to
  validate harness wiring, then iterate.

## Risks & Mitigations
- [ ] This checklist was drafted without the submodule checked out; treat
  every "Starting Point" claim as provisional until Roadmap step 0 confirms
  it, and update this document in the same change.
- [ ] Expression evaluation differences across languages: constrain to the
  cross-engine subset already documented for Python/Ruby.
- [ ] Timer and event ordering nuances: reuse Python's normalization
  switches; test with `advance_time` controls.
- [ ] Multi-document finalize ordering differences: wait on EXEC-D before
  committing to Swift-specific ordering guarantees.
- [ ] Harness build path is Linux-specific
  (`x86_64-unknown-linux-gnu`); confirm before assuming CI portability.

## Status Snapshot — 2026-07-05
- Submodule not initialized in the working tree used to draft this
  checklist; all "Starting Point" facts are inferred from
  `py/uber_test.py` and `docs/COMPATIBILITY.md`, not verified against
  `swift/` source.
- This checklist is newly drafted; no roadmap items are checked.
- Depends on Roadmap step 0 (submodule init + fact-check) before any other
  item is trustworthy, and on EXEC-D before Section 2 ordering work.

---

Back to
- Execution Concepts: `docs/concepts/SCJSON-EXEC-00-CONCEPTS.md`
- Compatibility Matrix: `docs/COMPATIBILITY.md`
- Project overview: `README.md`
