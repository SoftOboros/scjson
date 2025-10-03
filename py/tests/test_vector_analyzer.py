"""
Agent Name: python-vector-analyzer-tests

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Unit tests for analyzer helpers: alphabet extraction and invoke hints.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scjson.context import DocumentContext, ExecutionMode
from vector_lib.analyzer import extract_event_alphabet, extract_invoke_hints


def _chart_alphabet() -> str:
    return (
        """
        <scxml initial="s0" xmlns="http://www.w3.org/2005/07/scxml">
          <state id="s0">
            <transition event="a b" target="s1"/>
            <transition event="*" target="s0"/>
            <transition event="error.*" target="s0"/>
          </state>
          <state id="s1"/>
        </scxml>
        """
    ).strip()


def _chart_invoke_deferred() -> str:
    return (
        """
        <scxml initial="s0" xmlns="http://www.w3.org/2005/07/scxml">
          <state id="s0">
            <invoke type="mock:deferred"/>
          </state>
        </scxml>
        """
    ).strip()


def test_alphabet_extraction_ignores_wildcards() -> None:
    ctx = DocumentContext.from_xml_string(_chart_alphabet(), execution_mode=ExecutionMode.LAX)
    alpha = extract_event_alphabet(ctx)
    assert alpha == ["a", "b"], alpha


def test_invoke_hints_deferred_true() -> None:
    ctx = DocumentContext.from_xml_string(_chart_invoke_deferred(), execution_mode=ExecutionMode.LAX)
    hints = extract_invoke_hints(ctx)
    assert hints.get("has_deferred") is True
