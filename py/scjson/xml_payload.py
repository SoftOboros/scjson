"""The JSON representation of an XML wildcard element in mixed SCXML content.

Agent Name: python-mixed-payload

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.
"""

from __future__ import annotations

from typing import Annotated, TypeVar

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field


class XmlPayloadElement(BaseModel):
    """Preserve an extension element's qualified name, attributes and mixed text."""

    model_config = ConfigDict(extra="forbid")
    qname: str
    text: str | None = None
    tail: str | None = None
    children: list[XmlPayloadElement] = Field(default_factory=list)
    attributes: dict[str, str] = Field(default_factory=dict)


def _exclude_markup(value):
    if isinstance(value, dict) and "qname" in value:
        raise ValueError("A qualified XML element must use the XML payload representation.")
    return value


_Chart = TypeVar("_Chart")
NestedChart = Annotated[
    _Chart, BeforeValidator(_exclude_markup), Field(json_schema_extra={"not": {"required": ["qname"]}})
]
