<p align="center"><img src="scjson.png" alt="scjson logo" width="200"/></p>

# scjson

> A JSON-based serialization of SCXML (State Chart XML) for modern tooling, interoperability, and education.

**Execution Engines**
- Python engine: Deterministic trace emitter, vector generation, and compare tools. See `docs/ENGINE-PY.md` and `py/ENGINE-PY-DETAILS.md`.
- Ruby engine: Trace interface under active development with growing feature parity. See `docs/ENGINE-RB.md`.

**JS/TS Harness (via SCION)**
- The JS package ships a harness CLI `scjson-scion-trace` that directly requires `scion-core` to execute SCXML and emit JSONL traces. Install `scion-core` in your project to enable it.
- Supports both `.scxml` and `.scjson` input (the latter is converted to SCXML internally).
- Normalization flags: `--leaf-only`, `--omit-delta`, `--omit-transitions`, `--strip-step0-noise`, `--strip-step0-states`.
- Usage (package): `npx scjson-scion-trace -I chart.(scxml|scjson) -e events.jsonl [--xml] [--leaf-only] [--omit-delta] [...]`
- Dev alternative (in this repo): `node tools/scion-runner/scion-trace.cjs -I chart.scxml -e events.jsonl --xml`

---

## Overview

`scjson` is a structured, schema-based representation of [SCXML](https://www.w3.org/TR/scxml/), the W3C standard for state machine modeling. This format preserves the semantics and hierarchy of SCXML while making it more accessible to modern tools, languages, and interfaces.

Why JSON?

- Easier to parse in JavaScript, Python, Rust, etc.
- Fits naturally with REST APIs, editors, and static validation
- Can be round-tripped to and from standard SCXML
- Works with compact formats like MessagePack or Protobuf when needed

---

## Goals

- 💡 **Interoperability**: Serve as a bridge between SCXML and modern application ecosystems
- 📦 **Portability**: Enable translation to binary formats (MessagePack, Protobuf, etc.)
- 📚 **Pedagogy**: Make it easier to teach and learn state machines with cleaner syntax and visual tools
- 🔁 **Round-trip Fidelity**: Support conversion back to valid SCXML without semantic loss

---

## Schema

The canonical `scjson.schema.json` file is located in [`/scjson.schema.json`](./scjson.schema.json).
It is generated from Pydantic models and used to validate all `*.scjson` documents.
Current SCJSON representation and converter authority are documented in
[`docs/concepts/SCJSON-00-CONCEPTS.md`](./docs/concepts/SCJSON-00-CONCEPTS.md)
and
[`docs/concepts/SCJSON-CONV-00-CONCEPTS.md`](./docs/concepts/SCJSON-CONV-00-CONCEPTS.md).

---

## Authoring Metadata and Inclusion

scjson 0.4.0 adds first-class authoring metadata and stronger inclusion
coverage for chart documents:

- `help_text` is an optional `list[str]` field on SCJSON element models. It is
  for human-readable chart documentation and stays separate from
  `other_attributes`, which remains the extension metadata surface.
- SCXML comments are promoted into `help_text` during SCXML -> SCJSON
  conversion, and non-empty `help_text` entries are emitted back as leading
  SCXML comments during SCJSON -> SCXML conversion. This metadata does not
  affect validation, execution, transition selection, datamodel evaluation, or
  trace output.
- Inclusion and resource surfaces are preserved through conversion, including
  `<data src="...">`, `<script src="...">`, `<invoke src="...">`, inline nested
  `<scxml>` content, `<send>` payloads, and `<donedata>` payloads.
- XInclude is supported in two modes. The default `preserve` mode keeps
  unresolved `<xi:include>` directives as extension elements. The `resolve`
  mode expands includes before conversion when a loader or base path is
  available.

Canonical behavior is specified in
[`docs/concepts/SCJSON-CONV-00-CONCEPTS.md`](./docs/concepts/SCJSON-CONV-00-CONCEPTS.md);
the optional extension metadata registry is documented in
[`docs/concepts/SCJSON-OTHER-ATTRIBUTES-00-CONCEPTS.md`](./docs/concepts/SCJSON-OTHER-ATTRIBUTES-00-CONCEPTS.md).

---

## Directory Structure

Each language implementation lives in its own directory, as a standalone module or library root:

/schema/ → JSON Schema definition of scjson
/examples/ → SCXML and scjson sample pairs
/tutorial/ → Git submodule: Zhornyak SCXML tutorial
/python/ → Python reference implementation (CLI + library)
/js/ → JavaScript CLI and library
/ruby/ → Ruby CLI and gem
/go/ → Go command line utility
/rust/ → Rust command line utility
/swift/ → Swift command line tool
/java/ → Java command line tool
/lua/ → Lua scripts
/csharp/ → C# command line tool


Each directory is designed to be independently usable as a library or CLI tool.

---

## Converters & Engines

Language compatibility status is owned by
[`docs/COMPATIBILITY.md`](./docs/COMPATIBILITY.md). The table below is a package
map only; consult the compatibility matrix for current status tiers, parity
details, and test notes.

| Language  | Path | Notes |
|-----------|------|-------|
| Python    | [py](./py/README.md) | Canonical converter output and Python engine docs |
| JavaScript| [js](./js/README.md) | Converter package and SCION trace harness |
| Ruby      | [ruby](./ruby/README.md) | Converter package and Ruby engine docs |
| Rust      | [rust](./rust/README.md) | Converter package |
| Java      | [java](./java/README.md) | Converter package and [SCION](https://www.npmjs.com/package/scion)-backed runner |
| Go        | [go](./go/README.md) | Converter package |
| Swift     | [swift](./swift/README.md) | Converter package |
| C#        | [csharp](./csharp/README.md) | Converter package |
| Lua       | [lua](./lua/README.md) | Converter package |

---

## Examples & Test Suite

This repo includes a curated set of canonical SCXML examples and their equivalent `scjson` forms in [`/examples`](./examples). These are used for:

- Functional validation (SCXML ↔ scjson ↔ SCXML)
- Teaching state machine concepts via visual tools
- Demonstrating usage in editors, UI libraries, and low-code platforms

These examples are derived from and/or adapted from:

### 📚 Included Tutorial (as Git Submodule)

We include **Alex Zhornyak’s SCXML Editor Tutorial** as a Git submodule under [`/tutorial`](./tutorial).  
This provides a rich set of canonical SCXML test cases and diagrams.

> Attribution is provided for educational purposes. No endorsement is implied.  
> Source: [https://alexzhornyak.github.io/ScxmlEditor-Tutorial/](https://alexzhornyak.github.io/ScxmlEditor-Tutorial/)

---

### 🛠️ Submodule Setup

If you cloned this repo and `/tutorial` is empty, run:

```bash
git submodule init
git submodule update
Or clone with submodules in one step:

git clone --recurse-submodules https://github.com/your-org/scjson.git
```

This ensures you get the complete tutorial content alongside the examples and converters.

---

## Converters
All converters share the same schema and test suite to ensure compatibility.

---

## Getting Started

```bash
# Convert from SCXML to scjson
scjson convert --from scxml path/to/file.scxml --to scjson path/to/file.scjson

# Resolve XInclude directives before converting instead of preserving them
scjson json path/to/root.scxml --xinclude resolve --output path/to/root.scjson

# Validate a scjson file
scjson validate path/to/file.scjson
```

### Package Repostory Availability
pypi: [https://pypi.org/project/scjson/]
```bash
pip install scjson
```
npm: [https://www.npmjs.com/package/scjson]
```bash
npm install scjson
# harness requires scion-core
npm install scion-core
```

Harness (Node):
```bash
npx scjson-scion-trace -I path/to/chart.scxml -e events.jsonl --xml
```

rubygems: [https://rubygems.org/gems/scjson]
```bash
gem install scjson
```
RubyGems notes:
- Ruby CLI includes converters and a trace interface. See `docs/ENGINE-RB.md` for engine usage and maturity. The gem is published at the link above.

cargo: [https://crates.io/crates/scjson]
```bash
cargo install scjson
```

dockerhub: [https://hub.docker.com/r/iraa/scjson]
(Full development environment for all supported languages)
```bash
docker pull iraa/scjson:latest
```

For a full example of installing toolchains and dependencies across languages see [`codex/startup.sh`](codex/startup.sh).


## Documentation

- User guide (Python engine): `docs/ENGINE-PY.md`
- Architecture & in-depth reference (Python): `py/ENGINE-PY-DETAILS.md`
- Compatibility matrix: `docs/COMPATIBILITY.md`
- Testing guide: `TESTING.md`
- Agents overview: `AGENTS.md`


## Known Divergences and Issues

Cross‑engine comparisons sometimes surface intentional, documented differences (e.g., ordering nuances, ECMA `in` semantics, history re‑entry). Use these resources to understand, normalize, and triage behavior across SCION (Node), Python, and Ruby:

- Comprehensive overview: docs/COMPATIBILITY.md
- Normalization profile: `--norm scion` in exec_compare sets leaf‑only, omit‑delta, omit‑transitions, strip‑step0‑states, and ordering=scion.
  - Example: `python py/exec_compare.py tests/exec/toggle.scxml --events tests/exec/toggle.events.jsonl --reference "node tools/scion-runner/scion-trace.cjs" --norm scion`
- CI known‑diffs list: scripts/ci_ruby_known_diffs.txt (used by `scripts/ci_ruby_harness.sh --known` to keep CI green while still reporting expected mismatches).
- Ruby converter in CI: when Nokogiri isn’t available, the Ruby CLI falls back to the Python converter for SCXML↔scjson only; execution remains Ruby. See docs/ENGINE-RB.md (CI Notes).


## Quick Installs.

### Python Module
```bash
cd py
pip install -r requirements.txt
pytest -q
```

### JavaScript Module
```bash
cd js
npm ci
npm test --silent
```

### Ruby Module
```bash
cd ruby
gem install bundler
bundle install
bundle exec rspec
```

### Go Module
```bash
cd go
go test ./...
go build
```

### Rust Module
```bash
cd rust
cargo test
```

### Swift Module
```bash
cd swift
swift test
```

### C# Module
```bash
cd csharp
dotnet test -v minimal
```

### Lua Module
```bash
cd lua
luarocks install luaexpat --deps-mode=one
luarocks install dkjson --deps-mode=one
luarocks install busted --deps-mode=one
busted tests
```

## Legal and Documentation

All source code in this directory is released under the BSD 1-Clause license. See [LICENSE](./LICENSE) and [LEGAL.md](./LEGAL.md) for details. Additional documentation is available in [AGENTS.md](./AGENTS.md) and [TESTING.md](./TESTING.md).
