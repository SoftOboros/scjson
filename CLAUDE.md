<p align="center"><img src="scjson.png" alt="scjson logo" width="200"/></p>

# scjson Agent Instructions

This file is the repository-level contract for automated contributors. Keep
`AGENTS.md` and `CLAUDE.md` aligned when changing these instructions.

## Repository Purpose

`scjson` defines a JSON representation of SCXML state machines and keeps
language implementations, validators, converters, and execution traces aligned
around that representation.

## Pertinent Invariants

- Preserve SCXML hierarchy and execution semantics when converting between
  SCXML and SCJSON.
- Preserve round-trip fidelity: `SCXML -> SCJSON -> SCXML` must not introduce
  semantic drift.
- Treat `scjson.schema.json` as the canonical SCJSON validation artifact. When
  model definitions change, regenerate the schema and update affected language
  packages.
- Keep cross-language converters in parity with the canonical Python behavior
  unless a documented compatibility decision says otherwise.
- Treat SCION-compatible traces as the behavioral reference for execution
  engines. Any normalization or intentional delta must be documented in the
  relevant engine guide and checklist.
- Keep `docs/TODO-*.md` files as living checklists. Checked items reflect
  landed behavior; unchecked items remain pending. Update the relevant
  checklist in the same change as code that changes its status.
- Write agent-generated docs, comments, commit messages, and source text in
  American English (`en-US`). Do not maintain localized documentation trees in
  this repository; translated publication is handled by softoboros.com when it
  includes this repo as a submodule.

## Environment Discipline

- Python dependencies are preconfigured. Do not run `pip` or `poetry`.
- The JavaScript package entry point is `js/dist/index.js`; run
  `npm run build` in `js/` before invoking the package through Node or before
  running tests such as `py/uber_test.py` after JavaScript changes.
- Prefer the existing repo harnesses before adding new tooling:
  `PYTHONPATH=py pytest -q py/tests`, `python py/uber_test.py`, and
  `python py/exec_compare.py ...`.

## Documentation and Attribution

Source files authored or substantially rewritten by agents must include:

- A module-level docstring or file header explaining the file purpose.
- Docstrings for public classes and functions, including Doxygen-style params
  and returns where the language convention supports it.
- File-level attribution in this form for Python files:

```python
"""
Agent Name: <descriptive identifier>

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.
"""
```

## Spec-Before-Code Planning Discipline

Multi-phase scjson initiatives, including engine parity work in
`docs/TODO-ENGINE-PY.md` and `docs/TODO-ENGINE-RUBY.md`, follow a
spec-before-code cycle once they define cross-language behavior, trace schema,
semantic compatibility, or a phase plan with three or more steps. The goal is
to prevent vocabulary drift and invariant erosion across language
implementations.

Current semantic baseline: `docs/concepts/SCJSON-00-CONCEPTS.md`.

### Normative Keywords

The key words **MUST**, **MUST NOT**, **SHALL**, **SHOULD**, **SHOULD NOT**,
**MAY**, and **RECOMMENDED** in planning docs are interpreted per RFC 2119 and
RFC 8174 when capitalized. Lowercase words retain their ordinary English
meaning.

### Normative vs. Informative Sections

- Checklist acceptance criteria, reference semantics, trace schemas, and
  explicitly named invariants are normative.
- Problem statements, narrative context, status snapshots, risks, and change
  logs are informative unless an acceptance item cites them.
- README summaries are informative. They should cite the authoritative planning
  or engine doc instead of restating normative behavior.

### Definitions and Source of Truth

When a planning doc defines a term that already exists in code or schema, cite
the authoritative source and label the relationship:

- "As defined in `<path>:<line>`; used without modification."
- "As defined in `<path>:<line>`; adapted: `<delta>`."
- "Owned by `<doc or phase>`; does not exist in repo yet."

Silent restatement of converter, schema, or engine terms is prohibited because
it creates competing definitions.

### Frozen Decisions

Frozen enums, trace fields, schema field semantics, error-event names, ordering
policies, and compatibility classifications must declare a registration policy:

- **Standards Action**: changing the value requires a planning-doc amendment
  before implementation. Use for cross-language contracts.
- **Specification Required**: changing the value requires an update to the
  relevant engine, converter, or schema doc in the same change.
- **Expert Review**: local internal values may change with a clear PR or commit
  note when they do not affect cross-language behavior.

Default to Standards Action when a decision affects multiple languages,
generated schema, or public trace output.

### Execution Discipline

- Implement behavior only after the relevant checklist, engine doc, or concepts
  section names the expected semantics.
- Any change to a frozen decision or invariant requires the documentation update
  first, then the implementation.
- Code changes that land checklist work must update the matching checkbox in
  `docs/TODO-*.md`.
- Commit and PR descriptions for phase work should name the checklist item or
  planning section touched and state how affected invariants are preserved.

## Code Discipline

- Keep edits scoped to the language package, schema, docs, or harness touched by
  the task.
- Prefer structured XML, JSON, and schema tooling over ad hoc string
  manipulation.
- Keep generated files generated: change models/templates/scripts, then rerun
  the generator.
- Add or update focused tests when changing converter output, validation
  behavior, trace format, event ordering, or engine semantics.
- Do not change tutorial or external corpus content to make tests pass; add
  in-repo vectors or normalization rules instead.

## Agent Surfaces

- `scxml-to-scjson`: converts SCXML documents to SCJSON and validates against
  `scjson.schema.json`.
- `scjson-to-scxml`: converts SCJSON back to SCXML and validates against the
  W3C schema files under `xsd/`.
- `validate-scjson`: validates SCJSON documents against the generated schema.
- `validate-scxml`: validates SCXML documents against the W3C XSD set.
- `generate-jsonschema`: regenerates `scjson.schema.json` from the canonical
  model definitions.
- `roundtrip-test`: checks `SCXML -> SCJSON -> SCXML` fidelity.
- `schema-dump`: reports SCJSON structure and metadata for inspection.

## Worktree Hygiene Between Waves

Per parent `softoboros.com/CLAUDE.md` §(J): when fanning out parallel agents
on this submodule (engine-parity work splitting across `docs/TODO-ENGINE-PY.md`
/ `docs/TODO-ENGINE-RUBY.md` / `docs/TODO-ENGINE-RUST.md` lanes in their own
worktrees), clean leftover harness-allocated worktrees and their
`worktree-agent-*` branches between waves so the harness allocates fresh
against current HEAD:

```sh
# from the parent repo root (/Users/iraabbott/softoboros), BEFORE the next wave
for wt in $(git worktree list | awk '$3 ~ /^\[worktree-agent-/ {print $1}'); do
  git worktree remove --force "$wt"
done
git branch | awk '/worktree-agent-/ {print $1}' | xargs -r git branch -D
```

The harness can't allocate a stale-base worktree from one that doesn't exist.
This eliminates the `git checkout webslinger -- . && git reset webslinger`
recovery dance — error-prone because dropping the `-- .` silently switches the
worktree's branch onto `webslinger` and breaks isolation. Cost is a one-time
per-agent target-dir rebuild (~30–60s for Rust crate work, negligible for
Python / Ruby package work).
