from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Optional

__NAMESPACE__ = "http://www.w3.org/2005/07/scxml"


class AssignTypeDatatype(Enum):
    """The assign type that allows for precise manipulation of the datamodel
    location.

    Types are:
    replacechildren (default),
    firstchild, lastchild,
    previoussibling, nextsibling,
    replace, delete,
    addattribute
    """

    REPLACECHILDREN = "replacechildren"
    FIRSTCHILD = "firstchild"
    LASTCHILD = "lastchild"
    PREVIOUSSIBLING = "previoussibling"
    NEXTSIBLING = "nextsibling"
    REPLACE = "replace"
    DELETE = "delete"
    ADDATTRIBUTE = "addattribute"


class BindingDatatype(Enum):
    """
    The binding type in use for the SCXML document.
    """

    EARLY = "early"
    LATE = "late"


class BooleanDatatype(Enum):
    """Boolean: true or false only"""

    TRUE = "true"
    FALSE = "false"


class ExmodeDatatype(Enum):
    """
    Describes the processor execution mode for this document, being either "lax" or
    "strict".
    """

    LAX = "lax"
    STRICT = "strict"


class HistoryTypeDatatype(Enum):
    SHALLOW = "shallow"
    DEEP = "deep"


class TransitionTypeDatatype(Enum):
    """
    The type of the transition i.e. internal or external.
    """

    INTERNAL = "internal"
    EXTERNAL = "external"


@dataclass
class ScxmlCancelType:
    class Meta:
        name = "scxml.cancel.type"

    other_element: list[object] = field(
        default_factory=list,
        metadata={
            "type": "Wildcard",
            "namespace": "##other",
        },
    )
    sendid: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    sendidexpr: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    other_attributes: dict[str, str] = field(
        default_factory=dict,
        metadata={
            "type": "Attributes",
            "namespace": "##other",
        },
    )


@dataclass
class ScxmlContentType:
    class Meta:
        name = "scxml.content.type"

    other_attributes: dict[str, str] = field(
        default_factory=dict,
        metadata={
            "type": "Attributes",
            "namespace": "##other",
        },
    )
    expr: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    content: list[object] = field(
        default_factory=list,
        metadata={
            "type": "Wildcard",
            "namespace": "##any",
            "mixed": True,
        },
    )


@dataclass
class ScxmlDataType:
    class Meta:
        name = "scxml.data.type"

    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    src: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    expr: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    other_attributes: dict[str, str] = field(
        default_factory=dict,
        metadata={
            "type": "Attributes",
            "namespace": "##other",
        },
    )
    content: list[object] = field(
        default_factory=list,
        metadata={
            "type": "Wildcard",
            "namespace": "##any",
            "mixed": True,
        },
    )


@dataclass
class ScxmlElseType:
    class Meta:
        name = "scxml.else.type"

    other_attributes: dict[str, str] = field(
        default_factory=dict,
        metadata={
            "type": "Attributes",
            "namespace": "##other",
        },
    )


@dataclass
class ScxmlElseifType:
    class Meta:
        name = "scxml.elseif.type"

    cond: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    other_attributes: dict[str, str] = field(
        default_factory=dict,
        metadata={
            "type": "Attributes",
            "namespace": "##other",
        },
    )


@dataclass
class ScxmlLogType:
    class Meta:
        name = "scxml.log.type"

    other_element: list[object] = field(
        default_factory=list,
        metadata={
            "type": "Wildcard",
            "namespace": "##other",
        },
    )
    label: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    expr: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    other_attributes: dict[str, str] = field(
        default_factory=dict,
        metadata={
            "type": "Attributes",
            "namespace": "##other",
        },
    )


@dataclass
class ScxmlParamType:
    class Meta:
        name = "scxml.param.type"

    other_element: list[object] = field(
        default_factory=list,
        metadata={
            "type": "Wildcard",
            "namespace": "##other",
        },
    )
    name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    expr: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    location: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    other_attributes: dict[str, str] = field(
        default_factory=dict,
        metadata={
            "type": "Attributes",
            "namespace": "##other",
        },
    )


@dataclass
class ScxmlRaiseType:
    class Meta:
        name = "scxml.raise.type"

    event: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    other_attributes: dict[str, str] = field(
        default_factory=dict,
        metadata={
            "type": "Attributes",
            "namespace": "##other",
        },
    )


@dataclass
class ScxmlScriptType:
    class Meta:
        name = "scxml.script.type"

    src: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    other_attributes: dict[str, str] = field(
        default_factory=dict,
        metadata={
            "type": "Attributes",
            "namespace": "##other",
        },
    )
    content: list[object] = field(
        default_factory=list,
        metadata={
            "type": "Wildcard",
            "namespace": "##any",
            "mixed": True,
        },
    )


@dataclass
class Cancel(ScxmlCancelType):
    class Meta:
        name = "cancel"
        namespace = "http://www.w3.org/2005/07/scxml"


@dataclass
class Content(ScxmlContentType):
    class Meta:
        name = "content"
        namespace = "http://www.w3.org/2005/07/scxml"


@dataclass
class Data(ScxmlDataType):
    class Meta:
        name = "data"
        namespace = "http://www.w3.org/2005/07/scxml"


@dataclass
class Else(ScxmlElseType):
    class Meta:
        name = "else"
        namespace = "http://www.w3.org/2005/07/scxml"


@dataclass
class Elseif(ScxmlElseifType):
    class Meta:
        name = "elseif"
        namespace = "http://www.w3.org/2005/07/scxml"


@dataclass
class Log(ScxmlLogType):
    class Meta:
        name = "log"
        namespace = "http://www.w3.org/2005/07/scxml"


@dataclass
class Param(ScxmlParamType):
    class Meta:
        name = "param"
        namespace = "http://www.w3.org/2005/07/scxml"


@dataclass
class Raise(ScxmlRaiseType):
    class Meta:
        name = "raise"
        namespace = "http://www.w3.org/2005/07/scxml"


@dataclass
class Script(ScxmlScriptType):
    class Meta:
        name = "script"
        namespace = "http://www.w3.org/2005/07/scxml"


@dataclass
class ScxmlAssignType:
    class Meta:
        name = "scxml.assign.type"

    location: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    expr: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    type_value: AssignTypeDatatype = field(
        default=AssignTypeDatatype.REPLACECHILDREN,
        metadata={
            "name": "type",
            "type": "Attribute",
        },
    )
    attr: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    other_attributes: dict[str, str] = field(
        default_factory=dict,
        metadata={
            "type": "Attributes",
            "namespace": "##other",
        },
    )
    content: list[object] = field(
        default_factory=list,
        metadata={
            "type": "Wildcard",
            "namespace": "##any",
            "mixed": True,
        },
    )


@dataclass
class Assign(ScxmlAssignType):
    class Meta:
        name = "assign"
        namespace = "http://www.w3.org/2005/07/scxml"


@dataclass
class ScxmlDatamodelType:
    class Meta:
        name = "scxml.datamodel.type"

    data: list[Data] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    other_element: list[object] = field(
        default_factory=list,
        metadata={
            "type": "Wildcard",
            "namespace": "##other",
        },
    )
    other_attributes: dict[str, str] = field(
        default_factory=dict,
        metadata={
            "type": "Attributes",
            "namespace": "##other",
        },
    )


@dataclass
class ScxmlDonedataType:
    class Meta:
        name = "scxml.donedata.type"

    content: Optional[Content] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    param: list[Param] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    other_attributes: dict[str, str] = field(
        default_factory=dict,
        metadata={
            "type": "Attributes",
            "namespace": "##other",
        },
    )


@dataclass
class ScxmlSendType:
    class Meta:
        name = "scxml.send.type"

    content: list[Content] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    param: list[Param] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    other_element: list[object] = field(
        default_factory=list,
        metadata={
            "type": "Wildcard",
            "namespace": "##other",
        },
    )
    event: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "pattern": r"(\i|\d|\-)+(\.(\i|\d|\-)+)*",
        },
    )
    eventexpr: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    target: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    targetexpr: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    type_value: str = field(
        default="scxml",
        metadata={
            "name": "type",
            "type": "Attribute",
        },
    )
    typeexpr: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    idlocation: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    delay: str = field(
        default="0s",
        metadata={
            "type": "Attribute",
            "pattern": r"\d*(\.\d+)?(ms|s|m|h|d)",
        },
    )
    delayexpr: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    namelist: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    other_attributes: dict[str, str] = field(
        default_factory=dict,
        metadata={
            "type": "Attributes",
            "namespace": "##other",
        },
    )


@dataclass
class Datamodel(ScxmlDatamodelType):
    class Meta:
        name = "datamodel"
        namespace = "http://www.w3.org/2005/07/scxml"


@dataclass
class Donedata(ScxmlDonedataType):
    class Meta:
        name = "donedata"
        namespace = "http://www.w3.org/2005/07/scxml"


@dataclass
class Send(ScxmlSendType):
    class Meta:
        name = "send"
        namespace = "http://www.w3.org/2005/07/scxml"


@dataclass
class ScxmlIfType:
    class Meta:
        name = "scxml.if.type"

    other_element: list[object] = field(
        default_factory=list,
        metadata={
            "type": "Wildcard",
            "namespace": "##other",
        },
    )
    raise_value: list[Raise] = field(
        default_factory=list,
        metadata={
            "name": "raise",
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    if_value: list["If"] = field(
        default_factory=list,
        metadata={
            "name": "if",
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    foreach: list["Foreach"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    send: list[Send] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    script: list[Script] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    assign: list[Assign] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    log: list[Log] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    cancel: list[Cancel] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    elseif: Optional[Elseif] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    else_value: Optional[Else] = field(
        default=None,
        metadata={
            "name": "else",
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    cond: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    other_attributes: dict[str, str] = field(
        default_factory=dict,
        metadata={
            "type": "Attributes",
            "namespace": "##other",
        },
    )


@dataclass
class If(ScxmlIfType):
    class Meta:
        name = "if"
        namespace = "http://www.w3.org/2005/07/scxml"


@dataclass
class ScxmlForeachType:
    class Meta:
        name = "scxml.foreach.type"

    other_element: list[object] = field(
        default_factory=list,
        metadata={
            "type": "Wildcard",
            "namespace": "##other",
        },
    )
    raise_value: list[Raise] = field(
        default_factory=list,
        metadata={
            "name": "raise",
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    if_value: list[If] = field(
        default_factory=list,
        metadata={
            "name": "if",
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    foreach: list["Foreach"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    send: list[Send] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    script: list[Script] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    assign: list[Assign] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    log: list[Log] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    cancel: list[Cancel] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    array: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    item: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    index: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    other_attributes: dict[str, str] = field(
        default_factory=dict,
        metadata={
            "type": "Attributes",
            "namespace": "##other",
        },
    )


@dataclass
class Foreach(ScxmlForeachType):
    class Meta:
        name = "foreach"
        namespace = "http://www.w3.org/2005/07/scxml"


@dataclass
class ScxmlFinalizeType:
    class Meta:
        name = "scxml.finalize.type"

    other_element: list[object] = field(
        default_factory=list,
        metadata={
            "type": "Wildcard",
            "namespace": "##other",
        },
    )
    raise_value: list[Raise] = field(
        default_factory=list,
        metadata={
            "name": "raise",
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    if_value: list[If] = field(
        default_factory=list,
        metadata={
            "name": "if",
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    foreach: list[Foreach] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    send: list[Send] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    script: list[Script] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    assign: list[Assign] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    log: list[Log] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    cancel: list[Cancel] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    other_attributes: dict[str, str] = field(
        default_factory=dict,
        metadata={
            "type": "Attributes",
            "namespace": "##other",
        },
    )


@dataclass
class ScxmlOnentryType:
    class Meta:
        name = "scxml.onentry.type"

    other_element: list[object] = field(
        default_factory=list,
        metadata={
            "type": "Wildcard",
            "namespace": "##other",
        },
    )
    raise_value: list[Raise] = field(
        default_factory=list,
        metadata={
            "name": "raise",
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    if_value: list[If] = field(
        default_factory=list,
        metadata={
            "name": "if",
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    foreach: list[Foreach] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    send: list[Send] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    script: list[Script] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    assign: list[Assign] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    log: list[Log] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    cancel: list[Cancel] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    other_attributes: dict[str, str] = field(
        default_factory=dict,
        metadata={
            "type": "Attributes",
            "namespace": "##other",
        },
    )


@dataclass
class ScxmlOnexitType:
    class Meta:
        name = "scxml.onexit.type"

    other_element: list[object] = field(
        default_factory=list,
        metadata={
            "type": "Wildcard",
            "namespace": "##other",
        },
    )
    raise_value: list[Raise] = field(
        default_factory=list,
        metadata={
            "name": "raise",
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    if_value: list[If] = field(
        default_factory=list,
        metadata={
            "name": "if",
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    foreach: list[Foreach] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    send: list[Send] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    script: list[Script] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    assign: list[Assign] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    log: list[Log] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    cancel: list[Cancel] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    other_attributes: dict[str, str] = field(
        default_factory=dict,
        metadata={
            "type": "Attributes",
            "namespace": "##other",
        },
    )


@dataclass
class ScxmlTransitionType:
    class Meta:
        name = "scxml.transition.type"

    other_element: list[object] = field(
        default_factory=list,
        metadata={
            "type": "Wildcard",
            "namespace": "##other",
        },
    )
    raise_value: list[Raise] = field(
        default_factory=list,
        metadata={
            "name": "raise",
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    if_value: list[If] = field(
        default_factory=list,
        metadata={
            "name": "if",
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    foreach: list[Foreach] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    send: list[Send] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    script: list[Script] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    assign: list[Assign] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    log: list[Log] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    cancel: list[Cancel] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    event: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "pattern": r"\.?\*|(\i|\d|\-)+(\.(\i|\d|\-)+)*(\.\*)?(\s(\i|\d|\-)+(\.(\i|\d|\-)+)*(\.\*)?)*",
        },
    )
    cond: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    target: list[str] = field(
        default_factory=list,
        metadata={
            "type": "Attribute",
            "tokens": True,
        },
    )
    type_value: Optional[TransitionTypeDatatype] = field(
        default=None,
        metadata={
            "name": "type",
            "type": "Attribute",
        },
    )
    other_attributes: dict[str, str] = field(
        default_factory=dict,
        metadata={
            "type": "Attributes",
            "namespace": "##other",
        },
    )


@dataclass
class Finalize(ScxmlFinalizeType):
    class Meta:
        name = "finalize"
        namespace = "http://www.w3.org/2005/07/scxml"


@dataclass
class Onentry(ScxmlOnentryType):
    class Meta:
        name = "onentry"
        namespace = "http://www.w3.org/2005/07/scxml"


@dataclass
class Onexit(ScxmlOnexitType):
    class Meta:
        name = "onexit"
        namespace = "http://www.w3.org/2005/07/scxml"


@dataclass
class Transition(ScxmlTransitionType):
    class Meta:
        name = "transition"
        namespace = "http://www.w3.org/2005/07/scxml"


@dataclass
class ScxmlFinalType:
    class Meta:
        name = "scxml.final.type"

    onentry: list[Onentry] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    onexit: list[Onexit] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    donedata: list[Donedata] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    other_element: list[object] = field(
        default_factory=list,
        metadata={
            "type": "Wildcard",
            "namespace": "##other",
        },
    )
    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    other_attributes: dict[str, str] = field(
        default_factory=dict,
        metadata={
            "type": "Attributes",
            "namespace": "##other",
        },
    )


@dataclass
class ScxmlHistoryType:
    class Meta:
        name = "scxml.history.type"

    other_element: list[object] = field(
        default_factory=list,
        metadata={
            "type": "Wildcard",
            "namespace": "##other",
        },
    )
    transition: Optional[Transition] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
            "required": True,
        },
    )
    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    type_value: Optional[HistoryTypeDatatype] = field(
        default=None,
        metadata={
            "name": "type",
            "type": "Attribute",
        },
    )
    other_attributes: dict[str, str] = field(
        default_factory=dict,
        metadata={
            "type": "Attributes",
            "namespace": "##other",
        },
    )


@dataclass
class ScxmlInitialType:
    class Meta:
        name = "scxml.initial.type"

    other_element: list[object] = field(
        default_factory=list,
        metadata={
            "type": "Wildcard",
            "namespace": "##other",
        },
    )
    transition: Optional[Transition] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
            "required": True,
        },
    )
    other_attributes: dict[str, str] = field(
        default_factory=dict,
        metadata={
            "type": "Attributes",
            "namespace": "##other",
        },
    )


@dataclass
class ScxmlInvokeType:
    class Meta:
        name = "scxml.invoke.type"

    content: list[Content] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    param: list[Param] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    finalize: list[Finalize] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    other_element: list[object] = field(
        default_factory=list,
        metadata={
            "type": "Wildcard",
            "namespace": "##other",
        },
    )
    type_value: str = field(
        default="scxml",
        metadata={
            "name": "type",
            "type": "Attribute",
        },
    )
    typeexpr: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    src: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    srcexpr: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    idlocation: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    namelist: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    autoforward: BooleanDatatype = field(
        default=BooleanDatatype.FALSE,
        metadata={
            "type": "Attribute",
        },
    )
    other_attributes: dict[str, str] = field(
        default_factory=dict,
        metadata={
            "type": "Attributes",
            "namespace": "##other",
        },
    )


@dataclass
class Final(ScxmlFinalType):
    class Meta:
        name = "final"
        namespace = "http://www.w3.org/2005/07/scxml"


@dataclass
class History(ScxmlHistoryType):
    class Meta:
        name = "history"
        namespace = "http://www.w3.org/2005/07/scxml"


@dataclass
class Initial(ScxmlInitialType):
    class Meta:
        name = "initial"
        namespace = "http://www.w3.org/2005/07/scxml"


@dataclass
class Invoke(ScxmlInvokeType):
    class Meta:
        name = "invoke"
        namespace = "http://www.w3.org/2005/07/scxml"


@dataclass
class ScxmlStateType:
    class Meta:
        name = "scxml.state.type"

    onentry: list[Onentry] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    onexit: list[Onexit] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    transition: list[Transition] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    initial: list[Initial] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    state: list["State"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    parallel: list["Parallel"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    final: list[Final] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    history: list[History] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    datamodel: list[Datamodel] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    invoke: list[Invoke] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    other_element: list[object] = field(
        default_factory=list,
        metadata={
            "type": "Wildcard",
            "namespace": "##other",
        },
    )
    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    initial_attribute: list[str] = field(
        default_factory=list,
        metadata={
            "name": "initial",
            "type": "Attribute",
            "tokens": True,
        },
    )
    other_attributes: dict[str, str] = field(
        default_factory=dict,
        metadata={
            "type": "Attributes",
            "namespace": "##other",
        },
    )


@dataclass
class State(ScxmlStateType):
    class Meta:
        name = "state"
        namespace = "http://www.w3.org/2005/07/scxml"


@dataclass
class ScxmlParallelType:
    class Meta:
        name = "scxml.parallel.type"

    onentry: list[Onentry] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    onexit: list[Onexit] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    transition: list[Transition] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    state: list[State] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    parallel: list["Parallel"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    history: list[History] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    datamodel: list[Datamodel] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    invoke: list[Invoke] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    other_element: list[object] = field(
        default_factory=list,
        metadata={
            "type": "Wildcard",
            "namespace": "##other",
        },
    )
    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    other_attributes: dict[str, str] = field(
        default_factory=dict,
        metadata={
            "type": "Attributes",
            "namespace": "##other",
        },
    )


@dataclass
class Parallel(ScxmlParallelType):
    class Meta:
        name = "parallel"
        namespace = "http://www.w3.org/2005/07/scxml"


@dataclass
class ScxmlScxmlType:
    class Meta:
        name = "scxml.scxml.type"

    state: list[State] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    parallel: list[Parallel] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    final: list[Final] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    datamodel: list[Datamodel] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    script: list[Script] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    other_element: list[object] = field(
        default_factory=list,
        metadata={
            "type": "Wildcard",
            "namespace": "##other",
        },
    )
    initial: list[str] = field(
        default_factory=list,
        metadata={
            "type": "Attribute",
            "tokens": True,
        },
    )
    name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    version: Decimal = field(
        init=False,
        default=Decimal("1.0"),
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    datamodel_attribute: str = field(
        default="null",
        metadata={
            "name": "datamodel",
            "type": "Attribute",
        },
    )
    binding: Optional[BindingDatatype] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    exmode: Optional[ExmodeDatatype] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    other_attributes: dict[str, str] = field(
        default_factory=dict,
        metadata={
            "type": "Attributes",
            "namespace": "##other",
        },
    )


@dataclass
class Scxml(ScxmlScxmlType):
    class Meta:
        name = "scxml"
        namespace = "http://www.w3.org/2005/07/scxml"
