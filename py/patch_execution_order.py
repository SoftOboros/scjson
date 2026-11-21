"""
Agent Name: executable-order-generation

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Project the CONV executable-order field and repeatable elseif onto xsdata models.
"""

from pathlib import Path
import re
import sys


CONTAINERS = ("Onentry", "Onexit", "Transition", "Finalize", "Foreach", "If")


def patch_xsd(path):
    source = path.read_text(encoding="utf-8")
    one = 'ref="scxml.if.elseif.mix" minOccurs="0" maxOccurs="1"'
    many = one.replace('maxOccurs="1"', 'maxOccurs="unbounded"')
    if many not in source:
        if source.count(one) != 1:
            raise ValueError(f"Missing elseif cardinality in {path}")
        path.write_text(source.replace(one, many), encoding="utf-8", newline="\n")


def patch(path):
    source = path.read_text(encoding="utf-8")
    if "    execution_order:" in source:
        return
    is_pydantic = "from pydantic import" in source
    if is_pydantic:
        source = source.replace("from pydantic import BaseModel, ConfigDict, model_validator",
                                "from pydantic import BaseModel, ConfigDict, field_serializer, model_validator")
        source = source.replace("from xsdata_pydantic.fields import field",
                                "from xsdata_pydantic.fields import field\n\nfrom ..execution_order import ordered_children")
    for kind in CONTAINERS:
        match = re.search(rf"^class Scxml{kind}Type\b.*?(?=^class |^@dataclass|\Z)", source, re.M | re.S)
        if not match:
            raise ValueError(f"Missing Scxml{kind}Type in {path}")
        block = match.group()
        if is_pydantic:
            addition = (
                '    execution_order: list[str] = field(\n'
                '        default_factory=lambda: None, exclude_if=lambda value: value is None,\n'
                '        metadata={"type": "Ignore"},\n'
                '    )\n\n'
                '    @model_validator(mode="after")\n'
                '    def _validate_execution_order(self):\n'
                '        ordered_children(self)\n'
                '        return self\n\n'
            )
        else:
            addition = (
                '    execution_order: Optional[list[str]] = field(\n'
                '        default=None, metadata={"type": "Ignore"}\n'
                '    )\n'
            )
        # Append dataclass fields after existing ones to preserve positional callers.
        block = block.rstrip() + "\n\n" + addition + "\n\n"
        if kind == "If":
            if is_pydantic:
                block = block.replace("elseif: Optional[Elseif]", "elseif: Optional[Elseif | list[Elseif]]")
                block = block.replace("elseif: list[Elseif] = field(\n        default_factory=list,",
                                      "elseif: Optional[Elseif | list[Elseif]] = field(\n        default=None,")
                block = block.rstrip() + (
                    '\n\n    @field_serializer("elseif", mode="wrap")\n'
                    '    def _serialize_elseif(self, value, handler):\n'
                    '        payload = handler(value)\n'
                    '        return payload[0] if isinstance(payload, list) and len(payload) == 1 else payload\n\n\n'
                )
            else:
                block = block.replace("elseif: Optional[Elseif] = field(\n        default=None,",
                                      "elseif: list[Elseif] = field(\n        default_factory=list,")
        source = source[:match.start()] + block + source[match.end():]
    path.write_text(source, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    root = Path(__file__).parent
    if sys.argv[1:] == ["--xsd"]:
        for name in ("scxml-module-core.xsd", "scxml-core-strict.xsd"):
            patch_xsd(root.parent / "xsd" / name)
    else:
        for variant in ("dataclasses", "dataclasses_strict", "pydantic", "pydantic_strict"):
            patch(root / "scjson" / variant / "generated.py")
