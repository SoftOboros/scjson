```markdown
<p align="center"><img src="../scjson.png" alt="scjson logo" width="200"/></p>

# Converter Compatibility Matrix

Agent Name: documentation-compatibility
Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

This page summarizes the current state of cross-language compatibility for the
`scjson` converters. The Python CLI remains the canonical implementation; all
other agents are validated by comparing their output against Python with
`py/uber_test.py`.

Status tiers:

- **Canonical** – serves as the reference implementation.
- **Parity** – passes the tutorial corpus via `uber_test.py` and matches Python
  output after normalization.
- **Beta** – feature complete for day-to-day usage but pending full parity
  validation; expect occasional mismatches in the long tail of test vectors.
- **Experimental** – minimal support, primarily for exploration or future work.

| Language | Status | Notes |
|----------|--------|-------|
| Python | Canonical | Baseline for all diffs. |
| JavaScript | Parity | Passes tutorial corpus after normalization. |
| Ruby | Parity | Passes tutorial corpus after normalization. |
| Rust | Parity | Passes tutorial corpus after normalization. |
| Java | Parity | Uses the [SCION](https://www.npmjs.com/package/scion) reference runner; passes tutorial corpus after normalization. |
| Go | Beta | CLI stabilized; parity audit in progress. |
| Swift | Beta | CLI stabilized; parity audit in progress. |
| C# | Beta | CLI stabilized; parity audit in progress. |
| Lua | Experimental | Minimal subset converter. |

## Test Harness

Run the compatibility sweep locally with:

```bash
cd py
python uber_test.py
```

You can target a single implementation with `-l` (for example `-l java`). The
harness prints a summary of mismatching files and writes detailed output under
`uber_out/` for inspection.

## Behavioral Reference

Operational behavior (event execution traces) is validated against [SCION](https://www.npmjs.com/package/scion). The
Python documentation engine and the Java runner proxy to [SCION](https://www.npmjs.com/package/scion)’s CLI, ensuring
consistent semantics for the canonical examples. See `docs/TODO-ENGINE-PY.md`
for outstanding integration work.

See also
- User guide (Python engine): `docs/ENGINE-PY.md`
- Architecture & in-depth reference (Python): `py/ENGINE-PY-DETAILS.md`

## Python Engine vs [SCION](https://www.npmjs.com/package/scion) — Feature Support

The table below summarizes the current Python engine feature coverage relative to the [SCION](https://www.npmjs.com/package/scion) (Node) reference and highlights any nuanced differences that matter for compatibility.

| Area | Python Engine | [SCION](https://www.npmjs.com/package/scion) (Node) | Notes / Compatibility |
|------|---------------|--------------|-----------------------|
| Execution algorithm | Macro/microstep with quiescence | Same | Equivalent semantics |
| Transition selection | Document order; multi-token, `*`, `error.*` | Same | Equivalent |
| Condition evaluation | Sandboxed Python datamodel (`safe_eval`) | JS datamodel | Equivalent for tests; non-boolean cond → `error.execution` in Python |
| Executable content | assign, log, raise, if/elseif/else, foreach, send, cancel | Same | Equivalent; `script` is a warning/no-op in Python ([SCION](https://www.npmjs.com/package/scion) executes JS) |
| `script` blocks | No-op (warn) | Executes JS | Expected difference; tests avoid requiring `script` side effects |
| History | Shallow + deep | Same | Equivalent; deep restores exact descendant leaves |
| Parallel completion | Region done → parent done | Same | Equivalent ordering |
| Done events | `done.state.*`, `done.invoke*` | Same | Equivalent; see invoke ordering notes |
| Error events | `error.execution` (push-front) + generic `error` alias; `error.communication` (tail) | Emits error types | Python adds generic `error` alias for charts listening to `error.*` |
| Event matching | Exact, `*`, `error.*` prefix | Same | Equivalent |
| Timers | Deterministic via `advance_time` | Runtime timers | Python supports control tokens `{ "advance_time": N }` in event streams |
| External send targets | Not supported (emit `error.communication`) | Supports SCXML I/O processors | Expected difference; external processors out of scope |
| Invoke types | `mock:immediate`, `mock:record`, `mock:deferred`, `scxml`/`scjson` child | SCXML child, external processors | Equivalent for child machines; external processors out of scope |
| Parent↔child I/O | `#_parent`, `#_child`/`#_invokedChild`, `#_<id>` | Same | Equivalent |
| Finalize semantics | Runs in invoking state; `_event` = `{name,data,invokeid}` | Same | Equivalent |
| Invoke ordering | Modes: `tolerant` (default), `strict`, `scion` | N/A | `scion` mode aligns `done.invoke` ordering with [SCION](https://www.npmjs.com/package/scion) (generic before id-specific, push-front) |
| Step-0 normalization | Compare tooling strips step-0 noise | N/A | Reduces diffs due to initial transitions visibility |

---

Note on time-step emission
- The Python engine emits a synthetic trace step by default when an `{"advance_time": N}` control token is processed so that timer-driven changes are visible even without a subsequent external event. Use `--no-emit-time-steps` to suppress these steps when strict parity with tools that do not emit them is desired.

---

Back to
- User guide: `docs/ENGINE-PY.md`
- Architecture & reference: `py/ENGINE-PY-DETAILS.md`
- Project overview: `README.md`
## Navigation

- This page: Compatibility Matrix
  - [Status Tiers](#status-tiers)
  - [Test Harness](#test-harness)
  - [Behavioral Reference](#behavioral-reference)
  - [Python Engine vs SCION — Feature Support](#python-engine-vs-scion--feature-support) ([SCION](https://www.npmjs.com/package/scion))
- Python Engine User Guide: `docs/ENGINE-PY.md`
- Python Architecture & Reference: `py/ENGINE-PY-DETAILS.md`
- Project Overview: `README.md`
```
