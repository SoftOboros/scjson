# Changelog — `scjson` (Python)

All notable changes to the Python package will be documented in this file.

The Python package version is independent of the JS, Ruby, Rust, Java, Swift,
Lua, Go, and C# package versions; cross-language work is coordinated through
the top-level [`CHANGELOG.md`](../CHANGELOG.md).

## 0.3.7 — 2026-05-01

### Fixed

- **Engine: `<scxml name="X">` no longer collides with `<state id="X">`.**
  The root activation previously used the document's `name` attribute as its
  identifier (`_build_activation_tree`, `context.py`). When `name` matched a
  state `id`, three things broke at once:
  1. The state-id lookup table (`self.activations`) overwrote one entry with
     the other, so `_enter_target` resolved the colliding name to whichever
     activation was indexed last.
  2. `self.configuration` carried the root id from startup
     (`_from_model: ctx.configuration.add(root_state.id)`), so the colliding
     state appeared "already active" from byte one and `_enter_initial_states`
     short-circuited entries to it.
  3. `_is_user_state` (used by every `_filter_states` callsite, which feeds
     `trace_step`'s `firedTransitions`, `enteredStates`, `exitedStates`, and
     `configuration`) explicitly rejects anything equal to
     `root_activation.id`, silently scrubbing the legitimately-named state
     out of every observable trace output.

  The root activation now uses the sentinel `__scxml_root__`, which cannot
  collide with any user-authored state id (state ids are NCName-shaped per
  XML; double-underscored sentinels are not valid NCNames).

  Charts authored with a `name` attribute matching a top-level state id
  produced empty `firedTransitions` and an empty observable `configuration`
  before this fix, even though the dispatch table itself was correct. The
  failure was silent — no exception, no warning — which is why downstream
  consumers (codegen golden traces, vector verifiers, the Rust/TS runtime
  comparators) all carried the same wrong answer.

### Notes

- This is a **Python-engine-only** fix. The JS/Ruby/Rust/Java/Swift/Lua/Go/C#
  serializers do not implement the execution engine and are unaffected.
- No schema or wire-format change. Existing `.scjson` files remain valid.
- No breaking API change. `DocumentContext.root_activation.id` now returns
  `"__scxml_root__"` instead of `getattr(doc, "name", None) or "anon"`; any
  caller that relied on the old behaviour to recover the chart's `name`
  should read `ctx.doc.name` directly (which was always the source of truth).

## 0.3.6 and earlier

See git history; no per-package changelog was maintained prior to 0.3.7.
