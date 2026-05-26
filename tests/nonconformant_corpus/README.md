Agent Name: nonconformant-corpus

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

# Nonconformant Execution Fixtures

This directory contains charts that are intentionally rejected by the SCJSON
runtime validators. They are regression fixtures for negative tests and should
not be included in `exec_sweep.py` runs over `tests/sweep_corpus/`.

Current fixtures exercise the CONV-H / SCXML finalize restriction that
`<finalize>` must not contain `<send>` or `<raise>` children. The corresponding
tests assert that parsing fails with:

```text
SCXML finalize MUST NOT contain send or raise children
```
