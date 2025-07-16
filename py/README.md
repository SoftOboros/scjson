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

# SCJSON Caveats

The SCXML conversion helpers normalize data so it can be stored as JSON.
During `asdict()` serialization the generated dataclasses may contain
`Decimal` values and enumeration instances (e.g. `AssignTypeDatatype`).

- `Decimal` values are converted to floating point numbers.
- Enum values are stored using their `.value` string.

These conversions allow the JSON representation to be serialized by
`json.dumps` and then converted back via the `_to_dataclass` helper.

## License

All source code in this directory is released under the BSD&nbsp;1-Clause license. See `LICENSE` and `LEGAL.md` for details.

