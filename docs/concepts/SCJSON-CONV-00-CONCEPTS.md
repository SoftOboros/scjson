<p align="center"><img src="../../scjson.png" alt="scjson logo" width="200"/></p>

Agent Name: scjson-converter-concepts

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

# SCJSON-CONV-00 Concepts: Converter and Schema Semantics

## Section 0. Authority Policy

This document scopes the converter/schema initiative created by
`SCJSON-00-CONCEPTS.md`. It is the planning document for replacing the stale
inference guide with a current converter contract.

Normative sections: Section 3, Section 4, Section 5, Section 6, Section 7, and
Section 9.

Informative sections: Section 1, Section 2, Section 8, Section 10, and
Section 11.

Normative keywords **MUST**, **MUST NOT**, **SHOULD**, **MAY**, and
**RECOMMENDED** are interpreted per RFC 2119 and RFC 8174 when capitalized.

## Section 1. Purpose

The old `INFERENCE.md` captures useful examples but names the JavaScript
converter as the source of truth and lists a stale structural-field set. This
initiative creates a schema-first converter contract so every language can
implement the same SCXML to SCJSON projection without re-deriving rules from a
single implementation.

## Section 2. Current Drift

- `INFERENCE.md` says JavaScript owns inference behavior.
- `docs/COMPATIBILITY.md` says Python output is canonical for converters.
- `js/src/converters.js` includes structural tags absent from `INFERENCE.md`.
- `py/uber_test.py` has its own structural-field normalization set.
- Generated pydantic models now accept typed JSON metadata in
  `other_attributes`, while dataclass models intentionally remain string typed
  for XML serializer compatibility.

## Section 3. Canonical Definitions

### Converter Reference

Python converter output is canonical for language parity. Other converters
conform by matching Python output under the relevant harness and normalization
rules.

### Schema Reference

`scjson.schema.json` and generated pydantic models define the canonical SCJSON
field surface. Converter constants are mirrors and MUST NOT introduce fields
that are absent from the schema without a schema/model change.

### XML Element Name vs. SCJSON Field Name

Some XML element or attribute names map to different SCJSON property names to
avoid language/schema conflicts:

- XML `type` attribute maps to SCJSON `type_value`.
- XML `raise` element maps to SCJSON `raise_value`.
- XML `if` element maps to SCJSON `if_value`.
- XML `else` element maps to SCJSON `else_value`.
- XML `initial` attribute maps to SCJSON `initial_attribute`.
- XML `datamodel` attribute maps to SCJSON `datamodel_attribute`.

### Extension Metadata

Pydantic `other_attributes` fields MAY contain JSON-typed metadata. Dataclass
`other_attributes` fields remain string typed because xsdata XML serialization
requires XML attribute values.

## Section 4. Frozen Converter Invariants

- CONV-INV-1: SCJSON conversion MUST preserve SCXML hierarchy and executable
  ordering.
- CONV-INV-2: List-valued schema fields MUST remain arrays in canonical SCJSON,
  even for one child.
- CONV-INV-3: Token attributes such as transition `target` and state/root
  `initial` MUST be split into arrays where the schema marks token lists.
- CONV-INV-4: Unknown extension content MUST remain representable through
  `content`, `other_element`, or `other_attributes` surfaces.
- CONV-INV-5: Converter parity changes MUST update Python output, generated
  schema artifacts, and parity harness expectations in one change.
- CONV-INV-6: Localized docs MUST NOT be generated or maintained in this repo;
  softoboros.com owns translated publication.

## Section 5. Structural Field Registry

The authoritative registry is the generated schema. The current implementation
surface to audit and align is:

| Family | SCJSON field(s) | Notes |
|--------|------------------|-------|
| state hierarchy | `state`, `parallel`, `final`, `history`, `initial`, `transition` | `transition` is list-valued for states/parallel and scalar under `initial`/`history` in generated models. |
| executable containers | `onentry`, `onexit`, `finalize`, transition actions | Preserve authoring order. |
| executable actions | `assign`, `log`, `raise_value`, `if_value`, `foreach`, `send`, `cancel`, `script` | XML names may differ from SCJSON field names. |
| payloads | `content`, `param`, `donedata`, `datamodel`, `data` | Mixed content and typed JSON payload behavior needs explicit tests. |
| invokes | `invoke`, `finalize`, `content`, `param` | Invoke semantics are owned by execution docs, but representation is owned here. |
| extensions | `other_element`, `other_attributes` | Preserve unknowns within schema-supported surfaces. |

Changes to this registry require Standards Action because they affect every
language converter and generated type surface.

## Section 6. Work Packages

### CONV-A: Schema Field Registry Audit

Goal: mechanically compare generated pydantic fields, JavaScript converter
constants, and `py/uber_test.py` normalization constants.

Output:

- A generated or hand-maintained table of schema list fields.
- A decision list for mismatches such as `transition`, `if_value`, `else_value`,
  `raise_value`, `content`, and `other_element`.

Dependencies: `SCJSON-00-CONCEPTS.md`.

Independent from: execution semantics, Ruby engine behavior.

### CONV-B: Typed Extension Metadata Tests

Goal: prove the 0.3.7 pydantic `other_attributes: dict[str, Any]` behavior and
the dataclass `dict[str, str]` split.

Output:

- Focused Python tests for pydantic and pydantic_strict typed metadata.
- Release-note text for the pydantic/dataclass split.

Dependencies: none beyond the current branch.

Independent from: converter registry audit.

### CONV-C: Inference Guide Replacement

Goal: replace or archive `INFERENCE.md` after its examples are moved into a
current converter guide.

Output:

- New active converter guide citing this concepts doc.
- Archive header or removal plan for the old guide.

Dependencies: CONV-A.

Independent from: Python release hardening after CONV-B is done.

### CONV-D: Generator Tool Packaging Decision

Goal: decide whether generation scripts are package artifacts or repository-only
maintenance tools.

Output:

- `MANIFEST.in` and package metadata changes if scripts ship.
- Otherwise, a documented repository-only generator workflow.

Dependencies: CONV-B for release-note wording.

Independent from: execution semantics.

## Section 7. Acceptance Checklist

- [ ] CONV-A schema field registry audit lands.
- [x] CONV-B typed extension metadata tests land.
- [x] CONV-C active converter guide replaces stale inference claims.
- [x] CONV-D generator packaging decision lands. The generator patch scripts are
  documented as repository maintenance tools, not installed runtime package
  entry points.
- [x] `INFERENCE.md` no longer competes with schema/Python converter authority.

## Section 8. Manager Notes

Safe parallelism:

- CONV-A and CONV-B can run independently.
- CONV-C should wait for CONV-A.
- CONV-D can run with CONV-B but should not rewrite generated models.

Recommended worker boundaries:

- Worker 1: schema/constant audit only.
- Worker 2: tests for typed `other_attributes` only.
- Worker 3: docs replacement only after Worker 1 reports decisions.

## Section 9. Rejections

The Apache Commons comparison wrapper is not part of this converter initiative.
It remains rejected for Python 0.3.7 and is not a dependency.

## Section 10. Files Cited

- `INFERENCE.md`
- `docs/COMPATIBILITY.md`
- `docs/concepts/SCJSON-00-CONCEPTS.md`
- `js/src/converters.js`
- `py/uber_test.py`
- `py/scjson/pydantic/generated.py`
- `py/scjson/pydantic_strict/generated.py`

## Section 11. Change Log

- 2026-05-14: Initial converter concepts document.
