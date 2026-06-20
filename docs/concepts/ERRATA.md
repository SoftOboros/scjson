<p align="center"><img src="../../scjson.png" alt="scjson logo" width="200"/></p>

Agent Name: scjson-errata

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

# scjson Errata Log

Living institutional memory for accepted scjson defects, ratified deviations,
and pre-existing infrastructure bugs surfaced while implementing a phase.
Inbound bug triage stays in GitHub Issues; entries cross into this file once
root cause + fix scope are agreed and the issue is accepted.

This log is governed by the parent `softoboros.com/CLAUDE.md` Spec-Before-Code
discipline (§ "Errata logs (per spec family)") and the scjson-local
discipline declared in `CLAUDE.md`. Entries are permanent — resolved entries
stay as historical record. Status icons:

- 🟢 resolved (fix landed + verification evidence cited)
- 🟡 diagnosed (root cause known + fix prescription written; not yet landed)
- 🔴 open (symptom reproduced; root cause unknown or contested)
- ⚪ deviation-pending-ratification (fix path identified, spec amendment in
  flight)

## Open Questions

(none — EOQ-001-ERRATA-002 resolved 2026-06-20: EXEC-E §EXEC-E-D1..D5 ratified the
bound — `max_candidates=2000` + `time_budget_ms=30000` defaults, construct-aware
depth reduction, terminal `limited` (partial vectors + `truncated:true`) on budget
exhaustion; `blocked` is owned by M1P6 D-M1P6-8, not by the search.)

## Index

| ID         | Status | Title                                           | First seen | Owning phase |
|------------|--------|-------------------------------------------------|------------|--------------|
| ERRATA-001 | 🟢     | scjson@0.4.0 TypeScript surface missing helpText | 2026-05-28 | CONV-E       |
| ERRATA-002 | 🟢     | Vector-generation BFS has no candidate/time budget — permanent hang on `<parallel>`+`<invoke>` machines | 2026-06-19 | EXEC-E (`SCJSON-EXEC-00-CONCEPTS.md`) |

---

## ERRATA-001 — scjson@0.4.0 TypeScript surface missing `helpText`

- **Status**: 🟢 resolved (v0.4.1 release; resolving commits 7476dea +
  65c1af6 + 976eedd; verification 2026-05-28)
- **First seen**: 2026-05-28
- **Owning phase**: CONV-E (`docs/concepts/SCJSON-CONV-00-CONCEPTS.md` §6
  "CONV-E: Help Text Schema Surface")

### Symptom

The published `scjson@0.4.0` npm package — and its in-repo source at
`js/src/scjsonProps.ts` and built artifacts under `js/dist/` — does not
declare `helpText: string[]` on any of the 26 CONV-E applies-to interfaces
(`ScxmlProps`, `StateProps`, `ParallelProps`, `FinalProps`, `HistoryProps`,
`InitialProps`, `TransitionProps`, `OnentryProps`, `OnexitProps`,
`InvokeProps`, `FinalizeProps`, `DatamodelProps`, `DataProps`,
`DonedataProps`, `ContentProps`, `ParamProps`, `AssignProps`, `LogProps`,
`RaiseProps`, `IfProps`, `ElseifProps`, `ElseProps`, `ForeachProps`,
`SendProps`, `CancelProps`, `ScriptProps`). The corresponding
`defaultXxx()` factories likewise do not initialize the field.

Verified at `HEAD = 22d890a` (2026-05-28) via:

```
$ grep -c "helpText: string\[\]" js/src/scjsonProps.ts
0
$ grep -c "helpText" js/dist/scjsonProps.d.ts
0
```

The Python side does expose the typed field — verified via:

```
$ python3 -c "import scjson.pydantic as p; print('help_text' in p.Scxml.model_fields)"
True
```

and the generator's introspected JSON schema does include `help_text` under
the 26 applies-to definitions:

```
$ python3 -c "
import scjson.pydantic as p
print('help_text' in p.Scxml.model_json_schema()['\$defs']['Scxml']['properties'])"
True
```

### Root cause

The TypeScript binding at `js/src/scjsonProps.ts` was last regenerated
before CONV-E (Help Text Schema Surface) landed on 2026-05-24 — i.e. before
`py/patch_help_text.py` was wired into `py/gen_models.sh` and before the
applies-to models gained the field. The Jinja generator template at
`py/scjson/templates/scjson_props.ts.jinja2` iterates
`schema["properties"]` and would emit `helpText: string[]` correctly if
re-run; the bug is that no one re-ran `python -m scjson typescript` after
CONV-E landed and before the v0.4.0 cut.

This is a release-process gap, not a template gap. The rust/ruby/swift
sibling files (`rust/src/scjson_props.rs`, `ruby/lib/scjson/types.rb`,
`swift/Sources/SCJSONKit/{ScjsonTypes,Models}.swift`) carry the same
staleness, but their fix is intentionally deferred to a future release per
the v0.4.1 brief's "no cross-language behavior changes" scope.

### Downstream impact

The Infinity Stack `iState` frontend (consumer of `scjson@^0.4.x`) cannot
complete its scjson-0.4.0 type-cutover because its `_generated/` interfaces
are derived from the scjson npm surface, and re-deriving currently elides
`helpText`. The consumer is carrying a temporary local `HelpTextInput` shim
pending v0.4.1.

### Fix prescription

Path (b) per the v0.4.1 implementation brief (preferred — TS-surface only):

1. Run `python -m scjson typescript --output js/src` to regenerate
   `js/src/scjsonProps.ts` against the current pydantic models. Expected
   diff: `helpText: string[]` added to each of the 26 applies-to
   interfaces immediately after `otherAttributes`; each `defaultXxx()`
   factory gains `helpText: []`.
2. `cd js && npm run build` to refresh `dist/`.
3. Verify acceptance: `grep -c "helpText: string\[\]" js/dist/scjsonProps.d.ts`
   returns `26`; `grep -c "helpText: \[\]" js/dist/scjsonProps.js` returns
   `26`.
4. JS converter round-trip is unchanged — `help_text` was already in
   `STRUCTURAL_METADATA_KEYS` per the CONV-E JS commit (`e1e3d1f`,
   2026-05-24). The TS surface gain is type-surface-only; converters
   continue to operate on snake_case JSON wire (Interpretation X per the
   brief). No converter semantics change.
5. Cross-language version-bump-only parity: `0.4.0 → 0.4.1` in
   `js/package.json`, `py/pyproject.toml`, `ruby/scjson.gemspec` +
   `ruby/lib/scjson/version.rb`, `rust/Cargo.toml` + `rust/Cargo.lock`,
   `java/pom.xml`. Non-JS packages have no behavior change.

Path (a) — exposing a regenerator CLI for downstream consumers — is
explicitly rejected for this release because (b) is structurally cleaner
(scjson owns its TS surface; downstream consumers should not reach into
scjson internals to regenerate).

### Verification

Verified on `main` at HEAD = `976eedd` (2026-05-28):

```
$ grep -c "helpText: string\[\]" js/src/scjsonProps.ts       → 26
$ grep -c "helpText: \[\]"        js/src/scjsonProps.ts       → 26
$ grep -c "helpText: string\[\]" js/dist/scjsonProps.d.ts    → 26
$ grep -c "helpText: \[\]"        js/dist/scjsonProps.js      → 26
$ cd js && npm run build                                     → exit 0
$ cd js && npx jest                                          → 112 passed / 112 total
$ cd js && npx tsc --noEmit tests/help_text_consumer.test.ts → exit 0
$ PYTHONPATH=py python3 -m pytest -q py/tests -p no:django   → 404 passed, 1 skipped
$ diff -q scjson.schema.json js/scjson.schema.json           → (no diff)
$ diff -q scjson.schema.json java/src/main/resources/scjson.schema.json → (no diff)
$ python3 py/uber_test.py                                    → exit 0 (Python + JS
  clean; lua/go/swift/java/csharp skipped for missing local executables)
$ grep -n "0\.4\.0" js/package.json py/pyproject.toml rust/Cargo.toml \
  java/pom.xml ruby/scjson.gemspec ruby/lib/scjson/version.rb           → (no match)
```

### Tracking

- Ratification: `docs/concepts/SCJSON-CONV-00-CONCEPTS.md` §11 entry dated
  2026-05-28.
- Resolving commits:
  - `7476dea` — docs(concepts): file ERRATA-001 + ratify v0.4.1 fix path
  - `65c1af6` — release(0.4.1): cross-language version bump + CHANGELOG entries
  - `976eedd` — release(0.4.1): regenerate TypeScript helpText surface
- Downstream: `softoboros/docs/todo/istate/TODO-ISTATE-08-HELP-TEXT-ADOPTION.md`
  §16 "ISTATE08b backend half landed; frontend half deferred to scjson
  v0.4.1" (2026-05-27 entry).

---

## ERRATA-002 — Vector-generation BFS has no candidate/time budget — permanent hang on `<parallel>`+`<invoke>` machines

- **Status**: 🟢 resolved 2026-06-20 (EXEC-E §EXEC-E-D1..D5 ratified the bound;
  fix landed in the EXEC-E vector-search-bound commit on this branch). EOQ-001-ERRATA-002
  resolved.
- **First seen**: 2026-06-19, during the iState-over-MCP codegen probe for the
  rlvgl SCTD-01 tutorial-demo effort (a faithful Dining Philosophers machine
  submitted to `istate_codegen_create target_langs=["rust"]`).
- **Owning phase**: EXEC-E — Vector Generation Phase 3
  (`docs/concepts/SCJSON-EXEC-00-CONCEPTS.md` §EXEC-E, currently open; acceptance
  item "EXEC-E vector-generation Phase 3 plan drafted before implementation" is
  unchecked).

### Symptom

A codegen job over the Alex Z tutorial Dining Philosophers machine
(`tutorial/Examples/StateCharts/DiningPhilosphersProblem/machine_dining_philosphers.flat.scxml`
— `datamodel="ecmascript"`, root `<parallel>` with ten children, five nested
`<invoke>` blocks each carrying an inline `<content><scxml>…</scxml></content>`
child machine, `<foreach>`, dynamic `<send eventexpr= targetexpr= delayexpr=>`)
sits in `STARTED` indefinitely — observed 30+ minutes with no `error`, no
`warnings`, no `artifacts`, no terminal transition. A trivial 4-state
`datamodel="null"` machine through the identical path SUCCEEDED in ≤14 s,
isolating the hang to machine complexity, not a generator outage.

The hang is in vector generation, before any Rust template is rendered. Pinned
against scjson `HEAD = 25c79d7` (2026-06-19):

- `py/vector_lib/search.py:82` — the `while frontier:` BFS loop. It is
  depth-capped (`py/vector_lib/search.py:84`, `if len(seq) >= max_depth`) but
  has **no candidate-count cap and no wall-clock budget**; every candidate that
  increases coverage is appended to the frontier (`search.py:100-101`), so
  breadth grows ~`|alphabet|^depth`.
- `py/vector_gen.py` — each evaluated candidate calls a `ctx_factory()` that
  re-instantiates a fresh `DocumentContext.from_json_file(...)`. For this chart
  that means re-entering all parallel regions and starting five
  `SCXMLChildHandler` instances from inline `<content>` SCXML on **every** node
  visited.

The combination — large event alphabet × `max_depth=4` (the value the iState
caller passes, `backend/istate/codegen/vectors.py:60`) × an O(parallel × inline-
invoke child-machine init) per-node cost — makes the search effectively
non-terminating in practical wall-clock. (Runner-up, not yet excluded: a single
`ctx_factory()` blocking inside the child-invoke `_pump()` for a machine whose
inline children never quiesce.)

### Root cause

`generate_sequences` bounds only search *depth*, never *breadth* or *time*, and
the per-candidate context construction is unexpectedly expensive for machines
that combine a root `<parallel>` with inline-`<content>` `<invoke>` children.
EXEC-E (parallel/invoke corpus expansion + vector minimization) was never
drafted, so no committed bound exists; the defaults in
`generate_sequences(... max_depth=2, limit=1)` are the only guard, and the
iState caller overrides `max_depth` to 4. There is no terminal "search exhausted
the budget" outcome, so the only signal a too-complex machine produces is an
indefinite `STARTED`.

### Downstream impact

- iState codegen (`istate.codegen.generate`) inherits the hang and never
  reaches a terminal job state — see the reciprocal istate-side entry
  `softoboros/docs/todo/istate/ERRATA.md` ERRATA-006 (missing codegen watchdog +
  shallow context builder).
- rlvgl SCTD-01 (faithful tutorial-machine demo) is blocked on this:
  `ops/packer/submodules/rlvgl/docs/concepts/SCTD-00-CONCEPTS.md` §8 names iState
  MCP as the generation authority, and the tutorial machines cannot be generated
  until the search is bounded.

### Fix prescription

EXEC-E (spec first, per scjson `CLAUDE.md` — this changes cross-language trace
generation behavior):

1. Add a committed bound to `generate_sequences` in `py/vector_lib/search.py`:
   a candidate-count cap (e.g. `max_candidates`) and a wall-clock budget
   (`time_budget_ms`), checked at the top of the `while frontier:` loop, plus
   a construct-aware depth/alphabet reduction when the chart contains
   `<parallel>` and/or `<invoke>` (detectable from the doc before the search).
2. Define the terminal outcome of an exhausted/over-budget run: emit a
   `limited` result carrying whatever partial vectors were found plus a
   `truncated: true` marker, **or** a `blocked` result with an explicit reason
   — the choice is EOQ-001-ERRATA-002, to be ratified under EXEC-E.
3. Ensure `ctx_factory()` reuse / memoization where safe, so repeated node
   evaluation does not re-pay full inline-`<invoke>` child-machine
   initialization for an unchanged prefix.
4. Cross-check: the trivial null-datamodel baseline must stay byte-identical
   (no churn in existing golden vectors); add a regression vector from a small
   `<parallel>`+`<invoke>` machine that completes under the new budget.

The reciprocal istate-side watchdog (ERRATA-006) is belt-and-braces: even with
this fix, the codegen Celery task MUST carry an effective per-task time limit so
no future construct can park a job in `STARTED` forever.

### Verification

✅ 2026-06-20. `generate_sequences`/`generate_vectors` now carry `max_candidates`
+ `time_budget_ms` budgets checked at the top of the BFS loop, plus EXEC-E-D2
construct-aware depth reduction and a `truncated` marker. Evidence:
(a) the Dining Philosophers machine now **terminates in ~39 s** with 22 partial
sequences and `truncated: true` (was an indefinite 30+ min hang);
(b) the existing null-datamodel golden vectors are byte-identical — full scjson
suite **480 passed / 1 skipped** (baseline 410/1 before the EXEC-E + ecmascript
work, all prior tests still green);
(c) a new bounded `<parallel>`+`<invoke>` regression machine (`test_vector_search.py`)
completes under budget at effective depth 2. Memoization (EXEC-E-D3) deferred with
a TODO per spec (optional for first landing).

### Tracking

- Owning phase: `docs/concepts/SCJSON-EXEC-00-CONCEPTS.md` §EXEC-E (to be
  drafted with the bound decision + EOQ-001-ERRATA-002 resolution).
- Reciprocal istate entry: `softoboros/docs/todo/istate/ERRATA.md` ERRATA-006.
- Downstream demo: `ops/packer/submodules/rlvgl/docs/concepts/SCTD-00-CONCEPTS.md`
  §8 (iState MCP generation boundary).

---

## How to add an entry

1. Pick the next sequential `ERRATA-NNN` id.
2. Add a one-line row to the index table above with the title, status icon,
   first-seen date, and owning phase.
3. Add a new `## ERRATA-NNN — <title>` section after the existing entries
   with the canonical shape: Symptom (pinned to HEAD at first-seen time with
   `path:line` cites), Root cause, Downstream impact (if any), Fix
   prescription, Verification (resolving commit + evidence), Tracking
   (related phase docs / §11 cross-refs).
4. If the entry has an open question requiring user input or ratification,
   add it to the "Open Questions" section above with the stable handle
   `EOQ-NNN-ERRATA-NNN: <one-line ask>`.
5. Entries stay after resolution — flip status to 🟢, fill in Verification,
   and do not delete.
