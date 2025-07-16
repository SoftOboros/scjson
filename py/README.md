# scjson Python Package

This directory contains the Python implementation of **scjson**, a format for representing SCXML state machines in JSON. The package provides a command line interface and utility functions to convert between `.scxml` and `.scjson` files and to validate documents against the project's schema.

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

## Command Line Usage

After installation the `scjson` command is available:

```bash
# Convert a single file
scjson json path/to/machine.scxml

# Convert back to SCXML
scjson xml path/to/machine.scjson

# Validate recursively
scjson validate path/to/dir -r
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

## SCJSON Caveats

The SCXML conversion helpers normalize data so it can be stored as JSON.
During `asdict()` serialization the generated dataclasses may contain
`Decimal` values and enumeration instances (e.g. `AssignTypeDatatype`).

- `Decimal` values are converted to floating point numbers.
- Enum values are stored using their `.value` string.

These conversions allow the JSON representation to be serialized by
`json.dumps` and then converted back via the `_to_dataclass` helper.

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

## License

All source code in this directory is released under the BSD&nbsp;1-Clause license. See `LICENSE` and `LEGAL.md` for details.

