Agent Name: conv-corpus

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

# Focused Conversion Corpus

This corpus contains small SCXML documents for converter parity checks across
maintained language implementations. The fixtures are intentionally separate
from `tests/exec/` and `tests/sweep_corpus/` because many converter surfaces,
such as comments and unresolved XInclude directives, are representation
contracts rather than execution contracts.

Fixtures:

- `help_text_comments.scxml` covers CONV-E/F comment promotion into
  `help_text` and comment emission back to SCXML.
- `inclusion_surface.scxml` covers CONV-H root-reachable inclusion and
  communication fields: `invoke`, nested `scxml` content, `send`, `param`,
  `donedata`, `data.src`, `script.src`, and routing-string preservation.
- `xinclude_preserve.scxml` covers unresolved XInclude preservation through
  extension content. `xinclude_child.xml` is the include target used by
  resolved-mode tests and is not itself a corpus root.
