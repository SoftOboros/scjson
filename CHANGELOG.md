# Changelog — scjson (cross-language index)

scjson is a multi-language repository. Each implementation tracks its own
release cadence and version number; this file is a navigation index, not a
single version stream.

| Language | Path                  | Latest version  | Per-package log |
|----------|-----------------------|-----------------|------------------|
| Python   | `py/`                 | 0.4.0           | [`py/CHANGELOG.md`](py/CHANGELOG.md) |
| Ruby     | `ruby/`               | 0.3.5           | (in `git log`)   |
| JS       | `js/`                 | 0.4.0           | (in `git log`)   |
| Rust     | `rust/`               | 0.3.3           | (in `git log`)   |
| Java     | `java/`               | 0.3.3-SNAPSHOT  | (in `git log`)   |
| Swift    | `swift/`              | (see swift)     | [`swift/CHANGELOG.md`](swift/CHANGELOG.md) |
| Lua      | `lua/`                | (rockspec)      | (in `git log`)   |
| Go       | `go/`                 | (`go.mod`)      | (in `git log`)   |
| C#       | `csharp/`             | (csproj)        | (in `git log`)   |

## Cross-language entries

### 2026-05-24 — Python 0.4.0 + JavaScript 0.4.0 (help_text + SCXML comment promotion + extension metadata registry)

scjson 0.4.0 lands the cross-language CONV-E/F/G work planned in
`docs/concepts/SCJSON-CONV-00-CONCEPTS.md` and
`docs/concepts/SCJSON-OTHER-ATTRIBUTES-00-CONCEPTS.md`:

- **CONV-E (`help_text`).** `help_text: list[str]` is a first-class
  SCJSON authoring metadata field on every applies-to model surface
  (`Scxml`, `State`, `Parallel`, `Final`, `History`, `Initial`,
  `Transition`, `Onentry`, `Onexit`, `Invoke`, `Finalize`,
  `Datamodel`, `Data`, `Donedata`, `Content`, `Param`, `Assign`,
  `Log`, `Raise`, `If`, `Elseif`, `Else`, `Foreach`, `Send`,
  `Cancel`, `Script`). Distinct from `other_attributes` — chart
  documentation lives in `help_text`, extension metadata in
  `other_attributes`. Optional; canonical JSON omits empty arrays;
  scalar single-entry collapse is forbidden. Python (xsdata-derived
  pydantic + dataclass models, generated via `py/patch_help_text.py`)
  and JavaScript (`fast-xml-parser` ARRAY_KEYS + restoreKeys skip)
  preserve `help_text` through JSON ↔ JSON round-trips.
  `scjson.schema.json` validates it as `{type: array, items: {type: string}}`
  and stays byte-identical across the root, `js/`, and `java/` mirrors.

- **CONV-F (SCXML comment promotion).** SCXML comments now promote
  into `help_text` deterministically per the eight CONV-F attachment
  rules + edge cases. Python pre-pass uses `lxml` with comment
  preservation; JavaScript uses `fast-xml-parser` with
  `preserveOrder + commentPropName`. Both implementations share the
  same deterministic addressing shape `((local_tag, sibling_index_among_same_tag), ...)`
  for cross-language fixture parity. XML-comment-safe emission: `--`
  in body becomes `- -`, trailing `-` gets a space, multi-line
  common-indent dedent + leading/trailing blank-line trim, no
  paragraph wrap or coalescing. SCXML-side round trip is now
  end-to-end on both languages (xml → SCJSON via help_text → xml
  with leading comments before the owning element).
  `help_text` MUST NOT affect SCXML validation, execution, transition
  selection, datamodel evaluation, or trace output (CONV-INV-7).

- **CONV-G (extension metadata registry + optional schema catalog).**
  `SCJSON-OTHER-ATTRIBUTES-00-CONCEPTS.md` is the planning registry
  for documented `other_attributes` conventions, seeded by Infinity
  State `otherAttributes` names: `document_display`, `title_style`,
  `description`, `position`, `style`, `schema`, `arc`, `skew`,
  `base_pos`, `arrow_pos`, `help_text_box`, `condition_text_box`. The
  optional schema catalog lives under
  `docs/schemas/other_attributes/infinity-state/v1/` and is **not**
  part of `scjson.schema.json` — products opt into registry
  validation at import / export / publish boundaries. Core
  `scjson.schema.json` keeps `other_attributes` open to unknown
  extension keys (OA-INV-1).

The execution-engine semantics, trace output, and existing converter
parity are unchanged. See `docs/concepts/SCJSON-CONV-00-CONCEPTS.md`
§3-§7 for the canonical contract and
`docs/concepts/SCJSON-OTHER-ATTRIBUTES-00-CONCEPTS.md` §2-§10 for the
registry surface.

### 2026-05-01 — Python 0.3.7 (engine and metadata bugfixes)

Python-only fixes to the execution engine and generated pydantic model surface:
root activation no longer collides with state ids when `<scxml name="X">`
matches a `<state id="X">`, and pydantic `other_attributes` now accepts typed
JSON metadata while dataclass models remain string typed for XML
serialization. Other languages do not implement the Python engine and are not
affected by the engine fix. See
[`py/CHANGELOG.md`](py/CHANGELOG.md) for details.
