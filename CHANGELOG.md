# Changelog — scjson (cross-language index)

scjson is a multi-language repository. Each implementation tracks its own
release cadence and version number; this file is a navigation index, not a
single version stream.

| Language | Path                  | Latest version  | Per-package log |
|----------|-----------------------|-----------------|------------------|
| Python   | `py/`                 | 0.3.7           | [`py/CHANGELOG.md`](py/CHANGELOG.md) |
| Ruby     | `ruby/`               | 0.3.5           | (in `git log`)   |
| JS       | `js/`                 | 0.3.5           | (in `git log`)   |
| Rust     | `rust/`               | 0.3.3           | (in `git log`)   |
| Java     | `java/`               | 0.3.3-SNAPSHOT  | (in `git log`)   |
| Swift    | `swift/`              | (see swift)     | [`swift/CHANGELOG.md`](swift/CHANGELOG.md) |
| Lua      | `lua/`                | (rockspec)      | (in `git log`)   |
| Go       | `go/`                 | (`go.mod`)      | (in `git log`)   |
| C#       | `csharp/`             | (csproj)        | (in `git log`)   |

## Cross-language entries

### 2026-05-01 — Python 0.3.7 (engine bugfix)

Python-only fix to the execution engine: root activation no longer collides
with state ids when `<scxml name="X">` matches a `<state id="X">`. Other
languages do not implement the engine and are not affected. See
[`py/CHANGELOG.md`](py/CHANGELOG.md) for details.
