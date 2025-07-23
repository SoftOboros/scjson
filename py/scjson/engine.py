from __future__ import annotations

"""
Agent Name: python-engine

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Runtime scaffolding for SCXML execution.
"""

from .activation import ActivationRecord, ActivationStatus, TransitionSpec, SCXMLNode
from .context import DocumentContext
from .events import Event, EventQueue

__all__ = [
    "ActivationRecord",
    "ActivationStatus",
    "TransitionSpec",
    "SCXMLNode",
    "DocumentContext",
    "Event",
    "EventQueue",
]
