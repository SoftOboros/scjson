<p align="center"><img src="../scjson.png" alt="scjson logo" width="200"/></p>

Agent Name: csharp-engine-todo

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

# C# Execution Engine — Checklist Plan

This checklist tracks work to deliver a C# execution engine with full
[SCION](https://www.npmjs.com/package/scion)-compatible behavior and
cross-language parity with the Python engine. It is the EXEC-I work package
named in `docs/concepts/SCJSON-EXEC-00-CONCEPTS.md` Section 5. That document
is authoritative for trace schema, event-stream format, and frozen execution
invariants (EXEC-INV-1..7) — this checklist does not restate them.

## Starting Point

- C# currently ships a converter-only CLI: `json`, `xml`, `validate` switch
  cases (`csharp/ScjsonCli/Program.cs:40`, `:42`, `:44`), backed by
  `csharp/ScjsonCli/Converter.cs`, targeting `net8.0`.
- Tests already use xUnit (`csharp/Scjson.Tests/CliTests.cs`,
  `csharp/Scjson.Tests/Scjson.Tests.csproj:9-10`); reuse this framework for
  engine tests rather than introducing a second one.
- No execution/trace code exists yet (`engine-trace`, `advance_time`,
  microstep/macrostep are all absent from `csharp/`).
- `py/uber_test.py` already has a `LANG_CMDS["csharp"]` entry
  (`py/uber_test.py:76-95`) invoking `dotnet ScjsonCli.dll` from the Debug
  build output, so the compatibility harness can pick up an engine
  subcommand once it exists without further wiring changes. Note the
  existing aliases `"cs"` and `"dotnet"` both map to `"csharp"`
  (`py/uber_test.py:98-110`).

## Scope & Goals
- [ ] Implement the SCXML execution algorithm (macro/microstep), event
  processing, transition selection, conflict resolution, and configuration
  management in C#.
- [ ] Achieve SCION-compatible semantics per EXEC-INV-1..7, matching traces on
  the shared tutorial corpus (harness normalization permitted per Section 3
  "Harness Normalization").
- [ ] Mirror the Python engine first for a single document, then extend to
  multi-document behavior (invoke/finalize, child machines, done events).
- [ ] Reuse the existing Python harness (`py/exec_compare.py`,
  `py/uber_test.py`) to evaluate the C# engine against SCION and/or Python.
- [ ] Add a dedicated `docs/ENGINE-CSHARP.md` user guide and a
  `csharp/ENGINE-CSHARP-DETAILS.md` architecture reference, mirroring the
  Python and Ruby pairs.
- [ ] Update `docs/COMPATIBILITY.md`'s C# row only after the acceptance
  criteria below are met; do not hand-edit the status tier before then.

## Reference Semantics
- [ ] Use SCION (Node) as the behavioral reference, exactly as Python and
  Ruby do.
- [ ] Compare C# engine traces against SCION and Python traces via the
  existing Python harness tooling — no bespoke C#-side comparator.
- [ ] Any C#-specific ordering delta or implementation-defined behavior MUST
  be documented in `docs/ENGINE-CSHARP.md`, not silently normalized away.

## Roadmap (Iterations)

1) Bootstrap & Parity with Python (single document)
- [ ] Define the C# runtime core (document context, configuration, event
  queue, selection/conflict rules — single-transition case).
- [ ] Implement eventless transitions to quiescence (bounded macrostep).
- [ ] Implement LCA-based exit/entry ordering for single-transition
  microsteps (leaves-only configuration).
- [ ] Transition condition evaluation (literals, variables, comparisons).
- [ ] Executable content subset: `log`, `assign`, `raise`,
  `if`/`elseif`/`else`, `foreach`.
- [ ] Event I/O: internal queue, error events, timers via mock clock
  (`advance_time` control token accepted in event streams per EXEC-INV-2).
- [ ] Add an `engine-trace` verb to `csharp/ScjsonCli/Program.cs` alongside
  the existing `json`/`xml`/`validate` switch, emitting the Section 3 trace
  record schema as JSONL.
- [ ] Integrate with `py/exec_compare.py` as a secondary engine under test
  (`--secondary "dotnet .../ScjsonCli.dll engine-trace"`, matching the
  existing `LANG_CMDS["csharp"]` invocation shape).

2) Multi-document & Invoke/Finalize
- [ ] Implement `<invoke>` lifecycle, `<finalize>`, and
  `done.invoke`/`done.invoke.<id>` events per EXEC-INV-4.
- [ ] Support child machines (inline and `src`-file forms); `#_parent`,
  `#_child`/`#_invokedChild`, `#_<id>` targets; `autoforward`.
- [ ] Parallel completion, history (shallow/deep) targets, final-state
  semantics; enqueue `done.state.<id>` events.
- [ ] Error handling and ordering consistent with the ordering modes in
  EXEC-INV-5 (`tolerant`, `strict`, `scion`); this depends on EXEC-D settling
  invoke/finalize ordering policy before C# asserts its own.

3) Validation Harness Integration
- [ ] Wire the C# CLI into `py/exec_compare.py` and `py/exec_sweep.py`,
  reusing the existing `LANG_CMDS["csharp"]` entry rather than adding a
  parallel path.
- [ ] Normalize traces with the same leaf-only/omit-delta/step-0 controls
  Python and Ruby use.
- [ ] Add a CI target running a subset of charts against SCION and Python.

4) Documentation & Examples
- [ ] Create `docs/ENGINE-CSHARP.md` (user guide) mirroring
  `docs/ENGINE-PY.md`/`docs/ENGINE-RB.md` structure.
- [ ] Add `csharp/ENGINE-CSHARP-DETAILS.md` (architecture reference).
- [ ] Port example event streams into C#-focused examples without changing
  `tutorial/` content: membership, invoke_inline, invoke_timer,
  parallel_invoke.

5) Packaging & Release
- [ ] Update `csharp/README.md` to describe the engine alongside the
  existing converter usage.
- [ ] Confirm `dotnet build csharp/ScjsonCli` still builds the combined
  converter+engine assembly; evaluate NuGet packaging (`dotnet pack`) once
  the engine is stable.
- [ ] Version bump coordinated with the project's next minor release once
  EXEC-I lands.

## Test Vectors & Corpora
- [ ] Convert existing JS/Python/Ruby test event streams into C# vector
  extensions hosted in-repo. Do not modify `tutorial/` content.
- [ ] Ensure the Python harness can select C# via `-l csharp` (or the `cs`
  alias) and aggregate coverage in `uber_out/`.

## Acceptance Criteria
- [ ] C# engine traces match SCION on the canonical corpus (after
  normalization) and match Python on shared subsets.
- [ ] CI job runs `exec_compare` for C# vs SCION and reports zero mismatches
  on the acceptance suite.
- [ ] `docs/ENGINE-CSHARP.md` and `csharp/ENGINE-CSHARP-DETAILS.md` are
  published with runnable examples.
- [ ] `docs/COMPATIBILITY.md` C# row is updated to reflect engine parity
  status separately from converter status.

## Immediate Next Steps
- [ ] Draft trace schema parity notes for C# (reuse the Section 3 schema and
  flags from `SCJSON-EXEC-00-CONCEPTS.md` — do not redefine).
- [ ] Add an `engine-trace` CLI stub that prints a static trace line to
  validate harness wiring, then iterate.
- [ ] Add harness integration to `py/exec_compare.py` to invoke the C# CLI
  and parse trace output.

## Risks & Mitigations
- [ ] Expression evaluation differences across languages: constrain to the
  cross-engine subset already documented for Python/Ruby.
- [ ] Timer and event ordering nuances: reuse Python's normalization
  switches; test with `advance_time` controls.
- [ ] Multi-document finalize ordering differences: wait on EXEC-D before
  committing to C#-specific ordering guarantees.
- [ ] `dotnet` startup latency may affect harness sweep wall-clock time;
  consider a long-lived process mode only if this proves material, not
  speculatively.

## Status Snapshot — 2026-07-05
- Converter CLI (`json`/`xml`/`validate`) exists and is tested with xUnit
  (`csharp/Scjson.Tests/CliTests.cs`); no engine/trace code exists yet.
- This checklist is newly drafted; no roadmap items are checked.
- Depends on EXEC-D (invoke/finalize ordering concepts) before Section 2 of
  the roadmap can commit to ordering behavior.

---

Back to
- Execution Concepts: `docs/concepts/SCJSON-EXEC-00-CONCEPTS.md`
- Compatibility Matrix: `docs/COMPATIBILITY.md`
- Project overview: `README.md`
