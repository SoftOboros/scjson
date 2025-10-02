"""
Agent Name: python-events

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Event primitives used by the runtime engine.
"""

from __future__ import annotations

from collections import deque
from typing import Any, Deque, Optional

from pydantic import BaseModel


class Event(BaseModel):
    """Simple event container."""

    name: str
    data: Any | None = None
    send_id: str | None = None
    # SCXML Event I/O processor metadata
    origin: str | None = None
    origintype: str | None = None
    invokeid: str | None = None
    # Note: additional flags may be added in the future


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

    def push_front(self, evt: Event) -> None:
        """Prepend ``evt`` to the queue with priority.

        This is used for engine-generated error events so they are observed
        before subsequently enqueued normal events.

        :param evt: ``Event`` instance to enqueue at the front.
        :returns: ``None``
        """
        self._q.appendleft(evt)

    def pop(self) -> Optional[Event]:
        """Remove and return the next event if available.

        :returns: The next ``Event`` or ``None`` when empty.
        """
        return self._q.popleft() if self._q else None

    def cancel(self, send_id: str) -> bool:
        """Remove first queued event matching ``send_id``.

        :returns: ``True`` when an event was removed.
        """

        if not self._q:
            return False
        removed = False
        new_queue: Deque[Event] = deque()
        while self._q:
            evt = self._q.popleft()
            if not removed and evt.send_id == send_id:
                removed = True
                continue
            new_queue.append(evt)
        self._q = new_queue
        return removed

    def __bool__(self) -> bool:
        """Return ``True`` if any events are queued."""
        return bool(self._q)
