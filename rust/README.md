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


All source code in this directory is released under the BSD\u00A01-Clause license. See [LICENSE](./LICENSE) and [LEGAL.md](./LEGAL.md) for details.
