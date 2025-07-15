# scjson Python Package

This directory contains the Python implementation of **scjson**, a format for representing SCXML state machines in JSON. The package provides a command line interface and utility functions to convert between `.scxml` and `.scjson` files and to validate documents against the project's schema.

## Installation

```bash
pip install scjson
```

You can also install from a checkout of this repository:

```bash
cd py && pip install -e .
```

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

## License

All source code in this directory is released under the BSD&nbsp;1-Clause license. See `LEGAL.md` for details.

