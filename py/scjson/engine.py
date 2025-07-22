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
)

SCXMLNode = State | ScxmlParallelType | ScxmlFinalType | Scxml

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
    activations: Dict[str, ActivationRecord] = Field(default_factory=dict)

    # ------------------------------------------------------------------ #
    # Interpreter API – the real engine would call these
    # ------------------------------------------------------------------ #

    def enqueue(self, evt_name: str, data: Any | None = None) -> None:
        self.events.push(Event(name=evt_name, data=data))

    def microstep(self) -> None:
        """Execute one microstep of the interpreter.

        This inspects the current configuration for enabled transitions,
        updates the configuration, and processes a single event from the
        internal queue.
        """
        evt = self.events.pop()
        if not evt:
            return

        for state_id in list(self.configuration):
            act = self.activations.get(state_id)
            if not act:
                continue
            for trans in act.transitions:
                if trans.event is None or trans.event == evt.name:
                    if trans.cond is None or self._eval_condition(trans.cond, act):
                        self._fire_transition(act, trans)
                        print(
                            f"[microstep] {act.id} -> {','.join(trans.target)} on {evt.name}"
                        )
                        return

        print(f"[microstep] consumed event: {evt.name}")

    # ------------------------------------------------------------------ #
    # Construction helpers
    # ------------------------------------------------------------------ #

    @classmethod
    def from_doc(cls, doc: Scxml) -> "DocumentContext":
        """Parse the <scxml> element and build initial configuration.

        Args:
            doc: Parsed SCXML document tree.

        Returns:
            A ``DocumentContext`` ready for execution.
        """
        dm_attr = getattr(doc, "datamodel_attribute", "null")
        if not dm_attr or dm_attr == "null":
            doc.datamodel_attribute = "python"
        elif dm_attr != "python":
            raise ValueError("Only the python datamodel is supported")

        ident = getattr(doc, "id", None) or getattr(doc, "name", None) or "root"
        root_state = cls._build_activation_tree(doc, None)
        ctx = cls(doc=doc, root_activation=root_state)
        ctx.data_model = root_state.local_data
        ctx._index_activations(root_state)
        ctx.configuration.add(root_state.id)
        ctx._enter_initial_states(root_state)
        return ctx

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _build_activation_tree(
        node: SCXMLNode, parent: Optional[ActivationRecord]
    ) -> ActivationRecord:
        """Recursively create activations and collect datamodel entries."""

        ident = getattr(node, "id", None) or getattr(node, "name", None) or "anon"
        act = ActivationRecord(id=ident, node=node, parent=parent)
        act.local_data.update(DocumentContext._extract_datamodel(node))

        for t in getattr(node, "transition", []):
            trans = TransitionSpec(event=getattr(t, "event", None), target=list(getattr(t, "target", [])), cond=getattr(t, "cond", None))
            act.transitions.append(trans)

        for child in getattr(node, "state", []):
            act.add_child(DocumentContext._build_activation_tree(child, act))
        for child in getattr(node, "parallel", []):
            act.add_child(DocumentContext._build_activation_tree(child, act))
        for child in getattr(node, "final", []):
            act.add_child(DocumentContext._build_activation_tree(child, act))
        return act

    @staticmethod
    def _extract_datamodel(node: SCXMLNode) -> Dict[str, Any]:
        """Return a dict mapping data IDs to values for *node*'s datamodel."""
        result: Dict[str, Any] = {}
        for dm in getattr(node, "datamodel", []):
            for data in dm.data:
                value: Any = None
                if data.expr is not None:
                    try:
                        value = eval(data.expr, {}, {})
                    except Exception:
                        value = data.expr
                elif data.src:
                    try:
                        value = Path(data.src).read_text(encoding="utf-8")
                    except Exception:
                        value = None
                elif data.content:
                    value = "".join(str(x) for x in data.content)
                result[data.id] = value
        return result

    # ------------------------------------------------------------------ #
    # Index and entry helpers
    # ------------------------------------------------------------------ #

    def _index_activations(self, act: ActivationRecord) -> None:
        """Populate ``self.activations`` with the activation tree.

        Args:
            act: Activation record serving as traversal root.
        """
        self.activations[act.id] = act
        for child in act.children:
            self._index_activations(child)

    def _enter_initial_states(self, act: ActivationRecord) -> None:
        """Recursively enter initial states for *act*.

        Args:
            act: Activation to inspect for initial targets.
        """
        node = act.node
        targets: List[str] = []
        if isinstance(node, Scxml):
            targets = node.initial or [c.id for c in act.children[:1]]
        elif isinstance(node, State):
            if node.initial_attribute:
                targets = list(node.initial_attribute)
            elif node.initial:
                targets = list(node.initial[0].transition.target)
            elif act.children:
                targets = [act.children[0].id]
        elif isinstance(node, ScxmlParallelType):
            targets = [c.id for c in act.children]

        for tid in targets:
            child = self.activations.get(tid)
            if child and tid not in self.configuration:
                self.configuration.add(tid)
                self._enter_initial_states(child)

    def _eval_condition(self, expr: str, act: ActivationRecord) -> bool:
        """Evaluate a transition condition in the context of *act*.

        Args:
            expr: Python expression from the transition's ``cond`` attribute.
            act: Activation serving as the local scope root.

        Returns:
            The truthiness of the evaluated expression. Any errors are treated
            as ``False``.
        """
        env: Dict[str, Any] = {}
        env.update(self.data_model)
        for frame in act.path():
            env.update(frame.local_data)
        try:
            return bool(eval(expr, {}, env))
        except Exception:
            return False

    def _fire_transition(self, source: ActivationRecord, trans: TransitionSpec) -> None:
        """Apply *trans* from *source* updating the configuration.

        Args:
            source: Activation that owns the transition.
            trans: Transition specification to fire.
        """
        if source.id in self.configuration:
            self.configuration.remove(source.id)
        for tid in trans.target:
            target = self.activations.get(tid)
            if target:
                self.configuration.add(tid)
                self._enter_initial_states(target)

    @classmethod
    def from_json_file(cls, path: str | Path) -> "DocumentContext":
        """Load a SCJSON document from *path* and build the context.

        Args:
            path: Location of the SCJSON file.

        Returns:
            Instantiated ``DocumentContext``.
        """
        data = Path(path).read_text(encoding="utf-8")
        doc = Scxml.model_validate_json(data)
        return cls.from_doc(doc)

    @classmethod
    def from_xml_file(cls, path: str | Path) -> "DocumentContext":
        """Load an SCXML document from *path* and build the context.

        Args:
            path: Location of the SCXML file.

        Returns:
            Instantiated ``DocumentContext``.
        """
        handler = SCXMLDocumentHandler()
        xml_str = Path(path).read_text(encoding="utf-8")
        json_str = handler.xml_to_json(xml_str)
        doc = Scxml.model_validate_json(json_str)
        return cls.from_doc(doc)

    def run(self, steps: int = 1) -> None:
        """Execute ``steps`` microsteps of the state machine.

        Args:
            steps: Number of microsteps to execute.
        """
        for _ in range(steps):
            self.microstep()
