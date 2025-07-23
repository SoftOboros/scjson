"""
Agent Name: context-module

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Holds global execution state for one SCXML document instance.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, ConfigDict, Field

from .SCXMLDocumentHandler import SCXMLDocumentHandler
from .activation import ActivationRecord, TransitionSpec, SCXMLNode
from .events import Event, EventQueue
from .pydantic import Scxml, State, ScxmlParallelType, ScxmlFinalType


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
        """Add an event to the internal queue."""
        self.events.push(Event(name=evt_name, data=data))

    def microstep(self) -> None:
        """Execute one microstep of the interpreter."""
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
                        print(f"[microstep] {act.id} -> {','.join(trans.target)} on {evt.name}")
                        return

        print(f"[microstep] consumed event: {evt.name}")

    # ------------------------------------------------------------------ #
    # Construction helpers
    # ------------------------------------------------------------------ #

    @classmethod
    def from_doc(cls, doc: Scxml) -> "DocumentContext":
        """Parse the <scxml> element and build initial configuration."""
        dm_attr = getattr(doc, "datamodel_attribute", "null")
        if not dm_attr or dm_attr == "null":
            doc.datamodel_attribute = "python"
        elif dm_attr != "python":
            raise ValueError("Only the python datamodel is supported")

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
    def _build_activation_tree(node: SCXMLNode, parent: Optional[ActivationRecord]) -> ActivationRecord:
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
        """Populate ``self.activations`` with the activation tree."""
        self.activations[act.id] = act
        for child in act.children:
            self._index_activations(child)

    def _enter_initial_states(self, act: ActivationRecord) -> None:
        """Recursively enter initial states for *act*."""
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
        """Evaluate a transition condition in the context of *act*."""
        env: Dict[str, Any] = {}
        env.update(self.data_model)
        for frame in act.path():
            env.update(frame.local_data)
        try:
            return bool(eval(expr, {}, env))
        except Exception:
            return False

    def _fire_transition(self, source: ActivationRecord, trans: TransitionSpec) -> None:
        """Apply *trans* from *source* updating the configuration."""
        if source.id in self.configuration:
            self.configuration.remove(source.id)
        for tid in trans.target:
            target = self.activations.get(tid)
            if target:
                self.configuration.add(tid)
                self._enter_initial_states(target)

    @classmethod
    def from_json_file(cls, path: str | Path) -> "DocumentContext":
        """Load a SCJSON document from *path* and build the context."""
        data = Path(path).read_text(encoding="utf-8")
        doc = Scxml.model_validate_json(data)
        return cls.from_doc(doc)

    @classmethod
    def from_xml_file(cls, path: str | Path) -> "DocumentContext":
        """Load an SCXML document from *path* and build the context."""
        handler = SCXMLDocumentHandler()
        xml_str = Path(path).read_text(encoding="utf-8")
        json_str = handler.xml_to_json(xml_str)
        doc = Scxml.model_validate_json(json_str)
        return cls.from_doc(doc)

    def run(self, steps: int | None = None) -> None:
        """Execute pending events."""
        count = 0
        while self.events and (steps is None or count < steps):
            self.microstep()
            count += 1
