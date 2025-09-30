# SCXML-style execution engine with names:

### Layers
What you create when the interpreter starts	Lifetime	Typical contents

Document (global)	Document Context (sometimes “Data Model”)	Entire run	• all top-level <data> elements
• immutable constants
• a pointer to the current Root Activation (see next row)
• event queue / scheduler handle

Root state machine	Root Activation Record	Entire run	• ID of the root <scxml> element
• current configuration (set of active states)
• history snapshots, global timers, etc.
Every state / parallel that becomes active	State 

Activation Record (“local context”, “frame”, etc.)	From onentry to finishing onexit	• reference to parent activation
• runtime flags: isFinal, isParallel, hasHistory …
• any <data> scoped to the state
• temporary variables created by assign/var actions
• running timers raised by this state

## Why this layering works

### Isolation of transient data

A State Activation Record vanishes when the state exits, so any scratch variables or timers don’t leak upward. That matches SCXML’s expectation that local <data> is recreated on each re-entry.

### Hierarchy mirrors control flow

Because activations nest exactly like <state> / <parallel> nesting, algorithms like “is ancestor active?”, history restoration, and final-state detection become simple tree traversals.
Final-state bookkeeping

Mark an activation as final when its <final> child enters; propagate this upward so that a <parallel> completes only when all its children’s activations are in the final state.

### Low-level efficiency
If you implement activations as lightweight objects (or struct handles from an object pool), creating/destroying them on each entry/exit is cheap and keeps per-instance memory proportional to the active configuration, not the whole chart.

### A couple of implementation hints
Keep a “current configuration” set alongside the activation tree; most algorithms (microstep, legal transitions, conflict resolution) are set operations over the configuration.

Event queues live at the document or root level. Deliver events downward by walking the activation tree until someone consumes them.

History: store, on exit, the IDs (or pointers) of the child activations that were active. On history restore, recreate activations for those IDs instead of evaluating <initial>.

Global vs. local data: let state-level <data> shadow document-level entries; look-ups walk up the activation chain.

## Expression Sandbox & Trust Model

Python expressions inside `<assign>`, `<log>`, and transition `cond` attributes
are evaluated with a sandbox powered by [`py-sandboxed`](https://pypi.org/project/py-sandboxed/).
Only a curated subset of pure builtins (e.g. `abs`, `len`, `sum`, `sorted`) and
the `math` module are exposed by default; attempts to import modules, access
double-underscore attributes, or call `eval`/`exec` raise a
``SafeEvaluationError`` and fall back to the literal expression string when
possible. The helper `In(stateId)` function is injected automatically so charts
can query active states without opening the sandbox.

For environments that fully trust the input chart you can opt out of the
sandbox by passing `--unsafe-eval` to `scjson engine-trace` (or by constructing
`DocumentContext` with `allow_unsafe_eval=True`). This re-enables CPython’s
native `eval`, matching the previous engine behaviour.

## Canonical JSON Ingestion

Even when the CLI receives SCXML, the runtime first converts it into its
canonical SCJSON form and executes against the JSON tree. This guarantees the
same inference rules apply regardless of the source format and lets the engine
preserve authoring order for executable content by reading directly from the
normalised JSON structure.

## Reference Compatibility Guidance

The Python runtime treats [`scion-core`](https://github.com/ReactiveSystems/scion-core)
as the behavioural reference for SCXML execution:

- **Active upstream** – scion-core tracks the latest W3C spec and applies
  bug-fixes faster than the legacy Apache Commons engine.
- **Canonical semantics** – it resolves long-standing ambiguities around
  document order, parallel completion, and datamodel scoping in a
  widely-adopted way. Matching scion-core gives us predictable behaviour across
  platforms.
- **Scriptable runner** – the repository ships `tools/scion-runner/scion-trace.cjs`
  which is a thin wrapper exposing the same JSONL trace format as the Python
  engine. The comparison harness can therefore diff traces without bespoke
  adapters.

### Using the reference runner

1. Install Node.js 18+ and run `npm ci` inside `tools/scion-runner/`.
2. Invoke the runner directly or via `SCJSON_REF_ENGINE_CMD`, e.g.:

   ```bash
   export SCJSON_REF_ENGINE_CMD="node tools/scion-runner/scion-trace.cjs"
   python py/exec_compare.py examples/toggle.scxml --events tests/exec/toggle.events.jsonl
   ```

3. The comparison harness normalises traces before diffing; divergences surface
   in the first mismatching step and retain the raw artefacts for inspection.

### Dealing with known deltas

scion-core implements the ECMA datamodel by default. Our engine currently
supports the Python datamodel only; charts that rely on ECMA-specific helpers
should be converted to equivalent Python expressions before comparison. For
tests that still depend on `ecmascript` set `--unsafe-eval` temporarily or guard
them behind feature flags.

The reference run should precede new feature work. When extending the Python
runtime, add regression charts to `tests/exec/` and update the harness so the
new scenario is exercised against scion-core.

### Executable Content Status

- `<assign>`, `<log>`, and `<raise>` execute in authoring order and feed into the
  JSON trace.
- `<if>`/`<elseif>`/`<else>` and `<foreach>` respect document order by consulting
  the canonical JSON structure rather than regenerated dataclasses.
- `<send>` enqueues internal events (including `<param>` and `namelist`
  payloads); delayed sends are queued via the built-in scheduler and can be
  triggered in tests with `DocumentContext.advance_time(seconds)`. `<cancel>`
  removes pending internal sends by ID. Textual `<content>` blocks are
  normalised into JSON objects before validation so downstream consumers
  see a consistent structure, and nested markup is serialized into dictionaries
  with `qname`/`text`/`children` keys for compatibility with scion-core payloads.
- Transition bodies execute between exit and entry:
  executable content attached to a `<transition>` is run after the exit-set is
  processed and before the entry-set is taken, matching spec-friendly ordering.
- Targetless transitions are treated as internal: they do not exit any state.
  This is required for handlers such as `done.state.region` that update the
  datamodel but keep the configuration intact until a subsequent transition.
- External `<send>` targets are not executed; the runtime enqueues
  `error.communication` and skips delivery.
- `<script>` blocks are not executed (no-op with a warning).

### Invoke & Finalize (Scaffolding)

- The engine supports basic `<invoke>` semantics sufficient for testing:
  - On state entry (after `onentry` and initial processing), invocations listed
    under the state are started via a pluggable `InvokeRegistry`.
  - On state exit (before `onexit`), any active invocations for the state are
    canceled; their `<finalize>` blocks run in the invoking state's scope.
  - A mock registry ships with two handler types:
    - `mock:immediate`: completes immediately upon start and calls the done
      callback with the initial payload; the engine runs `<finalize>` and enqueues
      `done.invoke.<id>` with the payload.
    - `mock:record`: a no-op handler that records events forwarded via `send`.
  - Payload materialization mirrors `<send>`: collects `<param>`, `namelist`, and
    `<content>` into a dictionary available to the handler and as `_event.data`
    during `<finalize>`.
  - `idlocation` is respected; when `id` is not provided a UUID is generated.
  - `typeexpr` and `srcexpr` are evaluated in the state's scope when present.
  - `autoforward="true"` forwards external events (excluding `__*`, `error.*`,
    `done.state.*`, `done.invoke.*`) to the active handler via `handler.send(name, data)`.

Limitations:
- Full SCXML invoke semantics (processor coupling, nested machines, error
  handling parity) are not implemented. The current behavior is designed to
  unblock engine testing and can be extended behind the `InvokeRegistry`.

### Finalization and Done Events

- Entering a `<final>` child of a compound state immediately enqueues
  `done.state.<parentId>` after executing the `<final>`'s `onentry` actions.
- If the `<final>` element contains `<donedata>`:
  - `<content>` sets the full value of `_event.data` for the done event.
  - Otherwise `<param>` pairs become a dictionary assigned to `_event.data`.
- For `<parallel>`, the parent is considered complete only once all regions are
  final; at that point the engine enqueues `done.state.<parallelId>`.

### History (Shallow and Deep)

- Shallow history stores the set of active immediate children upon exit; on
  restoration, those children are re-entered using normal initial processing.
- Deep history stores the set of active descendant leaves under the parent; on
  restoration, the engine enters the exact path from the history's parent down
  to each saved leaf, without following `<initial>` of intermediate nodes.
  This yields return to the precise pre-exit nested configuration.

### Errors

- Conditions that fail to evaluate, or that produce non-boolean results, enqueue
  `error.execution` and evaluate to false.
- `<foreach>` evaluation failures also enqueue `error.execution` and iterate
  over an empty sequence.
- `<assign>` expression failures enqueue `error.execution` and store the raw
  expression string as the value.
- External `<send>` targets enqueue `error.communication` and are skipped.

### Tutorial Sweep & Skip List

The regression harness `py/uber_test.py::test_python_engine_executes_python_charts`
detects the Python engine at runtime, loads each tutorial chart with
`datamodel="python"`, and aggregates failures with their trace diffs.
Charts that depend on unsupported features are captured in
`ENGINE_KNOWN_UNSUPPORTED` (see `py/uber_test.py:44-58`); update that list
whenever new capabilities land so genuine regressions remain visible.
Warnings emitted during execution are preserved in the failure summary to
highlight gaps such as external targets or `<script>` bodies.

When adding coverage for new behaviours (e.g., delayed `<send>` cancellation),
prefer focused unit tests alongside the sweep and remove skip entries once the
scenario passes end-to-end.
