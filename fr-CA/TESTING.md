<p align="center"><img src="scjson.png" alt="scjson logo" width="200"/></p>

# Guide de test

Ce projet contient des implémentations dans plusieurs langages. Vous trouverez ci-dessous les commandes utilisées pour exécuter les suites de tests automatisés pour chaque module spécifique à un langage.

## Python
```bash
cd py
poetry install
poetry run pytest -q
```

## C#
```bash
cd csharp
# Assurez-vous que le SDK .NET est installé
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
