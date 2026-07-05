<p align="center"><img src="../../scjson.png" alt="scjson logo" width="200"/></p>

Agent Name: scjson-execution-concepts

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

# SCJSON-EXEC-00 Concepts: Execution, Trace, and Harness Semantics

## Section 0. Authority Policy

This document scopes the execution initiative created by
`SCJSON-00-CONCEPTS.md`. It defines the current public execution and trace
contract before deeper invoke/finalize and vector-generation work continues.

Normative sections: Section 3, Section 4, Section 5, Section 6, Section 7, and
Section 9.

Informative sections: Section 1, Section 2, Section 8, Section 10, and
Section 11.

Normative keywords **MUST**, **MUST NOT**, **SHOULD**, **MAY**, and
**RECOMMENDED** are interpreted per RFC 2119 and RFC 8174 when capitalized.

## Section 1. Purpose

Execution behavior is currently described across Python guides, Ruby guides,
TODO files, compatibility docs, and runtime code. This document isolates the
public contract and groups future execution backlog so parallel agents do not
change ordering, trace, or harness semantics accidentally.

## Section 2. Current Drift

- `docs/ENGINE-PY.md` says `advance_time` emits synthetic trace steps by
  default, but the CLI default is no synthetic step.
- Trace schema is repeated in several docs without one owner.
- Invoke/finalize ordering is still described as partly implementation-defined.
- Ruby execution TODOs mix release, packaging, and conformance work.
- Vector-generation Phase 3 depends on stable trace semantics but is listed as
  ordinary TODO work.

## Section 3. Canonical Execution Definitions

### Behavioral Reference

SCION is the behavioral reference for supported execution semantics. Python is
the primary in-repo implementation. Ruby is a parity target.

### Trace Record

A trace record is one JSON object in a JSONL trace. Public fields are:

- `step`
- `event`
- `firedTransitions`
- `enteredStates`
- `exitedStates`
- `configuration`
- `actionLog`
- `datamodelDelta`

### Event Stream

An event stream is JSONL input. Each line is either:

- an external event with `event` or `name` plus optional `data`, or
- a control token such as `advance_time`.

### Harness Normalization

Normalization is a comparison transform, not engine behavior. Flags such as
`--leaf-only`, `--omit-delta`, and `--strip-step0-noise` MUST be documented as
harness/trace-output controls.

## Section 4. Frozen Execution Invariants

- EXEC-INV-1: Trace fields listed in Section 3 MUST remain present unless a
  future trace-version amendment changes the contract.
- EXEC-INV-2: `advance_time` control tokens MUST NOT emit a trace step by
  default; synthetic time steps are opt-in through `--emit-time-steps`.
- EXEC-INV-3: Error event families are `error`, `error.execution`, and
  `error.communication`.
- EXEC-INV-4: Done event families are `done.state.<id>`, `done.invoke`, and
  `done.invoke.<id>`.
- EXEC-INV-5: Ordering modes are `tolerant`, `strict`, and `scion`.
- EXEC-INV-6: Known-diff lists and skip lists are triage tools, not hidden
  specifications.
- EXEC-INV-7: Execution docs MUST distinguish native engine behavior from
  comparison normalization.

## Section 5. Work Packages

### EXEC-A: Python Release Trace/Docs Correction

Goal: correct Python user docs so time-control behavior matches CLI defaults.

Output:

- `docs/ENGINE-PY.md` corrected.
- Any affected TODO checkboxes updated.

Dependencies: none.

Independent from: invoke/finalize ordering and Ruby conformance.

### EXEC-B: Root Activation Regression Test

Goal: prove the 0.3.7 root activation sentinel fix.

Output:

- Focused Python test using `<scxml name="X">` and `<state id="X">`.
- Assertion that user state remains visible in configuration/trace.

Dependencies: none.

Independent from: converter metadata tests.

### EXEC-C: Unsupported Corpus Review

Goal: review `ENGINE_KNOWN_UNSUPPORTED` and recursive tutorial validation.

Output:

- Retain/remove each unsupported chart with a note.
- Clear behavior when the `tutorial` submodule is absent.

Dependencies: initialized tutorial data for final validation, or explicit skip
policy.

Independent from: Ruby conformance.

### EXEC-D: Invoke/Finalize Ordering Concepts

Goal: settle policy for simultaneous invoke completion, child-to-parent sends,
and generic vs id-specific `done.invoke` ordering.

Output:

- A sub-phase concepts doc or amendment with ordering examples and test gates.
- Decision on whether `scion` mode becomes the default for any future release.

Dependencies: EXEC-A and Section 4 invariants.

Independent from: Python 0.3.7 release unless release scope expands.

### EXEC-E: Vector Generation Phase 3

**Status: owner-ratified 2026-06-20. This section is normative. The acceptance
checklist item "EXEC-E vector-generation Phase 3 plan drafted before
implementation" is satisfied by this section.**

The following decisions close EOQ-001-ERRATA-002 (see
`docs/concepts/ERRATA.md` ERRATA-002 for the symptom evidence and root cause).
Implementers MUST satisfy all five sub-decisions; changing any frozen value
requires a §15 amendment to this document before implementation.

#### EXEC-E-D1: Candidate-count cap and wall-clock budget (Standards Action)

`generate_sequences` in `py/vector_lib/search.py` currently bounds only
sequence length (`if len(seq) >= max_depth` at `search.py:84`). It has no
bound on how many candidates accumulate in `frontier` or on elapsed wall-clock
time.  ERRATA-002 shows that a root `<parallel>` with five inline-`<content>`
`<invoke>` children and `max_depth=4` (the value the iState caller passes at
`backend/istate/codegen/vectors.py:63`) makes the search effectively
non-terminating because alphabet breadth grows as `|alphabet|^depth` and each
frontier node calls `ctx_factory()` in full.

`generate_sequences` MUST accept two additional keyword parameters:

- `max_candidates: int` — maximum cumulative frontier entries to evaluate
  before stopping the `while frontier:` loop. Checked at the top of the loop,
  before popping the next sequence, so the loop exits cleanly with whatever
  partial results have been collected.
- `time_budget_ms: int` — elapsed wall-clock budget in milliseconds, measured
  from the moment `generate_sequences` is entered. Checked at the top of the
  same loop, immediately after the `max_candidates` check.

**Default values (proposed; flag for owner confirmation before freezing):**
`max_candidates=2000`, `time_budget_ms=30000` (30 s). These are deliberately
conservative for the common null-datamodel case, which completes in
milliseconds and is unaffected. The iState caller MAY lower these further for
interactive use.

Registration policy: **Standards Action** — changing either default requires
a §15 amendment to this document.

#### EXEC-E-D2: Construct-aware reduction (Standards Action)

When the chart being searched contains at least one `<parallel>` element or at
least one `<invoke>` element (detectable from the SCJSON document before the
first `ctx_factory()` call), the search MUST apply a construct-aware
reduction: the effective `max_depth` passed into the BFS expansion is capped
at `min(max_depth, 2)` for those charts, and the alphabet is reduced to the
set of events that appear in `event` attributes of `<transition>` elements in
the top-level (non-child-machine) document. The reduction is applied
statically, before the loop, and logged as a diagnostic so callers can observe
it.

**Rationale:** The per-candidate `ctx_factory()` call for a chart that
combines `<parallel>` and inline-`<content>` `<invoke>` re-instantiates all
parallel regions and starts each `SCXMLChildHandler` from scratch on every
frontier node (identified in ERRATA-002 as the dominant cost factor). The
depth+alphabet reduction substantially contracts the frontier while retaining
coverage of the top-level event/state topology. Full child-machine vector
generation is out of scope for EXEC-E; it depends on M1P6 G2 (the IR
front-end) and is deferred.

**A future amendment MAY relax the depth cap for `<parallel>`-only charts
(no `<invoke>`) once ctx-factory memoization is implemented (see EXEC-E-D3).**

Registration policy: **Standards Action** — the reduction trigger conditions
and the cap formula require a §15 amendment to change.

#### EXEC-E-D3: ctx_factory memoization for repeated prefixes (Specification Required)

For each distinct sequence prefix evaluated during BFS, the `ctx_factory()`
result SHOULD be reused across frontier nodes that share that prefix, rather
than re-instantiating from scratch. Implementation MAY memoize by prefix tuple
key, constructing a fresh context only for novel prefixes. This is particularly
load-bearing for inline-`<invoke>` charts because each `SCXMLChildHandler`
initialization re-parses the inline `<content>` XML.

Memoization is optional for the first landing of EXEC-E-D1 + EXEC-E-D2 (the
budget+reduction alone resolves the hang). It MUST land before the
construct-aware depth cap is relaxed per the note in EXEC-E-D2.

Registration policy: **Specification Required** — implementation details may
evolve without a §15 amendment as long as observable behavior (sequence
output, coverage scores, and the `limited`/`blocked` terminal outcomes) is
unchanged.

#### EXEC-E-D4: Terminal outcomes — `limited` and `blocked` (Standards Action)

This sub-decision resolves EOQ-001-ERRATA-002 and is co-owned with M1P6
D-M1P6-8 (`docs/todo/scjson/TODO-SCJSON-SCRIPT-M1P6.md` §"Frozen Decisions"
D-M1P6-8, ratified 2026-06-20). Do NOT restate the M1P6 definition here;
implementers MUST read D-M1P6-8 as the primary normative source.

The commitment here is the vector-search-layer contract:

- **`limited`**: if `generate_sequences` exits the `while frontier:` loop
  because `max_candidates` was reached or `time_budget_ms` elapsed, it MUST
  return whatever partial vector list has been collected (possibly empty),
  and MUST set a `truncated: True` flag on the return value (as a named
  result object or an out-of-band signal agreed with the caller). The caller
  (e.g. `vector_gen.generate_vectors` and the iState codegen path in
  `backend/istate/codegen/vectors.py`) MUST propagate `truncated: True`
  through to the terminal job status so consumers receive a `limited` outcome
  rather than a silent success or an indefinite `STARTED`.
- **`blocked`**: an un-lowerable construct (as defined by M1P6 D-M1P6-8) is
  NOT signaled by `generate_sequences` — it is a compile-time diagnostic
  emitted by the IR lowering layer (M1P6 G2). `blocked` is not a vector-search
  outcome and MUST NOT be synthesized inside `generate_sequences`.
- **Indefinite `STARTED`**: prohibited. A run that cannot terminate within the
  committed budget MUST produce `limited`, never hang.

Registration policy: **Standards Action** — the names `limited`/`blocked`, the
`truncated` flag semantics, and the prohibition on indefinite `STARTED` are
cross-family invariants (consumed by istate ERRATA-006 and rlvgl SCTD-00 §8).
Changing them requires a §15 amendment here and a reciprocal amendment to M1P6
D-M1P6-8.

#### EXEC-E-D5: Regression corpus requirement (Specification Required)

The following regression contract MUST hold across all EXEC-E implementation
PRs:

1. **Null-datamodel baseline unchanged.** The golden vectors for the existing
   null-datamodel test machines in the scjson corpus MUST remain byte-identical
   after EXEC-E-D1..D4 land. No churn in existing output is acceptable. The
   existing `PYTHONPATH=py pytest -q py/tests` suite is the verification gate.

2. **Bounded parallel+invoke regression vector.** A new corpus machine
   containing at least one `<parallel>` element and at least one
   inline-`<content>` `<invoke>` element MUST be added to the test corpus.
   The vector-generation run for that machine MUST complete within the
   committed `time_budget_ms` and MUST produce either a non-empty `limited`
   result or a `success` result with at least one vector. The machine SHOULD
   be small enough that the BFS completes well under the budget on any CI
   runner (suggested: two parallel regions, one nested `<invoke>` with a
   two-state child machine, alphabet of three events).

Registration policy: **Specification Required** — the corpus machine shape may
evolve; the two-part invariant (null-datamodel no-churn + bounded
parallel+invoke completion) requires only a PR-level note to change.

#### EXEC-E: Output summary

- `py/vector_lib/search.py` extended with `max_candidates` + `time_budget_ms`
  parameters, construct-aware depth/alphabet reduction, and `truncated` signal.
- `py/vector_gen.py` updated to propagate `truncated` to callers.
- iState codegen path (`backend/istate/codegen/vectors.py`) updated to treat
  `truncated: True` as a `limited` terminal outcome.
- New bounded `<parallel>`+`<invoke>` regression machine added to the corpus.

Dependencies: EXEC-E-D4 and the `limited`/`blocked` naming are jointly owned
with M1P6 D-M1P6-8; EXEC-E-D3 memoization SHOULD land before any future
relaxation of the EXEC-E-D2 depth cap; invoke ordering semantics remain under
EXEC-D.

Independent from: converter schema audit, Ruby conformance (EXEC-F), and the
M1P6 IR front-end (EXEC-E resolves the hang at the search layer; full
child-machine vectors depend on M1P6 G2).

### EXEC-F: Ruby Execution Conformance

Goal: rebaseline Ruby execution work against the execution contract.

Output:

- Ruby TODO cleanup.
- Ruby-specific acceptance corpus.
- CI subset plan against SCION and Python.

Dependencies: EXEC-D for ordering-sensitive claims.

Independent from: Python 0.3.7 release gates.

### EXEC-G: Go Execution Conformance

Goal: build a Go execution engine achieving SCION-compatible trace parity
per Section 3/4, starting from the existing Go converter CLI (`json`/`xml`/
`validate` at `go/main.go:123,199,272`). No execution/trace code exists in
`go/` today.

Output:

- `docs/TODO-ENGINE-GO.md` checklist plan (this document remains
  authoritative for trace/ordering semantics).
- Go engine `engine-trace` subcommand emitting the Section 3 trace record
  schema.
- Go acceptance corpus wired into the existing `py/uber_test.py`
  `LANG_CMDS["go"]` entry.

Dependencies: EXEC-D for ordering-sensitive claims.

Independent from: Python 0.3.7 release gates; EXEC-H, EXEC-I, EXEC-J.

### EXEC-H: Swift Execution Conformance

Goal: build a Swift execution engine achieving SCION-compatible trace
parity per Section 3/4. The `swift` submodule (nested, pointing at
`SoftOboros/scjson-swift`) was not checked out when this work package was
drafted; a submodule-init-and-fact-check step is a hard prerequisite before
any other Swift engine work is scheduled.

Output:

- `docs/TODO-ENGINE-SWIFT.md` checklist plan, including a Roadmap step 0 that
  verifies current Swift converter/CLI state against the submodule source
  before trusting any inference drawn from the harness.
- Swift engine `engine-trace` subcommand emitting the Section 3 trace record
  schema.
- Swift acceptance corpus wired into the existing `py/uber_test.py`
  `LANG_CMDS["swift"]` entry.

Dependencies: EXEC-D for ordering-sensitive claims; submodule initialization
precedes all other EXEC-H work.

Independent from: Python 0.3.7 release gates; EXEC-G, EXEC-I, EXEC-J.

### EXEC-I: C# Execution Conformance

Goal: build a C# execution engine achieving SCION-compatible trace parity
per Section 3/4, starting from the existing C# converter CLI (`json`/`xml`/
`validate` switch cases at `csharp/ScjsonCli/Program.cs:40,42,44`), tested
with xUnit (`csharp/Scjson.Tests/CliTests.cs`). No execution/trace code
exists in `csharp/` today.

Output:

- `docs/TODO-ENGINE-CSHARP.md` checklist plan.
- C# engine `engine-trace` verb emitting the Section 3 trace record schema.
- C# acceptance corpus wired into the existing `py/uber_test.py`
  `LANG_CMDS["csharp"]` entry (aliases `"cs"`, `"dotnet"`).

Dependencies: EXEC-D for ordering-sensitive claims.

Independent from: Python 0.3.7 release gates; EXEC-G, EXEC-H, EXEC-J.

### EXEC-J: Lua Execution Conformance

Goal: build a Lua execution engine achieving SCION-compatible trace parity
per Section 3/4. Unlike Go/Swift/C#, Lua's converter is rated Experimental
("minimal subset converter") in `docs/COMPATIBILITY.md`, not Beta — engine
work here has a converter-parity prerequisite that Go/Swift/C# do not.

Output:

- `docs/TODO-ENGINE-LUA.md` checklist plan, including an explicit Roadmap
  step 0 that scopes the converter-parity audit as CONV-family backlog
  rather than absorbing it into EXEC-J estimates.
- Lua engine `engine-trace` command emitting the Section 3 trace record
  schema, added to the existing `lua/bin/scjson` CLI.
- Lua acceptance corpus wired into the existing `py/uber_test.py`
  `LANG_CMDS["lua"]` entry.

Dependencies: EXEC-D for ordering-sensitive claims; a converter-parity pass
(coordinated with CONV-00, not restated here) precedes meaningful engine
trace comparison.

Independent from: Python 0.3.7 release gates; EXEC-G, EXEC-H, EXEC-I.

## Section 6. Python 0.3.7 Execution Gates

Only EXEC-A, EXEC-B, and the Python portion of EXEC-C are accepted as Python
0.3.7 release gates.

EXEC-D, EXEC-E, EXEC-F, EXEC-G, EXEC-H, EXEC-I, and EXEC-J are deferred to
larger initiatives.

## Section 7. Acceptance Checklist

- [x] EXEC-A Python time-control docs corrected.
- [x] EXEC-B root activation regression test lands.
- [x] EXEC-C unsupported corpus review lands or is explicitly deferred with
  submodule validation notes. Recursive tutorial CLI tests now skip clearly
  when tutorial data is absent; with initialized tutorial data, W3C optional
  `test457.scxml` was removed from `ENGINE_KNOWN_UNSUPPORTED` and retained
  entries now carry inline reasons.
- [ ] EXEC-D invoke/finalize ordering concepts drafted before behavioral
  changes.
- [x] EXEC-E vector-generation Phase 3 plan drafted before implementation.
  Ratified 2026-06-20; see §5 EXEC-E for the committed bound (EXEC-E-D1..D5)
  resolving EOQ-001-ERRATA-002.
- [ ] EXEC-F Ruby conformance TODOs rebaselined against this doc.
- [ ] EXEC-G Go execution engine checklist drafted against this doc.
  Satisfied by `docs/TODO-ENGINE-GO.md` (drafted 2026-07-05); engine
  implementation itself remains open.
- [ ] EXEC-H Swift execution engine checklist drafted against this doc.
  Satisfied by `docs/TODO-ENGINE-SWIFT.md` (drafted 2026-07-05); submodule
  initialization and fact-check (Roadmap step 0) and engine implementation
  remain open.
- [ ] EXEC-I C# execution engine checklist drafted against this doc.
  Satisfied by `docs/TODO-ENGINE-CSHARP.md` (drafted 2026-07-05); engine
  implementation itself remains open.
- [ ] EXEC-J Lua execution engine checklist drafted against this doc.
  Satisfied by `docs/TODO-ENGINE-LUA.md` (drafted 2026-07-05); the
  converter-parity prerequisite (Roadmap step 0) and engine implementation
  remain open.

## Section 8. Manager Notes

Safe parallelism:

- EXEC-A, EXEC-B, and converter CONV-B can run in parallel.
- EXEC-D should not run in the same write scope as EXEC-B.
- EXEC-E should wait for EXEC-D if it touches invoke/finalize vectors.
- EXEC-F can inventory Ruby docs in parallel, but should not assert new ordering
  policy before EXEC-D.
- EXEC-G, EXEC-H, EXEC-I, and EXEC-J are file-disjoint from each other
  (`go/`, `swift/`, `csharp/`, `lua/` respectively) and from EXEC-F
  (`ruby/`), so their checklists and eventual engine implementations may
  proceed in parallel worktrees. None should assert new ordering policy
  before EXEC-D. EXEC-H additionally cannot start real engine work until its
  Roadmap step 0 (submodule init) lands, and EXEC-J cannot start Roadmap
  step 1 until its converter-parity prerequisite (Roadmap step 0, owned by
  CONV-00) lands.

Recommended worker boundaries:

- Worker 1: Python docs correction only.
- Worker 2: Python root activation regression test only.
- Worker 3: unsupported corpus/submodule skip policy only.
- Worker 4: invoke/finalize ordering concepts only.
- Worker 5: Go engine checklist/implementation only (`go/`,
  `docs/TODO-ENGINE-GO.md`, `docs/ENGINE-GO.md`).
- Worker 6: Swift submodule init + fact-check only, before any Swift engine
  implementation is assigned.
- Worker 7: C# engine checklist/implementation only (`csharp/`,
  `docs/TODO-ENGINE-CSHARP.md`, `docs/ENGINE-CSHARP.md`).
- Worker 8: Lua converter-parity audit only (coordinate with CONV-00),
  strictly before any Lua engine implementation is assigned.

## Section 9. Rejections

The Apache Commons comparison wrapper and Java runner replacement are rejected
as Python 0.3.7 blockers. They are not dependencies for this execution
initiative.

## Section 10. Files Cited

- `docs/ENGINE-PY.md`
- `docs/ENGINE-RB.md`
- `docs/TODO-ENGINE-PY.md`
- `docs/TODO-ENGINE-RUBY.md`
- `docs/concepts/SCJSON-00-CONCEPTS.md`
- `docs/concepts/ERRATA.md` (ERRATA-002: vector-generation BFS hang; symptom
  evidence and root cause for EXEC-E)
- `py/scjson/cli.py`
- `py/scjson/context.py`
- `py/uber_test.py`
- `py/vector_lib/search.py` (EXEC-E: `generate_sequences` BFS, `while
  frontier:` at line 82, depth cap at line 84, frontier append at lines
  100–101)
- `py/vector_gen.py`
- `ruby/lib/scjson/engine/context.rb`
- `softoboros/backend/istate/codegen/vectors.py` (iState caller; passes
  `max_depth=4, limit=1` at line 63)
- `softoboros/docs/todo/scjson/TODO-SCJSON-SCRIPT-M1P6.md` (M1P6 D-M1P6-8:
  terminal codegen outcomes; G1 gate: vector-search bound)
- `go/main.go` (converter CLI: `json` at line 123, `xml` at line 199,
  `validate` at line 272), `go/converter.go`, `go/cli_test.go`,
  `go/README.md`
- `csharp/ScjsonCli/Program.cs` (converter CLI switch: `xml` at line 40,
  `json` at line 42, `validate` at line 44), `csharp/Scjson.Tests/CliTests.cs`,
  `csharp/README.md`
- `lua/bin/scjson` (usage/commands at lines 32-46), `lua/tests/scjson_spec.lua`,
  `lua/README.md`
- `.gitmodules` (`swift` submodule → `SoftOboros/scjson-swift`, not checked
  out at time of EXEC-H drafting)
- `py/uber_test.py` (`LANG_CMDS` mapping at lines 76-95; aliases including
  `"cs"`/`"dotnet"` → `"csharp"` and `"swfit"` → `"swift"` at lines 98-110)
- `docs/TODO-ENGINE-GO.md`, `docs/TODO-ENGINE-SWIFT.md`,
  `docs/TODO-ENGINE-CSHARP.md`, `docs/TODO-ENGINE-LUA.md`

## Section 11. Change Log

- 2026-05-14: Initial execution concepts document.
- 2026-06-20: §5 EXEC-E expanded with five normative sub-decisions
  (EXEC-E-D1..D5) committing the candidate-count cap, wall-clock budget,
  construct-aware reduction, ctx_factory memoization policy, `limited`/`blocked`
  terminal outcomes, and regression corpus requirement. Resolves
  EOQ-001-ERRATA-002 (`docs/concepts/ERRATA.md` ERRATA-002). Acceptance
  checklist item EXEC-E marked satisfied. §10 updated with EXEC-E cited files.
- 2026-07-05: §5 expanded with four new work packages — EXEC-G (Go), EXEC-H
  (Swift), EXEC-I (C#), EXEC-J (Lua) — each requesting full execution-engine
  parity with Python, mirroring EXEC-F's shape. All four are deferred to
  larger initiatives (§6) and are not Python 0.3.7 release gates. §7
  acceptance checklist gained four corresponding items, satisfied by the new
  `docs/TODO-ENGINE-GO.md`, `docs/TODO-ENGINE-SWIFT.md`,
  `docs/TODO-ENGINE-CSHARP.md`, and `docs/TODO-ENGINE-LUA.md` checklists
  (engine implementation itself remains open in all four). §8 updated with
  file-disjoint parallelism notes and four new recommended worker
  boundaries. §10 updated with cited converter/CLI/test files for all four
  languages. No implementation code was written as part of this change —
  planning only, per spec-before-code discipline.
