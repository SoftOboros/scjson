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
