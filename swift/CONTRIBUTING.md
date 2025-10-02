# Contributing to scjson Swift

Thanks for helping improve the Swift implementation of **scjson**. This package mirrors the behaviour of the Python canonical implementation, so please keep the following workflow in mind when contributing.

## Development Environment

- Install Swift 5.9 or newer.
- From the repository root run `swift build` to compile the package and `swift test` for the test suite.
- For CLI compatibility checks you can execute `python3 py/uber_test.py -l swift` (requires the Python environment described in the main project).

## Code Style

- All public types must include documentation comments and the standard project header block.
- Keep generated sources in `Sources/SCJSONKit/ScjsonTypes.swift` intact; update the Jinja templates under `py/scjson/templates/` if you need to regenerate code.
- Prefer value semantics (`struct`, `enum`) and mark new APIs as `public` only when they are part of the documented surface.

## Submitting Changes

1. Run `swift build` and `swift test` locally.
2. If the JSON schema changes, regenerate language bindings with `PYTHONPATH=py python3 -m scjson.cli swift -o swift/Sources/SCJSONKit`.
3. Update `CHANGELOG.md` with a short description of your change.
4. Open a pull request that links to any relevant GitHub issues and explains the validation you performed.

Thank you for keeping the Swift agent in sync with the wider **scjson** ecosystem!
