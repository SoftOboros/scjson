<p align="center"><img src="../../scjson.png" alt="scjson logo" width="200"/></p>

Agent Name: scjson-semantic-baseline

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

# SCJSON-00 Concepts: Semantic Baseline and Drift Inventory

## Section 0. Authority Policy

This document establishes the first spec-before-code baseline for repository
semantics. It inventories semantic drift in the pre-baseline docs and assigns
ownership for core definitions, frozen enums, and public compatibility claims.

Normative sections: Section 3, Section 4, Section 5, Section 6, Section 7,
Section 8, Section 9, Section 10, and Section 12.

Informative sections: Section 1, Section 2, Section 11, Section 13,
Section 14, and Section 15.

Normative keywords **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, **MAY**,
and **RECOMMENDED** are interpreted per RFC 2119 and RFC 8174 when capitalized.

## Section 1. Purpose

The repository has accumulated several layers of documentation:

- Converter inference docs.
- Compatibility matrix.
- Python engine user and implementation docs.
- Ruby engine user and implementation docs.
- Engine TODO checklists.
- README summaries.

These docs contain useful content, but several now make overlapping or
conflicting semantic claims. This baseline captures the essential definitions
before any archive pass so old docs can later become historical references
rather than competing specifications.

## Section 2. Problem Statement and Drift Inventory

The current documentation drift is observable in these areas.

### Drift D1: SCJSON conversion ownership

`INFERENCE.md` describes the JavaScript converter as the source of inference
logic and says other languages should reproduce it
(`INFERENCE.md:5`). That conflicts with the compatibility matrix, which says
the Python CLI remains canonical and other agents compare against Python
(`docs/COMPATIBILITY.md:10-13`).

Decision: Python-generated schema plus canonical Python conversion behavior own
the SCJSON representation. JavaScript remains a parity implementation.

### Drift D2: Structural field list is stale

`INFERENCE.md` lists lifted structural fields ending at `cancel`
(`INFERENCE.md:22-39`). The JavaScript converter also lifts `param`, `if`,
`elseif`, `else`, `foreach`, `raise`, and `content`
(`js/src/converters.js:52-60`).

Decision: the frozen structural-field set is owned by the generated schema and
must be mirrored by converters. `INFERENCE.md` is historical until rewritten
against this document.

### Drift D3: Attribute treatment is underspecified

`INFERENCE.md` says all XML attributes are copied as string properties
(`INFERENCE.md:15-18`) and retained exactly as strings
(`INFERENCE.md:54-58`). The JavaScript converter maps reserved attribute names
to schema names (`datamodel_attribute`, `initial_attribute`, `type_value`,
`raise_value`) and splits selected token attributes
(`js/src/converters.js:122-130`, `js/src/converters.js:174-180`).

Decision: schema-compatible attribute mapping and tokenization are normative;
"retained exactly" is no longer a complete rule.

### Drift D4: Time-control step emission contradicts code

The Python guide says `advance_time` control tokens emit synthetic trace steps
by default (`docs/ENGINE-PY.md:109-128`). The Python CLI currently defaults
`--emit-time-steps` to false and documents that disabled default in the option
help (`py/scjson/cli.py:439-447`). The same guide later says mid-sequence
`advance_time` advances without emitting a trace step
(`docs/ENGINE-PY.md:164-170`).

Decision: code owns current behavior. By default, `advance_time` control tokens
MUST NOT add trace steps. Synthetic time steps are opt-in through
`--emit-time-steps`.

### Drift D5: Ruby time-control statement mirrors the corrected behavior but
names Python incorrectly

The Ruby guide says `advance_time` emits no trace step and "mirrors Python"
(`docs/ENGINE-RB.md:94-96`). That is compatible with code but incompatible with
the earlier Python guide default claim.

Decision: keep the Ruby behavior; update the Python guide during doc
convergence.

### Drift D6: Language compatibility status disagrees across docs

The compatibility matrix classifies Go and Swift as Beta and Lua as
Experimental (`docs/COMPATIBILITY.md:24-34`). The README classifies Go, Swift,
and Lua as Parity (`README.md:74-84`).

Decision: `docs/COMPATIBILITY.md` owns status tiers until a future release doc
supersedes it. README status rows are summaries and MUST cite, not override,
the matrix.

### Drift D7: Engine docs mix product behavior and harness normalization

Engine guides, compatibility docs, and TODOs all describe trace schema,
normalization flags, step-0 stripping, error ordering, and invoke ordering.
Examples include the trace field list in the Ruby guide
(`docs/ENGINE-RB.md:42`), Python normalization notes
(`docs/ENGINE-PY.md:198-208`), and the compatibility feature table
(`docs/COMPATIBILITY.md:64-82`).

Decision: this concepts doc owns the public trace-contract terms. User guides
MAY explain CLI usage but MUST NOT define different trace semantics.

### Drift D8: Frozen enums exist in code but not in docs

Generated schema enums exist for assign type, binding, boolean, exmode,
history type, and transition type (`py/scjson/pydantic/generated.py:10-71`).
Python engine runtime enums and string-enums exist for execution mode and
ordering mode (`py/scjson/context.py:72-76`,
`py/scjson/context.py:112-113`). Ruby carries the same ordering-mode surface
(`ruby/lib/scjson/engine/context.rb:288-290`).

Decision: Section 7 registers these as frozen decisions with explicit change
policies.

## Section 3. Canonical Glossary

### SCXML

As defined by the W3C SCXML XML vocabulary and represented in this repository
by generated Pydantic classes rooted at `Scxml`
(`py/scjson/pydantic/generated.py:1127-1165`); used without modification for
syntax ownership.

### SCJSON

Owned by this document and by `scjson.schema.json`. SCJSON is the canonical JSON
projection of the supported SCXML subset. It preserves SCXML hierarchy,
attributes, executable content ordering, and validation-relevant structure.

### Canonical SCJSON

Owned by the generated schema and Python conversion behavior. Canonical SCJSON
uses schema field names, list-valued structural fields, tokenized target and
initial attributes, preserved unknown extension surfaces, and deterministic
normalization. Converters in other languages conform by matching the Python
output under `py/uber_test.py`.

### Structural Field

As implemented in converter code and schema-derived array keys
(`js/src/converters.js:17-60`); adapted: the schema is canonical, and converter
constants are mirrors. A structural field is a child-element family lifted from
generic `content` into a named SCJSON property.

### Generic Content

Owned by generated schema and converter behavior. Generic `content` stores text
payloads and extension children that are not lifted into structural fields.
Unknown extension elements MUST remain representable instead of being silently
dropped.

### Trace Record

Owned by this document and implemented by engine trace emitters. A trace record
is one JSON object in a JSONL execution trace. Public fields are registered in
Section 7.

### Event Stream

Owned by engine CLI docs and this document. An event stream is JSONL input where
each event has `event` or `name`, optional `data`, or a control token such as
`advance_time` (`docs/ENGINE-PY.md:90-107`).

### Behavioral Reference

Owned by this document. SCION is the behavioral reference for execution traces
when the feature is within supported scope (`docs/COMPATIBILITY.md:49-54`).
Python is the converter reference.

### Normalization Profile

Owned by comparison tooling and this document. A normalization profile is a
declared transform over trace records used to compare engines without changing
the engine behavior itself.

## Section 4. Source-of-Truth Map

| Concept | Owner | Relationship |
|---------|-------|--------------|
| SCJSON schema fields | `scjson.schema.json`; generated Pydantic classes | Canonical validation surface. |
| Python converter output | Python CLI and `py/uber_test.py` fixtures | Canonical converter behavior. |
| JavaScript converter constants | `js/src/converters.js` | Mirror of schema/Python behavior. |
| Execution behavior | SCION for reference semantics; Python engine for in-repo implementation | SCION is external reference; Python documents supported subset. |
| Ruby execution behavior | `ruby/lib/scjson/engine/context.rb` plus Ruby TODO | Parity target, not canonical unless explicitly named. |
| Trace schema | This document; engine emitters | Frozen public contract. |
| Compatibility status | `docs/COMPATIBILITY.md` until superseded | README is informative. |
| TODO status | `docs/TODO-ENGINE-PY.md`, `docs/TODO-ENGINE-RUBY.md` | Living checklists, not full specs. |

## Section 5. Core Invariants

The following invariants are frozen under Standards Action.

- INV-1: SCJSON MUST preserve SCXML hierarchy and execution-relevant ordering.
- INV-2: SCXML to SCJSON to SCXML MUST preserve semantics for supported SCXML.
- INV-3: Schema-generated field names MUST be used for reserved XML names that
  conflict with language keywords or schema naming (`type_value`,
  `raise_value`, `datamodel_attribute`, `initial_attribute`).
- INV-4: Structural child families MUST be list-valued in canonical SCJSON,
  even when there is only one child.
- INV-5: Unknown supported-extension surfaces MUST remain representable through
  generic content, other-element, or other-attributes fields.
- INV-6: Converter parity is measured against Python canonical output unless a
  compatibility document explicitly registers an exception.
- INV-7: Execution parity is measured against SCION-compatible traces inside
  the supported execution scope.
- INV-8: Harness normalization MUST be explicit and MUST NOT be described as
  native engine behavior.

## Section 6. Canonical Conversion Decisions

- The root SCXML element maps to an SCJSON object with `tag: "scxml"`.
- Element attributes map to schema-compatible object properties. Reserved names
  MUST follow generated schema aliases.
- Token attributes such as `target` and `initial` MUST become arrays where the
  schema marks them as token lists.
- Structural children MUST be lifted into named array fields.
- Non-structural children and mixed text payloads MUST remain in generic
  content surfaces.
- Authoring metadata and SCXML comment promotion are delegated to
  `SCJSON-CONV-00-CONCEPTS.md`. The planned `help_text` field and promoted
  comments MUST remain non-executable metadata.
- Top-level transitions under `<scxml>` are currently stripped for Python
  parity (`js/src/converters.js:107-120`). This decision is frozen as
  Specification Required until the Python converter behavior is audited against
  the W3C interpretation.
- Whitespace normalization MUST be field-specific. The broad statement
  "whitespace has no structural effect" is informative only.

## Section 7. Frozen Enumerations and Public Value Sets

### Schema enums: Standards Action

These are owned by generated schema and Pydantic output
(`py/scjson/pydantic/generated.py:10-71`):

- `AssignTypeDatatype`: `replacechildren`, `firstchild`, `lastchild`,
  `previoussibling`, `nextsibling`, `replace`, `delete`, `addattribute`.
- `BindingDatatype`: `early`, `late`.
- `BooleanDatatype`: `true`, `false`.
- `ExmodeDatatype`: `lax`, `strict`.
- `HistoryTypeDatatype`: `shallow`, `deep`.
- `TransitionTypeDatatype`: `internal`, `external`.

Changing these requires a schema/model change, generated artifact refresh, and
compatibility note.

### Engine execution modes: Standards Action

Owned by Python runtime (`py/scjson/context.py:72-76`):

- `strict`
- `lax`

### Invoke ordering modes: Standards Action

Owned by Python and Ruby runtime surfaces (`py/scjson/context.py:112-113`,
`ruby/lib/scjson/engine/context.rb:288-290`):

- `tolerant`
- `strict`
- `scion`

### Trace fields: Standards Action

Public trace records MUST keep these fields unless a future concepts amendment
changes the trace version:

- `step`
- `event`
- `firedTransitions`
- `enteredStates`
- `exitedStates`
- `configuration`
- `actionLog`
- `datamodelDelta`

### Normalization flags/profile values: Specification Required

The public comparison surface includes:

- `--leaf-only`
- `--full-states`
- `--omit-actions`
- `--omit-delta`
- `--omit-transitions`
- `--strip-step0-noise`
- `--strip-step0-states`
- `--keep-cond`
- `--norm scion`

### Error and done event name families: Standards Action

The public engine event families are:

- `error`
- `error.execution`
- `error.communication`
- `done.state.<id>`
- `done.invoke`
- `done.invoke.<id>`

`error.execution` MAY enqueue a generic `error` alias for compatibility; this is
current Python behavior (`py/scjson/context.py:1503-1540`).

### Compatibility status tiers: Specification Required

Owned by `docs/COMPATIBILITY.md:15-22`:

- `Canonical`
- `Parity`
- `Beta`
- `Experimental`

## Section 8. Trace and Event Semantics

- A trace is newline-delimited JSON. Each line is one trace record.
- Step 0 is initialization. Compare tooling MAY strip step-0 noise, but that is
  a normalization rule, not a change to engine execution.
- `advance_time` in an event stream advances deterministic mock time. It MUST
  NOT emit a trace step by default. Emitting a synthetic time step is opt-in via
  `--emit-time-steps` (`py/scjson/cli.py:439-447`, `py/scjson/cli.py:561-570`).
- Event matching supports exact event names, space-separated event lists,
  wildcard `*`, and prefix patterns such as `error.*`
  (`py/ENGINE-PY-DETAILS.md:72-73`).
- External send targets outside the supported parent/child/internal surfaces are
  out of scope and produce `error.communication`.

## Section 9. Behavioral Reference and Compatibility Invariants

- Converter compatibility is Python-output compatibility.
- Engine compatibility is SCION-trace compatibility.
- Expected implementation deltas MUST be listed in compatibility docs before
  tests are relaxed for them.
- Known-diff files and skip lists are temporary triage tools. They MUST NOT
  become hidden specifications.
- Ruby may use Python conversion fallback for SCXML-to-SCJSON ingestion, but
  Ruby execution remains a separate engine behavior surface
  (`docs/ENGINE-RB.md:98-106`).

## Section 10. Reconciliation Decisions

R-1: `docs/COMPATIBILITY.md` remains the active compatibility summary but must
be revised to cite this document for definitions.

R-2: `INFERENCE.md` should be rewritten or archived after its useful examples
are migrated into a converter concepts doc. Its current structural field list
and attribute claims are not authoritative.

R-3: `docs/ENGINE-PY.md` must be corrected so the time-control section agrees
with CLI defaults.

R-4: `docs/ENGINE-RB.md` can keep the no-step `advance_time` behavior, but its
"mirrors Python" phrasing should cite the corrected Python behavior after R-3.

R-5: README language-status rows should be regenerated from or reduced to a
pointer to `docs/COMPATIBILITY.md`.

R-6: Engine TODO files remain living checklists. They should not carry unique
definitions that are absent from this concepts doc or a successor phase doc.

R-7: Localized documentation trees are removed from this repository. Translated
publication is owned by softoboros.com through submodule inclusion, so localized
planning copies MUST NOT be regenerated here.

R-8: Converter and execution backlog is split into child concepts docs:
`SCJSON-CONV-00-CONCEPTS.md`, `SCJSON-EXEC-00-CONCEPTS.md`, and
`SCJSON-WORKSTREAMS-00-MANAGER-MAP.md`.

R-9: First-class chart documentation, SCXML comment promotion, and common
`other_attributes` registry work belong to `SCJSON-CONV-00-CONCEPTS.md`
CONV-E/F/G. The registry work should publish optional/suggested schemas outside
the core SCJSON schema so products can validate known extension metadata while
unknown extension keys still round-trip. The planning registry starts in
`SCJSON-OTHER-ATTRIBUTES-00-CONCEPTS.md`. Runtime engines MUST continue to
ignore those fields for execution semantics unless a future execution concepts
doc explicitly promotes a field.

R-10: Root-reachable chart inclusion and communication coverage belongs to
`SCJSON-CONV-00-CONCEPTS.md` CONV-H. The converter/schema contract MUST expose
`send`, `invoke`, nested `Scxml` payloads, `content`, `param`, `donedata`, and
external reference fields through the root schema/type graph without admitting
invalid direct root executable children.

## Section 11. Non-Goals

- This baseline does not prove that every implementation currently conforms.
- This baseline does not move or delete old docs.
- This baseline does not alter schema or runtime behavior.
- This baseline does not redefine unsupported external SCXML I/O processors.

## Section 12. Acceptance Checklist

- [x] Inventory existing drift across inference, compatibility, Python engine,
  Ruby engine, README, and runtime code.
- [x] Establish source-of-truth ownership for core conversion and execution
  definitions.
- [x] Register frozen schema enums, runtime modes, trace fields, event families,
  and compatibility tiers.
- [x] Record reconciliation decisions required before old docs can be archived.
- [x] Update old docs to cite this concepts doc and remove conflicting claims.
- [ ] Add archive index and move superseded docs only after their essential
  content has been captured in current concepts/user-guide docs.

## Section 13. Files Cited

- `AGENTS.md`
- `CLAUDE.md`
- `INFERENCE.md`
- `README.md`
- `docs/COMPATIBILITY.md`
- `docs/ENGINE-PY.md`
- `docs/ENGINE-RB.md`
- `docs/TODO-ENGINE-PY.md`
- `docs/TODO-ENGINE-RUBY.md`
- `docs/concepts/SCJSON-CONV-00-CONCEPTS.md`
- `docs/concepts/SCJSON-EXEC-00-CONCEPTS.md`
- `docs/concepts/SCJSON-OTHER-ATTRIBUTES-00-CONCEPTS.md`
- `docs/concepts/SCJSON-WORKSTREAMS-00-MANAGER-MAP.md`
- `js/src/converters.js`
- `py/ENGINE-PY-DETAILS.md`
- `py/scjson/cli.py`
- `py/scjson/context.py`
- `py/scjson/pydantic/generated.py`
- `ruby/lib/scjson/engine/context.rb`

## Section 14. Archive Plan

Do not archive docs solely because this baseline exists. Archive only after:

1. The doc's normative claims are either copied here, copied into a successor
   concepts doc, or intentionally rejected in Section 10.
2. User-facing usage material remains available in an active guide.
3. README and internal links point at active docs.
4. The archived file receives a short header naming its replacement.

Initial archive candidates after reconciliation:

- `INFERENCE.md`: replace with a converter concepts doc plus examples.
- Duplicated engine implementation notes in `py/scjson/ENGINE.md` and
  `py/ENGINE-PY-DETAILS.md`: consolidate into one active implementation
  reference.
- Ruby user-guide maturity notes that duplicate TODO status: keep current usage,
  move historical status into archive.

## Section 15. Change Log

- 2026-05-14: Initial baseline drafted from existing docs and runtime surfaces.
- 2026-05-14: Added child concept-doc split and localized-doc removal policy.
- 2026-05-24: Pointed authoring metadata and SCXML comment-promotion work at
  `SCJSON-CONV-00-CONCEPTS.md` CONV-E/F/G.
- 2026-05-24: Clarified that documented `other_attributes` conventions should
  become optional/suggested schemas outside the core SCJSON schema and linked
  the planning registry stub.
- 2026-05-26: Added R-10 to delegate root-reachable chart inclusion and
  communication coverage to `SCJSON-CONV-00-CONCEPTS.md` CONV-H.
