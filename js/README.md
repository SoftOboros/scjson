# scjson JavaScript Package

This directory contains the JavaScript implementation of **scjson**, a format for representing SCXML state machines in JSON. The package provides a command line interface to convert between `.scxml` and `.scjson` files and to validate documents against the project's schema.

For details on how SCXML elements are inferred during conversion see [INFERENCE.md](https://github.com/SoftOboros/scjson/blob/main/INFERENCE.md).

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

## Shared Converters
Both the Node and browser builds use the same conversion logic exposed in
`scjson/converters`. You can import these helpers directly if you need access to
the utility functions used by the CLI and browser modules.
```js
import { xmlToJson, jsonToXml } from 'scjson/converters';
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

## Known Issues
None at this time.

Operational conformance testing is performed via [uber_test.py](https://github.com/SoftOboros/scjson/blob/engine/py/uber_test.py)
```bash
/py# python uber_test.py -l javascript 2>&1 | tee test.log
```
Note: [uber_test.py](https://github.com/SoftOboros/scjson/blob/main/py/uber_test.py) applies all scxml files in [Zhornyak's ScxmlEditor-Tutorial](https://alexzhornyak.github.io/ScxmlEditor-Tutorial/) which provides a robest set of scxml test vectors useful for standard compliance verification.  This is the only file in the test suite which fails to verify round-trip.


### `scjson/props`

### Enums

Each enumeration represents a restricted string set used by SCXML. The values
shown below mirror those defined in the SCJSON schema.

enums use this pattern to all static and dynamic portions to be treated separately,
but mapped to the same name.
```typescript
export const BooleanDatatypeProps = {
    False: "false",
    True: "true",
} as const;

export type BooleanDatatypeProps = typeof BooleanDatatypeProps[keyof typeof BooleanDatatypeProps];
```

- `AssignTypeDatatypeProps` – how the `<assign>` element manipulates the datamodel.
  Values: `replacechildren`, `firstchild`, `lastchild`, `previoussibling`,
  `nextsibling`, `replace`, `delete`, `addattribute`.
- `BindingDatatypeProps` – determines if datamodel variables are bound `early` or
  `late` during execution.
- `BooleanDatatypeProps` – boolean attribute values `true` or `false`.
- `ExmodeDatatypeProps` – processor execution mode, either `lax` or `strict`.
- `HistoryTypeDatatypeProps` – type of `<history>` state: `shallow` or `deep`.
- `TransitionTypeDatatypeProps` – whether a `<transition>` is `internal` or
  `external`.

### Common Types

Several generated classes share generic helper fields:

- `other_attributes`: `Record<str, str>` capturing additional XML attributes from
  foreign namespaces.
- `other_element`: `list[object]` allowing untyped child nodes from other
  namespaces to be preserved.
- `content`: `list[object]` used when elements permit mixed or wildcard
  content.


### Document / Object Types
Plain typescript types without runtime validation.
- `AssignProps` `AssignArray`         – update a datamodel location with an expression or value.
- `CancelProps` `CancelArray`         – cancel a pending `<send>` operation.
- `ContentProps` `ContentArray`       – inline payload used by `<send>` and `<invoke>`.
- `DataProps` `DataArray`             – represents a single datamodel variable.
- `DatamodelProps` `DatamodelArray`   – container for one or more `<data>` elements.
- `DonedataProps` `DonedataArray`     – payload returned when a `<final>` state is reached.
- `ElseProps`                         – fallback branch for `<if>` conditions.
- `ElseifProps`                       – conditional branch following an `<if>`.
- `FinalProps` `FinalArray`           – marks a terminal state in the machine.
- `FinalizeProps` `FinalizeArray`     – executed after an `<invoke>` completes.
- `ForeachProps` `ForeachArray`       – iterate over items within executable content.
- `HistoryProps` `HistoryArray`       – pseudostate remembering previous active children.
- `IfProps` `IfArray`                 – conditional execution block.
- `InitialProps` `InitialArray`       – starting state within a compound state.
- `InvokeProps` `InvokeArray`         – run an external process or machine.
- `LogProps` `LogArray`               – diagnostic output statement.
- `OnentryProps` `OnentryArray`       – actions performed when entering a state.
- `OnexitProps` `OnexitArray`         – actions performed when leaving a state.
- `ParallelProps` `ParallelArray`     – coordinates concurrent regions.
- `ParamProps` `ParamArray`           – parameter passed to `<invoke>` or `<send>`.
- `RaiseProps` `RaiseArray`           – raise an internal event.
- `ScriptProps` `ScriptArray`         – inline executable script.
- `ScxmlProps`                        – root element of an SCJSON document.
- `SendProps` `SendArray`             – dispatch an external event.
- `StateProps` `StateArray`           – basic state node.
- `TransitionProps` `TransitionArray` – edge between states triggered by events.

### Object Management
- Kind - unique marker for each of the types.
```typescript
export type Kind = "number" | "string" | "record<string, object>" | "number[]" | "string[]"
                   | "record<string, object>[]" | "assign" | "assigntypedatatype" | "bindingdatatype" | "booleandatatype"
                   | "cancel" | "content" | "data" | "datamodel" | "donedata" | "else" | "elseif"
                   | "exmodedatatype" | "final" | "finalize" | "foreach" | "history" | "historytypedatatype" | "if"
                   | "initial" | "invoke" | "log" | "onentry" | "onexit" | "parallel" | "param" | "raise"
                   | "script" | "scxml" | "send" | "state" | "transition" | "transitiontypedatatype"
                   | "assignarray" | "cancelarray" | "contentarray" | "dataarray" | "datamodelarray"
                   | "donedataarray" | "finalarray" | "finalizearray" | "foreacharray" | "historyarray" | "ifarray"
                   | "initialarray" | "invokearray" | "logarray" | "onentryarray" | "onexitarray" | "parallelarray"
                   | "paramarray" | "raisearray" | "scriptarray" | "sendarray" | "statearray" | "transitionarray";
```
- PropsUnion - a union of the types used in the scxml data model
```typescript
export type PropsUnion = null | string | number | Record<string, object> | string[] | number[]
                         | Record<string, object>[] | AssignProps | AssignTypeDatatypeProps | BindingDatatypeProps
                         | BooleanDatatypeProps | CancelProps | ContentProps | DataProps | DatamodelProps | DonedataProps
                         | ElseProps | ElseifProps | ExmodeDatatypeProps | FinalProps | FinalizeProps | ForeachProps
                         | HistoryProps | HistoryTypeDatatypeProps | IfProps | InitialProps | InvokeProps | LogProps
                         | OnentryProps | OnexitProps | ParallelProps | ParamProps | RaiseProps | ScriptProps
                         | ScxmlProps | SendProps | StateProps | TransitionProps | TransitionTypeDatatypeProps
                         | AssignArray | CancelArray | ContentArray | DataArray | DatamodelArray | DonedataArray
                         | FinalArray | FinalizeArray | ForeachArray | HistoryArray | IfArray | InitialArray
                         | InvokeArray | LogArray | OnentryArray | OnexitArray | ParallelArray | ParamArray
                         | RaiseArray | ScriptArray | SendArray | StateArray | TransitionArray;
```
- KindMap - maps string name to type for the objects used in the scxml data model
```typescript
export type KindMap = {
    assign: AssignProps
    assignarray: AssignArray
    assigntypedatatype: AssignTypeDatatypeProps
    bindingdatatype: BindingDatatypeProps
    booleandatatype: BooleanDatatypeProps
    cancel: CancelProps
    cancelarray: CancelArray
    content: ContentProps
    contentarray: ContentArray
    data: DataProps
    dataarray: DataArray
    datamodel: DatamodelProps
    datamodelarray: DatamodelArray
    donedata: DonedataProps
    donedataarray: DonedataArray
    else: ElseProps
    elseif: ElseifProps
    exmodedatatype: ExmodeDatatypeProps
    final: FinalProps
    finalarray: FinalArray
    finalize: FinalizeProps
    finalizearray: FinalizeArray
    foreach: ForeachProps
    foreacharray: ForeachArray
    history: HistoryProps
    historyarray: HistoryArray
    historytypedatatype: HistoryTypeDatatypeProps
    if: IfProps
    ifarray: IfArray
    initial: InitialProps
    initialarray: InitialArray
    invoke: InvokeProps
    invokearray: InvokeArray
    log: LogProps
    logarray: LogArray
    onentry: OnentryProps
    onentryarray: OnentryArray
    onexit: OnexitProps
    onexitarray: OnexitArray
    parallel: ParallelProps
    parallelarray: ParallelArray
    param: ParamProps
    paramarray: ParamArray
    raise: RaiseProps
    raisearray: RaiseArray
    script: ScriptProps
    scriptarray: ScriptArray
    scxml: ScxmlProps
    send: SendProps
    sendarray: SendArray
    state: StateProps
    statearray: StateArray
    transition: TransitionProps
    transitionarray: TransitionArray
    transitiontypedatatype: TransitionTypeDatatypeProps
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

cargo: [https://crates.io/crates/scjson]
```bash
cargo install scjson
```

dockerhub: [https://hub.docker.com/r/iraa/scjson]
(Full development environment for all supported languages)
```bash
docker pull iraa/scjson:latest
```


All source code in this directory is released under the BSD\u00A01-Clause license. See [LICENSE](./LICENSE) and [LEGAL.md](./LEGAL.md) for details.
