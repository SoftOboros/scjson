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
java -jar target/scjson.jar run path/to/machine.scxml -e events.json -o trace.json
```

### Java Proxy Setup

The Java implementation uses Maven. If your environment requires an HTTP/HTTPS
proxy, create `~/.m2/settings.xml` with proxy settings before building:

```xml
<settings>
  <proxies>
    <proxy>
      <id>internal-proxy</id>
      <active>true</active>
      <protocol>http</protocol>
      <host>proxy</host>
      <port>8080</port>
      <nonProxyHosts>localhost|127.0.0.1</nonProxyHosts>s
    </proxy>
    <proxy>
      <id>internal-proxy-https</id>
      <active>true</active>
      <protocol>https</protocol>
      <host>proxy</host>
      <port>8080</port>
      <nonProxyHosts>localhost|127.0.0.1</nonProxyHosts>
    </proxy>
  </proxies>
</settings>
```

Build the module with:

```bash
cd java && mvn clean install -DskipTests -B && cd ..
```

#### Running SCXML documents
You can execute a state machine using the CLI:
```bash
java -jar target/scjson.jar run examples/example.scxml -e examples/events.json -o trace.json
```
This uses `ScxmlRunner` under the hood and requires the Apache Commons SCXML library. Ensure Maven can download dependencies or has them cached locally.

All source code in this directory is released under the BSD\u00A01-Clause license. See `LICENSE` and `LEGAL.md` for details.
