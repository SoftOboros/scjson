"""
Agent Name: python-vector-coverage-tests

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Unit tests for CoverageTracker aggregation.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from vector_lib.coverage import CoverageTracker


def test_coverage_tracker_accumulates_unique_items() -> None:
    cov = CoverageTracker()
    cov.add_step({
        "enteredStates": ["s1"],
        "firedTransitions": [{"source": "s0", "targets": ["s1"]}],
        "event": {"name": "done.state.s1"},
    })
    cov.add_step({
        "enteredStates": ["s1", "s2"],
        "firedTransitions": [{"source": "s1", "targets": ["s2"]}],
        "event": {"name": "error.execution"},
    })
    summary = cov.summary()
    assert summary["enteredStates"] == 2
    assert summary["firedTransitions"] == 2
    assert summary["doneEvents"] == 1
    assert summary["errorEvents"] == 1
