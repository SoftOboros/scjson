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

Goal: move vector minimization and parallel/invoke corpus expansion out of
generic TODOs into a phase with explicit trace dependencies.

Output:

- Work plan for delta-preserving minimization.
- Corpus expansion criteria for parallel, history, invoke, and step-0 variance.

Dependencies: EXEC-D for invoke ordering-sensitive vectors.

Independent from: converter schema audit except for input normalization.

### EXEC-F: Ruby Execution Conformance

Goal: rebaseline Ruby execution work against the execution contract.

Output:

- Ruby TODO cleanup.
- Ruby-specific acceptance corpus.
- CI subset plan against SCION and Python.

Dependencies: EXEC-D for ordering-sensitive claims.

Independent from: Python 0.3.7 release gates.

## Section 6. Python 0.3.7 Execution Gates

Only EXEC-A, EXEC-B, and the Python portion of EXEC-C are accepted as Python
0.3.7 release gates.

EXEC-D, EXEC-E, and EXEC-F are deferred to larger initiatives.

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
- [ ] EXEC-E vector-generation Phase 3 plan drafted before implementation.
- [ ] EXEC-F Ruby conformance TODOs rebaselined against this doc.

## Section 8. Manager Notes

Safe parallelism:

- EXEC-A, EXEC-B, and converter CONV-B can run in parallel.
- EXEC-D should not run in the same write scope as EXEC-B.
- EXEC-E should wait for EXEC-D if it touches invoke/finalize vectors.
- EXEC-F can inventory Ruby docs in parallel, but should not assert new ordering
  policy before EXEC-D.

Recommended worker boundaries:

- Worker 1: Python docs correction only.
- Worker 2: Python root activation regression test only.
- Worker 3: unsupported corpus/submodule skip policy only.
- Worker 4: invoke/finalize ordering concepts only.

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
- `py/scjson/cli.py`
- `py/scjson/context.py`
- `py/uber_test.py`
- `ruby/lib/scjson/engine/context.rb`

## Section 11. Change Log

- 2026-05-14: Initial execution concepts document.
