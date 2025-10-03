"""
Agent Name: python-vector-search-tests

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Tests for coverage-guided search ordering and pruning.
"""

from __future__ import annotations

from typing import Any, Callable

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scjson.context import DocumentContext, ExecutionMode
from vector_lib.search import generate_sequences


def _chart_go_noop() -> str:
    return (
        """
        <scxml initial="s0" xmlns="http://www.w3.org/2005/07/scxml">
          <state id="s0">
            <transition event="go" target="s1"/>
          </state>
          <state id="s1"/>
        </scxml>
        """
    ).strip()


def _factory(xml: str) -> Callable[[], DocumentContext]:
    def make() -> DocumentContext:
        return DocumentContext.from_xml_string(xml, execution_mode=ExecutionMode.LAX)
    return make


def test_generate_sequences_orders_by_coverage() -> None:
    xml = _chart_go_noop()
    ctx_factory = _factory(xml)
    alphabet: list[Any] = ["noop", "go"]
    seqs = generate_sequences(ctx_factory, alphabet, max_depth=1, limit=2)
    assert seqs, "expected sequences"
    # 'go' should be ranked before 'noop'
    assert seqs[0] == ["go"]
    # 'noop' may appear later, but is not required
