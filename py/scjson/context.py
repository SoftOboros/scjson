from __future__ import annotations

"""
Agent Name: python-context

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Runtime execution context with onentry/onexit and history support.
"""

from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple
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
    activation_order: Dict[str, int] = Field(default_factory=dict)

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
        event_consumed = evt is not None
        triggered = False

        if evt is not None:
            result = self._execute_transition(evt)
            if result:
                act, trans, _, _ = result
                triggered = True
                logger.info(
                    "[microstep] %s -> %s on %s",
                    act.id,
                    ",".join(trans.target),
                    evt.name,
                )

        while True:
            result = self._execute_transition(None)
            if not result:
                break
            triggered = True
            act, trans, _, _ = result
            logger.info(
                "[microstep] %s -> %s on %s",
                act.id,
                ",".join(trans.target),
                trans.event or "<epsilon>",
            )

        if event_consumed and not triggered and evt is not None:
            logger.info("[microstep] consumed event: %s", evt.name)

    def _activation_order_key(self, state_id: str) -> int:
        return self.activation_order.get(state_id, len(self.activation_order) + 1)

    def _select_transition(self, evt: Event | None) -> tuple[ActivationRecord, TransitionSpec] | None:
        """Return the first enabled transition for ``evt`` respecting document order."""

        event_name = evt.name if evt is not None else None
        for state_id in sorted(self.configuration, key=self._activation_order_key):
            act = self.activations.get(state_id)
            if not act:
                continue
            for trans in act.transitions:
                if evt is None:
                    if trans.event is not None:
                        continue
                else:
                    if trans.event != event_name:
                        continue
                if trans.cond is None or self._eval_condition(trans.cond, act):
                    return act, trans
        return None

    def _execute_transition(
        self, evt: Event | None
    ) -> Optional[Tuple[ActivationRecord, TransitionSpec, Set[str], Set[str]]]:
        sel = self._select_transition(evt)
        if not sel:
            return None
        act, trans = sel
        entered, exited = self._fire_transition(act, trans)
        return act, trans, entered, exited

    def trace_step(self, evt: Event | None = None) -> dict:
        """Execute one microstep and return a standardized trace entry."""

        if evt is not None:
            event_obj = evt
        else:
            event_obj = self.events.pop()

        config_before = set(self.configuration)
        dm_before = dict(self.data_model)
        action_count_before = len(self.action_log)
        fired: List[Dict[str, Any]] = []
        entered: Set[str] = set()
        exited: Set[str] = set()

        if event_obj is not None:
            result = self._execute_transition(event_obj)
            if result:
                act, trans, ent, ex = result
                fired.append(
                    {
                        "source": act.id,
                        "targets": list(trans.target),
                        "event": trans.event,
                        "cond": trans.cond,
                    }
                )
                entered.update(ent)
                exited.update(ex)

        while True:
            result = self._execute_transition(None)
            if not result:
                break
            act, trans, ent, ex = result
            fired.append(
                {
                    "source": act.id,
                    "targets": list(trans.target),
                    "event": trans.event,
                    "cond": trans.cond,
                }
            )
            entered.update(ent)
            exited.update(ex)

        dm_delta: Dict[str, Any] = {
            k: self.data_model[k]
            for k in self.data_model
            if dm_before.get(k) != self.data_model[k]
        }
        for key in dm_before:
            if key not in self.data_model:
                dm_delta[key] = None
        actions = self.action_log[action_count_before:]

        event_payload = (
            {"name": event_obj.name, "data": event_obj.data}
            if event_obj is not None
            else None
        )

        config_after = set(self.configuration)
        if not entered:
            entered = config_after - config_before
        if not exited:
            exited = config_before - config_after

        filtered_entered = self._filter_states(entered)
        if not filtered_entered:
            filtered_entered = self._filter_states(config_after - config_before)

        filtered_exited = self._filter_states(exited)
        if not filtered_exited:
            filtered_exited = self._filter_states(config_before - config_after)

        filtered_config = self._filter_states(self.configuration)

        filtered_transitions: List[Dict[str, Any]] = []
        for item in fired:
            src = item["source"]
            targets = [t for t in item["targets"] if self._is_user_state(t)]
            if not self._is_user_state(src):
                if not targets:
                    continue
                continue  # skip synthetic transitions entirely
            filtered_transitions.append(
                {
                    "source": src,
                    "targets": targets,
                    "event": item["event"],
                    "cond": item["cond"],
                }
            )

        return {
            "event": event_payload,
            "firedTransitions": filtered_transitions,
            "enteredStates": sorted(filtered_entered, key=self._activation_order_key),
            "exitedStates": sorted(filtered_exited, key=self._activation_order_key),
            "configuration": sorted(filtered_config, key=self._activation_order_key),
            "actionLog": actions,
            "datamodelDelta": dm_delta,
        }

    def _is_user_state(self, state_id: str) -> bool:
        return bool(state_id) and state_id != self.root_activation.id and not state_id.startswith("$generated-")

    def _filter_states(self, ids: Iterable[str]) -> List[str]:
        return [sid for sid in ids if self._is_user_state(sid)]

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
        ctx.drain_internal()
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
        if act.id not in self.activation_order:
            self.activation_order[act.id] = len(self.activation_order)
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

    def _fire_transition(
        self, source: ActivationRecord, trans: TransitionSpec
    ) -> tuple[Set[str], Set[str]]:
        before = set(self.configuration)

        exit_list = self._compute_exit_set(source, trans.target)
        for act in exit_list:
            if act.id in self.configuration:
                self._exit_state(act)

        enter_list = self._compute_entry_list(source, trans.target)
        for act in enter_list:
            if act.id not in self.configuration:
                self._enter_target(act)

        after = set(self.configuration)
        entered = after - before
        exited = before - after
        return entered, exited

    def _depth(self, act: ActivationRecord) -> int:
        depth = 0
        cur = act
        while cur.parent:
            depth += 1
            cur = cur.parent
        return depth

    def _least_common_ancestor(
        self, first: ActivationRecord, second: ActivationRecord
    ) -> Optional[ActivationRecord]:
        ancestors: Set[str] = set()
        cur = first
        while cur:
            ancestors.add(cur.id)
            cur = cur.parent
        cur = second
        while cur:
            if cur.id in ancestors:
                return cur
            cur = cur.parent
        return None

    def _compute_exit_set(
        self, source: ActivationRecord, targets: List[str]
    ) -> List[ActivationRecord]:
        exit_set: Dict[str, ActivationRecord] = {}

        if not targets:
            cur = source
            while cur:
                exit_set[cur.id] = cur
                cur = cur.parent
        else:
            for tid in targets:
                target_act = self.activations.get(tid)
                if not target_act:
                    continue
                normalized_target = (
                    target_act.parent
                    if isinstance(target_act.node, History)
                    else target_act
                )
                lca = self._least_common_ancestor(source, normalized_target or self.root_activation)
                cur = source
                while cur and cur is not lca:
                    exit_set[cur.id] = cur
                    cur = cur.parent

        ordered = sorted(exit_set.values(), key=self._depth, reverse=True)
        return ordered

    def _compute_entry_list(
        self, source: ActivationRecord, targets: List[str]
    ) -> List[ActivationRecord]:
        enter_order: List[ActivationRecord] = []
        seen: Set[str] = set()

        for tid in targets or []:
            target_act = self.activations.get(tid)
            if not target_act:
                continue
            normalized_target = (
                target_act.parent
                if isinstance(target_act.node, History)
                else target_act
            )
            lca = self._least_common_ancestor(source, normalized_target or self.root_activation)
            path: List[ActivationRecord] = []
            cur = target_act
            while cur and cur is not lca:
                path.append(cur)
                cur = cur.parent
            for act in reversed(path):
                if act.id not in seen:
                    seen.add(act.id)
                    enter_order.append(act)

        return enter_order

    def drain_internal(self) -> None:
        """Execute eventless transitions until quiescent."""

        while True:
            result = self._execute_transition(None)
            if not result:
                break

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
