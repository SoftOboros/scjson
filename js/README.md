# scjson JavaScript Package

This directory contains the JavaScript implementation of **scjson**, a format for representing SCXML state machines in JSON. The package provides a command line interface to convert between `.scxml` and `.scjson` files and to validate documents against the project's schema.

The package includes typescript types for the functions and default functions to return each.

## Installation

```bash
npm install scjson
```

You can also install from a checkout of this repository:

```bash
cd js && npm install
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

## Conversion Functions
```js
/**
 * xmlToJson
 * Convert an SCXML string to scjson.
 *
 * @param {string} xmlStr - XML input.
 * @param {boolean} [omitEmpty=true] - Remove empty values when true.
 * @returns {string} JSON representation.
 */

/**
 * jsonToXml
 * Convert a scjson string to SCXML.
 *
 * @param {string} jsonStr - JSON input.
 * @returns {string} XML output.
 */
```

## Common JS Translate Usage
```js
const { xmlToJson, jsonToXml } = require('scjson');

```

## ESR translate usage
```js
import { xmlToJson, jsonToXml }from "scjson/browser"
```

## Axios Endpoint Example
```typescript
import axios from "axios"
import * as scjson from "scjson/props"

// A function to creat a new doc with three states and transitions.
const newScxml = (): scjson.ScxmlProps => {
  const doc: scjson.ScxmlProps = scjson.defaultScxml();
  let state: scjson.StateProps = scjson.defaultState();
  let transition: scjson.TransitionProps = scjson.defaultTransition();
  doc.name = 'New State Machine';
  doc.exmode = scjson.ExmodeDatatypeProps.Lax;
  doc.binding = scjson.BindingDatatypeProps.Early;
  doc.initial.push('Start');
  state.id = 'Start';
  transition.target.push('Process');
  state.transition.push(transition);
  doc.state.push(state);
  state = scjson.defaultState();
  state.id = 'Process';
  transition = scjson.defaultTransition();
  transition.target.push('End');
  state.transition.push(transition);
  doc.state.push(state);
  state = scjson.defaultState();
  state.id = 'End';
  transition = scjson.defaultTransition();
  transition.target.push('Start');
  state.transition.push(transition);
  doc.state.push(state);
  return doc;
}

// Create Axios instance
const ax = axios.create({
  baseURL: "https://api.example.com/scxml",
  headers: { "Content-Type": "application/json" },
  withCredentials: true,
});

// Export a function to send the doc
export const sendNewScxml = () => {
  const doc = newScxml();
  ax.post('/newDoc', doc);
}

```

### Other Resources
github: [https://github.com/SoftOboros/scjson]
```bash
git clone https://github.com/SoftOboros/scjson.git

git clone git@github.com:SoftOboros/scjson.git

gh repo clone SoftOboros/scjson
```

pypi: [https://pypi.org/project/scjson/]
```bash
pip install scjson
```

cargo: [https://cargo.io/crates/scjson]
```bash
cargo install scjson
```

dockerhub: [https://hub.docker.com/r/iraa/scjson]
(Full development environment for all supported languages)
```bash
docker pull iraa/scjson:latest
```


All source code in this directory is released under the BSD\u00A01-Clause license. See `LICENSE` and `LEGAL.md` for details.
