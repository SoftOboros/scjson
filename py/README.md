<p align="center"><img src="https://raw.githubusercontent.com/SoftOboros/scjson/main/scjson.png" alt="scjson logo" width="200"/></p>

# scjson Python Package

This directory contains the Python implementation of **scjson**, a format for representing SCXML state machines in JSON. The package provides a command line interface and utility functions to convert between `.scxml` and `.scjson` files and to validate documents against the project's schema.

The package includes pydantic and dataclasses types for the associated objects / enums in both standard and strict forms.

For details on how SCXML elements are inferred during conversion see [INFERENCE.md](https://github.com/SoftOboros/scjson/blob/main/INFERENCE.md).  In python, inference for conversion is handled by the 
dataclasses models. See below.

## Installation

```bash
pip install scjson
```

You can also install from a checkout of this repository:

```bash
cd py && pip install -e .
```

## Source Code - Multi-Language Support
[https://github.com/SoftOboros/scjson/]
- csharp
- go
- java
- javascript / typescript
- lua
- python
- ruby
- rust
- swift

## Python Engine — User Guide

For end‑to‑end usage of the Python execution engine (tracing, comparing against a reference, generating vectors, sweeping corpora), see:

- docs/ENGINE-PY.md (in this repository)

Online: https://github.com/SoftOboros/scjson/blob/main/docs/ENGINE-PY.md

## SCION Reference Dependency

Several comparison tests (`py/tests/test_exec_compare_advanced.py`) and the
`exec_compare` tooling invoke the Node-based [SCION](https://www.npmjs.com/package/scion) runner bundled under
`tools/scion-runner`. Node.js must be able to resolve the [SCION](https://www.npmjs.com/package/scion) packages
(`scxml`, `jsdom`, and `regenerator-runtime`) via its module loader. Install
them once before running comparisons:

```bash
cd tools/scion-runner
npm ci  # or npm install
```

When running the Python tests or CLI comparisons, ensure `node` can load these
modules (for example by keeping the installation above in place or by adding
their location to `NODE_PATH`). Without the [SCION](https://www.npmjs.com/package/scion) packages, comparisons fall
back to the Python engine.

## Command Line Usage

After installation the `scjson` command is available:

```bash
# Convert a single file
scjson json path/to/machine.scxml

# Convert back to SCXML
scjson xml path/to/machine.scjson - o path/to/output.scxml

# Validate recursively
scjson validate path/to/dir -r

# Genrate typescript Types
scjson  typescript -o dir/of/output

# Genrate scjson.schema.json
scjson  schema -o dir/of/output
```

## FastAPI example Usage
This is a minimal FastAPI endpoint as an example usage of the SCXMLDocumentHandler class.

```python
import json
from fastapi import FastAPI, Request, HTTPException, Response
from scjson.SCXMLDocumentHandler import SCXMLDocumentHandler

app = FastAPI()
handler = SCXMLDocumentHandler(schema_path=None)

# In-memory store for demo
store = {}

@app.get("/xml/{slug}")
async def get_xml(slug: str):
    """Return the SCXML document as XML."""
    data = store.get(slug)
    if not data:
        raise HTTPException(status_code=404, detail="Document not found")
    xml_str = handler.json_to_xml(json.dumps(data))
    return Response(content=xml_str, media_type="application/xml")

@app.post("/xml/{slug}")
async def post_xml(slug: str, request: Request):
    """Accept an SCXML document and convert it to scjson."""
    xml_bytes = await request.body()
    xml_str = xml_bytes.decode("utf-8")
    json_str = handler.xml_to_json(xml_str)
    data = json.loads(json_str)
    data.setdefault("name", slug)
    store[slug] = data
    return data
```

## Importing Objects.
This imports the definitions of individual types.  See below for lib variats.
Class varaints available for pydantic and dataclasses implementing both the
standard and strict xsd variants.

```python
from scjson.pydantic import Scxml, State, Transition, Onentry # etc.

```

## SCJSON Caveats

The SCXML conversion helpers normalize data so it can be stored as JSON.
During `asdict()` serialization the generated dataclasses may contain
`Decimal` values and enumeration instances (e.g. `AssignTypeDatatype`).

- `Decimal` values are converted to floating point numbers.
- Enum values are stored using their `.value` string.

These conversions allow the JSON representation to be serialized by
`json.dumps` and then converted back via the `_to_dataclass` helper.

## Known Issues
None at this time.

Operational conformance testing is performed via [uber_test.py](https://github.com/SoftOboros/scjson/blob/engine/py/uber_test.py)
```bash
/py# python uber_test.py -l python 2>&1 | tee test.log
```
Note: [uber_test.py](https://github.com/SoftOboros/scjson/blob/main/py/uber_test.py) applies all scxml files in [Zhornyak's ScxmlEditor-Tutorial](https://alexzhornyak.github.io/ScxmlEditor-Tutorial/) which provides a robest set of scxml test vectors useful for standard compliance verification.  This is the only file in the test suite which fails to verify round-trip.

### Uber Test Harness

Run across all languages or a single language with alias support:

```bash
# All languages detected on PATH
python py/uber_test.py

# Single language (aliases allowed): py, python, js, ts, javascript, rs, rust, swift, java, csharp
python py/uber_test.py -l js
python py/uber_test.py -l swfit   # typo tolerated → swift

# Limit the corpus and treat consensus as warnings only
python py/uber_test.py -l swift -s "Examples/Qt/StopWatch/*.scxml" --consensus-warn
```

- `-s/--subset` filters SCXML files by a glob relative to `tutorial/`.
- `--consensus-warn` downgrades mismatches to warnings when reference languages (Python/JavaScript/Rust) match the canonical structure.
- The harness normalizes structural differences (see INFERENCE.md) to produce actionable diffs and prints a triage line with a recommendation.

## Model Variants

The Python package exposes four sets of generated models that mirror the
SCJSON schema. They all share the same field names and enumerations, but
offer different runtime characteristics.

### Enums

Each enumeration represents a restricted string set used by SCXML. The values
shown below mirror those defined in the SCJSON schema.

- `AssignTypeDatatype` – how the `<assign>` element manipulates the datamodel.
  Values: `replacechildren`, `firstchild`, `lastchild`, `previoussibling`,
  `nextsibling`, `replace`, `delete`, `addattribute`.
- `BindingDatatype` – determines if datamodel variables are bound `early` or
  `late` during execution.
- `BooleanDatatype` – boolean attribute values `true` or `false`.
- `ExmodeDatatype` – processor execution mode, either `lax` or `strict`.
- `HistoryTypeDatatype` – type of `<history>` state: `shallow` or `deep`.
- `TransitionTypeDatatype` – whether a `<transition>` is `internal` or
  `external`.

## Common Types

Several generated classes share generic helper fields:

- `other_attributes`: `dict[str, str]` capturing additional XML attributes from
  foreign namespaces.
- `other_element`: `list[object]` allowing untyped child nodes from other
  namespaces to be preserved.
- `content`: `list[object]` used when elements permit mixed or wildcard
  content.

### `scjson.dataclasses`

Plain Python dataclasses without runtime validation.

- `Assign` – update a datamodel location with an expression or value.
- `Cancel` – cancel a pending `<send>` operation.
- `Content` – inline payload used by `<send>` and `<invoke>`.
- `Data` – represents a single datamodel variable.
- `Datamodel` – container for one or more `<data>` elements.
- `Donedata` – payload returned when a `<final>` state is reached.
- `Else` – fallback branch for `<if>` conditions.
- `Elseif` – conditional branch following an `<if>`.
- `Final` – marks a terminal state in the machine.
- `Finalize` – executed after an `<invoke>` completes.
- `Foreach` – iterate over items within executable content.
- `History` – pseudostate remembering previous active children.
- `If` – conditional execution block.
- `Initial` – starting state within a compound state.
- `Invoke` – run an external process or machine.
- `Log` – diagnostic output statement.
- `Onentry` – actions performed when entering a state.
- `Onexit` – actions performed when leaving a state.
- `Parallel` – coordinates concurrent regions.
- `Param` – parameter passed to `<invoke>` or `<send>`.
- `Raise` – raise an internal event.
- `Script` – inline executable script.
- `Scxml` – root element of an SCJSON document.
- `Send` – dispatch an external event.
- `State` – basic state node.
- `Transition` – edge between states triggered by events.

### `scjson.dataclasses_strict`

The same dataclasses as above but configured for stricter type checking.

### `scjson.pydantic`

Pydantic `BaseModel` classes generated from the SCJSON schema. They provide
data validation and convenient `.model_dump()` helpers.

### `scjson.pydantic_strict`

Pydantic models with strict validation settings.

### Other Resources
github: [https://github.com/SoftOboros/scjson]
```bash
git clone https://github.com/SoftOboros/scjson.git

git clone git@github.com:SoftOboros/scjson.git

gh repo clone SoftOboros/scjson
```

npm: [https://www.npmjs.com/package/scjson]
```bash
npm install scjson
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

## License

All source code in this directory is released under the BSD 1-Clause license. See [LICENSE](./LICENSE) and [LEGAL.md](./LEGAL.md) for details.
