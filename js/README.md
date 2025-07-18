# scjson JavaScript Package

This directory contains the JavaScript implementation of **scjson**, a format for representing SCXML state machines in JSON. The package provides a command line interface to convert between `.scxml` and `.scjson` files and to validate documents against the project's schema.

## Installation

```bash
npm install scjson
```

You can also install from a checkout of this repository:

```bash
cd js && npm install
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

### Other Resources
github: [https://github.com/SoftOboros/scjson]
```bash
git clone https://github.com/SoftOboros/scjson.git

git clone git@github.com:SoftOboros/scjson.git

gh repo clone SoftOboros/scjson
```

pypi: [https://www.npmjs.com/package/scjson]
```bash
npm install scjson
```

dockerhub: [https://hub.docker.com/r/iraa/scjson]
(Full development environment for all supported languages)
```bash
docker pull iraa/scjson:latest
```


All source code in this directory is released under the BSD\u00A01-Clause license. See `LICENSE` and `LEGAL.md` for details.
