from __future__ import annotations

"""
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
from typing import Any, Deque, Dict, List, Optional, Set

from pydantic import BaseModel, ConfigDict, Field

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
)

SCXMLNode = State | ScxmlParallelType | ScxmlFinalType

# ---------------------------------------------------------------------------
#  Event plumbing
# ---------------------------------------------------------------------------


class Event(BaseModel):
    name: str
    data: Any | None = None


class EventQueue:
    """Simple FIFO for external/internal events."""

    def __init__(self) -> None:
        self._q: Deque[Event] = deque()

    def push(self, evt: Event) -> None:
        self._q.append(evt)

    def pop(self) -> Optional[Event]:
        return self._q.popleft() if self._q else None

    def __bool__(self) -> bool:
        return bool(self._q)


# ---------------------------------------------------------------------------
#  Activation records
# ---------------------------------------------------------------------------


class ActivationStatus(str, Enum):
    ACTIVE = "active"
    FINAL = "final"


class ActivationRecord(BaseModel):
    """Runtime frame for an entered state/parallel/final element."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str
    node: SCXMLNode
    parent: Optional["ActivationRecord"] = None
    status: ActivationStatus = ActivationStatus.ACTIVE
    local_data: Dict[str, Any] = Field(default_factory=dict)
    children: List["ActivationRecord"] = Field(default_factory=list)

    # ------------------------------------------------------------------ #
    # Life‑cycle helpers
    # ------------------------------------------------------------------ #

    def mark_final(self) -> None:
        self.status = ActivationStatus.FINAL
        if self.parent and all(c.status is ActivationStatus.FINAL for c in self.parent.children):
            self.parent.mark_final()

    def add_child(self, child: "ActivationRecord") -> None:
        self.children.append(child)

    # ------------------------------------------------------------------ #
    # Queries
    # ------------------------------------------------------------------ #

    def is_active(self) -> bool:  # noqa: D401
        """Return *True* while the activation is not finalised."""
        return self.status is ActivationStatus.ACTIVE

    def path(self) -> List["ActivationRecord"]:
        cur: Optional["ActivationRecord"] = self
        out: List["ActivationRecord"] = []
        while cur:
            out.append(cur)
            cur = cur.parent
        return list(reversed(out))


# ---------------------------------------------------------------------------
#  Document context
# ---------------------------------------------------------------------------


class DocumentContext(BaseModel):
    """Holds global execution state for one SCXML document instance."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    doc: Scxml
    data_model: Dict[str, Any] = Field(default_factory=dict)
    root_activation: ActivationRecord
    configuration: Set[str] = Field(default_factory=set)
    events: EventQueue = Field(default_factory=EventQueue)

    # ------------------------------------------------------------------ #
    # Interpreter API – the real engine would call these
    # ------------------------------------------------------------------ #

    def enqueue(self, evt_name: str, data: Any | None = None) -> None:
        self.events.push(Event(name=evt_name, data=data))

    def microstep(self) -> None:
        """Placeholder for the micro‑step algorithm (SCXML §5.4)."""
        evt = self.events.pop()
        # TODO: select enabled transitions, resolve conflicts, exit -> transit -> enter
        # For now just stub‑log the event.
        if evt:
            print(f"[microstep] consumed event: {evt.name}")

    # ------------------------------------------------------------------ #
    # Construction helpers
    # ------------------------------------------------------------------ #

    @classmethod
    def from_doc(cls, doc: Scxml) -> "DocumentContext":
        """Parse the <scxml> element and build initial configuration."""
        root_state = ActivationRecord(id=doc.id or "root", node=doc, parent=None)
        cfg = {root_state.id}
        return cls(doc=doc, root_activation=root_state, configuration=cfg)
