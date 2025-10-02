<p align="center"><img src="scjson.png" alt="scjson logo" width="200"/></p>

# SCXML to SCJSON Inference Guide

This document describes how the JavaScript converter transforms SCXML into the `scjson` format. It captures the *inference logic* encoded in [`js/src/converters.js`](js/src/converters.js) so that other language implementations can reproduce identical behaviour.

## 1. Overview

- **SCJSON** is a structured JSON representation of SCXML.
- The converter does more than copy element names. Certain SCXML structures are **inferred** and attached directly to their parent objects.
- Understanding these rules allows developers to implement compatible converters in Rust, Python, or any other language.

## 2. Conversion Entry Point

- The root element is `<scxml>`.
- Each element becomes an object with a `"tag"` field holding the tag name.
- All XML attributes are copied as string properties at the same level as `tag`.
- Children are processed recursively.

## 3. Structural Field Extraction

The converter lifts specific child elements out of `content[]` so that they live directly on the parent object. Each of the following tags becomes an array property on its parent:

- `state`
- `parallel`
- `final`
- `history`
- `transition`
- `onentry`
- `onexit`
- `invoke`
- `datamodel`
- `data`
- `initial`
- `script`
- `log`
- `assign`
- `send`
- `cancel`

When any of these elements are present:

1. Initialise an array for the matching property (e.g. `state: []`).
2. Place converted child objects in this array.
3. Do not leave the raw element in `content[]` unless its tag is unknown.

## 4. Content Array Handling

- Children that do **not** match a structural field stay inside `content[]`.
- Order is preserved, and each child is recursively converted.
- Attributes are flattened onto each object.
- An empty tag becomes `{ "tag": "..." }` with no additional fields.

## 5. Other Attributes and Fallbacks

- All XML attributes are retained exactly as strings.
- Namespacing is not applied unless explicitly added by future versions.
- Unknown elements and attributes are preserved without raising errors.
- These points are extension hooks for future schema updates.

## 6. Examples

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

### Converted SCJSON
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

The unknown `<foo/>` element remains inside `content[]` of the `onentry` block.

## 7. Notes on Determinism

- Conversions are deterministic: the same SCXML yields identical SCJSON.
- Whitespace has no structural effect.
- Attribute order does not influence the output.

## 8. Implementation Hints

- A recursive descent approach is used.
- Use `element.tagName`, `element.attributes`, and `element.children` when walking the DOM.
- `STRUCTURAL_FIELDS` is a `Set` controlling whether a child is lifted out of `content[]`.

