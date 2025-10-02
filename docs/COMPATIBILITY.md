<p align="center"><img src="../scjson.png" alt="scjson logo" width="200"/></p>

# Converter Compatibility Matrix

Agent Name: documentation-compatibility  
Part of the scjson project.  
Developed by Softoboros Technology Inc.  
Licensed under the BSD 1-Clause License.

This page summarises the current state of cross-language compatibility for the
`scjson` converters. The Python CLI remains the canonical implementation; all
other agents are validated by comparing their output against Python with
`py/uber_test.py`.

Status tiers:

- **Canonical** – serves as the reference implementation.
- **Parity** – passes the tutorial corpus via `uber_test.py` and matches Python
  output after normalisation.
- **Beta** – feature complete for day-to-day usage but pending full parity
  validation; expect occasional mismatches in the long tail of test vectors.
- **Experimental** – minimal support, primarily for exploration or future work.

| Language | Status | Notes |
|----------|--------|-------|
| Python | Canonical | Baseline for all diffs. |
| JavaScript | Parity | Passes tutorial corpus after normalisation. |
| Ruby | Parity | Passes tutorial corpus after normalisation. |
| Rust | Parity | Passes tutorial corpus after normalisation. |
| Java | Parity | Uses the SCION reference runner; passes tutorial corpus after normalisation. |
| Go | Beta | CLI stabilised; parity audit in progress. |
| Swift | Beta | CLI stabilised; parity audit in progress. |
| C# | Beta | CLI stabilised; parity audit in progress. |
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

## Behavioural Reference

Operational behaviour (event execution traces) is validated against SCION. The
Python documentation engine and the Java runner proxy to SCION’s CLI, ensuring
consistent semantics for the canonical examples. See `docs/TODO-ENGINE-PY.md`
for outstanding integration work.
