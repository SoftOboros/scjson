<p align="center"><img src="scjson.png" alt="scjson logo" width="200"/></p>

# SCXML to SCJSON Converter Guide

This guide is an informative orientation for SCXML-to-SCJSON conversion. It is
not the source of truth for converter behavior, schema fields, structural-field
membership, attribute aliases, or extension surfaces.

Authoritative conversion semantics live in
[`docs/concepts/SCJSON-CONV-00-CONCEPTS.md`](docs/concepts/SCJSON-CONV-00-CONCEPTS.md)
and the repository semantic baseline lives in
[`docs/concepts/SCJSON-00-CONCEPTS.md`](docs/concepts/SCJSON-00-CONCEPTS.md).
Those documents define Python converter output and `scjson.schema.json` as the
canonical references. JavaScript, Rust, and other language converters are parity
implementations, not independent sources of truth.

## Current Conversion Model

At a high level, canonical SCJSON preserves SCXML hierarchy, executable ordering,
schema-compatible field names, tokenized list attributes, and extension content
that remains representable through supported schema surfaces.

Use the concepts docs for details when implementing or auditing a converter:

- Converter reference: Python output under the repo parity harness.
- Schema reference: `scjson.schema.json` and generated Pydantic models.
- Structural fields: the generated schema owns the registry; converter constants
  mirror it.
- Reserved XML names: schema aliases such as `type_value`, `raise_value`,
  `if_value`, `else_value`, `initial_attribute`, and `datamodel_attribute`.
- Token attributes: fields such as transition `target` and state/root `initial`
  are arrays where the schema marks them as token lists.
- Unknown or extension content: preserve it through the schema-supported
  `content`, `other_element`, or `other_attributes` surfaces.

## Historical Note

Earlier versions of this file described the JavaScript converter as the
inference reference and listed a fixed structural-field set. That guidance is
superseded by the concepts docs above. Keep examples in this file illustrative;
do not update them into a competing registry.

## Example

### SCXML Input

```xml
<state id="parent">
  <transition event="go" target="child"/>
  <state id="child"/>
  <onentry>
    <log label="start" expr="enter"/>
    <foo/>
  </onentry>
</state>
```

### Informative SCJSON Shape

This example shows common output shape only. The schema and canonical Python
converter decide the exact field surface.

```json
{
  "tag": "state",
  "id": "parent",
  "transition": [{
    "tag": "transition",
    "event": "go",
    "target": ["child"]
  }],
  "state": [{ "tag": "state", "id": "child" }],
  "onentry": [{
    "tag": "onentry",
    "log": [{ "tag": "log", "label": "start", "expr": "enter" }],
    "content": [{ "tag": "foo" }]
  }]
}
```

The unknown `<foo/>` element is shown in `content` as one valid extension
surface. Current authoritative rules allow extension material to remain
representable through `content`, `other_element`, or `other_attributes`,
depending on the schema field and converter path.
