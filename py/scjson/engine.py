from __future__ import annotations

"""
Agent Name: python-engine

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Runtime scaffolding for SCXML execution.

This “upper‑level” module builds:
  • DocumentContext – one per SCXML document instance
  • ActivationRecord – one per active <state>, <parallel>, or <final>
The classes delegate to the generated Pydantic types under ``.pydantic`` for the
static schema of the document itself. Only runtime state lives here.

High‑level responsibilities
---------------------------
• Maintain the current configuration (set of active states).
• Dispatch external/internal events.
• Manage onentry/onexit, finalisation, parallel‐completion, and history.
• Provide an isolated local data‑model for every activation while sharing a
  global data‑model at the document level.
"""

from collections import deque
from enum import Enum, auto
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional, Set

from pydantic import BaseModel, ConfigDict, Field
from .SCXMLDocumentHandler import SCXMLDocumentHandler

# ---------------------------------------------------------------------------
#  Static SCXML schema – generated with xsdata‑pydantic and placed in
#  ``package_root/.pydantic/generated.py``.  Import only what we need here to
#  keep import cost low.
# ---------------------------------------------------------------------------

from .pydantic import (
    Scxml,
    State,
    ScxmlParallelType,
    ScxmlFinalType,
    History,
)

SCXMLNode = State | ScxmlParallelType | ScxmlFinalType | History | Scxml

# ---------------------------------------------------------------------------
#  Event plumbing
# ---------------------------------------------------------------------------


class Event(BaseModel):
    name: str
    data: Any | None = None


class EventQueue:
    """Simple FIFO for external/internal events."""

    def __init__(self) -> None:
        """Create an empty queue."""

        self._q: Deque[Event] = deque()

    def push(self, evt: Event) -> None:
        """Append ``evt`` to the queue.

        :param evt: ``Event`` instance to enqueue.
        :returns: ``None``
        """

        self._q.append(evt)

    def pop(self) -> Optional[Event]:
        """Remove and return the next event if available.

        :returns: The next ``Event`` or ``None`` when empty.
        """

        return self._q.popleft() if self._q else None

    def __bool__(self) -> bool:
        """Return ``True`` if any events are queued."""

        return bool(self._q)


# ---------------------------------------------------------------------------
#  Activation records
# ---------------------------------------------------------------------------


class ActivationStatus(str, Enum):
    ACTIVE = "active"
    FINAL = "final"


class TransitionSpec(BaseModel):
    """Simplified representation of a transition."""

    event: Optional[str] = None
    target: List[str] = Field(default_factory=list)
    cond: Optional[str] = None


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

    # ------------------------------------------------------------------ #
    # Life‑cycle helpers
    # ------------------------------------------------------------------ #

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

    # ------------------------------------------------------------------ #
    # Queries
    # ------------------------------------------------------------------ #

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


# ---------------------------------------------------------------------------
#  Document context
# ---------------------------------------------------------------------------

from .context import DocumentContext

