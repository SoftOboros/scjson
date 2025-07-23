"""
Agent Name: events-module

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Runtime event container and queue utilities.
"""

from __future__ import annotations

from collections import deque
from typing import Any, Deque, Optional

from pydantic import BaseModel


class Event(BaseModel):
    """Simple SCXML event."""

    name: str
    data: Any | None = None


class EventQueue:
    """Simple FIFO for external/internal events."""

    def __init__(self) -> None:
        self._q: Deque[Event] = deque()

    def push(self, evt: Event) -> None:
        """Add ``evt`` to the queue."""
        self._q.append(evt)

    def pop(self) -> Optional[Event]:
        """Remove and return the next queued event."""
        return self._q.popleft() if self._q else None

    def __bool__(self) -> bool:  # noqa: D401
        """Return ``True`` when events are pending."""
        return bool(self._q)
