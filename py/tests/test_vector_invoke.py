"""
Agent Name: python-vector-invoke-tests

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Tests for invoke-related vector hints and generation behavior.
"""

from __future__ import annotations

import json
from pathlib import Path

import sys
from pathlib import Path as _Path

ROOT = _Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scjson.context import DocumentContext, ExecutionMode
from vector_gen import generate_vectors
from vector_lib.analyzer import extract_invoke_hints


def _chart_deferred_only() -> str:
    return (
        """
        <scxml initial="s0" xmlns="http://www.w3.org/2005/07/scxml">
          <state id="s0">
            <invoke type="mock:deferred"/>
          </state>
        </scxml>
        """
    ).strip()


def test_invoke_hints_and_complete_in_generation(tmp_path: Path) -> None:
    xml = _chart_deferred_only()
    ctx = DocumentContext.from_xml_string(xml, execution_mode=ExecutionMode.LAX)
    hints = extract_invoke_hints(ctx)
    assert hints.get("has_deferred") is True

    chart = tmp_path / "inv.scxml"
    out_dir = tmp_path / "out"
    chart.write_text(xml, encoding="utf-8")
    out_dir.mkdir(parents=True, exist_ok=True)
    events_path = generate_vectors(chart, treat_as_xml=True, out_dir=out_dir, max_depth=1, limit=1)
    # With no alphabet tokens, the generator should emit the 'complete' stimulus
    items = [json.loads(line) for line in (out_dir / f"{chart.stem}.events.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(items) == 1 and items[0].get("event") == "complete"
