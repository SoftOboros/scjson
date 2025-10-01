<p align="center"><img src="../scjson.png" alt="scjson logo" width="200"/></p>

# scjson Ruby Gem

This directory contains the Ruby implementation of **scjson**. The gem provides a command line tool and library functions to convert between `.scxml` and `.scjson` files.

## Installation

```bash
gem install scjson
```

You can also install from a local checkout:

```bash
cd ruby && gem build scjson.gemspec && gem install scjson-*.gem
```

## Command Line Usage

```bash
scjson json path/to/machine.scxml
scjson xml path/to/machine.scjson
scjson validate path/to/dir -r
```

All source code in this directory is released under the BSD 1-Clause license. See [LICENSE](./LICENSE) and [LEGAL.md](./LEGAL.md) for details.
