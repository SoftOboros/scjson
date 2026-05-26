#!/usr/bin/env python3
"""
Agent Name: patch_help_text

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Inject a first-class ``help_text: list[str]`` field into every xsdata-generated
SCJSON element model class. This is the CONV-E (Help Text Schema Surface) patch
defined in ``docs/concepts/SCJSON-CONV-00-CONCEPTS.md`` (CONV-INV-7 / CONV-E).

Why: ``help_text`` is the canonical authoring-metadata field for chart
documentation. It is intentionally separate from ``other_attributes`` so
editors, visualizers, code generators, and assistants do not have to dig
through an open extension bag to find user-facing documentation. CONV-F will
later promote SCXML comments into this field; this patch only exposes the
field on the Python side so the JSON round-trip preserves it.

Applies-to surface (CONV-E): every model class that already carries an
``other_attributes`` field. That set is exactly the SCJSON element families
named in CONV-E (Scxml, State, Parallel, Final, History, Initial, Transition,
Onentry, Onexit, Invoke, Finalize, Datamodel, Data, Donedata, Content, Param,
Assign, Log, Raise, If, Elseif, Else, Foreach, Send, Cancel, Script). The
scalar datatype / enumeration models do not own ``other_attributes`` and so
do not receive ``help_text``.

XML serialization deferral: this patch tags ``help_text`` with xsdata
``metadata={"type": "Ignore"}``. As a result, ``help_text`` is NOT serialized
into SCXML output by either the dataclasses or the pydantic xsdata stack.
That is correct for CONV-E: comment promotion (CONV-F) owns the SCXML side of
the round-trip. JSON ↔ JSON round-trips preserve ``help_text`` because
``model_dump()`` / ``asdict()`` walk the dataclass fields regardless of xsdata
XML metadata.

USAGE::

    python patch_help_text.py --file path/to/generated.py

The patch is idempotent: re-running it adds nothing because the inserted line
is detected before insertion. Patch runs after ``patch_other_attributes_any.py``
in ``gen_models.sh``.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


# The xsdata-generated ``other_attributes`` field appears in two shapes,
# one per generator variant:
#
#   Pydantic (3-line, single metadata dict on the same physical line):
#       other_attributes: dict[str, Any] = field(
#           default_factory=dict, metadata={"type": "Attributes", "namespace": "##other"}
#       )
#
#   Dataclasses (7-line, expanded metadata dict):
#       other_attributes: dict[str, str] = field(
#           default_factory=dict,
#           metadata={
#               "type": "Attributes",
#               "namespace": "##other",
#           },
#       )
#
# Both shapes terminate with ``    )`` on its own line. We anchor the regex on
# the field name through that terminating line and insert ``help_text`` as the
# next sibling field.
_OTHER_ATTRS_BLOCK_RE = re.compile(
    r"(    other_attributes: dict\[str, (?:Any|str)\] = field\("
    r"[^)]*?"
    r"\n    \)\n)",
    re.DOTALL,
)

# The exact replacement we insert. ``metadata={"type": "Ignore"}`` instructs
# xsdata's serializer to skip the field entirely on XML emission, deferring
# comment-promotion semantics to CONV-F.
_HELP_TEXT_FIELD = (
    '    help_text: list[str] = field(\n'
    '        default_factory=list, metadata={"type": "Ignore"}\n'
    '    )\n'
)


def patch_file(path: Path) -> int:
    """Insert ``help_text`` after every ``other_attributes`` field.

    :param path: File to patch.
    :returns: Number of insertions made.
    """
    src = path.read_text()
    if "help_text: list[str]" in src:
        # Already patched; respect idempotency.
        return 0
    new_src, count = _OTHER_ATTRS_BLOCK_RE.subn(
        lambda m: m.group(1) + _HELP_TEXT_FIELD, src
    )
    if count == 0:
        return 0
    path.write_text(new_src)
    return count


def main() -> None:
    """CLI entry point: patch a single generated.py file."""
    parser = argparse.ArgumentParser(
        description="Inject help_text: list[str] into SCJSON element models."
    )
    parser.add_argument(
        "--file", required=True, help="Path to the generated Python model file."
    )
    args = parser.parse_args()
    path = Path(args.file)
    n = patch_file(path)
    print(f"Patched {path}: {n} help_text field(s) inserted")


if __name__ == "__main__":
    main()
