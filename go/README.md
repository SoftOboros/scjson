# scjson Go Package

This directory contains the Go implementation of **scjson**, a format for representing SCXML state machines in JSON. The command line tool can convert between `.scxml` and `.scjson` files and validate documents using the shared schema.

## Installation

```bash
go install github.com/softoboros/scjson/go@latest
```

You can also build from this repository:

```bash
cd go && go build
```

## Command Line Usage

```bash
scjson json path/to/machine.scxml
scjson xml path/to/machine.scjson
scjson validate path/to/dir -r
```

All source code in this directory is released under the BSD\u00A01-Clause license. See `LICENSE` and `LEGAL.md` for details.
