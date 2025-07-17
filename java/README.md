# scjson Java Package

This directory contains the Java implementation of **scjson** using Maven. It provides a command line interface to convert between `.scxml` and `.scjson` documents and validate them against the shared schema.

## Build

```bash
cd java && mvn package -DskipTests
```

## Command Line Usage

```bash
java -jar target/scjson.jar json path/to/machine.scxml
java -jar target/scjson.jar xml path/to/machine.scjson
java -jar target/scjson.jar validate path/to/dir -r
```

All source code in this directory is released under the BSD\u00A01-Clause license. See `LICENSE` and `LEGAL.md` for details.
