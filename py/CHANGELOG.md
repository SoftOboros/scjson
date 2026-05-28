# Changelog — `scjson` (Python)

All notable changes to the Python package will be documented in this file.

The Python package version is independent of the JS, Ruby, Rust, Java, Swift,
Lua, Go, and C# package versions; cross-language work is coordinated through
the top-level [`CHANGELOG.md`](../CHANGELOG.md).

## 0.4.1 — 2026-05-28

### Changed

- Version bump for cross-language parity with the 0.4.1 JS / TS
  type-surface release. No Python behavior or API change. See
  top-level `CHANGELOG.md` and `docs/concepts/ERRATA.md` ERRATA-001
  for details.

## 0.4.0 — 2026-05-24

### Added

- **CONV-E: `help_text: list[str]` as a first-class SCJSON authoring metadata field.**
  Added to every applies-to model surface (root `Scxml` plus 25 child element
  models) on all four generated.py variants (pydantic, pydantic_strict,
  dataclasses, dataclasses_strict). Injected by the new
  `py/patch_help_text.py` post-generation script, invoked from
  `py/gen_models.sh`. Field is optional; canonical JSON omits empty arrays;
  scalar single-entry collapse is forbidden; entry order is authoring order;
  no auto-dedup. `help_text` is intentionally separate from
  `other_attributes`. `scjson.schema.json` validates it as
  `{type: array, items: {type: string}}` and the root / `js/` / `java/`
  mirrors stay byte-identical.

- **CONV-F: SCXML comment promotion in Python.** New
  `py/scjson/comment_promotion.py` implements the comment-preserving lxml
  pre-pass before xsdata parsing and the post-pass XML comment injection
  after xsdata serialization. Deterministic addressing via tuple of
  `(local_tag, sibling_index_among_same_tag)` for cross-language fixture
  parity with the JS converter. Honors the eight CONV-F attachment rules,
  the script / data / extension non-promotion exclusions, the XML-comment
  text repair (`--` → `- -`, trailing `-` + space), and multi-line
  common-indent dedent. `SCXMLDocumentHandler.xml_to_json` and `json_to_xml`
  wire the pre-/post-pass around the existing xsdata pipeline.

- **CONV-F: SCXML comment promotion in JavaScript.** New
  `js/src/comment_promotion.js` mirrors the Python promotion and emission
  rules. `xmlToJson` harvests comments into `help_text` after canonical
  normalization; `jsonToXml` re-emits non-empty `help_text` entries as leading
  XML comments without serializing `help_text` as an attribute, child element,
  or generic content.

- **CONV-G: extension metadata registry.** New
  `docs/concepts/SCJSON-OTHER-ATTRIBUTES-00-CONCEPTS.md` documents
  `other_attributes` conventions and optional schema-catalog policy seeded
  from the downstream Infinity State `otherAttributes` registry. Optional
  draft schemas live under
  `docs/schemas/other_attributes/infinity-state/v1/` (annotation-box,
  node-position, transition-geometry). Core `scjson.schema.json` continues
  to preserve unknown `other_attributes` keys (OA-INV-1).

### Tests

- 249 new `help_text` round-trip tests (`py/tests/test_help_text_round_trip.py`).
- 28 new comment-promotion tests (`py/tests/test_comment_promotion.py`).
- JavaScript converter and comment-promotion suites cover `help_text`
  preservation, promotion, emission, escaping, and cross-language address
  parity.
- Full Python suite after CONV-H follow-up: 401 passed, 1 skipped (baseline
  before 0.4.0: 363 passed, 1 skipped).

### Invariants

- CONV-INV-7: `help_text` and promoted SCXML comments MUST NOT alter
  canonical execution semantics or trace output.
- CONV-INV-8: comment promotion MUST be deterministic across Python and
  JavaScript converters; Python remains the canonical output.

## 0.3.7 — 2026-05-01

### Fixed

- **Engine: `<scxml name="X">` no longer collides with `<state id="X">`.**
  The root activation previously used the document's `name` attribute as its
  identifier (`_build_activation_tree`, `context.py`). When `name` matched a
  state `id`, three things broke at once:
  1. The state-id lookup table (`self.activations`) overwrote one entry with
     the other, so `_enter_target` resolved the colliding name to whichever
     activation was indexed last.
  2. `self.configuration` carried the root id from startup
     (`_from_model: ctx.configuration.add(root_state.id)`), so the colliding
     state appeared "already active" from byte one and `_enter_initial_states`
     short-circuited entries to it.
  3. `_is_user_state` (used by every `_filter_states` callsite, which feeds
     `trace_step`'s `firedTransitions`, `enteredStates`, `exitedStates`, and
     `configuration`) explicitly rejects anything equal to
     `root_activation.id`, silently scrubbing the legitimately-named state
     out of every observable trace output.

  The root activation now uses the sentinel `__scxml_root__`, which cannot
  collide with any user-authored state id (state ids are NCName-shaped per
  XML; double-underscored sentinels are not valid NCNames).

  Charts authored with a `name` attribute matching a top-level state id
  produced empty `firedTransitions` and an empty observable `configuration`
  before this fix, even though the dispatch table itself was correct. The
  failure was silent — no exception, no warning — which is why downstream
  consumers (codegen golden traces, vector verifiers, the Rust/TS runtime
  comparators) all carried the same wrong answer.

### Notes

- This is a **Python-engine-only** fix. The JS/Ruby/Rust/Java/Swift/Lua/Go/C#
  serializers do not implement the execution engine and are unaffected.
- No schema or wire-format change. Existing `.scjson` files remain valid.
- No breaking API change. `DocumentContext.root_activation.id` now returns
  `"__scxml_root__"` instead of `getattr(doc, "name", None) or "anon"`; any
  caller that relied on the old behaviour to recover the chart's `name`
  should read `ctx.doc.name` directly (which was always the source of truth).
- **Pydantic: `other_attributes` accepts typed JSON metadata.**
  The generated `scjson.pydantic` and `scjson.pydantic_strict` models now type
  `other_attributes` as `dict[str, Any]`, allowing integer, boolean, array, and
  object values that downstream JSON tooling stores on extension attributes.
  The dataclass model families intentionally remain `dict[str, str]` because
  they back XML serialization, where attribute values are strings.

### Packaging Notes

- `py/gen_models.sh`, `py/patch_other_attributes_any.py`, and
  `py/patch_scxml_forward_ref.py` remain repository maintenance tools for
  regenerating checked-in models. They are not added to the Python runtime
  package surface or wheel entry points. Runtime package data continues to be
  limited to the files already included by `py/MANIFEST.in`, including README,
  license/legal text, tests, and bundled templates.

## 0.3.6 and earlier

See git history; no per-package changelog was maintained prior to 0.3.7.
