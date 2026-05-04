#!/usr/bin/env python3
"""
Agent Name: patch_other_attributes_any

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Loosen the typing of ``other_attributes`` from ``dict[str, str]`` to
``dict[str, Any]`` in xsdata-generated pydantic models.

Why: SCXML's ``xs:anyAttribute`` is XML-only string-valued, but the JSON
serialisation (scjson) is regularly used by tools that store typed metadata
in foreign-namespace attributes — e.g. Infinity State stores integer layout
coordinates (``POSITION_X``, ``POSITION_Y``) and nested dicts (codegen
options) on ``other_attributes``. Restricting to ``str`` rejects those
documents at pydantic-validation time even though they round-trip cleanly
through JSON. Loosening to ``Any`` matches what JSON can express.

Apply this patch only to the pydantic variants. The dataclasses variants
must keep ``dict[str, str]`` because xsdata's XML serializer rejects any
non-string value type on ``Attributes``-typed fields (xs:anyAttribute is
XML-only). Tools that need typed metadata in ``other_attributes`` work in
JSON; XML round-trips coerce values back to strings, which existing
consumers (e.g. ``frontend/src/app/components/istate/istateUtils.ts``
``coerceNumber``) already handle.

USAGE::
    python patch_other_attributes_any.py --file path/to/generated.py
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


_TYPING_IMPORT_RE = re.compile(r"^from typing import (.+)$", re.MULTILINE)
_OTHER_ATTRS_RE = re.compile(r"\bother_attributes:\s*dict\[str,\s*str\]")


def _ensure_any_in_typing_import(source: str) -> str:
    """Return ``source`` with ``Any`` present in the ``from typing import`` line.

    If no ``from typing import`` line exists, prepend one.
    """
    match = _TYPING_IMPORT_RE.search(source)
    if match is None:
        return "from typing import Any\n" + source
    names = [n.strip() for n in match.group(1).split(",")]
    if "Any" in names:
        return source
    names.append("Any")
    new_line = "from typing import " + ", ".join(sorted(set(names)))
    return source[: match.start()] + new_line + source[match.end():]


def patch_file(path: Path) -> int:
    """Rewrite ``other_attributes: dict[str, str]`` to ``dict[str, Any]``.

    :param path: File to patch.
    :returns: Number of substitutions made.
    """
    src = path.read_text()
    new_src, count = _OTHER_ATTRS_RE.subn(
        "other_attributes: dict[str, Any]", src
    )
    if count == 0:
        return 0
    new_src = _ensure_any_in_typing_import(new_src)
    path.write_text(new_src)
    return count


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Loosen other_attributes typing to dict[str, Any]."
    )
    parser.add_argument(
        "--file", required=True, help="Path to the generated Python model file."
    )
    args = parser.parse_args()
    path = Path(args.file)
    n = patch_file(path)
    print(f"✅ Patched {path}: {n} other_attributes occurrence(s) loosened to dict[str, Any]")


if __name__ == "__main__":
    main()
