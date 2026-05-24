<p align="center"><img src="../../scjson.png" alt="scjson logo" width="200"/></p>

Agent Name: scjson-other-attributes-concepts

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

# SCJSON-OTHER-ATTRIBUTES-00 Concepts: Extension Metadata Registry

## Section 0. Authority Policy

This document is the planning registry for documented `other_attributes`
conventions. It is subordinate to `SCJSON-00-CONCEPTS.md` and
`SCJSON-CONV-00-CONCEPTS.md` CONV-G.

Normative sections: Section 2, Section 3, Section 4, Section 5, and
Section 6.

Informative sections: Section 1, Section 7, Section 8, Section 9,
Section 10, Section 11, Section 12, Section 13, Section 14, and Section 15.

Normative keywords **MUST**, **MUST NOT**, **SHOULD**, **MAY**, and
**RECOMMENDED** are interpreted per RFC 2119 and RFC 8174 when capitalized.

## Section 1. Purpose

SCJSON has a core JSON Schema for the canonical SCXML projection. That schema
must preserve unknown extension metadata, but products still need discoverable
schemas for common editor, visualization, authoring, and assistant metadata.

This registry defines the shape of that optional schema catalog. It records
which `other_attributes` keys are known, which SCJSON object families they
apply to, whether a JSON Schema exists, and how products should handle casing
and migration.

## Section 2. Core Schema Boundary

The core `scjson.schema.json` validates canonical SCJSON structure. It MUST NOT
close the `other_attributes` map around the optional registry entries in this
document. Unknown extension metadata remains part of the round-trip surface.

Optional registry schemas MAY be used by products, editors, visualizers,
assistants, or publication pipelines that recognize a convention. Strict
registry validation is opt-in product policy, not core SCJSON validation.

## Section 3. Canonical Definitions

### Extension Metadata

Extension metadata is data stored under `other_attributes` for authoring,
editor, visualization, assistant, compatibility, or tool-specific purposes. It
does not change execution semantics.

### Optional Registry Schema

An optional registry schema is a JSON Schema that validates a known
`other_attributes` key or family of keys. It is a suggested contract for tools
that opt into the convention.

### Strict Registry Validation

Strict registry validation is product-local validation that rejects values that
claim to follow a known registry entry but do not match that entry's schema. It
MUST NOT be applied as a default replacement for core SCJSON validation.

### Product Wire Casing

Product wire APIs MAY expose casing that differs from canonical SCJSON
interchange names. Casing aliases must be documented by the product and by the
registry entry when the alias is expected to interoperate.

## Section 4. Scope

In scope:

- Suggested schemas for common `other_attributes` entries.
- Applies-to object families for each entry.
- Interchange snake_case names and product-specific aliases.
- Compatibility and migration notes.

Out of scope:

- Closing the core `other_attributes` map.
- Runtime execution behavior.
- First-class SCJSON fields such as `help_text`, which are owned by
  `SCJSON-CONV-00-CONCEPTS.md` CONV-E.

## Section 5. Non-Executable Invariants

- OA-INV-1: The core SCJSON schema MUST continue to permit unknown
  `other_attributes` keys for round-trip preservation.
- OA-INV-2: Optional registry schemas MUST NOT make unrecognized extension keys
  invalid unless a product explicitly opts into strict validation for a known
  registry profile.
- OA-INV-3: Registry entries MUST NOT affect SCXML validation, state-machine
  execution, transition selection, datamodel evaluation, or trace output.
- OA-INV-4: Registry entries SHOULD declare applies-to object families before
  code generators or editors rely on them.
- OA-INV-5: Canonical SCJSON interchange keys SHOULD use snake_case. Product
  APIs MAY expose aliases such as camelCase when documented.

## Section 6. Registry Entry Shape

Each optional schema entry SHOULD record:

| Field | Meaning |
| --- | --- |
| Key | Canonical `other_attributes` key used in SCJSON interchange. |
| Aliases | Product-specific spellings, including camelCase frontend names. |
| Applies to | SCJSON object families where the key is meaningful. |
| Value shape | Summary of the expected JSON value. |
| Schema | JSON Schema URI, file path, or planned schema placeholder. |
| Status | Proposed, ratified downstream, ratified scjson, deprecated, or legacy readable. |
| Semantics | Editor metadata, visualization metadata, assistant metadata, or compatibility metadata. |
| Migration | Compatibility, fallback, and writer behavior. |

## Section 7. Infinity State Seed Registry

The initial seed comes from the ratified SoftOboros Infinity State convention
document `docs/SCJSON-OTHER-ATTRIBUTES.md` in the downstream Infinity Stack
repository. These entries are not yet ratified as scjson core behavior.

| Key | Aliases | Applies to | Value shape | Schema | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `document_display` | `documentDisplay` | `scxml` root | object | downstream `schemas/istate/v1/document-display.schema.json` | ratified downstream | Document display metadata including sheet settings and canonical `snapToGrid`. |
| `title_style` | `titleStyle` | `scxml` root | object | downstream `schemas/istate/v1/title-style.schema.json` | ratified downstream | Editable document-title presentation metadata. |
| `snap_to_grid` | `snapToGrid` | legacy `scxml` root; canonical under `document_display` | number or null | covered by document-display schema | legacy readable | Readers normalize legacy root placement to `document_display.snap_to_grid`; writers should emit only the canonical nested form. |
| `description` | none | any SCJSON element | string | planned compatibility note | legacy readable | Compatibility source for products that stored documentation before `help_text`. New durable chart docs should use `help_text`. |
| `position` | none | `state`, `parallel`, `final`, `history`, and visual initial nodes where a product renders them | object `{x, y}`; legacy string `"x,y"` readable | `docs/schemas/other_attributes/infinity-state/v1/node-position.schema.json` | ratified downstream | Node placement metadata. |
| `style` | none | state-like objects and `transition` | object | downstream state/transition style override schemas | ratified downstream | Per-object visual style override. |
| `schema` | none | `data` | object | downstream `schemas/istate/v1/data-schema.schema.json` | ratified downstream | Authoring-time schema/type metadata for datamodel variables. |
| `arc` | none | `transition` | number | `docs/schemas/other_attributes/infinity-state/v1/transition-geometry.schema.json` | ratified downstream | Transition curvature hint. |
| `skew` | none | `transition` | number | `docs/schemas/other_attributes/infinity-state/v1/transition-geometry.schema.json` | ratified downstream | Transition arc-center offset. |
| `base_pos` | none | `transition` | object `{x, y}`; legacy string `"x,y"` readable | `docs/schemas/other_attributes/infinity-state/v1/transition-geometry.schema.json` | ratified downstream | Source endpoint anchor hint. |
| `arrow_pos` | none | `transition` | object `{x, y}`; legacy string `"x,y"` readable | `docs/schemas/other_attributes/infinity-state/v1/transition-geometry.schema.json` | ratified downstream | Target endpoint anchor hint. |
| `help_text_box` | `helpTextBox` | rendered objects with effective `help_text` | object | `docs/schemas/other_attributes/infinity-state/v1/annotation-box.schema.json` | proposed | Per-object help-text annotation visibility, geometry, shape, and spacing. |
| `condition_text_box` | `conditionTextBox` | `transition` condition labels and rendered condition blocks | object | `docs/schemas/other_attributes/infinity-state/v1/annotation-box.schema.json` | proposed | Condition annotation geometry mirroring `help_text_box`. |

## Section 8. Optional Schema Catalog

The catalog SHOULD live outside `scjson.schema.json`. Infinity State-derived
optional schemas are published under a dedicated tree:

```text
docs/schemas/other_attributes/infinity-state/v1/
```

The core schema may reference this registry in documentation, but it should not
use these optional schemas to reject unknown keys. Product validation can opt
into one or more registry schemas at import, export, publish, or editor-save
boundaries.

The initial draft files in this tree are:

| File | Purpose |
| --- | --- |
| `annotation-box.schema.json` | Shared value shape for `help_text_box` and `condition_text_box`. |
| `node-position.schema.json` | Value shape for `position` on state-like visual nodes, preferring `{x, y}` while accepting legacy `"x,y"`. |
| `transition-geometry.schema.json` | Geometry-key family for transition `other_attributes.arc`, `skew`, `base_pos`, and `arrow_pos`. |

## Section 9. Legacy Migration Notes

`description` is legacy documentation metadata. Products that already use it
SHOULD continue reading it, but generated documentation comments and new chart
documentation SHOULD prefer first-class `help_text` after CONV-E lands.

Product APIs that expose camelCase aliases MUST document their mapping to
canonical SCJSON keys. Interchange examples SHOULD use snake_case unless the
example explicitly targets a product-local API.

## Section 10. Inventory Backlog

The initial downstream scan found additional open-extension keys and surfaces
that need reconciliation before a full optional schema catalog is considered
complete. These are inventory candidates, not automatically ratified scjson
registry entries.

### Infinity State active extras

| Candidate | Applies to | Current role | Reconciliation question |
| --- | --- | --- | --- |
| `codegen.targetLangs` | `scxml` root | Editor/codegen target selection. | Should this become a documented codegen/editor namespace or stay product-local? |
| `defaultBubbleSize` | `scxml` root | Canvas layout default. | Should it move under document display or a node-layout schema? |
| `POSITION_X`, `POSITION_Y`, `positionX`, `positionY`, `posX`, `posY`, `x`, `y` | state-like visual nodes | Legacy coordinate spellings. | Which forms remain legacy-readable, and which canonical form should writers emit? |
| `BOX_SIZE`, `MARGIN` | state-like visual nodes | Legacy node size and spacing hints. | Should node geometry be separate from visual style? |
| `id` | `transition` | Rendered transition identifier. | Is transition identity a registry convention or a product DOM/rendering detail? |
| `style.parallelShadow` | parallel states | Canvas spelling for parallel-state shadow override. | Reconcile with the downstream schema spelling `style.shadow`. |

### Datamodel schema authority split

`data.other_attributes.schema` may contain both behavior-authority fields and
editor-only hints. Registry schemas should preserve that distinction.

- Behavior-authority candidates: `type`, `constraints`, and `default`.
- Editor-only candidates: `label`, `placeholder`, `help`, `hidden`,
  `readonly`, `order`, `group`, `widget`, and `description`.

### Other open-extension users

Downstream schematic, Streamz, and PCB schemas also use open `otherAttributes`
maps. Their conventions should be inventoried separately and only moved into
this registry when they are intended to interoperate with SCJSON tooling.

## Section 11. Consumer Guidance

Runtime engines MUST ignore registry metadata. Visualizers and editors MAY use
layout and annotation entries to seed rendering. Code generators SHOULD only
consume entries that are explicitly classified as codegen-facing metadata, such
as `help_text`; visual geometry entries should remain outside runtime codegen
unless a target is itself visual or documentary.

## Section 12. Non-Goals

- No core-schema closure around extension keys.
- No converter implementation change in this registry doc.
- No guarantee that downstream schemas are copied into this repo before a
  packaging/versioning decision lands.
- No runtime execution semantics.

## Section 13. Acceptance Checklist

- [x] Full key inventory is collected from downstream users and existing
  schemas. (Ratified 2026-05-24: §7 seed registry plus §10 inventory backlog
  covers the Infinity State active extras, the datamodel schema
  authority split, and sibling open-extension surfaces. Subsequent inventory
  additions are §15 amendments.)
- [x] Optional Infinity State draft schema package location is chosen:
  `docs/schemas/other_attributes/infinity-state/v1/`.
- [ ] Existing downstream schemas are either imported, copied, or referenced
  with stable URIs. (Open: iState side adoption is owned by parent ISTATE08a1
  and decides whether to copy-locally or `$ref`-to-upstream once a stable URI
  policy is published.)
- [x] Planned annotation geometry schemas define `help_text_box` and
  `condition_text_box` through
  `docs/schemas/other_attributes/infinity-state/v1/annotation-box.schema.json`.
- [x] Core `scjson.schema.json` remains open to unknown `other_attributes`.
  (Ratified 2026-05-24: every applies-to model retains
  `other_attributes: { additionalProperties: { type: "string" } }`; no
  closure introduced.)

## Section 14. Files Cited

- `docs/concepts/SCJSON-00-CONCEPTS.md`
- `docs/concepts/SCJSON-CONV-00-CONCEPTS.md`
- `docs/schemas/other_attributes/README.md`
- Downstream input: SoftOboros Infinity Stack
  `docs/SCJSON-OTHER-ATTRIBUTES.md`
- Downstream input: SoftOboros Infinity Stack `schemas/istate/v1/`

## Section 15. Change Log

- 2026-05-24: Initial optional registry stub seeded from the ratified Infinity
  State `otherAttributes` convention document.
- 2026-05-24: Added inventory backlog for active downstream extension keys,
  datamodel schema authority split, and non-SCJSON open-extension users.
- 2026-05-24: Added concrete Infinity State draft schema catalog path and
  draft schemas for annotation boxes, node position, and transition geometry.
- 2026-05-24: Ratified (CONV-G). Three of five §13 boxes flipped to closed:
  full key inventory (§7 + §10), core `scjson.schema.json` openness verified,
  and the prior two location/annotation-geometry boxes that were already
  closed. Section §2 boundary, §3 definitions, §5 invariants (OA-INV-1..5),
  §6 entry shape, §7 seed registry, and §10 inventory backlog are now
  normative. The remaining open box ("downstream schemas imported, copied, or
  referenced with stable URIs") moves to parent ISTATE08a1 ownership.
