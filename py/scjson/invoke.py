"""
Agent Name: python-invoke

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Lightweight invocation scaffolding used by the Python engine.

This module defines a minimal :class:`InvokeRegistry` with mock handlers so the
engine can start/cancel invocations, support `<finalize>`, and emit
`done.invoke.<id>` events without requiring a full external processor.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional
from pathlib import Path

from typing import TYPE_CHECKING
from .events import Event
if TYPE_CHECKING:  # pragma: no cover - type hints only
    from .context import DocumentContext


OnDone = Callable[[Any], None]


class InvokeHandler:
    """Base class for invocation handlers.

    Parameters
    ----------
    type_name : str
        The invocation type (e.g., ``scxml`` or a URI-like string).
    src : Any
        The source or configuration associated with the invocation.
    payload : Any
        Initial payload produced from `<param>`, `namelist`, and `<content>`.
    on_done : Callable[[Any], None]
        Callback invoked when the handler completes; receives optional data.
    """

    def __init__(self, type_name: str, src: Any, payload: Any, on_done: Optional[OnDone] = None) -> None:
        self.type_name = type_name
        self.src = src
        self.payload = payload
        self._on_done = on_done or (lambda data: None)
        self._emit: Callable[[Event], None] = lambda evt: None

    def start(self) -> None:  # noqa: D401
        """Start the invocation (no-op by default)."""

    def stop(self) -> None:  # noqa: D401
        """Stop the invocation if running (no-op by default)."""

    def cancel(self) -> None:  # noqa: D401
        """Cancel the invocation (no-op by default)."""

    def send(self, name: str, data: Any | None = None) -> None:  # noqa: D401
        """Send an event to the invocation (no-op by default)."""

    def set_emitter(self, emitter: Callable[[Event], None]) -> None:
        """Install a parent-emitter callback used to bubble child events.

        Parameters
        ----------
        emitter : Callable[[Event], None]
            Function that receives Event objects to enqueue at the parent.
        """
        self._emit = emitter


class ImmediateDoneHandler(InvokeHandler):
    """A mock handler that completes immediately upon start.

    It invokes the completion callback with its initial payload.
    """

    def start(self) -> None:  # noqa: D401
        self._on_done(self.payload)


class NoopHandler(InvokeHandler):
    """A handler that does nothing and never completes automatically."""

    pass


class InvokeRegistry:
    """Simple factory registry for invocation handlers.

    The default registry understands two types:
    - ``mock:immediate`` – completes instantly on start and passes payload
      to the done callback.
    - Any other type – returns a :class:`NoopHandler` (does nothing).

    Methods
    -------
    register(type_name, factory)
        Register a factory callable that returns an :class:`InvokeHandler` for
        the given type.
    create(type_name, src, payload, autostart, on_done)
        Create a handler for the given type. If ``autostart`` is true, callers
        should invoke ``start()`` after creation.
    """

    def __init__(self) -> None:
        self._factories: Dict[str, Callable[..., InvokeHandler]] = {}
        # Built-in mocks
        self.register("mock:immediate", lambda type_name, src, payload, on_done=None: ImmediateDoneHandler(type_name, src, payload, on_done))
        self.register("mock:record", lambda type_name, src, payload, on_done=None: RecordHandler(type_name, src, payload, on_done))
        # SCXML/SCJSON child-machine handler
        self.register("scxml", lambda type_name, src, payload, on_done=None: SCXMLChildHandler(type_name, src, payload, on_done))
        self.register("scjson", lambda type_name, src, payload, on_done=None: SCXMLChildHandler(type_name, src, payload, on_done))
        # Deferred mock that completes on a specific event
        self.register("mock:deferred", lambda type_name, src, payload, on_done=None: DeferredHandler(type_name, src, payload, on_done))

    def register(self, type_name: str, factory: Callable[..., InvokeHandler]) -> None:
        self._factories[type_name] = factory

    def create(
        self,
        type_name: str,
        src: Any,
        payload: Any,
        *,
        autostart: bool = True,
        on_done: Optional[OnDone] = None,
    ) -> InvokeHandler:
        factory = self._factories.get(type_name)
        handler: InvokeHandler
        if factory is not None:
            handler = factory(type_name, src, payload, on_done)
        else:
            handler = NoopHandler(type_name, src, payload, on_done)
        return handler


class RecordHandler(InvokeHandler):
    """A mock handler that records forwarded events via ``send``.

    Attributes
    ----------
    received : list[tuple[str, Any]]
        Sequence of (name, data) tuples in arrival order.
    """

    def __init__(self, type_name: str, src: Any, payload: Any, on_done: Optional[OnDone] = None) -> None:
        super().__init__(type_name, src, payload, on_done)
        self.received: list[tuple[str, Any]] = []

    def send(self, name: str, data: Any | None = None) -> None:  # noqa: D401
        self.received.append((name, data))


class SCXMLChildHandler(InvokeHandler):
    """Runs a nested SCXML/SCJSON machine using the Python engine.

    The child machine completes when it enqueues `done.state.<rootId>`; the
    handler then invokes the done callback with that event's data.
    """

    def __init__(self, type_name: str, src: Any, payload: Any, on_done: Optional[OnDone] = None) -> None:
        super().__init__(type_name, src, payload, on_done)
        self.child: 'DocumentContext' | None = None

    def start(self) -> None:  # noqa: D401
        # Prefer explicit src path
        path = self.src
        try:
            if isinstance(path, (str, Path)):
                p = Path(str(path))
                if p.suffix.lower() == ".scxml":
                    from .context import DocumentContext  # local to avoid import cycle
                    self.child = DocumentContext.from_xml_file(p)
                else:
                    from .context import DocumentContext  # local to avoid import cycle
                    self.child = DocumentContext.from_json_file(p)
            else:
                # Attempt inline content if provided in payload
                ctx = self._context_from_payload_content(self.payload)
                if ctx is not None:
                    self.child = ctx
                else:
                    xml_str = self._xml_from_payload_content(self.payload)
                    if xml_str:
                        from .context import DocumentContext  # local to avoid import cycle
                        self.child = DocumentContext.from_xml_string(xml_str)
        except Exception:
            self.child = None
            return
        # Attach emitter so child can bubble '#_parent' sends
        try:
            self.child._external_emitter = self._emit  # type: ignore[attr-defined]
        except Exception:
            pass
        # Inject payload params/namelist into child datamodel prior to entry
        try:
            self._inject_payload_into_child()
        except Exception:
            pass
        # If initial was deferred, enter now so onentry sends can bubble
        try:
            if self.child and len(self.child.configuration) == 1:
                self.child._enter_initial_states(self.child.root_activation)
                self.child.drain_internal()
        except Exception:
            pass
        self._pump()

    def stop(self) -> None:  # noqa: D401
        self.child = None

    def cancel(self) -> None:  # noqa: D401
        self.child = None

    def send(self, name: str, data: Any | None = None) -> None:  # noqa: D401
        if not self.child:
            return
        self.child.enqueue(name, data)
        # Run one external microstep then drain internal transitions
        self.child.microstep()
        self.child.drain_internal()
        self._pump()

    def _pump(self) -> None:
        """Drain child outputs and detect completion."""
        if not self.child:
            return
        root_id = self.child.root_activation.id
        while True:
            evt = self.child.events.pop()
            if not evt:
                break
            if evt.name == f"done.state.{root_id}":
                # Ordering guard: run onexit for any active <final> states
                # so that their sends (e.g. target="#_parent") are emitted
                # before the parent receives done.invoke.
                try:
                    emitted = self._run_child_final_onexit()
                except Exception:
                    emitted = False
                # Prefer front for done.invoke when no child-bubbled events exist
                # so done.invoke outranks pending timeouts (e.g., W3C 239/240/241)
                try:
                    setattr(self, '_prefer_front_done', not emitted)
                except Exception:
                    pass
                self._on_done(evt.data)
                break
            # Bubble the child's event to the parent
            try:
                self._emit(Event(name=evt.name, data=evt.data, send_id=evt.send_id))
            except Exception:
                pass

    def _run_child_final_onexit(self) -> bool:
        if not self.child:
            return
        try:
            # Lazy import to avoid cycles
            from .pydantic import ScxmlFinalType  # type: ignore
        except Exception:
            ScxmlFinalType = None  # type: ignore
        if ScxmlFinalType is None:
            return False
        emitted = False
        # Identify active final states and run their onexit blocks
        for act in self.child.activations.values():
            try:
                node = getattr(act, 'node', None)
                if node is None:
                    continue
                if not isinstance(node, ScxmlFinalType):
                    continue
                if act.id not in self.child.configuration:
                    continue
                exits = getattr(node, 'onexit', []) or []
                if exits:
                    # Wrap emitter to detect any bubbled output
                    original_emitter = getattr(self.child, '_external_emitter', None)
                    def mark_emit(evt):
                        nonlocal emitted
                        emitted = True
                        if callable(original_emitter):
                            original_emitter(evt)
                    try:
                        self.child._external_emitter = mark_emit
                        for onexit in exits:
                            self.child._run_actions(onexit, act)
                    finally:
                        self.child._external_emitter = original_emitter
            except Exception:
                continue
        return emitted

    def _inject_payload_into_child(self) -> None:
        """Write invoke payload variables into the child's datamodel.

        Only applies to dict payloads; keys named 'content' are ignored.
        """
        if not self.child:
            return
        if not isinstance(self.payload, dict):
            return
        for k, v in self.payload.items():
            if k == 'content':
                continue
            try:
                # Set in both global data_model and root activation locals
                self.child.data_model[k] = v
                self.child.root_activation.local_data[k] = v
                # Override across all activation frames to ensure params/namelist
                # take precedence over any child <datamodel> entries.
                for act in self.child.activations.values():
                    act.local_data[k] = v
            except Exception:
                continue

    def _xml_from_payload_content(self, payload: Any) -> str | None:
        content = None
        if isinstance(payload, dict):
            content = payload.get("content")
        if content is None:
            return None
        try:
            root_nodes = content if isinstance(content, list) else [content]
            # First, try SCION-style qname/text/children structure
            for node in root_nodes:
                if isinstance(node, dict) and (node.get("qname") or node.get("children") is not None):
                    qn = (node.get("qname") or "").rsplit("}", 1)[-1]
                    if qn == "scxml":
                        import xml.etree.ElementTree as ET
                        def build(elem_dict: dict) -> ET.Element:
                            qn2 = elem_dict.get("qname") or "scxml"
                            e = ET.Element(qn2)
                            attrs = elem_dict.get("attributes") or {}
                            for k, v in attrs.items():
                                e.set(k, str(v))
                            text = elem_dict.get("text")
                            if isinstance(text, str):
                                e.text = text
                            for child in elem_dict.get("children") or []:
                                if isinstance(child, dict):
                                    e.append(build(child))
                            return e
                        return ET.tostring(build(node), encoding="unicode")
            # Next, try SCJSON-like dict (keys: state, initial, final, ...)
            for node in root_nodes:
                if isinstance(node, dict) and ("state" in node or "initial" in node or "final" in node):
                    try:
                        import json as _json
                        from .SCXMLDocumentHandler import SCXMLDocumentHandler as _Handler  # local import
                        handler = _Handler(pretty=False, omit_empty=True, fail_on_unknown_properties=False)
                        return handler.json_to_xml(_json.dumps(node))
                    except Exception:
                        continue
        except Exception:
            pass
        return None

    def _context_from_payload_content(self, payload: Any):
        try:
            content = None
            if isinstance(payload, dict):
                content = payload.get("content")
            if content is None:
                return None
            nodes = content if isinstance(content, list) else [content]
            for node in nodes:
                if isinstance(node, dict) and ("state" in node or "initial" in node or "final" in node):
                    # Normalize SCJSON-like node: ensure list fields for 'initial' and transition 'target'
                    def normalize(n: Any) -> Any:
                        if isinstance(n, dict):
                            out = {}
                            for k, v in n.items():
                                if k == "initial" and isinstance(v, str):
                                    out[k] = [v]
                                else:
                                    out[k] = normalize(v)
                            # Fix transition target(s) specifically
                            if "transition" in out and isinstance(out["transition"], list):
                                tlist = []
                                for t in out["transition"]:
                                    if isinstance(t, dict) and isinstance(t.get("target"), str):
                                        t = {**t, "target": [t["target"]]}
                                    tlist.append(t)
                                out["transition"] = tlist
                            return out
                        if isinstance(n, list):
                            return [normalize(i) for i in n]
                        return n
                    norm = normalize(node)
                    from .pydantic import Scxml  # local import to avoid cycles
                    from .context import DocumentContext, ExecutionMode  # local import
                    doc = Scxml.model_validate(norm)
                    raw = doc.model_dump(mode="python")
                    return DocumentContext._from_model(
                        doc,
                        raw,
                        allow_unsafe_eval=False,
                        evaluator=None,
                        execution_mode=ExecutionMode.LAX,
                        source_xml=None,
                        base_dir=None,
                        defer_initial=True,
                    )
        except Exception:
            return None
        return None


class DeferredHandler(InvokeHandler):
    """Completes when it receives an event named 'complete'."""

    def send(self, name: str, data: Any | None = None) -> None:  # noqa: D401
        if name == "complete":
            self._on_done(self.payload)
