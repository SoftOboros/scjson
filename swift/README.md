# scjson Swift Package

This directory contains the Swift implementation of **scjson**. The package exposes a command line tool that can convert between `.scxml` and `.scjson` and perform validation using the shared schema.

## Installation

```bash
swift build -c release
```

After building, the `scjson` executable will be available in `.build/release`.

## Command Line Usage

```bash
scjson json path/to/machine.scxml
scjson xml path/to/machine.scjson
scjson validate path/to/dir -r
```

All source code in this directory is released under the BSD\u00A01-Clause license. See `LICENSE` and `LEGAL.md` for details.
