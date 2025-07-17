# scjson Rust Crate

This directory contains the Rust implementation of **scjson**. It offers a command line tool and supporting library to convert between `.scxml` and `.scjson` files and to validate documents.

## Installation

```bash
cargo install scjson
```

You can also build from this repository:

```bash
cd rust && cargo build --release
```

## Command Line Usage

```bash
scjson json path/to/machine.scxml
scjson xml path/to/machine.scjson
scjson validate path/to/dir -r
```

All source code in this directory is released under the BSD\u00A01-Clause license. See `LICENSE` and `LEGAL.md` for details.
