<p align="center"><img src="scjson.png" alt="scjson logo" width="200"/></p>

# Guía de Pruebas

Este proyecto contiene implementaciones en múltiples lenguajes. A continuación se muestran los comandos utilizados para ejecutar las suites de pruebas automatizadas para cada módulo específico del lenguaje.

## Python
```bash
cd py
poetry install
poetry run pytest -q
```

## C#
```bash
cd csharp
# Ensure the .NET SDK is installed
 dotnet test -v minimal
```

## Java
```bash
cd java
mvn test
```

## JavaScript
```bash
cd js
npm install
npm test --silent
```

## Go
```bash
cd go
go test ./...
```

## Rust
```bash
cd rust
cargo test
```

## Swift
```bash
cd swift
swift test
```

## Ruby
```bash
cd ruby
bundle install
bundle exec rspec
```

## Lua
```bash
cd lua
busted tests
```
