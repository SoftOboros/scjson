from __future__ import annotations

"""
Agent Name: python-context

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Runtime execution context with onentry/onexit and history support.
"""

import json
import re
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, Iterable, List, Mapping, Optional, Set, Tuple
import logging
from enum import Enum
from collections import defaultdict
from uuid import uuid4
from xml.etree import ElementTree as ET

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from .SCXMLDocumentHandler import SCXMLDocumentHandler
from .pydantic import (
    History,
    Scxml,
    ScxmlParallelType,
    ScxmlFinalType,
    State,
)
from .events import Event, EventQueue
from .safe_eval import SafeExpressionEvaluator, SafeEvaluationError
from .activation import ActivationRecord, TransitionSpec, ActivationStatus
from .invoke import InvokeRegistry, InvokeHandler
from . import dataclasses as dataclasses_module


logger = logging.getLogger(__name__)


class _EventDataProxy(dict):
    """Mapping wrapper that exposes dictionary entries as attributes."""

    def __getattr__(self, name: str) -> Any:
        if name in self:
            return self[name]
        raise AttributeError(name)

    def __setattr__(self, name: str, value: Any) -> None:
        self[name] = value

    def __delattr__(self, name: str) -> None:
        if name in self:
            del self[name]
            return
        raise AttributeError(name)


SCXMLNode = State | ScxmlParallelType | ScxmlFinalType | History | Scxml


_ACTION_SERIALIZER = SCXMLDocumentHandler(
    pretty=False,
    omit_empty=False,
    fail_on_unknown_properties=False,
)

class ExecutionMode(str, Enum):
    """Execution conformance modes supported by the interpreter."""

    STRICT = "strict"
    LAX = "lax"


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
    history_deep: Dict[str, List[str]] = Field(default_factory=dict)
    action_log: List[str] = Field(default_factory=list)
    activation_order: Dict[str, int] = Field(default_factory=dict)
    json_lookup: Dict[int, Any] = Field(default_factory=dict, exclude=True)
    json_order: Dict[int, List[str]] = Field(default_factory=dict, exclude=True)
    delayed_events: List[tuple[float, Event]] = Field(default_factory=list, exclude=True)
    _timer_now: float = PrivateAttr(default_factory=time.monotonic)
    _use_wall_clock: bool = PrivateAttr(default=True)
    _current_event: Event | None = PrivateAttr(default=None)
    execution_mode: ExecutionMode = ExecutionMode.STRICT
    allow_unsafe_eval: bool = False
    evaluator: SafeExpressionEvaluator = Field(default_factory=SafeExpressionEvaluator)
    # Invoke runtime
    invoke_registry: InvokeRegistry = Field(default_factory=InvokeRegistry)
    invocations: Dict[str, InvokeHandler] = Field(default_factory=dict)
    invocations_by_state: Dict[str, List[str]] = Field(default_factory=dict)
    _invoke_specs: Dict[str, tuple[Any, ActivationRecord]] = PrivateAttr(default_factory=dict)
    invocations_autoforward: Dict[str, bool] = Field(default_factory=dict)
    _invocations_started_for_state: Set[str] = PrivateAttr(default_factory=set)
    _base_dir: Optional[Path] = PrivateAttr(default=None)
    _external_emitter: Optional[Any] = PrivateAttr(default=None)
    # Ordering policy for parent queue emission from child invokes
    ordering_mode: str = "tolerant"  # tolerant | strict | scion
    _leaf_ids: Set[str] = PrivateAttr(default_factory=set)

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
        self._release_delayed_events()
        evt = self.events.pop()
        event_consumed = evt is not None
        triggered = False

        # Autoforward external events to active invocations before processing
        if evt is not None:
            self._autoforward_event(evt)

        # Process any immediate done.invoke events that were produced by
        # forwarding the external event, so that transitions on done.invoke
        # can fire within the same microstep (after finalize).
        try:
            while getattr(self.events, "_q", None):
                head = self.events._q[0]
                if not getattr(head, "name", "").startswith("done.invoke"):
                    break
                head_evt = self.events.pop()
                if head_evt is None:
                    break
                self._current_event = head_evt
                result = self._execute_transition(head_evt)
                self._current_event = None
                if result:
                    act, trans, _, _ = result
                    triggered = True
                    logger.info(
                        "[microstep] %s -> %s on %s",
                        act.id,
                        ",".join(trans.target),
                        head_evt.name,
                    )
        except Exception:
            pass

        if evt is not None:
            # Expose _event to expressions during processing
            self._current_event = evt
            result = self._execute_transition(evt)
            self._current_event = None
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
        # At the end of the microstep, start invocations for states that
        # remain active after all transitions in this step.
        try:
            self._start_invocations_for_active_states()
        except Exception:
            pass

    def _activation_order_key(self, state_id: str) -> int:
        return self.activation_order.get(state_id, len(self.activation_order) + 1)

    def _wrap_event_payload(self, value: Any) -> Any:
        """Return event payloads with attribute access for mapping entries."""

        if isinstance(value, Mapping):
            return _EventDataProxy({k: self._wrap_event_payload(v) for k, v in value.items()})
        if isinstance(value, list):
            return [self._wrap_event_payload(v) for v in value]
        return value

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
                    te = trans.event or ""
                    # SCXML allows space-separated event names and wildcard patterns
                    # Supported tokens:
                    #  - exact: "foo"
                    #  - any: "*" (matches any external event)
                    #  - prefix: "error.*" (matches e.g., error.execution)
                    def _matches(token: str, name: str | None) -> bool:
                        if name is None:
                            return False
                        if token == "*":
                            return True
                        if token.endswith(".*"):
                            prefix = token[:-2]
                            return name == prefix or name.startswith(prefix + ".")
                        return token == name

                    names = [n for n in te.split() if n]
                    if names and not any(_matches(token, event_name) for token in names):
                        continue
                    if not names and not _matches(te, event_name):
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

        self._release_delayed_events()
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
            self._current_event = event_obj
            result = self._execute_transition(event_obj)
            self._current_event = None
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

        result = {
            "event": event_payload,
            "firedTransitions": filtered_transitions,
            "enteredStates": sorted(filtered_entered, key=self._activation_order_key),
            "exitedStates": sorted(filtered_exited, key=self._activation_order_key),
            "configuration": sorted(filtered_config, key=self._activation_order_key),
            "actionLog": actions,
            "datamodelDelta": dm_delta,
        }
        # Start pending invocations for active states post-step
        try:
            self._start_invocations_for_active_states()
        except Exception:
            pass
        return result

    def _is_user_state(self, state_id: str) -> bool:
        return bool(state_id) and state_id != self.root_activation.id and not state_id.startswith("$generated-")

    def _filter_states(self, ids: Iterable[str]) -> List[str]:
        if not self._leaf_ids:
            try:
                self._leaf_ids = self.leaf_state_ids()
            except Exception:
                self._leaf_ids = set()
        return [
            sid
            for sid in ids
            if self._is_user_state(sid) and (not self._leaf_ids or sid in self._leaf_ids)
        ]

    # ------------------------------------------------------------------ #
    # Construction helpers
    # ------------------------------------------------------------------ #

    @classmethod
    def from_doc(
        cls,
        doc: Scxml,
        *,
        allow_unsafe_eval: bool = False,
        evaluator: SafeExpressionEvaluator | None = None,
        execution_mode: ExecutionMode | str = ExecutionMode.STRICT,
    ) -> "DocumentContext":
        """Parse the <scxml> element and build initial configuration.

        Parameters
        ----------
        doc:
            Root ``<scxml>`` element to execute.
        allow_unsafe_eval:
            When ``True`` fall back to Python's ``eval`` for expressions.
        evaluator:
            Optional pre-configured safe evaluator instance.
        execution_mode:
            Controls schema strictness; ``"strict"`` enforces schema fidelity
            while ``"lax"`` tolerates unknown elements and attributes.
        """
        dm_attr = getattr(doc, "datamodel_attribute", "null")
        if not dm_attr or dm_attr == "null":
            doc.datamodel_attribute = "python"
        elif dm_attr != "python":
            raise ValueError("Only the python datamodel is supported")
        raw_data = doc.model_dump(mode="python")
        raw_data["datamodel_attribute"] = doc.datamodel_attribute

        mode = (
            execution_mode
            if isinstance(execution_mode, ExecutionMode)
            else ExecutionMode(str(execution_mode).lower())
        )

        return cls._from_model(
            doc,
            raw_data,
            allow_unsafe_eval=allow_unsafe_eval,
            evaluator=evaluator,
            execution_mode=mode,
            source_xml=None,
        )

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _build_activation_tree(
        node: SCXMLNode,
        parent: Optional[ActivationRecord],
        evaluator: SafeExpressionEvaluator,
        allow_unsafe_eval: bool,
    ) -> ActivationRecord:
        """Recursively create activations and collect datamodel entries."""

        ident = getattr(node, "id", None) or getattr(node, "name", None) or "anon"
        act = ActivationRecord(id=ident, node=node, parent=parent)
        act.local_data.update(
            DocumentContext._extract_datamodel(node, evaluator, allow_unsafe_eval)
        )

        for t in getattr(node, "transition", []):
            trans = TransitionSpec(
                event=getattr(t, "event", None),
                target=list(getattr(t, "target", [])),
                cond=getattr(t, "cond", None),
                container=t,
            )
            act.transitions.append(trans)

        # Collect invocations declared on state-like nodes
        try:
            invokes = getattr(node, "invoke", [])
            if invokes:
                act.invokes = list(invokes)
        except Exception:
            pass

        for child in getattr(node, "state", []):
            act.add_child(
                DocumentContext._build_activation_tree(
                    child, act, evaluator, allow_unsafe_eval
                )
            )
        for child in getattr(node, "parallel", []):
            act.add_child(
                DocumentContext._build_activation_tree(
                    child, act, evaluator, allow_unsafe_eval
                )
            )
        for child in getattr(node, "final", []):
            act.add_child(
                DocumentContext._build_activation_tree(
                    child, act, evaluator, allow_unsafe_eval
                )
            )
        for child in getattr(node, "history", []):
            act.add_child(
                DocumentContext._build_activation_tree(
                    child, act, evaluator, allow_unsafe_eval
                )
            )
        return act

    @staticmethod
    def _extract_datamodel(
        node: SCXMLNode,
        evaluator: SafeExpressionEvaluator,
        allow_unsafe_eval: bool,
    ) -> Dict[str, Any]:
        """Return a dict mapping data IDs to values for *node*'s datamodel."""
        result: Dict[str, Any] = {}
        for dm in getattr(node, "datamodel", []):
            for data in dm.data:
                value: Any = None
                if data.expr is not None:
                    try:
                        value = DocumentContext._evaluate_static(
                            data.expr, {}, evaluator, allow_unsafe_eval
                        )
                    except (SafeEvaluationError, Exception):
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

    @staticmethod
    def _evaluate_static(
        expr: str,
        env: Mapping[str, Any],
        evaluator: SafeExpressionEvaluator,
        allow_unsafe_eval: bool,
    ) -> Any:
        """Evaluate ``expr`` during context construction."""

        if allow_unsafe_eval:
            return eval(expr, {}, dict(env))
        return evaluator.evaluate(expr, env)

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
        env = self._scope_env(act)
        try:
            value = self._evaluate_expr(expr, env)
            if isinstance(value, bool):
                return value
            # Non-boolean cond: treat as false and raise error.execution
            self._emit_error("error.execution", front=True)
            return False
        except (SafeEvaluationError, Exception):
            # Signal evaluation failure via error.execution and treat as false
            self._emit_error("error.execution", front=True)
            return False

    # ------------------------------------------------------------------ #
    # State entry/exit helpers
    # ------------------------------------------------------------------ #

    def _run_actions(self, container: Any, act: ActivationRecord) -> None:
        for kind, payload in self._iter_actions(container):
            self._dispatch_action(kind, payload, act)

    def _iter_actions(self, container: Any) -> List[tuple[str, Any]]:
        cache = getattr(self, "_action_cache", None)
        if cache is None:
            cache = {}
            setattr(self, "_action_cache", cache)
        key = id(container)
        if key in cache:
            return cache[key]

        sequence = self._build_action_sequence(container)
        cache[key] = sequence
        return sequence

    def _build_action_sequence(self, container: Any) -> List[tuple[str, Any]]:
        # Prefer the original XML child order when available
        try:
            order_seq = self.json_order.get(id(container))
        except Exception:
            order_seq = None
        if order_seq is not None:
            counters: Dict[str, int] = defaultdict(int)
            ordered: List[tuple[str, Any]] = []
            for local in order_seq:
                action = self._lookup_action(container, local, counters)
                if action is not None:
                    ordered.append(action)
            return ordered

        raw = self.json_lookup.get(id(container))
        if isinstance(raw, dict):
            ordered = self._build_action_sequence_from_json(container, raw)
            if ordered is not None:
                return ordered

        if hasattr(container, "__dataclass_fields__"):
            dataclass_obj = container
        elif hasattr(container, "model_dump"):
            try:
                cls = getattr(dataclasses_module, type(container).__name__)
            except AttributeError:
                return []
            data = container.model_dump(mode="python")
            dataclass_obj = _ACTION_SERIALIZER._to_dataclass(cls, data)
        else:
            return []

        try:
            xml_str = _ACTION_SERIALIZER.to_string(dataclass_obj)
        except Exception:
            return []

        try:
            root = ET.fromstring(xml_str)
        except ET.ParseError:
            return []

        indices: Dict[str, int] = defaultdict(int)
        ordered: List[tuple[str, Any]] = []

        for child in list(root):
            local = self._local_name(child.tag)
            if local == "raise" and hasattr(container, "raise_value"):
                items = getattr(container, "raise_value", [])
                idx = indices["raise_value"]
                if idx < len(items):
                    ordered.append(("raise", items[idx]))
                indices["raise_value"] += 1
            elif local == "if" and hasattr(container, "if_value"):
                items = getattr(container, "if_value", [])
                idx = indices["if_value"]
                if idx < len(items):
                    ordered.append(("if", items[idx]))
                indices["if_value"] += 1
            elif local == "foreach" and hasattr(container, "foreach"):
                items = getattr(container, "foreach", [])
                idx = indices["foreach"]
                if idx < len(items):
                    ordered.append(("foreach", items[idx]))
                indices["foreach"] += 1
            elif local == "assign" and hasattr(container, "assign"):
                items = getattr(container, "assign", [])
                idx = indices["assign"]
                if idx < len(items):
                    ordered.append(("assign", items[idx]))
                indices["assign"] += 1
            elif local == "log" and hasattr(container, "log"):
                items = getattr(container, "log", [])
                idx = indices["log"]
                if idx < len(items):
                    ordered.append(("log", items[idx]))
                indices["log"] += 1
            elif local == "script" and hasattr(container, "script"):
                items = getattr(container, "script", [])
                idx = indices["script"]
                if idx < len(items):
                    ordered.append(("script", items[idx]))
                indices["script"] += 1
            elif local == "send" and hasattr(container, "send"):
                items = getattr(container, "send", [])
                idx = indices["send"]
                if idx < len(items):
                    ordered.append(("send", items[idx]))
                indices["send"] += 1
            elif local == "cancel" and hasattr(container, "cancel"):
                items = getattr(container, "cancel", [])
                idx = indices["cancel"]
                if idx < len(items):
                    ordered.append(("cancel", items[idx]))
                indices["cancel"] += 1
            elif local == "elseif" and getattr(container, "elseif", None) is not None:
                ordered.append(("elseif", container.elseif))
            elif local == "else" and getattr(container, "else_value", None) is not None:
                ordered.append(("else", container.else_value))
            else:
                # ignore unsupported executable content for now
                continue

        return ordered

    @staticmethod
    def _local_name(tag: str) -> str:
        return tag.rsplit("}", 1)[-1] if "}" in tag else tag

    def _build_action_sequence_from_json(
        self, container: Any, raw: Dict[str, Any]
    ) -> Optional[List[tuple[str, Any]]]:
        if "elseif" in raw or "else_value" in raw:
            return None

        # Only use JSON ordering when the structure contains a single action type;
        # mixed types rely on XML round-tripping for fidelity.
        action_keys = [key for key in raw.keys() if key in {
            "raise_value",
            "if_value",
            "foreach",
            "assign",
            "log",
            "script",
            "send",
            "cancel",
        }]
        if len(set(action_keys)) <= 1:
            ordered: List[tuple[str, Any]] = []
            list_map: Dict[str, tuple[str, str]] = {
                "raise_value": ("raise_value", "raise"),
                "if_value": ("if_value", "if"),
                "foreach": ("foreach", "foreach"),
                "assign": ("assign", "assign"),
                "log": ("log", "log"),
                "script": ("script", "script"),
                "send": ("send", "send"),
                "cancel": ("cancel", "cancel"),
            }
            for key in action_keys:
                attr_name, action_kind = list_map[key]
                items = list(getattr(container, attr_name, []) or [])
                for item in items:
                    ordered.append((action_kind, item))
            return ordered

        return None

    def _dispatch_action(self, kind: str, payload: Any, act: ActivationRecord) -> None:
        if kind == "assign":
            self._do_assign(payload, act)
        elif kind == "log":
            self._do_log(payload, act)
        elif kind == "raise":
            self.enqueue(payload.event)
        elif kind == "if":
            self._do_if(payload, act)
        elif kind == "foreach":
            self._do_foreach(payload, act)
        elif kind == "send":
            self._do_send(payload, act)
        elif kind == "cancel":
            self._do_cancel(payload, act)
        elif kind == "script":
            self._do_script(payload, act)
        else:
            logger.debug("Ignoring unsupported executable action: %s", kind)

    def _do_if(self, block: Any, act: ActivationRecord) -> None:
        branches = self._split_if_branches(block)
        executed = False
        for branch in branches:
            kind = branch["kind"]
            if kind in {"if", "elseif"}:
                cond_expr = branch.get("cond") or "False"
                try:
                    branch_active = bool(self._evaluate_expr(cond_expr, self._scope_env(act)))
                except (SafeEvaluationError, Exception):
                    branch_active = False
            else:  # else
                branch_active = not executed

            if not branch_active:
                continue

            executed = True
            for action_kind, payload in branch["actions"]:
                self._dispatch_action(action_kind, payload, act)

    def _do_foreach(self, block: Any, act: ActivationRecord) -> None:
        env = self._scope_env(act)
        try:
            iterable = self._evaluate_expr(block.array or "[]", env)
        except (SafeEvaluationError, Exception):
            iterable = []
            self._emit_error("error.execution", front=True)
        if iterable is None:
            return
        # Validate index/item identifiers
        def _valid_ident(name: str) -> bool:
            return isinstance(name, str) and re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name) is not None

        index_name = getattr(block, "index", None)
        item_name = getattr(block, "item", None)
        if (index_name and not _valid_ident(index_name)) or (item_name and not _valid_ident(item_name)):
            self._emit_error("error.execution", front=True)
            return

        try:
            iterator = list(iterable)
        except TypeError:
            try:
                iterator = list(iter(iterable))
            except TypeError:
                self._emit_error("error.execution", front=True)
                return
        for idx, item in enumerate(iterator):
            if index_name:
                self._set_variable(index_name, idx, act)
            if item_name:
                self._set_variable(item_name, item, act)
            for kind, payload in self._iter_actions(block):
                self._dispatch_action(kind, payload, act)

    def _do_send(self, send: Any, act: ActivationRecord) -> None:
        env = self._scope_env(act)
        event_name = getattr(send, "event", None)
        if event_name is None and getattr(send, "eventexpr", None) is not None:
            try:
                event_name = self._evaluate_expr(send.eventexpr, env)
            except (SafeEvaluationError, Exception):
                event_name = None
        if not event_name:
            logger.warning("<send> missing event name; action skipped")
            return

        target = getattr(send, "target", None)
        if target is None and getattr(send, "targetexpr", None) is not None:
            try:
                target = self._evaluate_expr(send.targetexpr, env)
            except (SafeEvaluationError, Exception):
                target = None
        # Special target to bubble to parent as an external event
        if target and str(target) in {"#_parent", "#_scxml_parent"}:
            payload = self._build_send_payload(send, env, act)
            send_id = getattr(send, "id", None)
            if not send_id:
                # mark as parent-bubble event for the invoker pump
                send_id = f"$to-parent:{uuid4()}"
            event_obj = Event(name=str(event_name), data=payload, send_id=send_id)
            # Respect delay/delayexpr semantics: schedule on the child's queue,
            # then the invoker will bubble to the parent when due.
            if getattr(send, "delayexpr", None) is not None:
                try:
                    delay_value = self._evaluate_expr(send.delayexpr, env)
                except (SafeEvaluationError, Exception):
                    delay_value = None
                delay_seconds = self._parse_delay(delay_value)
            else:
                delay_seconds = self._parse_delay(getattr(send, "delay", None))
            if delay_seconds is None:
                delay_seconds = 0.0
            self._schedule_event(event_obj, delay_seconds)
            return

        # Special target to send to invoked child(ren) from this state or nearest ancestor
        if target and str(target) in {"#_child", "#_scxml_child", "#_invokedChild"}:
            payload = self._build_send_payload(send, env, act)
            # Find invocations associated with this state or nearest ancestor with invocations
            ids: list[str] = []
            cur = act
            while cur is not None and not ids:
                ids = list(self.invocations_by_state.get(cur.id, []))
                cur = cur.parent
            if not ids:
                self._emit_error("error.communication", front=False)
                return
            for inv_id in ids:
                handler = self.invocations.get(inv_id)
                if handler:
                    try:
                        handler.send(str(event_name), payload)
                    except Exception:
                        self._emit_error("error.communication", front=False)
            return
        # Explicit target to a specific invocation by id: target="#_<id>"
        if target and isinstance(target, str) and target.startswith("#_") and target not in {"#_parent", "#_scxml_parent", "#_child", "#_scxml_child", "#_invokedChild"}:
            inv_id = target[2:]
            payload = self._build_send_payload(send, env, act)
            handler = self.invocations.get(inv_id)
            if handler:
                try:
                    handler.send(str(event_name), payload)
                except Exception:
                    self._emit_error("error.communication", front=False)
            else:
                self._emit_error("error.communication", front=False)
            return

        if target and str(target) not in {"#_internal", "_internal"}:
            logger.warning(
                "External <send> target '%s' is not supported yet; skipping", target
            )
            # Signal communication error per SCXML error event guidance
            self._emit_error("error.communication", front=False)
            return

        delay_seconds: Optional[float]
        if getattr(send, "delayexpr", None) is not None:
            try:
                delay_value = self._evaluate_expr(send.delayexpr, env)
            except (SafeEvaluationError, Exception):
                delay_value = None
            delay_seconds = self._parse_delay(delay_value)
        else:
            delay_seconds = self._parse_delay(getattr(send, "delay", None))
        if delay_seconds is None:
            logger.warning(
                "Unable to parse <send> delay '%s'; treating as immediate",
                getattr(send, "delay", None),
            )
            delay_seconds = 0.0

        send_id = getattr(send, "id", None)
        if not send_id and getattr(send, "idlocation", None):
            send_id = str(uuid4())
            self._set_variable(send.idlocation, send_id, act)

        payload = self._build_send_payload(send, env, act)
        event_obj = Event(name=str(event_name), data=payload, send_id=send_id)
        self._schedule_event(event_obj, delay_seconds)

    def _do_cancel(self, cancel: Any, act: ActivationRecord) -> None:
        env = self._scope_env(act)
        send_id = getattr(cancel, "sendid", None)
        if send_id is None and getattr(cancel, "sendidexpr", None) is not None:
            try:
                send_id = self._evaluate_expr(cancel.sendidexpr, env)
            except (SafeEvaluationError, Exception):
                send_id = None
        if not send_id:
            logger.warning("<cancel> missing send identifier; action skipped")
            return

        removed = self.events.cancel(str(send_id)) or self._cancel_delayed_event(str(send_id))
        if not removed:
            logger.warning("<cancel> could not find pending send with id '%s'", send_id)

    def _do_script(self, script: Any, act: ActivationRecord) -> None:
        logger.warning("<script> execution is not yet implemented; skipping block")

    def _build_send_payload(self, send: Any, env: Dict[str, Any], act: ActivationRecord) -> Any:
        payload: Dict[str, Any] = {}

        for param in getattr(send, "param", []) or []:
            name = getattr(param, "name", None)
            if not name:
                continue
            value: Any = None
            if getattr(param, "expr", None) is not None:
                try:
                    value = self._evaluate_expr(param.expr, env)
                except (SafeEvaluationError, Exception):
                    value = None
            elif getattr(param, "location", None):
                value = self._resolve_variable(param.location, act)
            payload[name] = value

        namelist = getattr(send, "namelist", None)
        if namelist:
            for name in namelist.split():
                payload[name] = env.get(name)

        content_items = getattr(send, "content", []) or []
        if content_items:
            content_value = self._resolve_send_content(content_items, env)
            if content_value is not None:
                payload.setdefault("content", content_value)

        return payload or None

    def _resolve_send_content(
        self, content_items: Iterable[Any], env: Mapping[str, Any]
    ) -> Any:
        for content in content_items:
            materialized = self._materialize_content_value(content, env)
            if materialized is not None:
                return materialized
        return None

    def _materialize_content_value(
        self, content_obj: Any, env: Mapping[str, Any]
    ) -> Any:
        expr = getattr(content_obj, "expr", None)
        if expr is not None:
            try:
                return self._evaluate_expr(expr, env)
            except (SafeEvaluationError, Exception):
                return None

        raw = self.json_lookup.get(id(content_obj))
        if raw is None:
            if hasattr(content_obj, "model_dump"):
                raw = content_obj.model_dump(mode="python")
            else:
                raw = content_obj

        return self._coerce_content_node(raw)

    def _coerce_content_node(self, node: Any) -> Any:
        if isinstance(node, dict):
            if "content" in node:
                values = [self._coerce_content_node(item) for item in node["content"]]
                if not values:
                    return ""
                if all(isinstance(value, str) for value in values):
                    return "".join(values)
                return [value for value in values if value is not None]

            filtered: Dict[str, Any] = {}
            for key, value in node.items():
                if key == "other_attributes" and not value:
                    continue
                filtered[key] = self._coerce_content_node(value)
            return filtered

        if isinstance(node, list):
            values = [self._coerce_content_node(item) for item in node]
            if not values:
                return []
            if all(isinstance(value, str) for value in values):
                return "".join(values)
            return [value for value in values if value is not None]

        return node

    def _split_if_branches(self, block: Any) -> List[Dict[str, Any]]:
        order_seq = self.json_order.get(id(block))
        if order_seq is None:
            try:
                cls = getattr(dataclasses_module, type(block).__name__)
            except AttributeError:
                return []
            data = block.model_dump(mode="python")
            dataclass_obj = _ACTION_SERIALIZER._to_dataclass(cls, data)
            try:
                xml_str = _ACTION_SERIALIZER.to_string(dataclass_obj)
                root = ET.fromstring(xml_str)
                order_seq = [self._local_name(child.tag) for child in list(root)]
            except Exception:
                order_seq = []

        counters: Dict[str, int] = defaultdict(int)
        branches: List[Dict[str, Any]] = [
            {"kind": "if", "cond": block.cond, "actions": []}
        ]
        current = branches[0]

        for local in order_seq:
            if local == "elseif":
                cond = getattr(block.elseif, "cond", None) if getattr(block, "elseif", None) else None
                current = {"kind": "elseif", "cond": cond, "actions": []}
                branches.append(current)
                continue
            if local == "else":
                current = {"kind": "else", "cond": None, "actions": []}
                branches.append(current)
                continue

            action = self._lookup_action(block, local, counters)
            if action is not None:
                current["actions"].append(action)

        return branches

    def _lookup_action(
        self,
        container: Any,
        local: str,
        counters: Dict[str, int],
    ) -> Optional[tuple[str, Any]]:
        mapping: Dict[str, tuple[str, str]] = {
            "raise": ("raise_value", "raise"),
            "if": ("if_value", "if"),
            "foreach": ("foreach", "foreach"),
            "assign": ("assign", "assign"),
            "log": ("log", "log"),
            "script": ("script", "script"),
            "send": ("send", "send"),
            "cancel": ("cancel", "cancel"),
        }
        if local not in mapping:
            return None
        attr_name, kind = mapping[local]
        items = getattr(container, attr_name, []) or []
        idx = counters[attr_name]
        counters[attr_name] += 1
        if idx >= len(items):
            return None
        return kind, items[idx]

    def _set_variable(self, name: str, value: Any, act: ActivationRecord) -> None:
        for frame in reversed(act.path()):
            if name in frame.local_data:
                frame.local_data[name] = value
                return
        if name in self.data_model:
            self.data_model[name] = value
        else:
            # Default to the global datamodel for new variables
            self.data_model[name] = value

    def _resolve_variable(self, name: str, act: ActivationRecord) -> Any:
        env = self._scope_env(act)
        return env.get(name)

    def _schedule_event(self, event: Event, delay: float) -> None:
        if delay <= 0:
            self.events.push(event)
            return
        if self._use_wall_clock:
            self._timer_now = time.monotonic()
        due = self._timer_now + delay
        self.delayed_events.append((due, event))
        self.delayed_events.sort(key=lambda item: item[0])

    def _cancel_delayed_event(self, send_id: str) -> bool:
        removed = False
        remaining: List[tuple[float, Event]] = []
        for due, evt in self.delayed_events:
            if not removed and evt.send_id == send_id:
                removed = True
                continue
            remaining.append((due, evt))
        self.delayed_events = remaining
        return removed

    def _release_delayed_events(self) -> None:
        if not self.delayed_events:
            return
        if self._use_wall_clock:
            self._timer_now = time.monotonic()
        ready: List[tuple[float, Event]] = []
        remaining: List[tuple[float, Event]] = []
        for due, evt in self.delayed_events:
            if due <= self._timer_now:
                ready.append((due, evt))
            else:
                remaining.append((due, evt))
        self.delayed_events = remaining
        for _, evt in sorted(ready, key=lambda item: item[0]):
            self.events.push(evt)

    def advance_time(self, seconds: float) -> None:
        if seconds < 0:
            return
        self._use_wall_clock = False
        self._timer_now += seconds
        self._release_delayed_events()
        # Propagate time to active invocations (child machines)
        for handler in list(self.invocations.values()):
            try:
                handler.advance_time(seconds)
            except Exception:
                continue

    # -------------------------------
    # Invoke lifecycle
    # -------------------------------
    def _start_invocations_for_state(self, act: ActivationRecord) -> None:
        for inv in getattr(act, "invokes", []) or []:
            explicit_id = getattr(inv, "id", None)
            inv_id = explicit_id or f"$invoke-{uuid4()}"
            # Reflect the chosen invocation id into idlocation, when provided
            if getattr(inv, "idlocation", None):
                self._set_variable(inv.idlocation, inv_id, act)

            # Evaluate type and src if expressions provided
            env = self._scope_env(act)
            inv_type = getattr(inv, "type_value", None) or "scxml"
            if getattr(inv, "typeexpr", None):
                try:
                    inv_type = str(self._evaluate_expr(inv.typeexpr, env))
                except Exception:
                    # signal evaluation failure
                    try:
                        self._emit_error("error.execution", front=True)
                    except Exception:
                        self._emit_error("error.execution", front=False)
            # Normalize well-known SCXML type URI
            if str(inv_type).strip().lower() in {"http://www.w3.org/tr/scxml/", "w3c:scxml"}:
                inv_type = "scxml"
            inv_src = getattr(inv, "src", None)
            if getattr(inv, "srcexpr", None):
                try:
                    inv_src = self._evaluate_expr(inv.srcexpr, env)
                except Exception:
                    try:
                        self._emit_error("error.execution", front=True)
                    except Exception:
                        self._emit_error("error.execution", front=False)
            # Resolve file: URIs and relative paths using the parent's base_dir
            if isinstance(inv_src, str):
                src_text = inv_src
                if src_text.startswith("file:"):
                    src_text = src_text[5:]
                try:
                    p = Path(src_text)
                    if not p.is_absolute() and self._base_dir is not None:
                        inv_src = (self._base_dir / p).resolve()
                    else:
                        inv_src = p
                except Exception:
                    pass

            payload = self._build_invoke_payload(inv, env, act)

            try:
                handler = self.invoke_registry.create(
                    inv_type, inv_src, payload, autostart=True,
                    on_done=lambda data, _id=inv_id: self._on_invoke_done(_id, data)
                )
                try:
                    mode = str(self.ordering_mode).lower()
                    # strict: enqueue child→parent events normally (tail)
                    # scion: emulate SCION by using normal enqueue for child emissions,
                    #        while done.invoke is pushed to front in _on_invoke_done.
                    # tolerant (default): be generous and use front insertion to surface
                    # child emissions earlier when charts rely on it.
                    if mode in {"strict", "scion"}:
                        handler.set_emitter(lambda e: self.events.push(e))
                    else:
                        handler.set_emitter(lambda e: getattr(self.events, 'push_front', self.events.push)(e))
                except Exception:
                    pass
                # Inform handler of invocation id for SCXML Event I/O metadata if supported
                try:
                    setattr(handler, 'invoke_id', inv_id)
                except Exception:
                    pass
                self.invocations[inv_id] = handler
                self.invocations_by_state.setdefault(act.id, []).append(inv_id)
                self._invoke_specs[inv_id] = (inv, act)
                # Record autoforward setting
                af = getattr(inv, "autoforward", None)
                self.invocations_autoforward[inv_id] = str(af).lower().endswith("true") if af is not None else False
                handler.start()
                # If a child-machine handler failed to initialize (e.g., bad src),
                # surface a communication error to the parent queue.
                try:
                    tname = getattr(handler, 'type_name', '')
                    if tname in {"scxml", "scjson"} and getattr(handler, 'child', None) is None:
                        self._emit_error("error.communication", front=False)
                except Exception:
                    pass
            except Exception:
                self.events.push(Event(name="error.communication"))
            # Process any immediately available done.invoke events so that
            # generic/specific done transitions can fire during initialization.
            try:
                while getattr(self.events, "_q", None):
                    head = self.events._q[0]
                    if not getattr(head, "name", "").startswith("done.invoke"):
                        break
                    head_evt = self.events.pop()
                    if head_evt is None:
                        break
                    # Only consume now when a transition for this event exists; otherwise
                    # keep the event queued for normal processing.
                    self._current_event = head_evt
                    sel = self._select_transition(head_evt)
                    if not sel:
                        # If an id-specific event is at the head but only a
                        # generic done.invoke transition exists, consume the
                        # next generic event now and restore the id-specific
                        # to the front.
                        name = getattr(head_evt, "name", "")
                        if name.startswith("done.invoke.") and getattr(self.events, "_q", None):
                            nxt = self.events._q[0]
                            if getattr(nxt, "name", "") == "done.invoke":
                                # Check if generic would fire
                                gen_evt = Event(name="done.invoke", data=head_evt.data, send_id=getattr(head_evt, "send_id", None))
                                sel_gen = self._select_transition(gen_evt)
                                if sel_gen:
                                    # Pop the generic event and process it
                                    _ = self.events.pop()
                                    self._current_event = gen_evt
                                    self._execute_transition(gen_evt)
                                    self._current_event = None
                                    # Restore id-specific to the front
                                    self.events.push_front(head_evt)
                                    self._current_event = None
                                    continue
                        # If a generic event is at the head but only an
                        # id-specific transition exists, consume the
                        # id-specific next and restore the generic to the
                        # front.
                        if name == "done.invoke" and getattr(self.events, "_q", None):
                            nxt = self.events._q[0]
                            if isinstance(getattr(nxt, "name", None), str) and nxt.name.startswith("done.invoke."):
                                sel_id = self._select_transition(nxt)
                                if sel_id:
                                    # Pop the id-specific now, then restore generic
                                    _ = self.events.pop()
                                    self.events.push_front(head_evt)
                                    self._current_event = nxt
                                    self._execute_transition(nxt)
                                    self._current_event = None
                                    continue
                        # put back at front and stop consuming
                        try:
                            self.events.push_front(head_evt)
                        finally:
                            self._current_event = None
                        break
                    self._execute_transition(head_evt)
                    self._current_event = None
            except Exception:
                pass

    def _build_invoke_payload(self, inv: Any, env: Dict[str, Any], act: ActivationRecord) -> Any:
        payload: Dict[str, Any] = {}
        for param in getattr(inv, "param", []) or []:
            name = getattr(param, "name", None)
            if not name:
                continue
            value: Any = None
            if getattr(param, "expr", None) is not None:
                try:
                    value = self._evaluate_expr(param.expr, env)
                except Exception:
                    value = None
            elif getattr(param, "location", None):
                value = self._resolve_variable(param.location, act)
            payload[name] = value
        namelist = getattr(inv, "namelist", None)
        if namelist:
            for name in namelist.split():
                if name not in env:
                    raise ValueError(f"namelist variable '{name}' is not defined")
                payload[name] = env.get(name)
        content_items = getattr(inv, "content", []) or []
        if content_items:
            cv = self._resolve_send_content(content_items, env)
            if cv is not None:
                payload.setdefault("content", cv)
        return payload or None

    def _on_invoke_done(self, inv_id: str, data: Any = None) -> None:
        spec_act = self._invoke_specs.get(inv_id)
        if spec_act is not None:
            spec, act = spec_act
            try:
                self._run_finalize(spec, act, inv_id, data)
            except Exception:
                pass
        # Enqueue done.invoke using the configured ordering policy.
        #
        # scion: push to front with generic before id-specific to enable
        #        same-microstep transitions following SCION's observed order.
        # tolerant: push to front only when handler indicated preference
        #           (i.e., no child→parent emissions yet); otherwise use tail.
        # strict: always use tail ordering (id-specific then generic).
        handler = self.invocations.get(inv_id)
        mode = str(getattr(self, 'ordering_mode', 'tolerant')).lower()
        prefer_front = bool(getattr(handler, '_prefer_front_done', False))
        if mode == "scion" and hasattr(self.events, 'push_front'):
            self.events.push_front(Event(name="done.invoke", data=data, send_id=inv_id))
            self.events.push_front(Event(name=f"done.invoke.{inv_id}", data=data, send_id=inv_id))
        elif prefer_front and hasattr(self.events, 'push_front'):
            self.events.push_front(Event(name=f"done.invoke.{inv_id}", data=data, send_id=inv_id))
            self.events.push_front(Event(name="done.invoke", data=data, send_id=inv_id))
        else:
            self.events.push(Event(name=f"done.invoke.{inv_id}", data=data, send_id=inv_id))
            self.events.push(Event(name="done.invoke", data=data, send_id=inv_id))
        handler = self.invocations.pop(inv_id, None)
        if handler:
            try:
                handler.stop()
            except Exception:
                pass

    def _cancel_invocations_for_state(self, act: ActivationRecord) -> None:
        ids = list(self.invocations_by_state.get(act.id, []))
        for inv_id in ids:
            handler = self.invocations.get(inv_id)
            if handler:
                try:
                    handler.cancel()
                except Exception:
                    pass
                # Execute <finalize> on cancel as per scion-core behavior
                spec_act = self._invoke_specs.get(inv_id)
                if spec_act is not None:
                    spec, inv_act = spec_act
                    try:
                        self._run_finalize(spec, inv_act, inv_id, None)
                    except Exception:
                        pass
            # Keep handler mapping for post-microstep inspection, but mark canceled via handler.cancel().
        # Clear ancestor lookup to prevent future parent->child sends to canceled invocations
        if ids:
            self.invocations_by_state[act.id] = [x for x in self.invocations_by_state.get(act.id, []) if x not in set(ids)]
        # Mark state as no longer started
        try:
            self._invocations_started_for_state.discard(act.id)
        except Exception:
            pass

    def _start_invocations_for_active_states(self) -> None:
        """Start invocations for states that are active and not yet started.

        According to spec, invokes are executed at macrostep end for states
        entered and not exited during the step.
        """
        for sid in list(self.configuration):
            act = self.activations.get(sid)
            if not act or not getattr(act, "invokes", None):
                continue
            if sid in self._invocations_started_for_state:
                continue
            self._start_invocations_for_state(act)
            self._invocations_started_for_state.add(sid)

    def _run_finalize(self, spec: Any, act: ActivationRecord, inv_id: str, data: Any) -> None:
        # Inject _event during finalize execution; use a dict for bracket access
        saved = act.local_data.pop("_event", None)
        try:
            act.local_data["_event"] = {"name": f"done.invoke.{inv_id}", "data": data}
            for fin in getattr(spec, "finalize", []) or []:
                self._run_actions(fin, act)
        finally:
            if saved is not None:
                act.local_data["_event"] = saved
            else:
                act.local_data.pop("_event", None)

    def _autoforward_event(self, evt: Event) -> None:
        # Skip obvious engine-internal categories
        name = evt.name or ""
        if (
            name.startswith("__")
            or name.startswith("error.")
            or name.startswith("done.state.")
            or name.startswith("done.invoke.")
        ):
            return
        # Forward external events to active invocations. Engines vary on
        # whether autoforward must be explicitly enabled; our tests assume
        # convenience forwarding for simple mock handlers (e.g. mock:deferred),
        # so we forward to all active invocations while preserving compatibility
        # with charts that set autoforward by simply doing the same here.
        for _inv_id, handler in list(self.invocations.items()):
            # Skip canceled/terminated handlers
            if getattr(handler, 'is_canceled', False):
                continue
            try:
                handler.send(evt.name, evt.data)
            except Exception:
                # ignore forwarding errors
                pass


    def _parse_delay(self, value: Any) -> Optional[float]:
        if value is None:
            return 0.0
        if isinstance(value, (int, float)):
            return max(0.0, float(value))
        text = str(value).strip()
        if not text:
            return 0.0
        # Accept numbers like ".5s", "0.5s", "1s", "100ms"
        match = re.fullmatch(r"((?:[0-9]*\.[0-9]+)|(?:[0-9]+))(ms|s|m|h|d)?", text)
        if not match:
            return None
        magnitude = float(match.group(1))
        unit = match.group(2) or "s"
        multiplier = {
            "ms": 0.001,
            "s": 1.0,
            "m": 60.0,
            "h": 3600.0,
            "d": 86400.0,
        }.get(unit, 1.0)
        return max(0.0, magnitude * multiplier)

    def _emit_error(self, name: str, front: bool = True, alias_front: bool = False) -> None:
        """Emit an engine error event, plus a generic alias.

        Parameters
        ----------
        name : str
            Fully qualified error name such as ``"error.execution"`` or
            ``"error.communication"``.
        front : bool
            When ``True``, insert the specific error at the front of the queue
            to prioritize its handling ahead of subsequently enqueued normal
            events. When ``False``, append it preserving document order.

        Returns
        -------
        None
            The event is enqueued for later processing.
        """
        evt = Event(name=name)
        if front and hasattr(self.events, "push_front"):
            self.events.push_front(evt)
        else:
            self.events.push(evt)
        # Also enqueue a generic 'error' for broader compatibility with
        # charts that listen for error.* without the subtype. Limit this to
        # execution errors to avoid interleaving with ordering-sensitive
        # external communication errors. Placement of the alias can be
        # requested via alias_front to satisfy specific ordering semantics
        # (e.g., startup/onentry error before previously enqueued events).
        try:
            if name == "error.execution":
                alias = Event(name="error")
                if alias_front and hasattr(self.events, "push_front"):
                    self.events.push_front(alias)
                else:
                    self.events.push(alias)
        except Exception:
            pass

    def _scope_env(self, act: ActivationRecord) -> Dict[str, Any]:
        env: Dict[str, Any] = {}
        env.update(self.data_model)
        for frame in act.path():
            env.update(frame.local_data)
        env.setdefault("In", self._in_state)
        # Provide _event mapping for expressions
        cur_evt = getattr(self, "_current_event", None)
        if cur_evt is not None:
            payload = self._wrap_event_payload(cur_evt.data) if cur_evt.data is not None else None
            ev_map: Dict[str, Any] = {"name": cur_evt.name, "data": payload}
            invokeid: str | None = None
            if getattr(cur_evt, "invokeid", None):
                try:
                    invokeid = str(cur_evt.invokeid)
                except Exception:
                    invokeid = None
            elif cur_evt.name and cur_evt.name.startswith("done.invoke."):
                parts = cur_evt.name.split(".", 2)
                if len(parts) == 3:
                    invokeid = parts[2]
            elif cur_evt.name == "done.invoke" and getattr(cur_evt, "send_id", None):
                try:
                    invokeid = str(cur_evt.send_id)
                except Exception:
                    invokeid = None
            if invokeid:
                ev_map["invokeid"] = invokeid
            # Propagate origin/origintype when present (SCXML Event I/O metadata)
            if getattr(cur_evt, "origin", None) is not None:
                ev_map["origin"] = cur_evt.origin
            if getattr(cur_evt, "origintype", None) is not None:
                ev_map["origintype"] = cur_evt.origintype
            try:
                env["_event"] = SimpleNamespace(**ev_map)
            except Exception:
                env["_event"] = ev_map
        return env

    def _evaluate_expr(self, expr: str, env: Mapping[str, Any]) -> Any:
        """Evaluate ``expr`` with the configured sandbox or raw ``eval``."""

        if self.allow_unsafe_eval:
            return eval(expr, {}, dict(env))
        return self.evaluator.evaluate(expr, env)

    def _in_state(self, state_id: str) -> bool:
        """Return ``True`` when ``state_id`` is currently active."""

        return state_id in self.configuration

    def _do_assign(self, assign: Any, act: ActivationRecord) -> None:
        env = self._scope_env(act)
        value: Any = None
        if assign.expr is not None:
            try:
                value = self._evaluate_expr(assign.expr, env)
            except (SafeEvaluationError, Exception):
                value = assign.expr
                self._emit_error("error.execution", front=True)
        elif assign.content:
            value = "".join(str(x) for x in assign.content)
        target = assign.location
        # Assign only to existing locations per spec; otherwise raise error
        # and do not create a new variable here.
        for frame in reversed(act.path()):
            if target in frame.local_data:
                frame.local_data[target] = value
                return
        if target in self.data_model:
            self.data_model[target] = value
            return
        # Invalid location: emit execution error and ensure the alias 'error'
        # is prioritized before any previously enqueued events from onentry.
        self._emit_error("error.execution", front=True, alias_front=True)

    def _do_log(self, log: Any, act: ActivationRecord) -> None:
        env = self._scope_env(act)
        value = None
        if log.expr is not None:
            try:
                value = self._evaluate_expr(log.expr, env)
            except (SafeEvaluationError, Exception):
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
        # If we have just entered a <final> state, raise done.state events
        # and mark completion for the containing state/parallel.
        if isinstance(act.node, ScxmlFinalType):
            self._handle_entered_final(act)

    def _handle_entered_final(self, final_act: ActivationRecord) -> None:
        """Handle entry into a ``<final>`` state.

        Generates a ``done.state.<parentId>`` internal event with optional
        donedata payload, marks the containing state as finalized, and emits
        ``done.state.<parallelId>`` for any ancestor parallel whose regions
        have all completed.

        :param final_act: Activation corresponding to the entered ``<final>``.
        :returns: ``None``
        """

        parent = final_act.parent
        if not parent:
            return

        # Build donedata payload (if any) for the parent's done event
        env = self._scope_env(parent)
        payload = self._build_donedata_payload(final_act.node, env, parent)

        # Emit done.state for the immediate parent compound state
        self.events.push(Event(name=f"done.state.{parent.id}", data=payload))

        # Mark the parent as final; this may propagate to ancestors (e.g. parallel)
        parent.mark_final()

        # For any ancestor <parallel> that is now complete, emit its done.state
        cur = parent.parent
        while cur is not None:
            if isinstance(cur.node, ScxmlParallelType):
                if all(child.status is ActivationStatus.FINAL for child in cur.children):
                    self.events.push(Event(name=f"done.state.{cur.id}", data=None))
            cur = cur.parent

    def _build_donedata_payload(self, final_node: ScxmlFinalType, env: Mapping[str, Any], act: ActivationRecord) -> Any:
        """Materialize a ``<donedata>`` payload for a containing state's done event.

        Rules follow SCXML semantics:
        - If ``<donedata><content>`` is present, the event's data is exactly the
          materialized content value (string/object), ignoring ``<param>``.
        - Otherwise, ``<param>`` entries are evaluated and returned as a dict.

        :param final_node: The ``<final>`` element being entered.
        :param env: Current evaluation environment for expressions.
        :param act: Activation in whose lexical scope evaluation occurs.
        :returns: Arbitrary JSON-serializable payload or ``None``.
        """
        try:
            donelist = getattr(final_node, "donedata", []) or []
        except Exception:
            donelist = []

        payload: Any = None

        # The schema allows at most one <donedata>
        done = donelist[0] if donelist else None
        if done is None:
            return None

        # If there is content, it defines the full value of event.data
        content_obj = getattr(done, "content", None)
        if content_obj is not None:
            materialized = self._materialize_content_value(content_obj, env)
            return materialized

        # Otherwise collect named params into a dict
        result: Dict[str, Any] = {}
        for param in getattr(done, "param", []) or []:
            name = getattr(param, "name", None)
            if not name:
                continue
            value: Any = None
            if getattr(param, "expr", None) is not None:
                try:
                    value = self._evaluate_expr(param.expr, env)
                except (SafeEvaluationError, Exception):
                    value = None
            elif getattr(param, "location", None):
                value = self._resolve_variable(param.location, act)
            result[name] = value

        return result or None

    def _exit_state(self, act: ActivationRecord) -> Set[str]:
        """Exit ``act`` and return the set of activation IDs that became inactive."""

        if act.id not in self.configuration:
            return set()

        exited: Set[str] = set()
        active_children = [c.id for c in act.children if c.id in self.configuration]
        if getattr(act.node, "history", []):
            self.history[act.id] = active_children
            # Deep history snapshot: collect active descendant leaves under this state
            try:
                self.history_deep[act.id] = self._active_leaves_under(act)
            except Exception:
                self.history_deep[act.id] = list(active_children)
        # Cancel invocations for this state prior to onexit
        self._cancel_invocations_for_state(act)
        for cid in active_children:
            child = self.activations[cid]
            exited.update(self._exit_state(child))
        for onexit in getattr(act.node, "onexit", []):
            self._run_actions(onexit, act)
        self.configuration.discard(act.id)
        exited.add(act.id)
        return exited

    def _snapshot_active_histories(self) -> None:
        """Refresh shallow and deep history caches for active states."""

        for state_id in list(self.configuration):
            act = self.activations.get(state_id)
            if not act or not getattr(act.node, "history", []):
                continue
            active_children = [c.id for c in act.children if c.id in self.configuration]
            self.history[act.id] = list(active_children)
            try:
                self.history_deep[act.id] = self._active_leaves_under(act)
            except Exception:
                self.history_deep[act.id] = list(active_children)

    def _enter_history(self, act: ActivationRecord) -> None:
        parent = act.parent
        if not parent:
            return
        if parent.id not in self.configuration:
            self.configuration.add(parent.id)
            for onentry in getattr(parent.node, "onentry", []):
                self._run_actions(onentry, parent)

        # Decide shallow vs deep restoration
        from .pydantic import HistoryTypeDatatype  # avoid top-level import cycle
        hist_type = getattr(act.node, "type_value", None)

        targets: List[str] | None
        if hist_type == HistoryTypeDatatype.DEEP:
            targets = self.history_deep.get(parent.id)
        else:
            targets = self.history.get(parent.id)

        # Fallback to default transition when no snapshot exists
        default_transition = None
        if not targets:
            transitions = getattr(act.node, "transition", [])
            if isinstance(transitions, list):
                default_transition = transitions[0] if transitions else None
            else:
                default_transition = transitions
            if default_transition is not None:
                targets = list(getattr(default_transition, "target", []))
            else:
                targets = []

        if hist_type == HistoryTypeDatatype.DEEP and targets:
            for tid in targets:
                target_act = self.activations.get(tid)
                if not target_act:
                    continue
                for node in self._path_from_parent(parent, target_act):
                    if node.id not in self.configuration:
                        self._enter_state_exact(node)
        else:
            # Shallow history: optionally execute default transition actions
            if default_transition is not None:
                for kind, payload in self._iter_actions(default_transition):
                    self._dispatch_action(kind, payload, parent)
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
        self._snapshot_active_histories()
        exit_list = self._compute_exit_set(source, trans.target)
        exited_ids: Set[str] = set()
        for act in exit_list:
            if act.id in self.configuration:
                exited_ids.update(self._exit_state(act))

        # Execute transition body (executable content) in document order
        container = getattr(trans, "container", None)
        if container is not None:
            for kind, payload in self._iter_actions(container):
                self._dispatch_action(kind, payload, source)

        enter_list = self._compute_entry_list(source, trans.target)
        entered_ids: Set[str] = set()
        for act in enter_list:
            before_enter = set(self.configuration)
            self._enter_target(act)
            after_enter = set(self.configuration)
            entered_ids.update(after_enter - before_enter)

        return entered_ids, exited_ids

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

        # Targetless transitions are internal and must not exit any state.
        if not targets:
            return []
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
                if (
                    isinstance(target_act.node, History)
                    and target_act.parent is not None
                    and source.id == target_act.parent.id
                ):
                    for child in target_act.parent.children:
                        if child.id in self.configuration:
                            exit_set[child.id] = child
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
    def from_json_file(
        cls,
        path: str | Path,
        *,
        allow_unsafe_eval: bool = False,
        evaluator: SafeExpressionEvaluator | None = None,
        execution_mode: ExecutionMode | str = ExecutionMode.STRICT,
    ) -> "DocumentContext":
        text = Path(path).read_text(encoding="utf-8")
        data = cls._prepare_raw_data(json.loads(text))
        doc = Scxml.model_validate(data)
        mode = (
            execution_mode
            if isinstance(execution_mode, ExecutionMode)
            else ExecutionMode(str(execution_mode).lower())
        )
        return cls._from_model(
            doc,
            data,
            allow_unsafe_eval=allow_unsafe_eval,
            evaluator=evaluator,
            execution_mode=mode,
            source_xml=None,
        )

    @classmethod
    def from_xml_file(
        cls,
        path: str | Path,
        *,
        allow_unsafe_eval: bool = False,
        evaluator: SafeExpressionEvaluator | None = None,
        execution_mode: ExecutionMode | str = ExecutionMode.STRICT,
    ) -> "DocumentContext":
        mode = (
            execution_mode
            if isinstance(execution_mode, ExecutionMode)
            else ExecutionMode(str(execution_mode).lower())
        )
        handler = SCXMLDocumentHandler(fail_on_unknown_properties=mode is ExecutionMode.STRICT)
        xml_str = Path(path).read_text(encoding="utf-8")
        json_str = handler.xml_to_json(xml_str)
        data = cls._prepare_raw_data(json.loads(json_str))
        doc = Scxml.model_validate(data)
        ctx = cls._from_model(
            doc,
            data,
            allow_unsafe_eval=allow_unsafe_eval,
            evaluator=evaluator,
            execution_mode=mode,
            source_xml=xml_str,
            base_dir=Path(path).resolve().parent,
        )
        return ctx

    @classmethod
    def from_xml_string(
        cls,
        xml_str: str,
        *,
        allow_unsafe_eval: bool = False,
        evaluator: SafeExpressionEvaluator | None = None,
        execution_mode: ExecutionMode | str = ExecutionMode.STRICT,
    ) -> "DocumentContext":
        """Create a DocumentContext from an XML string.

        Parameters
        ----------
        xml_str: str
            The SCXML document as a string.
        allow_unsafe_eval: bool
            Use Python eval for expressions if True.
        evaluator: SafeExpressionEvaluator | None
            Optional evaluator instance.
        execution_mode: ExecutionMode | str
            Strict or lax parsing.

        Returns
        -------
        DocumentContext
            Initialized runtime context.
        """
        mode = (
            execution_mode
            if isinstance(execution_mode, ExecutionMode)
            else ExecutionMode(str(execution_mode).lower())
        )
        handler = SCXMLDocumentHandler(fail_on_unknown_properties=mode is ExecutionMode.STRICT)
        json_str = handler.xml_to_json(xml_str)
        data = cls._prepare_raw_data(json.loads(json_str))
        doc = Scxml.model_validate(data)
        ctx = cls._from_model(
            doc,
            data,
            allow_unsafe_eval=allow_unsafe_eval,
            evaluator=evaluator,
            execution_mode=mode,
            source_xml=xml_str,
            base_dir=None,
        )
        return ctx

    @classmethod
    def _from_model(
        cls,
        doc: Scxml,
        raw_data: Dict[str, Any],
        *,
        allow_unsafe_eval: bool,
        evaluator: SafeExpressionEvaluator | None,
        execution_mode: ExecutionMode,
        source_xml: str | None = None,
        base_dir: Path | None = None,
        defer_initial: bool = False,
    ) -> "DocumentContext":
        evaluator = evaluator or SafeExpressionEvaluator()
        lookup, path_map = cls._build_json_lookup(doc, raw_data)
        root_state = cls._build_activation_tree(doc, None, evaluator, allow_unsafe_eval)
        ctx = cls(
            doc=doc,
            root_activation=root_state,
            execution_mode=execution_mode,
            allow_unsafe_eval=allow_unsafe_eval,
            evaluator=evaluator,
            json_lookup=lookup,
        )
        try:
            ctx._base_dir = base_dir
        except Exception:
            ctx._base_dir = None
        ctx._action_cache = {}
        ctx.json_order = cls._build_order_map(raw_data, path_map, source_xml)
        ctx.data_model = root_state.local_data
        ctx._index_activations(root_state)
        try:
            ctx._leaf_ids = ctx.leaf_state_ids()
        except Exception:
            ctx._leaf_ids = set()
        ctx.configuration.add(root_state.id)
        if not defer_initial:
            ctx._enter_initial_states(root_state)
            ctx.drain_internal()
            # Start invocations for active states after initial macrostep
            try:
                ctx._start_invocations_for_active_states()
            except Exception:
                pass
        return ctx

    @staticmethod
    def _build_json_lookup(model: Any, raw: Any) -> tuple[Dict[int, Any], Dict[int, Tuple[tuple[str, int], ...]]]:
        lookup: Dict[int, Any] = {}
        path_map: Dict[int, Tuple[tuple[str, int], ...]] = {}

        def walk(obj: Any, blob: Any, path: List[tuple[str, int]]) -> None:
            if isinstance(obj, BaseModel):
                lookup[id(obj)] = blob
                path_map[id(obj)] = tuple(path)
                if isinstance(blob, dict):
                    for name in obj.__class__.model_fields:
                        value = getattr(obj, name, None)
                        raw_value = blob.get(name) if isinstance(blob, dict) else None
                        if isinstance(value, list):
                            raw_list = raw_value or []
                            for idx, (sub_obj, sub_blob) in enumerate(zip(value, raw_list)):
                                walk(sub_obj, sub_blob, path + [(name, idx)])
                        elif isinstance(value, BaseModel):
                            walk(value, raw_value, path + [(name, 0)])
                return
            if isinstance(obj, list) and isinstance(blob, list):
                for idx, (sub_obj, sub_blob) in enumerate(zip(obj, blob)):
                    walk(sub_obj, sub_blob, path + [("item", idx)])

        walk(model, raw, [])
        return lookup, path_map

    @staticmethod
    def _prepare_raw_data(data: Any) -> Any:
        def wrap_content_list(items: List[Any]) -> List[Any]:
            new_items: List[Any] = []
            for item in items:
                if isinstance(item, str):
                    new_items.append({"content": [item]})
                elif isinstance(item, dict):
                    content_value = item.get("content")
                    if isinstance(content_value, str):
                        item = {**item, "content": [content_value]}
                    elif isinstance(content_value, list):
                        item = {**item, "content": wrap_content_list(content_value)}
                    new_items.append(item)
                else:
                    new_items.append(walk(item))
            return new_items

        def walk(node: Any, skip_content: bool = False) -> Any:
            if isinstance(node, dict):
                updated: Dict[str, Any] = {}
                for key, value in node.items():
                    if key == "content" and isinstance(value, list) and not skip_content:
                        processed = wrap_content_list(value)
                        updated[key] = [
                            walk(elem, skip_content=True) if isinstance(elem, (dict, list)) else elem
                            for elem in processed
                        ]
                        continue
                    if key == "assign" and isinstance(value, list):
                        updated[key] = []
                        for item in value:
                            if isinstance(item, dict):
                                other_attrs = item.get("other_attributes")
                                if "location" not in item and isinstance(other_attrs, dict):
                                    location_value = other_attrs.pop("id", None)
                                    if location_value is not None:
                                        item["location"] = location_value
                                updated[key].append(walk(item))
                            else:
                                updated[key].append(walk(item))
                        continue
                    updated[key] = walk(value)
                return updated
            if isinstance(node, list):
                return [walk(item) for item in node]
            return node

        return walk(data)

    @staticmethod
    def _build_order_map(
        raw_data: Dict[str, Any],
        path_map: Dict[int, Tuple[tuple[str, int], ...]],
        source_xml: str | None,
    ) -> Dict[int, List[str]]:
        if source_xml is not None:
            xml_candidates = [source_xml]
        else:
            try:
                xml_candidates = [_ACTION_SERIALIZER.json_to_xml(json.dumps(raw_data, default=str))]
            except Exception:
                xml_candidates = []

        tag_to_field = {
            "state": "state",
            "onentry": "onentry",
            "onexit": "onexit",
            "if": "if_value",
            "foreach": "foreach",
            "raise": "raise_value",
            "log": "log",
            "assign": "assign",
            "script": "script",
            "send": "send",
            "cancel": "cancel",
            "transition": "transition",
            "final": "final",
            "parallel": "parallel",
            "history": "history",
            "datamodel": "datamodel",
            "data": "data",
        }

        list_fields = {
            "state",
            "onentry",
            "onexit",
            "if_value",
            "foreach",
            "raise_value",
            "log",
            "assign",
            "script",
            "send",
            "cancel",
            "transition",
            "final",
            "parallel",
            "history",
            "datamodel",
            "data",
        }

        order_by_path: Dict[Tuple[tuple[str, int], ...], List[str]] = {}

        for candidate in xml_candidates:
            try:
                root = ET.fromstring(candidate)
            except ET.ParseError:
                continue

            def traverse(elem: ET.Element, path: List[tuple[str, int]]) -> None:
                local = DocumentContext._local_name(elem.tag)
                field = tag_to_field.get(local, local)
                child_tags = [DocumentContext._local_name(child.tag) for child in list(elem)]
                order_by_path[tuple(path)] = child_tags

                child_counts: Dict[str, int] = defaultdict(int)
                for child in list(elem):
                    child_local = DocumentContext._local_name(child.tag)
                    child_field = tag_to_field.get(child_local, child_local)
                    if child_field in list_fields:
                        idx = child_counts[child_field]
                        child_counts[child_field] += 1
                        traverse(child, path + [(child_field, idx)])
                    else:
                        traverse(child, path + [(child_field, 0)])

            traverse(root, [])

        order_map: Dict[int, List[str]] = {}
        for obj_id, p in path_map.items():
            if p in order_by_path:
                order_map[obj_id] = order_by_path[p]

        return order_map

    def run(self, steps: int | None = None) -> None:
        """Execute microsteps until the queue is empty or ``steps`` is reached.

        :param steps: Maximum number of microsteps to run, or ``None`` for no
            limit.
        :returns: ``None``
        """

        count = 0
        self._release_delayed_events()
        while self.events and (steps is None or count < steps):
            self.microstep()
            count += 1

    # -------------------------------
    # Helpers for deep history
    # -------------------------------
    def _active_leaves_under(self, act: ActivationRecord) -> List[str]:
        """Return IDs of active leaf descendants under ``act``.

        :param act: Activation serving as the subtree root.
        :returns: Sorted list of leaf activation IDs currently active.
        """
        leaves: List[str] = []

        def descend(node: ActivationRecord) -> None:
            active_child_ids = [c.id for c in node.children if c.id in self.configuration]
            if not active_child_ids:
                if node.id in self.configuration and node.id != act.id:
                    leaves.append(node.id)
                return
            for cid in active_child_ids:
                child = self.activations[cid]
                descend(child)

        descend(act)
        return sorted(set(leaves), key=self._activation_order_key)

    def leaf_state_ids(self) -> Set[str]:
        """Return the set of leaf state IDs in the chart.

        A leaf is any activation whose node is a ``<final>`` element or a
        ``<state>``/``<parallel>`` without child ``state`` or ``parallel``.

        Returns
        -------
        set[str]
            Identifiers for leaf states in deterministic activation order.
        """
        leaves: list[str] = []
        for act in self.activations.values():
            node = getattr(act, "node", None)
            # finals are leaves
            if isinstance(node, ScxmlFinalType):
                if act.id:
                    leaves.append(act.id)
                continue
            # states/parallels without state/parallel children are leaves
            has_child_states = bool(getattr(node, "state", [])) or bool(
                getattr(node, "parallel", [])
            ) or bool(getattr(node, "final", []))
            if getattr(act, "id", None) and not has_child_states:
                leaves.append(act.id)
        return set(sorted(set(leaves), key=self._activation_order_key))

    def _path_from_parent(self, parent: ActivationRecord, target: ActivationRecord) -> List[ActivationRecord]:
        """Compute the entry chain from ``parent`` to ``target`` (exclusive of parent).

        :param parent: Ancestor activation that is already active.
        :param target: Descendant activation to restore.
        :returns: List of activations from the child of ``parent`` down to ``target``.
        """
        path: List[ActivationRecord] = []
        cur = target
        while cur is not None and cur is not parent:
            path.append(cur)
            cur = cur.parent
        path.reverse()
        return path

    def _enter_state_exact(self, act: ActivationRecord) -> None:
        if act.id in self.configuration:
            return
        self.configuration.add(act.id)
        for onentry in getattr(act.node, "onentry", []):
            self._run_actions(onentry, act)
