<p align="center"><img src="https://raw.githubusercontent.com/SoftOboros/scjson/main/scjson.png" alt="scjson logo" width="200"/></p>

# scjson Swift Package

This directory contains the Swift implementation of **scjson**. The package exposes a reusable library (`SCJSONKit`) and a command line tool that can convert between `.scxml` and `.scjson` and perform validation using the shared schema.

## Installation

```bash
swift build -c release
```

After building, the `scjson` executable will be available in `.build/release`.

## Library Usage

Add `SCJSONKit` as a dependency in your `Package.swift` and import the models:

```swift
import SCJSONKit

let doc = ScjsonDocument()
```

## Command Line Usage

```bash
scjson json path/to/machine.scxml
scjson xml path/to/machine.scjson
scjson validate path/to/dir -r
```

All source code in this directory is released under the BSD 1-Clause license. See [LICENSE](./LICENSE) and [LEGAL.md](./LEGAL.md) for details.
