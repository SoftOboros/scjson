<p align="center"><img src="scjson.png" alt="scjson logo" width="200"/></p>

# scjson

> A JSON-based serialization of SCXML (State Chart XML) for modern tooling, interoperability, and education. Includes execution engines (Python, Ruby) for SCXML/SCML traces.

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
Detailed inference rules used by the converters are described in [INFERENCE.md](./INFERENCE.md).

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

| Language  | Status | Path | Notes |
|-----------|--------|------|-------|
| Python    | ✅ Canonical | [py](./py/README.md) | Reference implementation and compatibility baseline |
| JavaScript| ✅ Parity | [js](./js/README.md) | Matches Python output on the tutorial corpus |
| Ruby      | ✅ Parity | [ruby](./ruby/README.md) | Converter parity; engine trace interface under active development |
| Rust      | ✅ Parity | [rust](./rust/README.md) | Matches Python output on the tutorial corpus |
| Java      | ✅ Parity | [java](./java/README.md) | Uses [SCION](https://www.npmjs.com/package/scion)-backed runner; matches Python output |
| Go        | ✅ Parity | [go](./go/README.md) | Matches Python output on the tutorial corpus |
| Swift     | ✅ Parity | [swift](./swift/README.md) | Matches Python output on the tutorial corpus |
| C#        | ⚠️ Beta | [csharp](./csharp/README.md) | Functional CLI; parity work in progress |
| Lua       | ✅ Parity | [lua](./lua/README.md) | Matches Python output on the tutorial corpus |

See [docs/COMPATIBILITY.md](./docs/COMPATIBILITY.md) for the latest cross-language
parity details and test notes.

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
```

rubygems: [https://rubygems.org/gems/scjson]
```bash
gem install scjson
```

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
