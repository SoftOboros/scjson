Agent Name: exec-tests

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

# Execution Harness Fixtures

This directory contains sample SCXML documents and matching event streams used by
`exec_compare.py`. Each `.scxml` file should have a sibling `.events.jsonl` file
providing one JSON object per line with the event name and optional data.

## Files

- `toggle.scxml` – two-state machine (`idle` ↔ `active`) that increments
  `count` on entry to `active`.
- `toggle.events.jsonl` – event script exercising `start`, `go`, and `reset`.

Feel free to add additional fixtures as the comparison harness grows.

## Reference Runner ([Scion](https://www.npmjs.com/package/scion))

The default reference engine used by `py/exec_compare.py` is a thin wrapper
around the [SCION](https://www.npmjs.com/package/scion) Node implementation.

1. Install dependencies once:

   ```bash
   cd tools/scion-runner
   npm install
   ```

2. Generate a trace directly:

   ```bash
   node scion-trace.cjs -I ../../tests/exec/toggle.scxml \
       -e ../../tests/exec/toggle.events.jsonl \
       -o toggle.scion.trace.jsonl
   ```

3. Compare Python vs [Scion](https://www.npmjs.com/package/scion) (and optionally a secondary engine) using:

   ```bash
   cd ../../py
   python exec_compare.py ../tests/exec/toggle.scxml \
       --events ../tests/exec/toggle.events.jsonl
   ```

Set `SCJSON_SECONDARY_ENGINE_CMD` or `--secondary` to supply an additional
engine (e.g., Apache Commons SCXML) for three-way comparisons.
 EOF
