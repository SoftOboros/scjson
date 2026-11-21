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
| ERRATA-003 | 🟡     | `In()` cross-region predicate not in the admitted ECMAScript subset — blocks real infotainment control cores | 2026-06-20 | M1P6 (`docs/todo/scjson/TODO-SCJSON-SCRIPT-M1P6.md` D-M1P6-2) |
| ERRATA-004 | 🟢 | Inline JSON data becomes text in the Python engine and disappears from executable IR | 2026-11-21 | Python execution / M1P6 |
| ERRATA-005 | 🔴 | First-use foreach bindings have the expected values but the chart selects the wrong final | 2026-11-21 | EXEC-C |
| ERRATA-006 | 🔴 | Execution continues after a failing action inside foreach | 2026-11-21 | EXEC-C |
| ERRATA-007 | 🔴 | Converted SCJSON disagrees with XML on foreach action order and data witnesses | 2026-11-21 | EXEC-C / conversion |
| ERRATA-008 | 🟡 | The canonical Python model rejects authored literal send and donedata payloads | 2026-11-21 | Conversion / Python model |
| ERRATA-009 | 🔴 | Original ECMA execution cases select the wrong final in the 0.4.2 pilot | 2026-11-21 | EXEC-C |
| ERRATA-010 | 🔴 | Python qualification has reproducibility, fixture, and platform failures | 2026-11-21 | Python CLI / harness |

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

## ERRATA-003 — `In()` cross-region predicate not in the admitted ECMAScript subset

- **Status**: 🟡 diagnosed 2026-06-20 (workaround prescribed; admitted-subset extension is a future generator phase). Surfaced during the SCTD Media Player feasibility assessment of the Skoda Bolero infotainment machine.
- **First seen**: 2026-06-20, lowering `tutorial/Examples/Qt/SkodaBoleroInfotainment/Model/bolero.scxml` through `exec_ir.lower_document`.
- **Owning phase**: M1P6 (`docs/todo/scjson/TODO-SCJSON-SCRIPT-M1P6.md` §"Admitted ECMAScript Subset", D-M1P6-2).

### Symptom

`bolero.scxml` (a Qt compound document — the `_virtual*.scxml` siblings are editor artifacts already merged inline; the machine has **0** `<invoke>` and 203 states) lowers 87% admitted, but its **media-transport control core is a structural dead end**: `mediaPlayerSourceCheck` decides play-vs-pause via `cond="In('muteOn')"` / `cond="In('muteOff')"`, and `mediaStopped`/`mediaPlaying` onentry choose repeat-vs-next via `In("mediaRepeatTrack")`. `In(...)` is an SCXML **runtime cross-region active-state predicate**, not an ECMAScript expression, so the constrained front-end (D-M1P6-2) lowers each `In()` to `UnsupportedExpr` → falsey at runtime. Net: neither play nor pause ever fires; the control loop cannot run. 10 of the machine's 25 `reject` diagnostics are `In()` calls (plus 9 `parse-error` from radio helper functions stored as `<data expr="function(x){...}">`, which JS-`function` syntax also outside the subset).

### Root cause

D-M1P6-2 admits expressions/statements but not the SCXML `In(<stateid>)` predicate (it needs the runtime to answer "is state X in the active configuration" — which the IR/runtime *does* track, but the front-end has no admitted form for it). Real infotainment/automotive charts (Bolero, likely Morse and others) lean on `In()` for orthogonal-region-aware dispatch, so this gap blocks faithful lowering of that class of machine.

### Fix prescription

- **Now (workaround, used for SCTD):** normalize the machine — replace `In(<region-state>)` checks with explicit datamodel state variables that mirror the orthogonal-region intent (e.g. `s_mute`/`s_repeat`/`s_source`), an admitted D-M1P6-2 form. This is the SCTD-00 §5.3 normalized-form path with provenance back to the upstream source; it is how the SCTD "Media Player" machine is produced (a normalized media-player derived from Bolero, lowering with 0 diagnostics).
- **Future (real fix):** extend the admitted subset to support `In(<stateid>)` as a `cond`-context predicate, lowered to a runtime configuration-membership check (the runtime already tracks the active set). This is the path to lowering the **real** Bolero control core. It is an admitted-subset change → a M1P6 D-M1P6-2 amendment (Specification Required) + a new scjson generator phase; out of scope for v0.4.2.

### Verification

Pending the future extension. The workaround is verified: the normalized media-player derived from Bolero lowers with 0 diagnostics, emits, and `cargo check` passes (SCTD demo, 2026-06-20).

### Tracking

- Admitted-subset owner: `docs/todo/scjson/TODO-SCJSON-SCRIPT-M1P6.md` D-M1P6-2 (a reciprocal note records the `In()` gap + the normalized-media-player conformance decision).
- SCTD consumer: rlvgl `docs/concepts/SCTD-00-CONCEPTS.md` §5.1/§5.3 (Media Player = normalized, provenance to bolero).
- Also surfaced: radio helper functions stored as `<data expr="function(){…}">` (JS function-literals) are likewise outside D-M1P6-2; same normalize-or-extend disposition.

---

## ERRATA-004 — Inline data initialization in the Python engine and executable IR

**Resolved on the Python `v0.4.3` branch.** First reproduced on 2026-11-21
with published version 0.4.2, tag `1363d3e`. Package publication is a
separate release action.

**Symptom and root cause.** Original Alex Z test 155 declares an inline array
at `tutorial/Tests/ecma/W3C/Mandatory/Auto/test155.scxml:8`. The converter
stores the characters, including indentation, in the declaration's
`content` list. On 0.4.2, `py/scjson/context.py:2249` wrapped those strings
on both file routes and `context.py:562` joined the Python representations
of those wrappers. The direct validated-model route joined the original
strings. Both paths gave foreach a string to iterate. The file routes
left `Var2` equal to the closing brace of a dictionary representation.
Separately, `py/scjson/exec_ir.py:1133` read only the declaration's `expr`
attribute. The inline slot therefore had no initial value. Expression
collections could also silently lose unrepresentable members, including
signed numbers.

**Fix and downstream impact.** Commit `b0a9a372af55e06256bd9a26d9a3e9cfa147a3c0`
preserves character-data parts on file intake, decodes inline JSON once at
initialization, and uses the same value in the IR. The IR keeps complete
constant collections and leaves a collection with a dynamic member unknown.
Authored character data survives the XML round trip. iState removed its
inline-to-expression vector rewrite in `2a4f6c4174ce8b3cc536ab2c59d66229394a6250`.
[Python engine guide](../ENGINE-PY.md#overview)

**Verification.** With the pinned tutorial submodule initialized, run
`PYTHONPATH=py python -m pytest -q py/tests/test_engine.py py/tests/test_exec_ir.py`.
The original ECMAScript and Python 155 files both reached `pass` via
`from_xml_file` and `from_json_file`, with `Var1 = 6`, `Var2 = 3`, and
`Var3 = [1,2,3]`. Changing the last element to 4 gave `fail`, 7, and 4.
The 23 conversions in the Docker VM comparison were byte-identical between
versions. Both SoS charts matched through both routes and all seven native
SoS vectors passed. See the regression tests
`test_inline_foreach_original_155` and `test_original_155_lowers_inline_collection_and_loop`.

| Qualification artifact | SHA-256 |
| --- | --- |
| Python 0.4.3 wheel | `91aa75003aa3ddee81ad7f50265cced68dcbc905d974cd582d0243cb4f0628f5` |
| Docker VM 0.4.2 baseline evidence | `c7fea263cf59b64804d2ce154147c4ba85fe5f40c3d44d45262a55c534553262` |
| Docker VM 0.4.3 upstream evidence | `f45c01d6f5eeeb84dcee5d0e5bf1214177a86a4983e4ee5f40619ca3610e07a2` |
| iState generated-code review ZIP | `5fc281610a9ec1fe882a7d8c2c70ee61e0b0b6847f9061ee1a6a35bc18b1ceed` |

The three entries below use the same two VM receipts and Alex Z Tests tree
`aa46a43361f6281a70d0809e45a3ce3dd906c486`. Across 20 original foreach
charts, counts matching the authored final **and** selected data fields rose
from 8 to 14 on XML and from 4 to 8 on SCJSON. Each open entry requires a
fix and a regression test in both dialects.

## ERRATA-005 — First-use item and index bindings reach the wrong final

**Open, EXEC-C.** Tests 150 and 151 fail through XML and SCJSON on 0.4.2
and on `b0a9a37`. On 0.4.3 the last declared and first-use item/index
pairs both equal `(3, 2)`, yet both charts select `fail`. Their final
guards read the newly introduced item and index respectively. Trace the
bindings across the state change and the eventless guard before assigning
a root cause. Close when both original charts reach `pass` and retain
both pairs through both file loaders.

## ERRATA-006 — An action failure inside foreach leaves later iterations running

**Open, EXEC-C.** In original mandatory test 156 the body increments
`Var1`, then attempts `<assign location="Var5" expr="return"/>`. On
`b0a9a37` the XML and SCJSON engines finish at `fail` with counter and
last item both equal to 3. The chart expects the loop to stop on the first
error. Trace expression failure, error-event delivery, and propagation
out of the loop. Close when both loaders select `pass` with counter and
last item equal to 1, alongside a control whose valid body visits all items.

## ERRATA-007 — Converted SCJSON loses behavior in three original foreach charts

**Open, EXEC-C / conversion.** In both original dialects on `b0a9a37`,
XML matches the expected state and fields. Normal SCJSON conversion followed
by strict JSON-file execution gives the observations below.

| Alex Z test | XML | Converted SCJSON |
| --- | --- | --- |
| 153, conditional assignments inside foreach | `pass`, `Var4 = 1` | `fail`, `Var4 = 0` |
| 457, invalid bindings followed by a valid loop | `pass`, `Var6 = 6` | `fail`, `Var6 = 0` |
| 459, ordered values with an index | `pass`, `Var5 = 1` | `pass`, `Var5 = 0` |

Trace the first differing action against the original XML order for each
chart. Check what survives conversion before assigning the defect to a
serializer or engine. Close each case when both routes reproduce the
authored final and data witness. A final-state-only assertion misses 459.

## ERRATA-008 — Literal send and donedata payloads fail canonical validation

**Diagnosed, conversion / Python model.** On 0.4.2 the converter returns
literal character data for `<send><content>` and `<donedata><content>`.
At `py/scjson/pydantic/generated.py:93`, `ScxmlContentType.content` expects
a list of nested charts. Direct validation of the converter's SCJSON therefore
rejects the first string, including valid ordinary text, digits, multiline
text, and JSON-shaped text. ERRATA-004 concerns the separate `<data>` type.

The pinned Alex Z census found 17 such roots in the Tests tree identified
in ERRATA-004. These are the two ECMA Custom/types
`testConditionalExpressions*` charts, both dialects of mandatory 179,
354 and 529, ECMA mandatory 294, and both dialects of optional 520, 532,
562 and 578. The separate malformed Python 401 assignment and the ECMA
`test-enc-UTF8` root transition account for the other two intake refusals.
Replaying all 19 on both package versions produced byte-identical intake
results, SHA-256 `6775c9ffd2b163e0daa7a5d0d81577501c1825ac5d46ba14d95428f9da5199a5`.

**Fix target.** Correct the source definition and generation of mixed payload
content, regenerate the affected models/schema, and check maintained bindings.
Replay XML conversion, canonical validation, SCJSON-to-XML, and the actual
delivered payload. Retain text, whitespace, nested markup, and nested-chart
controls. Keep the two malformed inputs as explicit refusals.

## ERRATA-009 — Original execution cases select the wrong final

**Open, EXEC-C.** The initial 0.4.2 Docker VM pilot ran 14 original ECMA
mandatory automatic charts, each in both strict and lax mode. Seven selected
`fail` where the chart expected `pass`. Case 151 is tracked in ERRATA-005.
Case 570 passed the subsequent control that drained immediate work before
advancing the clock. Retain that scheduling order in future runs.

| Case | Executable requirement to reproduce and fix |
| --- | --- |
| 159 | An error in a send skips subsequent actions in the executable block. Capture the following assignment and the pending error event. |
| 173 | A send uses the current value of `targetexpr`. Record the evaluated destination and delivered event. |
| 216 | Invocation uses the current value of `srcexpr`. Supply the original child file and check completion in the parent. |
| 404 | Exits run child before parent, with reverse document order for ties. Capture the actions in order. |
| 500 | The SCXML event I/O processor exposes its location. Record the value read by the authored guard. |

**Closure.** Carry each row independently. Establish the first discrepancy
with its original companion files, then require the authored final and the
intermediate observation in the table. Preserve 570 as a passing control.
The original pilot result has SHA-256
`8ea277ae7dac00910f5f2d20d28f0e9e7a1936b442bb329f1e3bac1322dad9ce`.
The bounded Windows replay of both releases on the original schedule ran
56 checks (14 charts × two modes × two versions). Each group retained
the same seven passes and seven failures. No process timed out. Replay
SHA-256 `8ed4e0a83ebf7d063f69e1fb356ba1d3337acb4782ca54f9a5db14a8626facbd`.
The separate two-schedule replay on each wheel reproduced the distinction
between 216 and 570. The 0.4.3 timing receipt has SHA-256
`119ad0e234302bfd0c39fdd28570272ddb992b566f971d9213e9b8e558d6d41e`.

## ERRATA-010 — Qualification fixture, CLI, and platform failures

**Open, Python CLI / harness.** Running `python -m pytest -q py/tests`
on Windows against `b0a9a37` produced 567 passes, 17 failures and three
skips. Every failing test reproduced on baseline `d04ae8f` at the same
assertion with the same failure signature. The eight affected test modules
matched between revisions. The targeted baseline comparison has SHA-256
`8bb2fd18ad3f8be85e4fcba32365aaecbf673bf605ba0764e7812439f450fac1`.
Track these independently of the runtime cases above.

| Affected checks | Reproduction and fix target |
| --- | --- |
| Three `test_cli.py` recursive conversion, validation, and verification tests | The first conversion exits 1 with `FileNotFoundError` at the original temp path. A shorter pytest temp root recovered conversion and validation. Verification then reached line 163 and misread the original XML using the host encoding. All five sampled originals parsed with explicit UTF-8 BOM handling. Check both path length and encoding on Windows. |
| Nine reference-launch cases in `test_exec_compare_advanced.py`, `test_exec_compare_integration.py`, `test_exec_sweep_integration.py`, and `test_uber_conv_corpus.py` | `_build_trace_cmd` loses backslashes when a Windows interpreter path is parsed as unquoted POSIX shell text. Preserve argument boundaries and rerun each comparison, including paths with spaces. |
| `test_xinclude_resolve_mode_converts_assembled_tree` | A drive-letter parent path resolves to bare `child.scxml`. Resolve relative includes against the actual document directory and check both preserve and resolve modes. |
| Swift source check in `test_conv_h.py` | The Swift submodule was absent. Initialize the pinned fixture for qualification and distinguish an unavailable checkout from a binding failure. |
| `test_uber_test_runs_focused_conversion_corpus` | The redirected Windows CLI banner cannot encode the arrow. The harness skips the converter and later misses its output. `PYTHONUTF8=1` made the unchanged test pass. Check CLI output encoding and make converter startup failure visible. |
| `test_payload_heuristics_chained_range` and `test_exec_sweep_small_corpus` | The inline test fixture and `tests/sweep_corpus/range.scxml` both contain raw less-than signs in an XML attribute. The unit test stops at parsing and the sweep misses its coverage row. Correct the test-owned XML fixtures and require an actual coverage row and payload assertion. |

Close each row with the affected test IDs, platform, interpreter, result,
and any required test dependency. Keep individual outcomes visible when a
common fix clears several checks.

Two Windows recovery runs isolated setup effects. The three recursive CLI
tests passed with a shorter pytest temp root and `PYTHONUTF8=1`. The three
maintained-binding checks passed after initializing Swift at the recorded
gitlink `38b5c24d3c7777d9c7287b9020d4e0885685a29c`.

On docker-vm the same wheel passed the full Python suite with both the
tutorial and Swift gitlinks populated: 585 passed, zero failures, two
optional SCION comparisons skipped because SCION was unavailable. The
one failure in the preceding Linux run was the missing Swift fixture.
All 587 test IDs matched between runs. Full Linux evidence SHA-256
`fe47b20e7552c574eb8069a9094dd089ce677f81ca2aba9fcc3062c790a2fa6f`.

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
