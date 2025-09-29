"""
Agent Name: python-engine-compat

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Deprecated compatibility shim that re-exports the runtime engine API from the
primary modules (`context`, `activation`, `events`). New code should import from
those modules directly.
"""

from __future__ import annotations

from .activation import ActivationRecord, ActivationStatus, TransitionSpec
from .context import DocumentContext
from .events import Event, EventQueue

__all__ = [
    "ActivationRecord",
    "ActivationStatus",
    "TransitionSpec",
    "DocumentContext",
    "Event",
    "EventQueue",
]
