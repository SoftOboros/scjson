#!/usr/bin/env python3
"""
Agent Name: patch_finalize_restrictions

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Apply the CONV-H finalize restriction after xsdata generation.

The bundled SCXML strict XSD carries an assertion that ``<finalize>`` must not
contain ``<send>`` or ``<raise>``. xsdata does not project that XSD 1.1
assertion into the generated pydantic models or JSON Schema, so this patch adds
the equivalent validation surface explicitly.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


_IMPORT_RE = re.compile(r"from pydantic import ([^\n]+)")
_FINALIZE_HELP_TEXT_RE = re.compile(
    r"(class ScxmlFinalizeType\(BaseModel\):.*?"
    r"    help_text: list\[str\] = field\(\n"
    r"        default_factory=list, metadata=\{\"type\": \"Ignore\"\}\n"
    r"    \)\n)",
    re.DOTALL,
)
_VALIDATOR = '''

    @model_validator(mode="after")
    def _reject_send_raise_in_finalize(self):
        """Reject non-conformant ``send``/``raise`` children in ``finalize``."""
        if self.send or self.raise_value:
            raise ValueError(
                "SCXML finalize MUST NOT contain send or raise children"
            )
        return self
'''


def patch_pydantic_model(path: Path) -> int:
    """Patch a generated pydantic model file.

    :param path: Generated pydantic ``generated.py`` file.
    :returns: Number of logical patches applied.
    """
    src = path.read_text()
    count = 0
    new_src = src

    import_match = _IMPORT_RE.search(new_src)
    if import_match:
        names = [part.strip() for part in import_match.group(1).split(",")]
        if "model_validator" not in names:
            names.append("model_validator")
            new_src = _IMPORT_RE.sub(
                "from pydantic import " + ", ".join(names),
                new_src,
                count=1,
            )
            count += 1

    if "_reject_send_raise_in_finalize" not in new_src:
        new_src, validator_count = _FINALIZE_HELP_TEXT_RE.subn(
            lambda match: match.group(1) + _VALIDATOR,
            new_src,
            count=1,
        )
        count += validator_count

    if new_src != src:
        path.write_text(new_src)
    return count


def _finalize_no_send_raise_allof() -> list[dict]:
    """Return the JSON Schema fragments that reject non-empty send/raise."""
    return [
        {
            "not": {
                "required": ["send"],
                "properties": {"send": {"type": "array", "minItems": 1}},
            }
        },
        {
            "not": {
                "required": ["raise_value"],
                "properties": {
                    "raise_value": {"type": "array", "minItems": 1}
                },
            }
        },
    ]


def patch_schema(path: Path) -> int:
    """Patch one ``scjson.schema.json`` file.

    :param path: Schema file to patch.
    :returns: ``1`` when the file changed, otherwise ``0``.
    """
    schema = json.loads(path.read_text())
    finalize = schema.get("$defs", {}).get("Finalize")
    if not isinstance(finalize, dict):
        raise ValueError(f"{path} does not contain $defs.Finalize")

    expected = _finalize_no_send_raise_allof()
    if finalize.get("allOf") == expected:
        return 0
    finalize["allOf"] = expected
    path.write_text(json.dumps(schema, indent=4) + "\n")
    return 1


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Patch CONV-H finalize restrictions into generated files."
    )
    parser.add_argument("--pydantic-file", action="append", default=[])
    parser.add_argument("--schema-file", action="append", default=[])
    args = parser.parse_args()

    changed = 0
    for filename in args.pydantic_file:
        changed += patch_pydantic_model(Path(filename))
    for filename in args.schema_file:
        changed += patch_schema(Path(filename))
    print(f"Patched finalize restrictions: {changed} change(s)")


if __name__ == "__main__":
    main()
