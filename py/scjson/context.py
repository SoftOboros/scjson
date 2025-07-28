from __future__ import annotations

"""
Agent Name: python-context

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Runtime execution context with onentry/onexit and history support.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import logging

from pydantic import BaseModel, ConfigDict, Field

from .SCXMLDocumentHandler import SCXMLDocumentHandler
from .pydantic import (
    History,
    Scxml,
    ScxmlParallelType,
    ScxmlFinalType,
    State,
)
from .events import Event, EventQueue
from .activation import ActivationRecord, TransitionSpec


logger = logging.getLogger(__name__)


SCXMLNode = State | ScxmlParallelType | ScxmlFinalType | History | Scxml


class DocumentContext(BaseModel):
    """Holds global execution state for one SCXML document instance."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    doc: Scxml
    data_model: Dict[str, Any] = Field(default_factory=dict)
    root_activation: ActivationRecord
    configuration: Set[str] = Field(default_factory=set)
    events: EventQueue = Field(default_factory=EventQueue)
    activations: Dict[str, ActivationRecord] = Field(default_factory=dict)
    history: Dict[str, List[str]] = Field(default_factory=dict)
    action_log: List[str] = Field(default_factory=list)

    # ------------------------------------------------------------------ #
    # Interpreter API – the real engine would call these
    # ------------------------------------------------------------------ #

    def enqueue(self, evt_name: str, data: Any | None = None) -> None:
        """Add an event to the queue for later processing.

        :param evt_name: Name of the event to enqueue.
        :param data: Optional payload for the event.
        :returns: ``None``
        """

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
                        logger.info(
                            "[microstep] %s -> %s on %s",
                            act.id,
                            ",".join(trans.target),
                            evt.name,
                        )
                        return

        logger.info("[microstep] consumed event: %s", evt.name)

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
    def _build_activation_tree(
        node: SCXMLNode, parent: Optional[ActivationRecord]
    ) -> ActivationRecord:
        """Recursively create activations and collect datamodel entries."""

        ident = getattr(node, "id", None) or getattr(node, "name", None) or "anon"
        act = ActivationRecord(id=ident, node=node, parent=parent)
        act.local_data.update(DocumentContext._extract_datamodel(node))

        for t in getattr(node, "transition", []):
            trans = TransitionSpec(
                event=getattr(t, "event", None),
                target=list(getattr(t, "target", [])),
                cond=getattr(t, "cond", None),
            )
            act.transitions.append(trans)

        for child in getattr(node, "state", []):
            act.add_child(DocumentContext._build_activation_tree(child, act))
        for child in getattr(node, "parallel", []):
            act.add_child(DocumentContext._build_activation_tree(child, act))
        for child in getattr(node, "final", []):
            act.add_child(DocumentContext._build_activation_tree(child, act))
        for child in getattr(node, "history", []):
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
                self._enter_target(child)

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

    # ------------------------------------------------------------------ #
    # State entry/exit helpers
    # ------------------------------------------------------------------ #

    def _run_actions(self, container: Any, act: ActivationRecord) -> None:
        for assign in getattr(container, "assign", []):
            self._do_assign(assign, act)
        for log in getattr(container, "log", []):
            self._do_log(log, act)
        for raise_ in getattr(container, "raise_value", []):
            self.enqueue(raise_.event)

    def _scope_env(self, act: ActivationRecord) -> Dict[str, Any]:
        env: Dict[str, Any] = {}
        env.update(self.data_model)
        for frame in act.path():
            env.update(frame.local_data)
        return env

    def _do_assign(self, assign: Any, act: ActivationRecord) -> None:
        env = self._scope_env(act)
        value: Any = None
        if assign.expr is not None:
            try:
                value = eval(assign.expr, {}, env)
            except Exception:
                value = assign.expr
        elif assign.content:
            value = "".join(str(x) for x in assign.content)
        target = assign.location
        for frame in reversed(act.path()):
            if target in frame.local_data:
                frame.local_data[target] = value
                return
        if target in self.data_model:
            self.data_model[target] = value
        else:
            act.local_data[target] = value

    def _do_log(self, log: Any, act: ActivationRecord) -> None:
        env = self._scope_env(act)
        value = None
        if log.expr is not None:
            try:
                value = eval(log.expr, {}, env)
            except Exception:
                value = log.expr
        entry = f"{log.label or ''}:{value}"
        self.action_log.append(entry)

    def _enter_state(self, act: ActivationRecord) -> None:
        if act.id in self.configuration:
            return
        self.configuration.add(act.id)
        for onentry in getattr(act.node, "onentry", []):
            self._run_actions(onentry, act)
        self._enter_initial_states(act)

    def _exit_state(self, act: ActivationRecord) -> None:
        active_children = [c.id for c in act.children if c.id in self.configuration]
        if getattr(act.node, "history", []):
            self.history[act.id] = active_children
        for cid in active_children:
            self._exit_state(self.activations[cid])
        for onexit in getattr(act.node, "onexit", []):
            self._run_actions(onexit, act)
        self.configuration.discard(act.id)

    def _enter_history(self, act: ActivationRecord) -> None:
        parent = act.parent
        if not parent:
            return
        if parent.id not in self.configuration:
            self.configuration.add(parent.id)
            for onentry in getattr(parent.node, "onentry", []):
                self._run_actions(onentry, parent)
        targets = self.history.get(parent.id)
        if not targets:
            trans = act.node.transition[0]
            targets = list(trans.target)
        for tid in targets:
            child = self.activations.get(tid)
            if child:
                self._enter_state(child)

    def _enter_target(self, act: ActivationRecord) -> None:
        if isinstance(act.node, History):
            self._enter_history(act)
        else:
            self._enter_state(act)

    def _fire_transition(self, source: ActivationRecord, trans: TransitionSpec) -> None:
        if source.id in self.configuration:
            self._exit_state(source)
        for tid in trans.target:
            target = self.activations.get(tid)
            if target:
                self._enter_target(target)

    @classmethod
    def from_json_file(cls, path: str | Path) -> "DocumentContext":
        data = Path(path).read_text(encoding="utf-8")
        doc = Scxml.model_validate_json(data)
        return cls.from_doc(doc)

    @classmethod
    def from_xml_file(cls, path: str | Path) -> "DocumentContext":
        handler = SCXMLDocumentHandler()
        xml_str = Path(path).read_text(encoding="utf-8")
        json_str = handler.xml_to_json(xml_str)
        doc = Scxml.model_validate_json(json_str)
        return cls.from_doc(doc)

    def run(self, steps: int | None = None) -> None:
        """Execute microsteps until the queue is empty or ``steps`` is reached.

        :param steps: Maximum number of microsteps to run, or ``None`` for no
            limit.
        :returns: ``None``
        """

        count = 0
        while self.events and (steps is None or count < steps):
            self.microstep()
            count += 1
