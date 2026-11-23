"""
Agent Name: executable-order-generation

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Project the CONV order fields and repeatable elseif onto xsdata models.
"""

from pathlib import Path
import json
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
                                "from pydantic import BaseModel, ConfigDict, field_serializer, model_serializer, model_validator")
        source = source.replace("from xsdata_pydantic.fields import field",
                                "from xsdata_pydantic.fields import field\n\nfrom ..execution_order import ScxmlModel, ordered_children")
        source = source.replace("(BaseModel):", "(ScxmlModel):")
        source = source.replace("from pydantic import BaseModel, ", "from pydantic import ")
    for kind in CONTAINERS:
        match = re.search(rf"^class Scxml{kind}Type\b.*?(?=^class |^@dataclass|\Z)", source, re.M | re.S)
        if not match:
            raise ValueError(f"Missing Scxml{kind}Type in {path}")
        block = match.group()
        if is_pydantic:
            addition = (
                '    execution_order: list[str] = field(\n'
                '        default_factory=lambda: None,\n'
                '        metadata={"type": "Ignore"},\n'
                '    )\n\n'
                '    @model_validator(mode="after")\n'
                '    def _validate_execution_order(self):\n'
                '        ordered_children(self)\n'
                '        return self\n\n'
                '    @model_serializer(mode="wrap")\n'
                '    def _serialize_execution_order(self, handler):\n'
                '        data = handler(self)\n'
                '        if self.execution_order is None:\n'
                '            data.pop("execution_order", None)\n'
                '        return data\n\n'
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


def patch_structural_order(path):
    """Generate optional, validated order on the three structural owners."""
    source = path.read_text(encoding="utf-8")
    is_pydantic = "from pydantic import" in source
    if is_pydantic:
        if "from typing import Literal," not in source:
            source = source.replace("from typing import ", "from typing import Literal, ", 1)
        source = re.sub(r"^from \.\.execution_order import .*",
                        "from ..execution_order import ScxmlModel, ordered_children, ordered_regions, ordered_state_children",
                        source, count=1, flags=re.M)
    for owner in ("Parallel", "State", "Scxml"):
        block = re.search(rf"^class Scxml{owner}Type\b.*?(?=^class |^@dataclass|\Z)", source, re.M | re.S)
        if not block:
            raise ValueError(f"Missing Scxml{owner}Type in {path}")
        if owner == "Parallel":
            name, validator, kinds = "region_order", "ordered_regions", '"state", "parallel"'
        else:
            name, validator, kinds = "state_order", "ordered_state_children", '"state", "parallel", "final"'
        if f"    {name}:" in block.group():
            continue
        if is_pydantic:
            addition = f'''    {name}: list[Literal[{kinds}]] = field(
        default_factory=lambda: None, metadata={{"type": "Ignore"}}
    )

    @model_validator(mode="after")
    def _validate_{name}(self):
        {validator}(self)
        return self

    @model_serializer(mode="wrap")
    def _serialize_{name}(self, handler):
        data = handler(self)
        if self.{name} is None:
            data.pop("{name}", None)
        return data'''
        else:
            addition = f'''    {name}: Optional[list[str]] = field(
        default=None, metadata={{"type": "Ignore"}}
    )'''
        source = source[:block.end()].rstrip() + "\n\n" + addition + "\n\n\n" + source[block.end():]
    path.write_text(source, encoding="utf-8", newline="\n")


def patch_schema(path):
    """Project the optional structural-order property without changing unrelated schema fields."""
    from scjson.pydantic import Scxml

    schema = json.loads(path.read_bytes())
    defs = Scxml.model_json_schema()["$defs"]
    for owner, field in (("Parallel", "region_order"), ("State", "state_order"), ("Scxml", "state_order")):
        schema["$defs"][owner]["properties"][field] = defs[owner]["properties"][field]
    schema["properties"]["state_order"] = defs["Scxml"]["properties"]["state_order"]
    path.write_bytes((json.dumps(schema, indent=4) + "\n").encode("utf-8"))


if __name__ == "__main__":
    root = Path(__file__).parent
    if sys.argv[1:] == ["--xsd"]:
        for name in ("scxml-module-core.xsd", "scxml-core-strict.xsd"):
            patch_xsd(root.parent / "xsd" / name)
    elif len(sys.argv) == 3 and sys.argv[1] == "--schema-file":
        patch_schema(Path(sys.argv[2]))
    else:
        for variant in ("dataclasses", "dataclasses_strict", "pydantic", "pydantic_strict"):
            path = root / "scjson" / variant / "generated.py"
            patch(path)
            patch_structural_order(path)
