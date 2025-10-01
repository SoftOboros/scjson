# scjson Rust Crate

This directory contains the Rust implementation of **scjson**. It offers a command line tool and supporting library to convert between `.scxml` and `.scjson` files and to validate documents.

For details on how SCXML elements are inferred during conversion see [INFERENCE.md](https://github.com/SoftOboros/scjson/blob/main/INFERENCE.md).


## Installation

```bash
cargo install scjson
```

You can also build from this repository:

```bash
cd rust && cargo build --release
```

# Source Code - Multi-Language Support
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

```bash
scjson json path/to/machine.scxml
scjson xml path/to/machine.scjson
scjson validate path/to/dir -r
```

## Known Issues
None at this time.

Operational conformance testing is performed via [uber_test.py](https://github.com/SoftOboros/scjson/blob/engine/py/uber_test.py)
```bash
/py# python uber_test.py -l javascript 2>&1 | tee test.log
```
Note: [uber_test.py](https://github.com/SoftOboros/scjson/blob/main/py/uber_test.py) applies all scxml files in [Zhornyak's ScxmlEditor-Tutorial](https://alexzhornyak.github.io/ScxmlEditor-Tutorial/) which provides a robest set of scxml test vectors useful for standard compliance verification.  This is the only file in the test suite which fails to verify round-trip.


### Enums
Each enumeration represents a restricted string set used by SCXML. The values
shown below mirror those defined in the SCJSON schema.
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

pypi: [https://pypi.org/project/scjson/]
```bash
pip install scjson
```

dockerhub: [https://hub.docker.com/r/iraa/scjson]
(Full development environment for all supported languages)
```bash
docker pull iraa/scjson:latest
```


All source code in this directory is released under the BSD 1-Clause license. See [LICENSE](./LICENSE) and [LEGAL.md](./LEGAL.md) for details.
