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

    def start(self) -> None:  # noqa: D401
        """Start the invocation (no-op by default)."""

    def stop(self) -> None:  # noqa: D401
        """Stop the invocation if running (no-op by default)."""

    def cancel(self) -> None:  # noqa: D401
        """Cancel the invocation (no-op by default)."""

    def send(self, name: str, data: Any | None = None) -> None:  # noqa: D401
        """Send an event to the invocation (no-op by default)."""


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
