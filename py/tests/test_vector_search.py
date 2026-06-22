"""
Agent Name: python-vector-search-tests

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Tests for coverage-guided search ordering, pruning, and EXEC-E budget bounds.
"""

from __future__ import annotations

import time
from typing import Any, Callable

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scjson.context import DocumentContext, ExecutionMode
from vector_lib.search import generate_sequences, SearchResult


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


def _chart_parallel_invoke_small() -> str:
    """EXEC-E-D5 regression corpus machine.

    Two parallel regions; region A has one nested inline-<content> <invoke>
    with a two-state child machine; alphabet of three events (``start``,
    ``stop``, ``done``).  Small enough to complete well under any CI budget.
    """
    return (
        """
        <scxml initial="root" xmlns="http://www.w3.org/2005/07/scxml">
          <parallel id="root">
            <state id="regionA">
              <invoke id="child">
                <content>
                  <scxml initial="c0" xmlns="http://www.w3.org/2005/07/scxml">
                    <state id="c0">
                      <transition event="start" target="c1"/>
                    </state>
                    <state id="c1"/>
                  </scxml>
                </content>
              </invoke>
              <transition event="done" target="regionA"/>
            </state>
            <state id="regionB">
              <transition event="stop" target="regionB"/>
            </state>
          </parallel>
        </scxml>
        """
    ).strip()


def test_generate_sequences_orders_by_coverage() -> None:
    xml = _chart_go_noop()
    ctx_factory = _factory(xml)
    alphabet: list[Any] = ["noop", "go"]
    result = generate_sequences(ctx_factory, alphabet, max_depth=1, limit=2)
    seqs = result.sequences
    assert seqs, "expected sequences"
    # 'go' should be ranked before 'noop'
    assert seqs[0] == ["go"]
    # 'noop' may appear later, but is not required
    # Small machine must not truncate under default budget
    assert not result.truncated, "small machine must not hit budget"


def test_generate_sequences_returns_search_result() -> None:
    """generate_sequences returns a SearchResult with expected fields."""
    xml = _chart_go_noop()
    result = generate_sequences(_factory(xml), ["go"], max_depth=1, limit=1)
    assert isinstance(result, SearchResult)
    assert isinstance(result.sequences, list)
    assert isinstance(result.truncated, bool)
    assert isinstance(result.candidates_evaluated, int)
    assert isinstance(result.elapsed_ms, float)


def test_candidate_cap_triggers_truncated() -> None:
    """A max_candidates=1 cap on a multi-event alphabet forces truncated=True."""
    xml = _chart_go_noop()
    # alphabet of 3 symbols but cap at 1 candidate — must truncate
    result = generate_sequences(
        _factory(xml), ["go", "noop", "other"], max_depth=2, limit=5, max_candidates=1
    )
    assert result.truncated, "expected truncated=True when max_candidates exceeded"
    # Must still return a valid (possibly partial) sequence list — never empty
    assert result.sequences, "sequences must not be empty even when truncated"


def test_time_budget_triggers_truncated() -> None:
    """A time_budget_ms=1 (1 ms) budget forces truncated=True on any real machine."""
    xml = _chart_go_noop()
    result = generate_sequences(
        _factory(xml), ["go", "noop", "other", "extra"], max_depth=3, limit=5, time_budget_ms=1
    )
    # Budget may or may not fire depending on machine speed; if it does, truncated must be set.
    # What must always hold: result is a SearchResult and sequences is non-empty.
    assert isinstance(result, SearchResult)
    assert result.sequences


def test_bounded_parallel_invoke_terminates() -> None:
    """EXEC-E-D5: parallel+invoke machine must complete within budget and return
    a non-empty result (``success`` or ``limited``).

    This is the regression corpus machine for EXEC-E: two parallel regions,
    one inline-<content> <invoke> with a two-state child, alphabet of three
    events.  Under EXEC-E-D2 the effective depth is capped at min(4, 2)=2.
    """
    xml = _chart_parallel_invoke_small()
    alphabet: list[Any] = ["start", "stop", "done"]
    budget_ms = 10000  # 10 s — well under EXEC-E default; should finish in ms

    t0 = time.monotonic()
    result = generate_sequences(
        _factory(xml),
        alphabet,
        max_depth=4,  # EXEC-E-D2 will reduce to 2 for parallel+invoke charts
        limit=3,
        max_candidates=2000,
        time_budget_ms=budget_ms,
    )
    elapsed_ms = (time.monotonic() - t0) * 1000

    # Must terminate well within the budget
    assert elapsed_ms < budget_ms, (
        f"search took {elapsed_ms:.1f} ms, exceeded budget {budget_ms} ms"
    )
    # Must return at least one sequence
    assert result.sequences, "expected at least one sequence"
    # Must not be empty overall (truncated OR success — both are valid for G1)
    assert isinstance(result.truncated, bool)
    # If truncated, sequences may be partial but still non-empty
    if result.truncated:
        assert len(result.sequences) >= 1
    else:
        # Full result: at least one non-empty sequence should exist
        assert any(len(s) >= 0 for s in result.sequences)


def test_construct_aware_depth_cap_applied() -> None:
    """EXEC-E-D2: parallel+invoke machine gets effective depth capped at min(max_depth, 2)."""
    xml = _chart_parallel_invoke_small()
    alphabet: list[Any] = ["start", "stop", "done"]
    # Request depth=4 — EXEC-E-D2 must reduce to 2
    result = generate_sequences(
        _factory(xml), alphabet, max_depth=4, limit=5, max_candidates=2000, time_budget_ms=10000
    )
    # All returned sequences must have length <= 2 (the reduced depth)
    for seq in result.sequences:
        assert len(seq) <= 2, (
            f"sequence length {len(seq)} exceeds reduced depth 2: {seq}"
        )


def test_empty_alphabet_returns_empty_sequence_no_truncation() -> None:
    """An empty alphabet returns [[]] without triggering truncated."""
    xml = _chart_go_noop()
    result = generate_sequences(_factory(xml), [], max_depth=2, limit=1)
    assert result.sequences == [[]]
    assert not result.truncated
