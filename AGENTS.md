# AGENTS

This file defines agents and their respective roles for the `scjson` project. Each agent is responsible for a specific transformation, validation, or extraction task.

---
## Python Configuration
Python is setup with all modules specified.  Do not run pip or poetry.

## Javascript Configuration
The package.json for js directory specifies dist/index.js as the entrypoint.  Therefore
the package needs to be cpiled with 'npm run build' prior to execution via node
or testing after changes with uber_test.py.


## Documentation and Attribution Requirements

All agents **must** include:

- A full **module-level docstring** at the top of each file
- doctrings for classes and function including doxygen style params / returns.
- File-level attribution in the following format:

```python
"""
Agent Name: <descriptive identifier>

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.
"""
```

---

## Agent: scxml-to-scjson

- **Input**: SCXML document (`*.scxml`, XML format)
- **Output**: SCJSON object (`*.scjson`, JSON format)
- **Mode**: One-way structural transformation
- **Validation**: Against `scjson.schema.json`
- **Notes**:
  - Converts tag structure, attributes, and nesting from XML to JSON
  - Strips comments and unsupported SCXML extensions
  - Preserves hierarchy and execution semantics

---

## Agent: scjson-to-scxml

- **Input**: SCJSON object (`*.scjson`, JSON format)
- **Output**: SCXML document (`*.scxml`, XML format)
- **Mode**: Reversible transformation
- **Validation**: Against SCXML XSD (`scxml.xsd`)
- **Notes**:
  - Generates valid SCXML conforming to W3C schema
  - Output is functionally equivalent to input, structure-first

---

## Agent: validate-scjson

- **Input**: SCJSON object (`*.scjson`)
- **Output**: Pass/Fail + list of validation errors
- **Mode**: Stateless
- **Validator**: `scjson.schema.json`
- **Notes**:
  - Can be used independently or as a preflight step
  - Compatible with `jsonschema` validator libraries

---

## Agent: validate-scxml

- **Input**: SCXML document (`*.scxml`)
- **Output**: Pass/Fail + list of validation errors
- **Mode**: Stateless
- **Validator**: `scxml.xsd` (W3C)
- **Notes**:
  - Requires an XML Schema validator (e.g., lxml, xmllint)
  - Assumes UTF-8 encoded XML input

---

## Agent: generate-jsonschema

- **Input**: Internal Pydantic model definitions
- **Output**: JSON Schema (`scjson.schema.json`)
- **Mode**: Build-time
- **Notes**:
  - Canonical schema used for all SCJSON validation
  - Should be regenerated if models change

---

## Agent: roundtrip-test

- **Input**: SCXML → SCJSON → SCXML
- **Output**: Pass/Fail + diffs
- **Mode**: Test utility
- **Notes**:
  - Detects loss of fidelity or semantic drift
  - Useful for CI integration and regression checks

---

## Agent: schema-dump

- **Input**: SCJSON file
- **Output**: Metadata block or structure summary
- **Mode**: Introspective
- **Notes**:
  - Prints root tag, state count, and feature coverage
  - Optional: hash of structure for test matching

