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
| ERRATA-003 | 🟢 | Portable state membership in transition and conditional-action guards | 2026-06-20 | M1P6 D-M1P6-2 |
| ERRATA-004 | 🟢 | Inline JSON data becomes text in the Python engine and disappears from executable IR | 2026-11-21 | Python execution / M1P6 |
| ERRATA-005 | 🟢 | First-use foreach bindings have the expected values but the chart selects the wrong final | 2026-11-21 | EXEC-C |
| ERRATA-006 | 🟢 | Execution continues after a failing action inside foreach | 2026-11-21 | EXEC-C |
| ERRATA-007 | 🟢 | Converted SCJSON disagrees with XML on foreach action order and data witnesses | 2026-11-21 | EXEC-C / conversion |
| ERRATA-008 | 🟢 | The canonical Python model rejects authored literal send and donedata payloads | 2026-11-21 | Conversion / Python model |
| ERRATA-009 | 🟢 | Original ECMA execution cases select the wrong final in the 0.4.2 pilot | 2026-11-21 | EXEC-C |
| ERRATA-010 | 🟢 | Python qualification has reproducibility, fixture, and platform failures | 2026-11-21 | Python CLI / harness |
| ERRATA-011 | 🟢 | Conversion loses the authored order of parallel regions of different element kinds | 2026-11-21 | Conversion / execution |
| ERRATA-012 | 🟢 | Implicit initial state selection loses document order across child kinds at the root and in compound states | 2026-11-21 | Conversion / execution |
| ERRATA-013 | 🟢 | Raw SCJSON executable keys can silently drop an action or branch | 2026-11-21 | Conversion / intake |
| ERRATA-014 | 🟢 | Offline vector generation consumes host time between chart steps | 2026-11-22 | EXEC-E / Python vectors |

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

- **Status**: 🟢 resolved on `v0.4.3` and in the iState executable-IR Rust generator. Docker VM verification completed 2026-11-21.
- **First seen**: 2026-06-20, lowering `tutorial/Examples/Qt/SkodaBoleroInfotainment/Model/bolero.scxml` through `exec_ir.lower_document`.
- **Owning phase**: M1P6 (`docs/todo/scjson/TODO-SCJSON-SCRIPT-M1P6.md` §"Admitted ECMAScript Subset", D-M1P6-2).

### Original symptom

In the original Qt Bolero chart, `mediaPlayerSourceCheck` selects play or
pause by checking `muteOff` and `muteOn` in another region. On entry,
`mediaStopped` checks `mediaRepeatTrack` to choose play or next track.
`mediaPlaying` checks `mediaPlayerScanModeOn` to schedule a delayed forward
command. The 0.4.2 generator lowered the membership calls to unsupported
expressions. A bare guard could never take its branch, and negation could
make an unsupported guard succeed.

### Root cause

The original D-M1P6-2 whitelist omitted the SCXML membership predicate.
Generated guard evaluation could read the datamodel and event, but had
no access to the current session's active configuration.

### June 2026 disposition

- **Now (workaround, used for SCTD):** normalize the machine — replace `In(<region-state>)` checks with explicit datamodel state variables that mirror the orthogonal-region intent (e.g. `s_mute`/`s_repeat`/`s_source`), an admitted D-M1P6-2 form. This is the SCTD-00 §5.3 normalized-form path with provenance back to the upstream source; it is how the SCTD "Media Player" machine is produced (a normalized media-player derived from Bolero, lowering with 0 diagnostics).
- **Future (real fix):** extend the admitted subset to support `In(<stateid>)` as a `cond`-context predicate, lowered to a runtime configuration-membership check (the runtime already tracks the active set). This is the path to lowering the **real** Bolero control core. It is an admitted-subset change → a M1P6 D-M1P6-2 amendment (Specification Required) + a new scjson generator phase; out of scope for v0.4.2.

### Historical verification

The normalized media-player fixture lowered with zero diagnostics and
passed `cargo check` for the SCTD demo on 2026-06-20.

**Open at the 0.4.3 package boundary.** At `76ab694`, the original Bolero
chart has 40 literal `In()` calls across 29 guard sites. A parallel-region
probe distinguished the existing interpreter from generated Rust. Both
could identify the active leaf and its ancestors directly, but the generated
positive and negated guards selected the wrong branches. A lowerer must
carry the current session's configuration into guard evaluation, including
conditional actions. The next D-M1P6-2 amendment should specify the admitted
argument, evaluation timing, and unknown-state behavior, then test those
choices against compiled code on both source routes. Host probe SHA-256
`2c448429605fe8cf0d03bfe057f1b34ec076b264c050b860ad6a62bdfb7475a8`.

### Tracking

- Admitted-subset owner: `docs/todo/scjson/TODO-SCJSON-SCRIPT-M1P6.md` D-M1P6-2 (a reciprocal note records the `In()` gap + the normalized-media-player conformance decision).
- SCTD consumer: rlvgl `docs/concepts/SCTD-00-CONCEPTS.md` §5.1/§5.3 (Media Player = normalized, provenance to bolero).
- Also surfaced: radio helper functions stored as `<data expr="function(){…}">` (JS function-literals) are likewise outside D-M1P6-2; same normalize-or-extend disposition.

### Verified repair on 2026-11-21

The D-M1P6-2 amendment in parent commit `6a3e06e94` admits
`In('stateId')` in transition, `if`, and `elseif` conditions.
The lowerer emits an existing `CallNode` with a single string literal.
The generated Rust runtime checks the entered states of the instance
executing the guard. The Python and Rust engines select transitions
before exits. Their exit handlers, transition actions and entry handlers
see the configuration at their respective points in the microstep.
An unsupported operand disables the whole guard, including under negation.

The docker-vm matrix used scjson `2a9c9eb2bc9f98836a961f2294830090f5ec3925`
and iState `ccbf0b585b7cf1c1897948ca99e98a99c36f56ac`. The XML and
canonical SCJSON inputs produced byte-identical generated crate members for
all 25 charts. Each route compiled and executed its own crate.

| Witness | Results on both input routes |
| --- | --- |
| Original Alex Z tutorial tests | All 15 charts containing membership guards reached the authored `pass` in Python and Rust. Three single-edit controls reached `fail`. The census covered 440 SCXML files at tutorial commit `a442d41e`. |
| Bolero guard coverage | 28 admitted guards, 38 calls, 84 combinations. Both engines matched the independently computed truth table. The remaining guard has two calls in an unsupported ternary and was rejected. On the baseline Rust missed 56 of the 84 combinations on each route. |
| Bolero media source | Three original state elements were copied into an isolated controller. The original valid-source event reached `mediaPlayerDoPlay` when unmuted and `mediaPlayerDoPause` when muted. |
| Whole Bolero | The original XML and corresponding SCJSON compiled. When pending startup events were serviced before external input, Python consumed `error.execution` and reached `fail`. Rust remained in the five startup leaves and reached the radio configuration on power-on. The raw Qt chart depends on unimplemented host/script behavior. |
| SoS | The counter and guarded-transition charts matched their five scenarios in both engines. The independent native runner passed its seven vectors and rejected an altered tick count. |

The Python wheel is `scjson-0.4.3-py3-none-any.whl`, SHA-256
`bea391cba142d5e81ac46bcbf02c160205f5245b7d0c3246b0d40c6168ff578e`.
The full Python suite passed 779 tests on Linux with two optional skips,
and 778 tests on Windows with three optional skips. The focused docker-vm
gate passed 52 upstream tests and 26 iState emitter and compatibility tests.
The final matrix receipt SHA-256 is `4a938815bdc325868cf891feb66bdf5210ead5f6c1f941031c4513099d15bc3d`.
Python and Rust each passed all 112 scenarios with expected results on each
route. The internal-event-first whole-chart trace is recorded separately.
The generated crates and their run inputs are in the parent project's
`.aws-release/scjson-ir-membership-20261121/state-membership-generated-rust-review.zip`,
SHA-256 `bb0b0cb763bf55590bb41339308f89733add51326eec4a4b244d3fd316b69573`.

**Consumer observation.** Interactive Dining's original five `break.N`
transitions default to external. They can exit and reenter other regions,
which breaks one of seven existing expectations. A disposable copy declaring
those five transitions internal passed all seven original tests on docker-vm.
The review packet includes the exact patch. ERRATA-011 records a separate
loss of structural region order that can affect membership during entry.

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

**Resolved, EXEC-C, 2026-11-21.** Tests 150 and 151 failed through XML and SCJSON on 0.4.2
and on `b0a9a37`. On 0.4.3 the last declared and first-use item/index
pairs both equal `(3, 2)`, yet both charts select `fail`. Their final
guards read the newly introduced item and index respectively. At entry to
`s2` the guard evaluated to 3 or 2. The old guard handler required a Boolean
instance, queued `error.execution`, and selected the unconditional fallback.

Commit `d0cb3791aeeb951297ad54d9cbc862a4c13e41ff` applies datamodel
truth testing after sandbox evaluation. On docker-vm the untouched ECMA
and Python 150 and 151 charts passed on all eight XML and SCJSON routes
with both pairs intact. Numeric zero took the fallback without an error.
A missing variable and original invalid-condition test 344 retained their
error event. Both SoS charts and all seven native vectors passed.
The 20-chart final-and-data counts improved from 14 to 18 for XML and
from 8 to 12 for SCJSON. All previous passes were retained.
[SCXML conditional expressions](https://www.w3.org/TR/scxml/#ConditionalExpression)

| ERRATA-005 verification | SHA-256 |
| --- | --- |
| Baseline VM evidence | `c3c10ebdf8393c942f2b6435e9fd0c72d599a7c7c7eae028bed0694258a5af1d` |
| Qualified Python 0.4.3 wheel | `f6c19292c1744a58aed718ce7af3fea330e6805af7a1086a529a78c7bfd9c104` |
| Candidate VM evidence | `b8d8cc6d1556025dd36128e6d40ad583140a36efad01b2e097dc00de5e9a6564` |

## ERRATA-006 — An action failure inside foreach leaves later iterations running

**Resolved, EXEC-C.** In original mandatory test 156 the body increments
`Var1`, then attempts `<assign location="Var5" expr="return"/>`. On
`b0a9a37` the XML and SCJSON engines finish at `fail` with counter and
last item both equal to 3. The chart expects the loop to stop on the first
error. At `961f7e1`, both dialects and both file loaders select `pass` with
counter and last item equal to 1. The valid control visits all three items.
Test 159 preserves the variable that follows a failed send and delivers
`error.communication`. All 20 block-boundary tests passed on docker-vm.
The VM evidence archive has SHA-256
`9a25ce9edc887b4d99837f045620d711bf26ff2f0ef0dcd9672561717171312f`.

The broader sweep also exposed earlier false passes in ECMA 460 and 525
and Python 525. The old engine stored a failed assignment's source text.
The corrected engine leaves the previous collection intact on failure.
The ECMA array operation and original Python type error have separate
regression coverage.

## ERRATA-007 — Converted SCJSON loses behavior in three original foreach charts

**Resolved, EXEC-C / conversion.** In both original dialects on `b0a9a37`,
XML matches the expected state and fields. Normal SCJSON conversion followed
by strict JSON-file execution gives the observations below.

| Alex Z test | XML | Converted SCJSON |
| --- | --- | --- |
| 153, conditional assignments inside foreach | `pass`, `Var4 = 1` | `fail`, `Var4 = 0` |
| 457, invalid bindings followed by a valid loop | `pass`, `Var6 = 6` | `fail`, `Var6 = 0` |
| 459, ordered values with an index | `pass`, `Var5 = 1` | `pass`, `Var5 = 0` |

Grouping actions by kind erased the interleaving of assignments, other
actions, and conditional markers. The optional `execution_order` list now
preserves that information. Original 153, 457 and 459 select `pass` through
both loaders in both dialects, with `Var4 = 1`, `Var6 = 6`, and `Var5 = 1`
respectively. The first VM run found three failures when an absent field
serialized as null on Pydantic 2.11.7. At `a9b82e9` all 34 order checks
passed on that version, including legacy documents and explicit empty lists.
See the [wire contract](SCJSON-CONV-00-CONCEPTS.md#executable-child-order-errata-007).

On docker-vm the packed JavaScript converter from `bc58fae` converted and
restored 47 original and SoS charts. Python independently executed both
returned forms of 150, 151, 153, 155, 457 and 459 in both dialects. All
24 final-and-data checks passed. The tarball has SHA-256
`1ab72f3bd0113ac15a20b34662094eec780f957616b7c1cb47e9bb8bef485890`.
The packed-converter VM evidence has SHA-256
`8f040e6692f2ae030610de72f94900d2441d3bb29c4ccb7ed3b99d4a00cebecf`.

## ERRATA-008 — Literal send and donedata payloads fail canonical validation

**Resolved, conversion / Python model.** On 0.4.2 the converter returns
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

Commit `bf1f852` preserves literal text, qualified XML elements, and inline
charts in the canonical payload model. All 17 originals passed intake,
model and schema validation, and literal round-trip checks on docker-vm.
The focused tests also checked whitespace, nested markup, actual send and
done data, child completion, and the two independent malformed inputs.
The combined ERRATA-007/008 run at `a9b82e9` passed all 82 focused checks
and the SoS controls. The tested wheel has SHA-256
`c4e01488d8521c1ac6ddccd2500477e64d4d09e4bd850d7e9bd9c331dfbb6cf9`.
The VM archive has SHA-256
`0c1ee9f9bff0cf73ca1f22dca83d67892c558f0ba024c6e89671e9f369163b96`.

An XML parser independently compared all 17 original payload literals with
the XML restored by the packed JavaScript converter. Every string matched.
Rust 1.85.1, Ruby 3.3.14 and Swift 6.2.4 also decoded and encoded a sparse
chart with text, qualified markup, an inline chart, an omitted order, an
explicit empty order and repeated conditional markers. Native binding
evidence SHA-256
`b60336985d1c0826e38431402af6b7aea5af0ca5ec0e0bb60bddc9aec3439189`.

The final wheel at `76ab694` admitted 425 of 427 Alex Z root charts on
docker-vm, up from 408. The run verified the original hashes of all
440 files and excluded the same 13 invocation helpers. All 17 newly
accepted roots are the payload cases above. Every previously accepted
root still validated. Intake evidence SHA-256
`d13f3dfcceeb229f337d640ec2738768e95fb41a9113a077f2d7ee94e0f85af6`.

## ERRATA-009 — Original execution cases select the wrong final

**Resolved, EXEC-C.** The initial 0.4.2 Docker VM pilot ran 14 original ECMA
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

At `a7592d18111c12e472a7098ea02d6a4faa414171` the five cases and
timing control 570 passed in both dialects on both XML and SCJSON entry
points (24 observations). In 159 the failed send left the counter at
zero. In 173 the event reached `#_internal` after the target variable
changed. In 216 the parent loaded the original sibling file and received
`done.invoke` before the timeout. In 404 the exit and transition actions
raised `event1`, `event2`, `event3`, and `event4` in order. In 500 the
authored expression returned the registered address of its own session.
Separate controls verified self-addressed delivery and distinct session
addresses. A nonempty string containing the unevaluated expression had
previously made the guard in 500 pass.

**404 verification, November 22, 2026.** On docker-vm, both original Alex Z
dialects reached `pass` in strict Python and iState's compiled executable-IR
Rust through XML and converter-produced SCJSON read back from disk. The
observed producers were the exit handlers of `s01p2`, `s01p1`, and `s01p`,
followed by the effect of `s01p → s02`. The receivers consumed the four
events in FIFO order, advancing from `s02` through `s03`, `s04`, and `s05`
to `pass`. Python then drained its synthetic root-completion event. The Rust
public startup call had already drained the four authored events on return.

Swapping sibling elements made `event2` arrive first. Moving transition
content ahead of exits in the diagnostic runtimes made `event4` arrive
first. Both controls selected the wildcard to `fail` in `s02`. Renaming the
siblings while preserving their positions retained the original behavior.
The trace checker also detected a deliberately incorrect attribution of
`event4` to the parent exit with the correct queue and final. The four
original Rust libraries were byte-identical. This confirms the existing
ERRATA-009 repair on the 0.4.3 wheel with SHA-256
`1041e450f54836886449b7c0351fa8864078005fa7b241444f440bcfa492cdcc`.
The 404 review ZIP has SHA-256
`5154b97c4d8e692f8acc9e8d2d8f76eec7faf4ff8ef1c716070aa6eac336b58c`.
The accompanying SoS replay matched all 84 Python and generated Rust
snapshots across the counter and guard charts. All seven native SoS vectors
passed, and the native runner rejected the one-field wrong golden. SoS ZIP
SHA-256 `5db3e9a83e069f3c16ba223007163bd58c8c77af9e35298615b59951a497d2f9`.
[Python regression](../../py/tests/test_parallel_exit_order.py)

The same VM run matched the authored foreach final and data on 19 of 20
originals through each loader. In ECMA 460 and 525 the collection became
`[1,2,3,4,4,4]` in exactly three iterations. Python 525 evaluates
`Var1 + '4'` with a list on the left. Its first assignment raises a type
error and correctly leaves the counter at zero and the list at `[1,2,3]`.
The original chart therefore selects `fail`. All four SoS file routes
and seven native vectors passed. VM evidence SHA-256
`6b379f1d98f1a26858ad2b249a5105e46fe8d2bb3fc5b76fc5678fe2ae0ed2e6`.

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

**Resolved, Python CLI / harness.** Running `python -m pytest -q py/tests`
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

The portability repair runs reference commands with platform-native argument
boundaries, uses the Windows extended path form for recursive conversions,
and resolves local XInclude file and directory URIs. The two chained-range
fixtures now encode their XML attribute correctly. The Windows run repeated
all 17 failing test IDs plus three tests for argument quoting, deep paths,
and relative includes. All 20 passed. The full standalone Python run passed
587 tests and skipped three optional SCION and Ruby checks. The Linux
portability run passed all 11 selected tests with the same source changes,
including a real reference process and generated conversion and sweep files.
Its verified evidence SHA-256 is
`e33bd1fffbc89a9d1e2f29c08893acc4819e970fb48e82082badf57cee25b187`.

### Final 0.4.3 package qualification for ERRATA-005 through ERRATA-010

Implementation commit `76ab694fe1ddfc08de8d53cd97d1bd01f46497f3`
passed 718 full-suite tests on Linux and 717 on Windows. Both skipped two
optional SCION comparisons. Windows also skipped the Ruby CLI comparison.
The independent Ruby binding test ran on docker-vm. The final semantic run
passed 111 focused checks, all 24 adjacent-case checks, both SoS charts
through both loaders, and all seven native vectors. The final packed Node
rerun used the same Python wheel for its returned-file execution checks.

| Artifact or result | SHA-256 |
| --- | --- |
| Python wheel | `4a5ac91456755725607908b92772007528a18f703b299c23dc7cfee2d82c90a4` |
| npm tarball | `1ab72f3bd0113ac15a20b34662094eec780f957616b7c1cb47e9bb8bef485890` |
| Linux full-suite archive | `26f1716e6225c4c25c382170097a22ac6783fe82b81af7e69bbfb64917b1bc46` |
| Windows full-suite result | `ba250c56f0ec1207425cc103ea0403cb5376220af279ba28b8286dcef61b237b` |
| Final semantic archive | `f23ef65c039072349af10a3a1e4538841e33aa52d59a83275e029d1175b722d2` |
| Final packed Node archive | `ee58b74a2df668fd509b05394a66997c4c85cc2f0ff3b9b661ef54854cf9f886` |
| Combined package and review ZIP | `207e2197310324c92ba2e554ab89b20062c57701f6005417cc7484907741cc6e` |

## ERRATA-011 — Structural order of mixed parallel regions

**Diagnosed on 2026-11-21 at Python 0.4.3 candidate `2a9c9eb`.**
Two XML charts reverse a nested `<parallel id="first">` and a sibling
`<state id="second">`. The old converter emitted byte-identical SCJSON,
SHA-256 `ffb067a26c81a34af68536195446b46c200276c54649161d743b659603c10c59`.
The structural model collected children by kind. Both file loaders entered
`second` before `first`, including when the author placed `first` first.
An entry action in `second` that tested `In('first')` consequently missed
its authored effect. Both charts reached the same final set of active states.

The original Alex Z `testDoneParallelThreeLevels.scxml` still reached `pass`
through both loaders. Its terminal state alone concealed the entry-order
error. The original witnesses and observations are in the ERRATA-003 review
packet under `review-extras/mixed-structural-order/`.
Host result SHA-256 `91a22a9a1268029db55029c533fef3ebe061a783c65efa989f44fb718b8a0b0e`.

### Verified repair on v0.4.3

Mixed `<parallel>` elements now record each direct region in `region_order`.
Each `state` or `parallel` entry consumes the next child in the matching
array. Nested parents carry independent lists. Comments, history, handlers,
and foreign elements do not consume a region. ERRATA-007's `execution_order`
continues to describe executable children. [Conversion contract](SCJSON-CONV-00-CONCEPTS.md#parallel-region-order-errata-011)

Unmarked SCJSON still reads each `state` in array order, then each `parallel`.
The original XML is needed to recover an interleaving that the old converter
discarded. The standalone native Rust XML exporter previously used lexical
key order, which put `parallel` first. It now follows the common state-first
rule. Authors can specify a parallel-first list to reproduce that output.

On docker-vm, the Python engine and independently compiled iState Rust
agreed with the authored results on 45 routes per engine across 16 charts.
The mixed cases ran from original XML, saved SCJSON, and re-exported XML.
Six permutations covered repeated children of the same kind. The two
unchanged Alex Z mixed-region originals both reached `pass`. An instrumented
copy of the three-level original exposed the intermediate results below.

| Input | Expected entry effects | Baseline | Fixed Python and Rust |
| --- | --- | --- | --- |
| Nested `first` before sibling `second` | `first`, `second` with `In('first')` true | `second`, `first` (false) | `first`, `second` (true) |
| Sibling `second` before nested `first` | `second`, `first` with `In('first')` false | `second`, `first` (false) | `second`, `first` (false) |
| Three-level instrumented Alex Z chart | Outer `12`, inner `34`, preceding region active | `21`, `34`, `0` | `12`, `34`, `1` |

The exact unmarked legacy witness retained its state-first entry log through
SCJSON and restored XML in both engines. All 21 malformed input checks
refused the supplied sequence. Deliberately swapping the expected order
failed in both engines on all three input routes. The native SoS suite
passed all seven vectors. A separate Windows replay compared 113 scenarios
over 25 previously saved SCJSON files with their earlier observations. All
matched, as did three additional legacy order fixtures.

The Alex Z catalog contained 440 files, including 13 helpers. Direct
canonical-model validation admitted the same 425 of 427 roots before and
after the repair. The context loader's input preparation also admitted
Python 401, for 426 of 427 on each revision. The execution matrix covered
the two originals with mixed regions. The rest of the census checked intake.

The standalone Rust converter passed all 24 locked tests on docker-vm.
Its CLI round-tripped both original Alex Z charts and both order witnesses,
and exported the exact legacy file with states first. The review ZIP
contains the qualified wheel and npm tarball, generated sources for all 47
candidate Rust runs, the input charts, per-route traces, and raw receipts.

| Evidence | Revision or SHA-256 |
| --- | --- |
| SCJSON Python, schema and JavaScript candidate | `891373068f9a5f913e8cfbb41c94c0b7530c2307` |
| iState generated Rust emitter | `1997bb599daafe5f2da270a11e81c0c52d08d9be` |
| Standalone native Rust converter and CLI | `c59a31f3a011734142a4ef7c618ddaaf9aa2ae33` |
| VM mixed-region matrix, generated crates and observations | `1aa128ddff16fec9d59fbe151f7b3b61958d15d4cd27a7d3412f720b51ed75ed` |
| Installed Python 0.4.3 wheel | `48d019b2bbba76dcab6037a79b2a1d61408d72afe2a6737219c21faa259b3149` |
| VM full wheel suite, 809 passed, two SCION skips | `513146aa69b61af551cb6e18d9ce7b278565a80bfab0dd4183f6e532685182dc` |
| VM focused wire/runtime suite (30) and iState Rust emitter suite (27) | `7a9475956cac80850cfe301e117d860c026f18ade1d873129263d0826e5ead72` |
| VM baseline and candidate canonical-model intake census | `8cc6227e8d7e46759e307d1eadc70486ee1b4665964e9b383729382ec6107cfe` |
| VM packed npm and Swift Codable checks | `2558ff6b5af3503b9b64df72227b454f500555f558717af116cc3eb19ba7d5b4` |
| VM native Rust locked suite and CLI conversions | `58c047411453b48a0da7abd24f360471c412c3d72605f68b8230b66cd9a55f6e` |
| `structural-region-order-generated-rust-review.zip` (929 members) | `75e21a545f7531a24ac5c57ef6791226ec9e6f6b1c9bf17bc2c3bde023b89b8b` |

---

## ERRATA-012 — Implicit initial state selection across child kinds

**Status.** Verified on the v0.4.3 branch on 2026-11-21. The original
diagnosis used the installed Python 0.4.2 package and the 0.4.3 candidate
`dd4debe3c57e24ba89de0b79d4d0c808671c86b5`.

**Symptom.** In the following chart, the first child of the document is
`p`. Its initial configuration must include `pLeaf`. Both Python file
loaders entered `s`. Moving `s` before `p` produced identical SCJSON.
Putting the same pair inside a compound state, or placing a `<final>`
before `s`, exposed the same loss. SCXML defines the first child state in
document order as the implicit initial target for both owners.
[SCXML root and compound-state rules](https://www.w3.org/TR/scxml/#scxml)

```xml
<scxml xmlns="http://www.w3.org/2005/07/scxml" version="1.0">
  <parallel id="p"><state id="pLeaf"/></parallel>
  <state id="s"/>
</scxml>
```

**Cause and impact.** At `dd4debe`, `py/scjson/execution_order.py:167`
captures `region_order` on a parallel owner. A document or compound state
has grouped `state`, `parallel`, and `final` arrays. With no explicit initial
target, `py/scjson/context.py:512` builds its children by kind and the
ordinary state wins in these examples. The change in active leaf precedes
the first event. A final child can also determine whether the machine
should finish at startup. ERRATA-011 covers entering all regions of a
parallel parent and remains resolved.

**Repair and verification criteria.** Preserve the implied first child in
conversion and execution at both owners, including children without an
authored ID. Retain explicit initial targets and a documented read rule
for older SCJSON. Before closing, compare the original, swapped and
explicit-target controls in Python and generated Rust through XML, saved
SCJSON and restored XML. Check both the active leaves and completion.

**Reproduction.** Eight host charts covered the two parent kinds, two
child-kind pairs and both orders. Each Python version chose the wrong
leaf in four of eight charts through each loader. Within each swapped
pair, canonical SCJSON was byte-identical. A scan of all 440 Alex Z XML
files found no parent with this implicit-target ordering inversion.
The 0.4.3 observation file has SHA-256
`ace22d626fda53e875bc918a8147d1ba498055ad354c8c669a800f458ee26841`.
The 0.4.2 replay has SHA-256
`f8adcbec282b9f234f17dc1d2bc13818cc2aff4bc415e49b37ed7fee970abc4e`.

### Verified repair on v0.4.3

XML conversion records the order of mixed `state`, `parallel`, and `final`
children in the owning document or compound state's `state_order`. Startup
uses the first recorded child when the owner has no explicit initial target.
Children without an authored ID participate in the same order. A legacy
document without the list reads `state`, then `parallel`, then `final`,
preserving array order within each kind. Restoring an interleaving that the
old converter discarded requires the original XML or an author-supplied
list. [Conversion contract](SCJSON-CONV-00-CONCEPTS.md#document-and-compound-state-child-order-errata-012)

Python and compiled iState Rust on docker-vm produced the following leaves
from the eight original XML witnesses, their newly saved SCJSON, and XML
restored from it. The eight frozen legacy SCJSON inputs still selected `s`.

| Authored order | First active leaf at the document root | First active leaf inside the compound state |
| --- | --- | --- |
| `parallel p`, `state s` | `pLeaf` | `pLeaf` |
| `state s`, `parallel p` | `s` | `s` |
| `final f`, `state s` | `f`, document finished | `f`, compound state completed and document still active |
| `state s`, `final f` | `s` | `s` |

Explicit initial attributes selected the named state or parallel in either
owner. On the baseline, a compound `<initial>` transition selected the right
target but skipped its assignment. Both engines produced `2`. The repair
runs that assignment after owner entry and before target entry, yielding
`42`. A two-target transition produced `1234` on startup and ordinary
re-entry. Direct entry into the same two descendants produced `134` and
left the initial-transition count unchanged. [Two-target source chart](../../py/tests/fixtures/compound_initial.scxml)

The Docker VM matrix covered 30 charts and 98 runs per engine. It included
anonymous children, document completion, nested `done.state` delivery, the
preceding-region guards, Alex Z test 310, and two SoS charts. The separate
native SoS runner passed all seven vectors. The Alex Z conversion census
admitted the same 425 of 427 roots and restored the authored order at all
524 mixed owners in the 424 admitted roots that contained them. A Windows
replay also matched all 113 saved scenarios from 25 older SCJSON documents
and three additional historical witnesses.

The generated Rust `Machine::is_finished()` agreed with direct inspection
of the active top-level final states on all 155 recorded snapshots. The
deliberately wrong `s` expectation failed in both engines on all three
current routes for the parallel-first root and passed on the old JSON.
For all 30 charts, XML, saved SCJSON, and restored XML generated identical
library sources. The review ZIP contains the crates, inputs, traces, exact
wheel and npm tarball, and per-route comparisons.

| Evidence | Revision or SHA-256 |
| --- | --- |
| Tested scjson v0.4.3 implementation | `09d424b35afa1c8de061bc16023772a5678be7c7` |
| Tested iState Rust emitter | `2b724c43147e5f60b155cc96a9212c1f5b2b480f` |
| Installed Python wheel | `7882545eb82fad861e8fe562a3f1302b1cf76d5985e0cd7e7f5a0d53ad537c1e` |
| VM baseline | `36eb868403e6ecd250aa9716705b42875086c629dde6888079bbcb4cb06b411c` |
| VM startup matrix with direct Rust completion calls | `ce4ab16bdb611e3c02139416964d1f05b1cf0896c73ed5c916fe78e9ebc62cc0` |
| VM full wheel suite, 905 passed, two optional SCION tests skipped | `35dea7bacfed0fcd0ac2943a349384e3c164ade7de148015dd38c4845fae8851` |
| VM focused scjson suite (96) and iState Rust emitter suite (33) | `14a52d74fe70e4797231c604c97f9ac30162628393bcafdf6fbd92ed2370432d` |
| VM Alex Z canonical intake and order census | `399195193aabc822a031138f6b14817b709da107423ccb4a1b2e7720ecd5b498` |
| Windows replay of historical SCJSON | `978ae08cd3a8007ea3ab0a8f7d360daf2bd2c6f2a1b4cd1206ddcbe4983ac15a` |
| `implicit-initial-generated-rust-review.zip` (1,621 members) | `f3fd7f70e87a9fb05fe83ba42acf6a4c36ef55af677bda558abc4147e44ed671` |

---

<a id="errata-013"></a>

## ERRATA-013 — Raw SCJSON executable keys can silently drop an action or branch

At v0.4.3 `4a95164`, replacing `raise_value` with `raise` in an entry
block removed the event in the default reverse converter and in both
Python model families. The original reached `done`. The edited document
was admitted and remained in `s`. A lone `raiseValue` produced the same
loss on the canonical Python paths. The generated schema allowed extra
properties and both the model and the reverse converter ignored the key.
The intake rule is recorded under XML Element Name vs. SCJSON Field Name in
[the converter contract](SCJSON-CONV-00-CONCEPTS.md).

The installed Python **v0.4.2** package reproduced the loss on the host.
Both `Scxml.model_validate` and `SCXMLDocumentHandler.json_to_xml`
preserved the `tick` event for `raise_value` and omitted it for `raise` and
`raiseValue`. The v0.4.2 receipt records these two entry points. The
v0.4.3 VM receipt also exercises the runtime configuration.

### Resolution and verification

On v0.4.3, canonical readers reject XML and camelCase spellings on modeled
executable owners and diagnose colliding spellings before normalization.
Python exposes `validate_executable_keys(data, allow_camel=True)` for
clients that explicitly project camelCase. The Python schema, strict and
normal models, and reverse converter enforce the canonical spelling.
A single-file `scjson xml` refusal exits 1 before writing the destination,
including when a previous file exists. Wildcard payloads, extension
metadata, and child-kind strings in `execution_order` retain their own keys
and values. Rust and Swift native converters now reject ambiguous and
noncanonical spellings in the exercised inputs. Swift also uses the
structural field name for untagged canonical children.

| Checked on docker-vm | Result |
| --- | --- |
| Python wheel at `6d186ff` | Full suite passed 927 tests. Two optional SCION comparisons skipped. CLI validation and reverse conversion each refused both edited witnesses. Runtime reached `done` on the canonical witness. |
| JavaScript npm package at `fd009c5` | One canonical reverse conversion and nine rejection controls passed on the packed distribution. |
| Rust native converter at `54df565` | 27 tests passed. The CLI round-tripped the canonical event and refused eight edited inputs without creating output. |
| Swift native converter at `06df1b6` | The CLI round-tripped the canonical event and refused all eight edited inputs without creating output. A directly linked runner passed the checked-in XCTest. The VM image lacks SwiftPM's automatic-discovery library `libIndexStore.so`. |

The Swift direct-client comparison also identified two element tables
initialized only when the executable's main function ran. A trivial XCTest
passed in the same harness. The converter XCTest crashed on `23dcefd` and
passed on `06df1b6` with lazily initialized static tables. The complete
native comparison used the same compiler, locked ArgumentParser and test
source. The combined scjson implementation is `53f7a159fcf18b6daf9047ed97f2d91966c1f255`.
Qualification covers the four package readers in the table. The remaining
standalone language readers are unqualified for this erratum. The iState
generator matrix, editor storage routes, and Alex Z 403b evaluation have
separate evidence.

| Evidence | SHA-256 |
| --- | --- |
| Original installed v0.4.2 host reproduction | `7affbbe3af97cdb1f98e4d4bfb005e0f9f1a49a5b54380151af2a256be2e5d78` |
| Python wheel | `1041e450f54836886449b7c0351fa8864078005fa7b241444f440bcfa492cdcc` |
| npm tarball | `767e0264ad7c34707905614f5878c1ef44ccc5a0e3db566b730eb5225b949732` |
| Final installed-wheel suite and CLI control receipt | `ae0f475b7126b56d5135a0b03644e419eca6675f8840308c0b09dfd4fea1a394` |
| Swift direct-client and CLI successor receipt | `74062de8cfbbb7a01596c68d052c36bd66f2a73201998ff09588e0d6e159ac30` |
| `scjson-executable-keys-review.zip` with code, packages, and all nine VM attempts (73 entries) | `3c4777e9a29b7adcf7393b62e78baee007cd0307789e0dbf08191561f89eb8d4` |

---

## ERRATA-014 — Offline vector generation consumes host time between chart steps

**Symptom.** In the held-region variant of Alex Z 417, two package builds on
docker-vm emitted different time advances for the same one-second send.
One advanced 999 milliseconds and the other advanced 1000 milliseconds.

**Root cause.** At `845f6c0`, `py/vector_gen.py:38` and `:163` load ordinary
wall-clock contexts. Startup and each replay can consume part of the chart
delay before `:255` computes the time remaining. Coverage replay at `:288`
also dispatches a time-control record as an external event named `None`.

**Correction and verification.** Each root chart opened for offline vector
generation MUST begin at logical time zero before entry actions. Only explicit
advances move its clock. Search deadlines and elapsed search time continue to
use the host clock under EXEC-E-D1. Coverage replay MUST apply time controls
without dispatching an external event, following EXEC-INV-2. The regression
cases in `py/tests/test_vector_gen.py` exercise SCXML and SCJSON with a
controlled host clock, a timer scheduled at startup and a transition authored
for the event named `None`. This scope covers the generator's root context.
Nested invoked interpreters have their own clocks.

**Verified on docker-vm.** Source `6519862e9d42094946ee1bd3d8e38df7af2b73a5`
on v0.4.3 produced wheel SHA-256
`3e8430c0b7a462ef5c8da8ad154c6dd5c09c0ba25108b788a7bb30f1e52ba227`
in two clean builds. Six iState mixed Rust/TypeScript jobs replayed the
same 417 chart while the root engine's simulated host clock advanced by
0, 1, or 7 milliseconds on every read. The previous wheel emitted
`@advance 1000`, `@advance 999`, and `@advance 993`. The corrected
wheel emitted `@advance 1000` in every case. Both XML and saved SCJSON
passed the held-region comparison. All 18 vector-generator cases passed.
The full Python suite passed 933 tests, with two optional SCION cases
skipped because the runner was unavailable.

| Evidence | SHA-256 |
| --- | --- |
| Six mixed jobs and installed-wheel vector tests | `accad41dbdd1b3c12f46050c3afc96bffc390a0f4c8499120f49bf29296b39ad` |
| Held-first and held-second region replay | `08ef26c32ca1432f3ac8b87006abce61faf9048f288c85ed0eb374f3c7e68c35` |
| Full upstream JUnit report | `b2153079a5d6e99e0ba68652b494cf73ab1a6e73a4f5826e72666a6f11507b69` |
| `scjson-vector-clock-wheel-review.zip` with wheel, build receipts, and full suite | `40ed075d3c25cf2c2c9d6c89d53b16ea8796f03f8545823a4f3975584436289c` |

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
