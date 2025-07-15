# scjson

> A JSON-based serialization of SCXML (State Chart XML) for modern tooling, interoperability, and education.

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

The canonical `scjson.schema.json` file is located in [`/schema`](./schema).  
It is generated from Pydantic models and used to validate all `*.scjson` documents.

---

## Directory Structure

Each language implementation lives in its own directory, as a standalone module or library root:

/schema/ → JSON Schema definition of scjson
/examples/ → SCXML and scjson sample pairs
/tutorial/ → Git submodule: Zhornyak SCXML tutorial
/python/ → Python reference implementation (CLI + library)
/typescript/ → TypeScript converter and tooling (WIP)
/rust/ → Rust module for scjson (planned)
/go/ → Go implementation (planned)
/csharp/ → C# implementation (planned)


Each directory is designed to be independently usable as a library or CLI tool.

---

## Converters

| Language     | Status     | Path                          | Notes                      |
|--------------|------------|-------------------------------|----------------------------|
| Python       | ✅ Stable  | [`/python`](./python)         | Reference implementation   |
| TypeScript   | ⏳ WIP     | [`/typescript`](./typescript) | AJV + XML parser planned   |
| Rust         | ⏳ Planned | [`/rust`](./rust)             | `serde` + `quick-xml`      |
| Go           | ⏳ Planned | [`/go`](./go)                 | `encoding/json` + `xml`    |
| C#           | ⏳ Planned | [`/csharp`](./csharp)         | LINQ-to-XML, Json.NET      |

---## Examples & Test Suite

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

Language-specific converters for SCXML ↔ scjson are under active development.

Currently supported:
- ✅ Python (reference implementation)
- ⏳ TypeScript/JavaScript (planned)
- ⏳ Rust (planned)
- ⏳ Go (planned)
- ⏳ C# (planned)
- ⏳ lua (planned)

All converters (will) share the same schema and test suite to ensure compatibility.

---

## Getting Started

```bash
# Convert from SCXML to scjson
scjson convert --from scxml path/to/file.scxml --to scjson path/to/file.scjson

# Validate a scjson file
scjson validate path/to/file.scjson
