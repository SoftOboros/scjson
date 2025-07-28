from decimal import Decimal
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from xsdata_pydantic.fields import field

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
    """type of `<history>` state: `shallow` or `deep`."""

    SHALLOW = "shallow"
    DEEP = "deep"


class TransitionTypeDatatype(Enum):
    """
    The type of the transition i.e. internal or external.
    """

    INTERNAL = "internal"
    EXTERNAL = "external"


class ScxmlCancelType(BaseModel):

    class Meta:
        name = "scxml.cancel.type"

    model_config = ConfigDict(defer_build=True)
    other_element: list[object] = field(
        default_factory=list, metadata={"type": "Wildcard", "namespace": "##other"}
    )
    sendid: Optional[str] = field(default=None, metadata={"type": "Attribute"})
    sendidexpr: Optional[str] = field(default=None, metadata={"type": "Attribute"})
    other_attributes: dict[str, str] = field(
        default_factory=dict, metadata={"type": "Attributes", "namespace": "##other"}
    )


class ScxmlContentType(BaseModel):
    content: Optional[List["Scxml"]] = None
    expr: Optional[str] = None
    other_attributes: dict[str, str] = field(
        default_factory=dict, title="Other Attributes"
    )

    class Meta:
        name = "scxml.content.type"

    model_config = ConfigDict(defer_build=True)


class ScxmlDataType(BaseModel):

    class Meta:
        name = "scxml.data.type"

    model_config = ConfigDict(defer_build=True)
    id: str = field(metadata={"type": "Attribute", "required": True})
    src: Optional[str] = field(default=None, metadata={"type": "Attribute"})
    expr: Optional[str] = field(default=None, metadata={"type": "Attribute"})
    other_attributes: dict[str, str] = field(
        default_factory=dict, metadata={"type": "Attributes", "namespace": "##other"}
    )
    content: list[object] = field(
        default_factory=list,
        metadata={"type": "Wildcard", "namespace": "##any", "mixed": True},
    )


class ScxmlElseType(BaseModel):

    class Meta:
        name = "scxml.else.type"

    model_config = ConfigDict(defer_build=True)
    other_attributes: dict[str, str] = field(
        default_factory=dict, metadata={"type": "Attributes", "namespace": "##other"}
    )


class ScxmlElseifType(BaseModel):

    class Meta:
        name = "scxml.elseif.type"

    model_config = ConfigDict(defer_build=True)
    cond: str = field(metadata={"type": "Attribute", "required": True})
    other_attributes: dict[str, str] = field(
        default_factory=dict, metadata={"type": "Attributes", "namespace": "##other"}
    )


class ScxmlLogType(BaseModel):

    class Meta:
        name = "scxml.log.type"

    model_config = ConfigDict(defer_build=True)
    other_element: list[object] = field(
        default_factory=list, metadata={"type": "Wildcard", "namespace": "##other"}
    )
    label: Optional[str] = field(default=None, metadata={"type": "Attribute"})
    expr: Optional[str] = field(default=None, metadata={"type": "Attribute"})
    other_attributes: dict[str, str] = field(
        default_factory=dict, metadata={"type": "Attributes", "namespace": "##other"}
    )


class ScxmlParamType(BaseModel):

    class Meta:
        name = "scxml.param.type"

    model_config = ConfigDict(defer_build=True)
    other_element: list[object] = field(
        default_factory=list, metadata={"type": "Wildcard", "namespace": "##other"}
    )
    name: str = field(metadata={"type": "Attribute", "required": True})
    expr: Optional[str] = field(default=None, metadata={"type": "Attribute"})
    location: Optional[str] = field(default=None, metadata={"type": "Attribute"})
    other_attributes: dict[str, str] = field(
        default_factory=dict, metadata={"type": "Attributes", "namespace": "##other"}
    )


class ScxmlRaiseType(BaseModel):

    class Meta:
        name = "scxml.raise.type"

    model_config = ConfigDict(defer_build=True)
    event: str = field(metadata={"type": "Attribute", "required": True})
    other_attributes: dict[str, str] = field(
        default_factory=dict, metadata={"type": "Attributes", "namespace": "##other"}
    )


class ScxmlScriptType(BaseModel):

    class Meta:
        name = "scxml.script.type"

    model_config = ConfigDict(defer_build=True)
    src: Optional[str] = field(default=None, metadata={"type": "Attribute"})
    other_attributes: dict[str, str] = field(
        default_factory=dict, metadata={"type": "Attributes", "namespace": "##other"}
    )
    content: list[object] = field(
        default_factory=list,
        metadata={"type": "Wildcard", "namespace": "##any", "mixed": True},
    )


class Cancel(ScxmlCancelType):
    """cancel a pending `<send>` operation."""

    class Meta:
        name = "cancel"
        namespace = "http://www.w3.org/2005/07/scxml"

    model_config = ConfigDict(defer_build=True)


class Content(ScxmlContentType):
    """inline payload used by `<send>` and `<invoke>`."""

    class Meta:
        name = "content"
        namespace = "http://www.w3.org/2005/07/scxml"

    model_config = ConfigDict(defer_build=True)


class Data(ScxmlDataType):
    """represents a single datamodel variable."""

    class Meta:
        name = "data"
        namespace = "http://www.w3.org/2005/07/scxml"

    model_config = ConfigDict(defer_build=True)


class Else(ScxmlElseType):
    """fallback branch for `<if>` conditions."""

    class Meta:
        name = "else"
        namespace = "http://www.w3.org/2005/07/scxml"

    model_config = ConfigDict(defer_build=True)


class Elseif(ScxmlElseifType):
    """conditional branch following an `<if>`."""

    class Meta:
        name = "elseif"
        namespace = "http://www.w3.org/2005/07/scxml"

    model_config = ConfigDict(defer_build=True)


class Log(ScxmlLogType):
    """diagnostic output statement."""

    class Meta:
        name = "log"
        namespace = "http://www.w3.org/2005/07/scxml"

    model_config = ConfigDict(defer_build=True)


class Param(ScxmlParamType):
    """parameter passed to `<invoke>` or `<send>`."""

    class Meta:
        name = "param"
        namespace = "http://www.w3.org/2005/07/scxml"

    model_config = ConfigDict(defer_build=True)


class Raise(ScxmlRaiseType):
    """raise an internal event."""

    class Meta:
        name = "raise"
        namespace = "http://www.w3.org/2005/07/scxml"

    model_config = ConfigDict(defer_build=True)


class Script(ScxmlScriptType):
    """inline executable script."""

    class Meta:
        name = "script"
        namespace = "http://www.w3.org/2005/07/scxml"

    model_config = ConfigDict(defer_build=True)


class ScxmlAssignType(BaseModel):

    class Meta:
        name = "scxml.assign.type"

    model_config = ConfigDict(defer_build=True)
    location: str = field(metadata={"type": "Attribute", "required": True})
    expr: Optional[str] = field(default=None, metadata={"type": "Attribute"})
    type_value: AssignTypeDatatype = field(
        default=AssignTypeDatatype.REPLACECHILDREN,
        metadata={"name": "type", "type": "Attribute"},
    )
    attr: Optional[str] = field(default=None, metadata={"type": "Attribute"})
    other_attributes: dict[str, str] = field(
        default_factory=dict, metadata={"type": "Attributes", "namespace": "##other"}
    )
    content: list[object] = field(
        default_factory=list,
        metadata={"type": "Wildcard", "namespace": "##any", "mixed": True},
    )


class Assign(ScxmlAssignType):
    """update a datamodel location with an expression or value."""

    class Meta:
        name = "assign"
        namespace = "http://www.w3.org/2005/07/scxml"

    model_config = ConfigDict(defer_build=True)


class ScxmlDatamodelType(BaseModel):

    class Meta:
        name = "scxml.datamodel.type"

    model_config = ConfigDict(defer_build=True)
    data: list[Data] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    other_element: list[object] = field(
        default_factory=list, metadata={"type": "Wildcard", "namespace": "##other"}
    )
    other_attributes: dict[str, str] = field(
        default_factory=dict, metadata={"type": "Attributes", "namespace": "##other"}
    )


class ScxmlDonedataType(BaseModel):

    class Meta:
        name = "scxml.donedata.type"

    model_config = ConfigDict(defer_build=True)
    content: Optional[Content] = field(
        default=None,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    param: list[Param] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    other_element: list[object] = field(
        default_factory=list, metadata={"type": "Wildcard", "namespace": "##other"}
    )
    other_attributes: dict[str, str] = field(
        default_factory=dict, metadata={"type": "Attributes", "namespace": "##other"}
    )


class ScxmlSendType(BaseModel):

    class Meta:
        name = "scxml.send.type"

    model_config = ConfigDict(defer_build=True)
    content: list[Content] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    param: list[Param] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    other_element: list[object] = field(
        default_factory=list, metadata={"type": "Wildcard", "namespace": "##other"}
    )
    event: Optional[str] = field(
        default=None,
        metadata={"type": "Attribute", "pattern": "(\\i|\\d|\\-)+(\\.(\\i|\\d|\\-)+)*"},
    )
    eventexpr: Optional[str] = field(default=None, metadata={"type": "Attribute"})
    target: Optional[str] = field(default=None, metadata={"type": "Attribute"})
    targetexpr: Optional[str] = field(default=None, metadata={"type": "Attribute"})
    type_value: str = field(
        default="scxml", metadata={"name": "type", "type": "Attribute"}
    )
    typeexpr: Optional[str] = field(default=None, metadata={"type": "Attribute"})
    id: Optional[str] = field(default=None, metadata={"type": "Attribute"})
    idlocation: Optional[str] = field(default=None, metadata={"type": "Attribute"})
    delay: str = field(
        default="0s",
        metadata={"type": "Attribute", "pattern": "\\d*(\\.\\d+)?(ms|s|m|h|d)"},
    )
    delayexpr: Optional[str] = field(default=None, metadata={"type": "Attribute"})
    namelist: Optional[str] = field(default=None, metadata={"type": "Attribute"})
    other_attributes: dict[str, str] = field(
        default_factory=dict, metadata={"type": "Attributes", "namespace": "##other"}
    )


class Datamodel(ScxmlDatamodelType):
    """container for one or more `<data>` elements."""

    class Meta:
        name = "datamodel"
        namespace = "http://www.w3.org/2005/07/scxml"

    model_config = ConfigDict(defer_build=True)


class Donedata(ScxmlDonedataType):
    """payload returned when a `<final>` state is reached."""

    class Meta:
        name = "donedata"
        namespace = "http://www.w3.org/2005/07/scxml"

    model_config = ConfigDict(defer_build=True)


class Send(ScxmlSendType):
    """dispatch an external event."""

    class Meta:
        name = "send"
        namespace = "http://www.w3.org/2005/07/scxml"

    model_config = ConfigDict(defer_build=True)


class ScxmlIfType(BaseModel):

    class Meta:
        name = "scxml.if.type"

    model_config = ConfigDict(defer_build=True)
    other_element: list[object] = field(
        default_factory=list, metadata={"type": "Wildcard", "namespace": "##other"}
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
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    send: list[Send] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    script: list[Script] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    assign: list[Assign] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    log: list[Log] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    cancel: list[Cancel] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    elseif: Optional[Elseif] = field(
        default=None,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    else_value: Optional[Else] = field(
        default=None,
        metadata={
            "name": "else",
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
        },
    )
    cond: str = field(metadata={"type": "Attribute", "required": True})
    other_attributes: dict[str, str] = field(
        default_factory=dict, metadata={"type": "Attributes", "namespace": "##other"}
    )


class If(ScxmlIfType):
    """conditional execution block."""

    class Meta:
        name = "if"
        namespace = "http://www.w3.org/2005/07/scxml"

    model_config = ConfigDict(defer_build=True)


class ScxmlForeachType(BaseModel):

    class Meta:
        name = "scxml.foreach.type"

    model_config = ConfigDict(defer_build=True)
    other_element: list[object] = field(
        default_factory=list, metadata={"type": "Wildcard", "namespace": "##other"}
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
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    send: list[Send] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    script: list[Script] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    assign: list[Assign] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    log: list[Log] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    cancel: list[Cancel] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    array: str = field(metadata={"type": "Attribute", "required": True})
    item: str = field(metadata={"type": "Attribute", "required": True})
    index: Optional[str] = field(default=None, metadata={"type": "Attribute"})
    other_attributes: dict[str, str] = field(
        default_factory=dict, metadata={"type": "Attributes", "namespace": "##other"}
    )


class Foreach(ScxmlForeachType):
    """iterate over items within executable content."""

    class Meta:
        name = "foreach"
        namespace = "http://www.w3.org/2005/07/scxml"

    model_config = ConfigDict(defer_build=True)


class ScxmlFinalizeType(BaseModel):

    class Meta:
        name = "scxml.finalize.type"

    model_config = ConfigDict(defer_build=True)
    other_element: list[object] = field(
        default_factory=list, metadata={"type": "Wildcard", "namespace": "##other"}
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
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    send: list[Send] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    script: list[Script] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    assign: list[Assign] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    log: list[Log] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    cancel: list[Cancel] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    other_attributes: dict[str, str] = field(
        default_factory=dict, metadata={"type": "Attributes", "namespace": "##other"}
    )


class ScxmlOnentryType(BaseModel):

    class Meta:
        name = "scxml.onentry.type"

    model_config = ConfigDict(defer_build=True)
    other_element: list[object] = field(
        default_factory=list, metadata={"type": "Wildcard", "namespace": "##other"}
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
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    send: list[Send] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    script: list[Script] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    assign: list[Assign] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    log: list[Log] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    cancel: list[Cancel] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    other_attributes: dict[str, str] = field(
        default_factory=dict, metadata={"type": "Attributes", "namespace": "##other"}
    )


class ScxmlOnexitType(BaseModel):

    class Meta:
        name = "scxml.onexit.type"

    model_config = ConfigDict(defer_build=True)
    other_element: list[object] = field(
        default_factory=list, metadata={"type": "Wildcard", "namespace": "##other"}
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
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    send: list[Send] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    script: list[Script] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    assign: list[Assign] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    log: list[Log] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    cancel: list[Cancel] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    other_attributes: dict[str, str] = field(
        default_factory=dict, metadata={"type": "Attributes", "namespace": "##other"}
    )


class ScxmlTransitionType(BaseModel):

    class Meta:
        name = "scxml.transition.type"

    model_config = ConfigDict(defer_build=True)
    other_element: list[object] = field(
        default_factory=list, metadata={"type": "Wildcard", "namespace": "##other"}
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
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    send: list[Send] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    script: list[Script] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    assign: list[Assign] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    log: list[Log] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    cancel: list[Cancel] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    event: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "pattern": "\\.?\\*|(\\i|\\d|\\-)+(\\.(\\i|\\d|\\-)+)*(\\.\\*)?(\\s(\\i|\\d|\\-)+(\\.(\\i|\\d|\\-)+)*(\\.\\*)?)*",
        },
    )
    cond: Optional[str] = field(default=None, metadata={"type": "Attribute"})
    target: list[str] = field(
        default_factory=list, metadata={"type": "Attribute", "tokens": True}
    )
    type_value: Optional[TransitionTypeDatatype] = field(
        default=None, metadata={"name": "type", "type": "Attribute"}
    )
    other_attributes: dict[str, str] = field(
        default_factory=dict, metadata={"type": "Attributes", "namespace": "##other"}
    )


class Finalize(ScxmlFinalizeType):
    """executed after an `<invoke>` completes."""

    class Meta:
        name = "finalize"
        namespace = "http://www.w3.org/2005/07/scxml"

    model_config = ConfigDict(defer_build=True)


class Onentry(ScxmlOnentryType):
    """actions performed when entering a state."""

    class Meta:
        name = "onentry"
        namespace = "http://www.w3.org/2005/07/scxml"

    model_config = ConfigDict(defer_build=True)


class Onexit(ScxmlOnexitType):
    """actions performed when leaving a state."""

    class Meta:
        name = "onexit"
        namespace = "http://www.w3.org/2005/07/scxml"

    model_config = ConfigDict(defer_build=True)


class Transition(ScxmlTransitionType):
    """edge between states triggered by events."""

    class Meta:
        name = "transition"
        namespace = "http://www.w3.org/2005/07/scxml"

    model_config = ConfigDict(defer_build=True)


class ScxmlFinalType(BaseModel):

    class Meta:
        name = "scxml.final.type"

    model_config = ConfigDict(defer_build=True)
    onentry: list[Onentry] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    onexit: list[Onexit] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    donedata: list[Donedata] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    other_element: list[object] = field(
        default_factory=list, metadata={"type": "Wildcard", "namespace": "##other"}
    )
    id: Optional[str] = field(default=None, metadata={"type": "Attribute"})
    other_attributes: dict[str, str] = field(
        default_factory=dict, metadata={"type": "Attributes", "namespace": "##other"}
    )


class ScxmlHistoryType(BaseModel):

    class Meta:
        name = "scxml.history.type"

    model_config = ConfigDict(defer_build=True)
    other_element: list[object] = field(
        default_factory=list, metadata={"type": "Wildcard", "namespace": "##other"}
    )
    transition: Transition = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
            "required": True,
        }
    )
    id: Optional[str] = field(default=None, metadata={"type": "Attribute"})
    type_value: Optional[HistoryTypeDatatype] = field(
        default=None, metadata={"name": "type", "type": "Attribute"}
    )
    other_attributes: dict[str, str] = field(
        default_factory=dict, metadata={"type": "Attributes", "namespace": "##other"}
    )


class ScxmlInitialType(BaseModel):

    class Meta:
        name = "scxml.initial.type"

    model_config = ConfigDict(defer_build=True)
    other_element: list[object] = field(
        default_factory=list, metadata={"type": "Wildcard", "namespace": "##other"}
    )
    transition: Transition = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.w3.org/2005/07/scxml",
            "required": True,
        }
    )
    other_attributes: dict[str, str] = field(
        default_factory=dict, metadata={"type": "Attributes", "namespace": "##other"}
    )


class ScxmlInvokeType(BaseModel):

    class Meta:
        name = "scxml.invoke.type"

    model_config = ConfigDict(defer_build=True)
    content: list[Content] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    param: list[Param] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    finalize: list[Finalize] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    other_element: list[object] = field(
        default_factory=list, metadata={"type": "Wildcard", "namespace": "##other"}
    )
    type_value: str = field(
        default="scxml", metadata={"name": "type", "type": "Attribute"}
    )
    typeexpr: Optional[str] = field(default=None, metadata={"type": "Attribute"})
    src: Optional[str] = field(default=None, metadata={"type": "Attribute"})
    srcexpr: Optional[str] = field(default=None, metadata={"type": "Attribute"})
    id: Optional[str] = field(default=None, metadata={"type": "Attribute"})
    idlocation: Optional[str] = field(default=None, metadata={"type": "Attribute"})
    namelist: Optional[str] = field(default=None, metadata={"type": "Attribute"})
    autoforward: BooleanDatatype = field(
        default=BooleanDatatype.FALSE, metadata={"type": "Attribute"}
    )
    other_attributes: dict[str, str] = field(
        default_factory=dict, metadata={"type": "Attributes", "namespace": "##other"}
    )


class Final(ScxmlFinalType):
    """marks a terminal state in the machine."""

    class Meta:
        name = "final"
        namespace = "http://www.w3.org/2005/07/scxml"

    model_config = ConfigDict(defer_build=True)


class History(ScxmlHistoryType):
    """pseudostate remembering previous active children."""

    class Meta:
        name = "history"
        namespace = "http://www.w3.org/2005/07/scxml"

    model_config = ConfigDict(defer_build=True)


class Initial(ScxmlInitialType):
    """starting state within a compound state."""

    class Meta:
        name = "initial"
        namespace = "http://www.w3.org/2005/07/scxml"

    model_config = ConfigDict(defer_build=True)


class Invoke(ScxmlInvokeType):
    """run an external process or machine."""

    class Meta:
        name = "invoke"
        namespace = "http://www.w3.org/2005/07/scxml"

    model_config = ConfigDict(defer_build=True)


class ScxmlStateType(BaseModel):

    class Meta:
        name = "scxml.state.type"

    model_config = ConfigDict(defer_build=True)
    onentry: list[Onentry] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    onexit: list[Onexit] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    transition: list[Transition] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    initial: list[Initial] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    state: list["State"] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    parallel: list["Parallel"] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    final: list[Final] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    history: list[History] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    datamodel: list[Datamodel] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    invoke: list[Invoke] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    other_element: list[object] = field(
        default_factory=list, metadata={"type": "Wildcard", "namespace": "##other"}
    )
    id: Optional[str] = field(default=None, metadata={"type": "Attribute"})
    initial_attribute: list[str] = field(
        default_factory=list,
        metadata={"name": "initial", "type": "Attribute", "tokens": True},
    )
    other_attributes: dict[str, str] = field(
        default_factory=dict, metadata={"type": "Attributes", "namespace": "##other"}
    )


class State(ScxmlStateType):
    """basic state node."""

    class Meta:
        name = "state"
        namespace = "http://www.w3.org/2005/07/scxml"

    model_config = ConfigDict(defer_build=True)


class ScxmlParallelType(BaseModel):

    class Meta:
        name = "scxml.parallel.type"

    model_config = ConfigDict(defer_build=True)
    onentry: list[Onentry] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    onexit: list[Onexit] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    transition: list[Transition] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    state: list[State] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    parallel: list["Parallel"] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    history: list[History] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    datamodel: list[Datamodel] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    invoke: list[Invoke] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    other_element: list[object] = field(
        default_factory=list, metadata={"type": "Wildcard", "namespace": "##other"}
    )
    id: Optional[str] = field(default=None, metadata={"type": "Attribute"})
    other_attributes: dict[str, str] = field(
        default_factory=dict, metadata={"type": "Attributes", "namespace": "##other"}
    )


class Parallel(ScxmlParallelType):
    """coordinates concurrent regions."""

    class Meta:
        name = "parallel"
        namespace = "http://www.w3.org/2005/07/scxml"

    model_config = ConfigDict(defer_build=True)


class ScxmlScxmlType(BaseModel):

    class Meta:
        name = "scxml.scxml.type"

    model_config = ConfigDict(defer_build=True)
    state: list[State] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    parallel: list[Parallel] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    final: list[Final] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    datamodel: list[Datamodel] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    script: list[Script] = field(
        default_factory=list,
        metadata={"type": "Element", "namespace": "http://www.w3.org/2005/07/scxml"},
    )
    other_element: list[object] = field(
        default_factory=list, metadata={"type": "Wildcard", "namespace": "##other"}
    )
    initial: list[str] = field(
        default_factory=list, metadata={"type": "Attribute", "tokens": True}
    )
    name: Optional[str] = field(default=None, metadata={"type": "Attribute"})
    version: Decimal = field(
        const=True,
        default=Decimal("1.0"),
        metadata={"type": "Attribute", "required": True},
    )
    datamodel_attribute: str = field(
        default="null", metadata={"name": "datamodel", "type": "Attribute"}
    )
    binding: Optional[BindingDatatype] = field(
        default=None, metadata={"type": "Attribute"}
    )
    exmode: Optional[ExmodeDatatype] = field(
        default=None, metadata={"type": "Attribute"}
    )
    other_attributes: dict[str, str] = field(
        default_factory=dict, metadata={"type": "Attributes", "namespace": "##other"}
    )


class Scxml(ScxmlScxmlType):
    """root element of an SCJSON document."""

    class Meta:
        name = "scxml"
        namespace = "http://www.w3.org/2005/07/scxml"

    model_config = ConfigDict(defer_build=True)
