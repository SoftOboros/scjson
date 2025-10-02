# ``SCJSONKit``

Gain programmatic access to canonical SCXML ⇄ SCJSON conversions, models, and utilities from Swift.

## Overview

``SCJSONKit`` exposes a `ScjsonCodable` protocol alongside the generated ``ScjsonDocument`` data structures, letting you decode, inspect, and emit SCJSON directly inside Swift applications. The package also ships with a command-line tool for batch conversion and validation that shares the same implementation pipeline.

## Topics

### Core Types

- ``ScjsonDocument``
- ``JSONValue``
- ``ScjsonCodable``

### Supporting Enumerations

- ``AssignType``
- ``TransitionTypeDatatypeProps``
- ``ScjsonKind``

