<p align="center"><img src="../scjson.png" alt="scjson logo" width="200"/></p>

Agent Name: lua-engine-todo

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

# Lua Execution Engine — Checklist Plan

This checklist tracks work to deliver a Lua execution engine with full
[SCION](https://www.npmjs.com/package/scion)-compatible behavior and
cross-language parity with the Python engine. It is the EXEC-J work package
named in `docs/concepts/SCJSON-EXEC-00-CONCEPTS.md` Section 5. That document
is authoritative for trace schema, event-stream format, and frozen execution
invariants (EXEC-INV-1..7) — this checklist does not restate them.

## Starting Point

Lua starts furthest behind of the four languages in this checklist family:
`docs/COMPATIBILITY.md` already rates it **Experimental** ("minimal subset
converter"), not Beta like Go/Swift/C#. Engine work here is a two-stage
climb — converter parity, then engine parity — not engine work alone.

- Current CLI (`lua/bin/scjson:32-46`): commands `json`, `xml`, `validate`;
  options `-o/--output`, `-r/--recursive`, `--verify`, `--keep-empty`,
  `--skip-unknown`, `--fail-unknown`, `-h/--help`, `--version`.
- Tests use busted-style syntax (`lua/tests/scjson_spec.lua:9` `describe`,
  `:13`/`:21` `it` blocks); reuse this framework for engine tests.
- Runtime dependencies per `lua/README.md`: `lua5.4`, `luaexpat`, `dkjson`.
- No execution/trace code exists yet (`engine-trace`, `advance_time`,
  microstep/macrostep are all absent from `lua/`).
- `py/uber_test.py` already has a `LANG_CMDS["lua"]` entry
  (`py/uber_test.py:76-95`) invoking `lua/bin/scjson` directly, so the
  compatibility harness can pick up an engine subcommand once it exists
  without further wiring changes.

## Scope & Goals
- [ ] Close the converter parity gap first: bring the Lua converter from
  "minimal subset" to passing `py/uber_test.py -l lua` against the tutorial
  corpus (this is CONV-family work, not EXEC-family — coordinate with
  `docs/concepts/SCJSON-CONV-00-CONCEPTS.md` rather than duplicating scope
  here; do not silently expand converter coverage inside an engine PR).
- [ ] Implement the SCXML execution algorithm (macro/microstep), event
  processing, transition selection, conflict resolution, and configuration
  management in Lua.
- [ ] Achieve SCION-compatible semantics per EXEC-INV-1..7, matching traces on
  the shared tutorial corpus (harness normalization permitted per Section 3
  "Harness Normalization").
- [ ] Mirror the Python engine first for a single document, then extend to
  multi-document behavior (invoke/finalize, child machines, done events).
- [ ] Reuse the existing Python harness (`py/exec_compare.py`,
  `py/uber_test.py`) to evaluate the Lua engine against SCION and/or Python.
- [ ] Add a dedicated `docs/ENGINE-LUA.md` user guide and a
  `lua/ENGINE-LUA-DETAILS.md` architecture reference, mirroring the Python
  and Ruby pairs.
- [ ] Update `docs/COMPATIBILITY.md`'s Lua row only after the acceptance
  criteria below are met; do not hand-edit the status tier before then.

## Reference Semantics
- [ ] Use SCION (Node) as the behavioral reference, exactly as Python and
  Ruby do.
- [ ] Compare Lua engine traces against SCION and Python traces via the
  existing Python harness tooling — no bespoke Lua-side comparator.
- [ ] Any Lua-specific ordering delta or implementation-defined behavior MUST
  be documented in `docs/ENGINE-LUA.md`, not silently normalized away.

## Roadmap (Iterations)

0) Converter Parity Prerequisite
- [x] Audit the current "minimal subset converter" against the schema and
  the CONV-E/F/H accepted surfaces; gaps filed as CONV-family backlog in
  `docs/concepts/CONV-I-LUA-PARITY-AUDIT.md` (2026-07-05): no
  `other_attributes`/`other_element`, no `help_text`, no SCXML comment
  promotion, no XInclude handling, and minimal test coverage
  (LUA-CONV-G1..G5). This was a static code review — no Lua runtime was
  available in the auditing environment, so the live `uber_test.py -l lua`
  corpus run (LUA-CONV-G6) is deferred, not done. Treat G1-G5 as real but
  unconfirmed-by-execution until G6 lands.
- [ ] Land LUA-CONV-G1 through LUA-CONV-G5 (see the audit doc's Section 4
  gate table) in the Lua converter.
- [ ] Run LUA-CONV-G6 (`python py/uber_test.py -l lua` against the tutorial
  corpus, on a machine/CI with Lua 5.4 + `luaexpat` + `dkjson` available)
  once G1-G5 land, to confirm the audit's static findings and close the
  loop before claiming converter parity.
- [ ] Do not start Section 1 engine work on a converter that cannot yet
  round-trip the corpus used for trace comparison — engine traces are only
  meaningful once the underlying SCJSON documents parse correctly.

1) Bootstrap & Parity with Python (single document)
- [ ] Define the Lua runtime core (document context, configuration, event
  queue, selection/conflict rules — single-transition case).
- [ ] Implement eventless transitions to quiescence (bounded macrostep).
- [ ] Implement LCA-based exit/entry ordering for single-transition
  microsteps (leaves-only configuration).
- [ ] Transition condition evaluation (literals, variables, comparisons).
- [ ] Executable content subset: `log`, `assign`, `raise`,
  `if`/`elseif`/`else`, `foreach`.
- [ ] Event I/O: internal queue, error events, timers via mock clock
  (`advance_time` control token accepted in event streams per EXEC-INV-2).
- [ ] Add an `engine-trace` command to `lua/bin/scjson` alongside the
  existing `json`/`xml`/`validate` commands, emitting the Section 3 trace
  record schema as JSONL.
- [ ] Integrate with `py/exec_compare.py` as a secondary engine under test
  (`--secondary "lua/bin/scjson engine-trace"`, matching the existing
  `LANG_CMDS["lua"]` invocation shape).

2) Multi-document & Invoke/Finalize
- [ ] Implement `<invoke>` lifecycle, `<finalize>`, and
  `done.invoke`/`done.invoke.<id>` events per EXEC-INV-4.
- [ ] Support child machines (inline and `src`-file forms); `#_parent`,
  `#_child`/`#_invokedChild`, `#_<id>` targets; `autoforward`.
- [ ] Parallel completion, history (shallow/deep) targets, final-state
  semantics; enqueue `done.state.<id>` events.
- [ ] Error handling and ordering consistent with the ordering modes in
  EXEC-INV-5 (`tolerant`, `strict`, `scion`); this depends on EXEC-D settling
  invoke/finalize ordering policy before Lua asserts its own.

3) Validation Harness Integration
- [ ] Wire the Lua CLI into `py/exec_compare.py` and `py/exec_sweep.py`,
  reusing the existing `LANG_CMDS["lua"]` entry rather than adding a
  parallel path.
- [ ] Normalize traces with the same leaf-only/omit-delta/step-0 controls
  Python and Ruby use.
- [ ] Add a CI target running a subset of charts against SCION and Python.

4) Documentation & Examples
- [ ] Create `docs/ENGINE-LUA.md` (user guide) mirroring
  `docs/ENGINE-PY.md`/`docs/ENGINE-RB.md` structure.
- [ ] Add `lua/ENGINE-LUA-DETAILS.md` (architecture reference).
- [ ] Port example event streams into Lua-focused examples without changing
  `tutorial/` content: membership, invoke_inline, invoke_timer,
  parallel_invoke.

5) Packaging & Release
- [ ] Update `lua/README.md` to describe the engine alongside the existing
  converter usage.
- [ ] Evaluate a LuaRocks rockspec for packaging once the engine is stable
  (none exists today; `lua/README.md` currently documents apt/luarocks
  install steps for runtime dependencies only, not a published package).
- [ ] Version bump coordinated with the project's next minor release once
  EXEC-J lands.

## Test Vectors & Corpora
- [ ] Convert existing JS/Python/Ruby test event streams into Lua vector
  extensions hosted in-repo. Do not modify `tutorial/` content.
- [ ] Ensure the Python harness can select Lua via `-l lua` and aggregate
  coverage in `uber_out/`.

## Acceptance Criteria
- [ ] Lua converter reaches Parity tier in `docs/COMPATIBILITY.md` (CONV-family
  prerequisite; tracked here for visibility, owned by CONV-00).
- [ ] Lua engine traces match SCION on the canonical corpus (after
  normalization) and match Python on shared subsets.
- [ ] CI job runs `exec_compare` for Lua vs SCION and reports zero mismatches
  on the acceptance suite.
- [ ] `docs/ENGINE-LUA.md` and `lua/ENGINE-LUA-DETAILS.md` are published with
  runnable examples.
- [ ] `docs/COMPATIBILITY.md` Lua row is updated to reflect engine parity
  status separately from converter status.

## Immediate Next Steps
- [ ] File the converter-parity audit as CONV-family backlog (Section 0
  above) before scheduling any EXEC-J engine work.
- [ ] Draft trace schema parity notes for Lua (reuse the Section 3 schema and
  flags from `SCJSON-EXEC-00-CONCEPTS.md` — do not redefine).
- [ ] Add an `engine-trace` CLI stub that prints a static trace line to
  validate harness wiring, then iterate.

## Risks & Mitigations
- [ ] Converter gap may hide engine work behind a larger-than-expected
  prerequisite; scope Section 0 explicitly so EXEC-J estimates aren't
  silently absorbed by CONV-family debt.
- [ ] Expression evaluation differences across languages: constrain to the
  cross-engine subset already documented for Python/Ruby.
- [ ] Timer and event ordering nuances: reuse Python's normalization
  switches; test with `advance_time` controls.
- [ ] Multi-document finalize ordering differences: wait on EXEC-D before
  committing to Lua-specific ordering guarantees.

## Status Snapshot — 2026-07-05
- Converter CLI (`json`/`xml`/`validate`) exists, rated Experimental in
  `docs/COMPATIBILITY.md`; no engine/trace code exists yet.
- Converter-parity audit complete (static code review):
  `docs/concepts/CONV-I-LUA-PARITY-AUDIT.md`. Five concrete gaps accepted
  as backlog (LUA-CONV-G1..G5); live harness confirmation (LUA-CONV-G6)
  deferred on Lua runtime availability.
- Depends on LUA-CONV-G1..G5 landing (Section 0) before Section 1 engine
  work is meaningful, and on EXEC-D before Section 2 ordering work.

---

Back to
- Execution Concepts: `docs/concepts/SCJSON-EXEC-00-CONCEPTS.md`
- Compatibility Matrix: `docs/COMPATIBILITY.md`
- Project overview: `README.md`
