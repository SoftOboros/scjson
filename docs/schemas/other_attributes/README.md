# Optional other_attributes Schema Catalog

## Status

Planning stub for `SCJSON-CONV-00-CONCEPTS.md` CONV-G and
`SCJSON-OTHER-ATTRIBUTES-00-CONCEPTS.md`.

This catalog is intentionally separate from `scjson.schema.json`. The core
schema owns canonical SCJSON structure and must continue to preserve unknown
`other_attributes` keys. The schemas listed here are optional validation aids
for products that recognize a documented convention.

## Core Schema Boundary

- Core SCJSON validation checks the chart representation.
- Optional registry validation checks known extension metadata.
- Products may opt into one or more registry schemas at import, export,
  publish, or editor-save boundaries.
- Unknown extension metadata remains valid core SCJSON and must round-trip.

## Catalog Entries

Initial entries are seeded from the ratified downstream Infinity State
`otherAttributes` convention document. Infinity State-derived optional schemas
live under:

```text
docs/schemas/other_attributes/infinity-state/v1/
```

Entries that already have downstream schemas are referenced here until a
copy/reference packaging decision lands. Entries without downstream schemas use
small draft schemas in the catalog path above.

| Entry | Key | Applies to | Schema status |
| --- | --- | --- | --- |
| Document display metadata | `document_display` | `scxml` root | downstream schema exists |
| Title style metadata | `title_style` | `scxml` root | downstream schema exists |
| State style override | `style` | state-like objects | downstream schema exists |
| Transition style override | `style` | `transition` | downstream schema exists |
| Datamodel data schema | `schema` | `data` | downstream schema exists |
| Help text annotation box | `help_text_box` | rendered objects with effective `help_text` | `infinity-state/v1/annotation-box.schema.json` |
| Condition text annotation box | `condition_text_box` | transition condition labels / rendered condition blocks | `infinity-state/v1/annotation-box.schema.json` |
| Node position | `position` | state-like visual nodes | `infinity-state/v1/node-position.schema.json` |
| Transition geometry | `arc`, `skew`, `base_pos`, `arrow_pos` | `transition` | `infinity-state/v1/transition-geometry.schema.json` |

## Inventory Backlog

The full catalog still needs to reconcile downstream keys that exist today but
are not yet preferred optional schema entries:

| Candidate | Applies to | Status |
| --- | --- | --- |
| `codegen.targetLangs` | `scxml` root | Inventory only; decide codegen/editor namespace. |
| `defaultBubbleSize` | `scxml` root | Inventory only; decide document display vs node defaults. |
| Legacy coordinate keys | state-like visual nodes | Inventory only; includes `POSITION_X`, `POSITION_Y`, `positionX`, `positionY`, `posX`, `posY`, `x`, and `y`. |
| Legacy size/spacing keys | state-like visual nodes | Inventory only; includes `BOX_SIZE` and `MARGIN`. |
| `id` | `transition` | Inventory only; reconcile with transition identity policy. |
| `style.parallelShadow` | parallel states | Inventory only; reconcile with `style.shadow` schema spelling. |
| Datamodel schema UI hints | `data.other_attributes.schema` | Inventory only; distinguish behavior-authority fields from editor-only hints. |

## Validation Modes

Recommended validation modes:

- `core`: validate only against `scjson.schema.json`.
- `known-registry`: validate known registry keys when present, preserve unknown
  keys.
- `strict-profile`: product-specific mode that may reject unknown keys for a
  named profile. This mode is not core SCJSON behavior.

## Casing

Canonical SCJSON interchange keys should use snake_case. Product APIs may
publish documented aliases, such as camelCase frontend names.

## Schema URI Policy

Catalog draft schemas use stable file paths under
`docs/schemas/other_attributes/infinity-state/v1/`. Their `$id` values are
provisional documentation identifiers until publication packaging is ratified.
Downstream schema references are informative during this planning phase.

## Versioning

Optional registry schemas should use additive versioning. Adding optional
properties is non-breaking. Removing keys, tightening constraints, or changing
meaning requires a new versioned schema location or a documented migration.
