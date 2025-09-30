"""
Agent Name: python-activation

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Activation record definitions for the runtime engine.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field
from .pydantic import Scxml, State, ScxmlParallelType, ScxmlFinalType, History

SCXMLNode = State | ScxmlParallelType | ScxmlFinalType | History | Scxml


class ActivationStatus(str, Enum):
    """Enumeration of activation states."""

    ACTIVE = "active"
    FINAL = "final"


class TransitionSpec(BaseModel):
    """Simplified representation of a transition."""

    event: Optional[str] = None
    target: List[str] = Field(default_factory=list)
    cond: Optional[str] = None
    container: Optional[Any] = None


class ActivationRecord(BaseModel):
    """Runtime frame for an entered state/parallel/final element."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str
    node: SCXMLNode
    parent: Optional["ActivationRecord"] = None
    status: ActivationStatus = ActivationStatus.ACTIVE
    local_data: Dict[str, Any] = Field(default_factory=dict)
    children: List["ActivationRecord"] = Field(default_factory=list)
    transitions: List["TransitionSpec"] = Field(default_factory=list)
    invokes: List[Any] = Field(default_factory=list)

    def mark_final(self) -> None:
        """Flag this activation and its ancestors as final when complete."""
        self.status = ActivationStatus.FINAL
        if self.parent and all(c.status is ActivationStatus.FINAL for c in self.parent.children):
            self.parent.mark_final()

    def add_child(self, child: "ActivationRecord") -> None:
        """Add ``child`` to this activation's children list.

        :param child: Activation record to attach.
        :returns: ``None``
        """
        self.children.append(child)

    def is_active(self) -> bool:  # noqa: D401
        """Return *True* while the activation is not finalised."""
        return self.status is ActivationStatus.ACTIVE

    def path(self) -> List["ActivationRecord"]:
        """Return the ancestry chain from root to ``self``.

        :returns: ``list`` of activations starting at the root.
        """
        cur: Optional["ActivationRecord"] = self
        out: List["ActivationRecord"] = []
        while cur:
            out.append(cur)
            cur = cur.parent
        return list(reversed(out))
