# Changelog — scjson (cross-language index)

scjson is a multi-language repository. Each implementation tracks its own
release cadence and version number; this file is a navigation index, not a
single version stream.

| Language | Path                  | Latest version  | Per-package log |
|----------|-----------------------|-----------------|------------------|
| Python   | `py/`                 | 0.4.0           | [`py/CHANGELOG.md`](py/CHANGELOG.md) |
| Ruby     | `ruby/`               | 0.4.0           | (in `git log`)   |
| JS       | `js/`                 | 0.4.0           | (in `git log`)   |
| Rust     | `rust/`               | 0.4.0           | (in `git log`)   |
| Java     | `java/`               | 0.4.0           | (in `git log`)   |
| Swift    | `swift/`              | (see swift)     | [`swift/CHANGELOG.md`](swift/CHANGELOG.md) |
| Lua      | `lua/`                | (rockspec)      | (in `git log`)   |
| Go       | `go/`                 | (`go.mod`)      | (in `git log`)   |
| C#       | `csharp/`             | (csproj)        | (in `git log`)   |

## Cross-language entries

### 2026-05-26 — 0.4.0 release prep (help_text docs + inclusion surfaces)

The `release/0.4.0-help-text-comments` branch is prepared for package release
with aligned touched-package versions and public README coverage for the new
authoring metadata and inclusion behavior:

- **Package version alignment.** Python, JavaScript, Ruby, and Java release
  metadata now report `0.4.0` across their package-manager configuration
  surfaces (`pyproject.toml`, `package.json`, `package-lock.json`, gemspec,
  Ruby version constant, `Gemfile.lock`, and Maven `pom.xml`).
- **README feature documentation.** The top-level README now documents
  `help_text` as first-class authoring metadata, explains SCXML comment
  promotion and re-emission, and states that `help_text` does not affect
  validation, execution, datamodel evaluation, transition selection, or trace
  output.
- **Inclusion and resource surface documentation.** The README now calls out
  preservation of `<data src="...">`, `<script src="...">`,
  `<invoke src="...">`, inline nested `<scxml>` content, `<send>` payloads, and
  `<donedata>` payloads. It also documents XInclude `preserve` and `resolve`
  modes and shows the `scjson json ... --xinclude resolve` CLI form.
- **CI sweep corpus hygiene.** Nonconformant finalize fixtures that intentionally
  contain forbidden `<send>` children now live under
  `tests/nonconformant_corpus/` instead of `tests/sweep_corpus/`, keeping the
  generated-vector execution sweep limited to conformant runtime charts while
  preserving negative validator coverage.
- **Rust package alignment.** The Rust package is now `0.4.0` and preserves
  JSON-typed `other_attributes` metadata during JSON -> XML -> JSON conversion
  by serializing object/array metadata as XML attribute JSON and parsing it back
  into `other_attributes`.

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
