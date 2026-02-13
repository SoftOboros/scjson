<p align="center"><img src="scjson.png" alt="scjson logo" width="200"/></p>

# Testing Guide

This project contains implementations across multiple languages. Below are the commands used to run the automated test suites for each language-specific module.

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
