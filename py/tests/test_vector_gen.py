"""
Agent Name: python-vector-tests

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Tests for Phase 2 vector generation: payload heuristics and auto-advance.
"""

from __future__ import annotations

from pathlib import Path
import sys

# Ensure local package is importable when running tests directly
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import json

from scjson.context import DocumentContext, ExecutionMode
from vector_lib.analyzer import extract_payload_heuristics
from vector_lib.search import generate_sequences
from vector_gen import generate_vectors, _minimize_sequence


def _chart_cond_flag() -> str:
    """Return a small chart with event-data conditions on a single event.

    Two transitions listen on the same event "go" and branch on
    ``_event.data.flag`` to reach distinct targets.
    """
    return (
        """
        <scxml initial="s0" xmlns="http://www.w3.org/2005/07/scxml">
          <state id="s0">
            <transition event="go" cond="_event.data.flag" target="s1"/>
            <transition event="go" cond="not _event.data.flag" target="s2"/>
          </state>
          <state id="s1"/>
          <state id="s2"/>
        </scxml>
        """
    ).strip()


def _chart_delayed_send() -> str:
    """Return a chart that schedules a delayed send during initialization."""
    return (
        """
        <scxml initial="idle" xmlns="http://www.w3.org/2005/07/scxml">
          <state id="idle">
            <onentry>
              <send event="tick" delay="1s"/>
            </onentry>
          </state>
        </scxml>
        """
    ).strip()


def _chart_membership() -> str:
    """Chart with membership test in condition."""
    return (
        """
        <scxml initial="s0" xmlns="http://www.w3.org/2005/07/scxml">
          <state id="s0">
            <transition event="go" cond="_event.data.kind in ['A','B']" target="ok"/>
          </state>
          <state id="ok"/>
        </scxml>
        """
    ).strip()


def _chart_chained_range() -> str:
    """Chart with chained comparison around numeric data."""
    return (
        """
        <scxml initial="s0" xmlns="http://www.w3.org/2005/07/scxml">
          <state id="s0">
            <transition event="go" cond="0 < _event.data.n < 5" target="ok"/>
          </state>
          <state id="ok"/>
        </scxml>
        """
    ).strip()


def _chart_reversed_membership() -> str:
    """Chart with reversed membership literal in container path."""
    return (
        """
        <scxml initial="s0" xmlns="http://www.w3.org/2005/07/scxml">
          <state id="s0">
            <transition event="go" cond="'A' in _event.data.items" target="ok"/>
          </state>
          <state id="ok"/>
        </scxml>
        """
    ).strip()


def _chart_variable_membership() -> str:
    """Chart where membership container comes from datamodel variable."""
    return (
        """
        <scxml initial="s0" xmlns="http://www.w3.org/2005/07/scxml">
          <datamodel>
            <data id="allowed" expr="['A','B']"/>
          </datamodel>
          <state id="s0">
            <transition event="go" cond="_event.data.kind in allowed" target="ok"/>
          </state>
          <state id="ok"/>
        </scxml>
        """
    ).strip()


def _chart_fusion_two_fields() -> str:
    """Chart with two independent conditions for same event to enable fusion."""
    return (
        """
        <scxml initial="s0" xmlns="http://www.w3.org/2005/07/scxml">
          <state id="s0">
            <transition event="go" cond="_event.data.a == 1" target="s1"/>
            <transition event="go" cond="_event.data.b == 2" target="s2"/>
          </state>
          <state id="s1"/>
          <state id="s2"/>
        </scxml>
        """
    ).strip()


def _chart_fusion_conflict() -> str:
    """Chart with conflicting conditions to ensure fusion avoids conflicts."""
    return (
        """
        <scxml initial="s0" xmlns="http://www.w3.org/2005/07/scxml">
          <state id="s0">
            <transition event="go" cond="_event.data.a == 1" target="s1"/>
            <transition event="go" cond="_event.data.a == 2" target="s2"/>
          </state>
          <state id="s1"/>
          <state id="s2"/>
        </scxml>
        """
    ).strip()


def test_payload_heuristics_extracts_event_data_variants() -> None:
    ctx = DocumentContext.from_xml_string(_chart_cond_flag(), execution_mode=ExecutionMode.LAX)
    hints = extract_payload_heuristics(ctx)
    assert "go" in hints and isinstance(hints["go"], list)
    # Expect at least True/False variants for flag
    payloads = hints["go"]
    keys = [list(p.keys()) for p in payloads]
    assert any("flag" in p or ("flag" in p[0] if p else False) for p in payloads)
    # At least one variant sets flag True and one sets False
    values = {json.dumps(p, sort_keys=True) for p in payloads}
    assert any("true" in s.lower() for s in values) or any(": true" in s.lower() for s in values)
    assert any("false" in s.lower() for s in values)


def test_payload_heuristics_membership_variants() -> None:
    ctx = DocumentContext.from_xml_string(_chart_membership(), execution_mode=ExecutionMode.LAX)
    hints = extract_payload_heuristics(ctx)
    payloads = hints.get("go") or []
    assert payloads, "expected membership-derived payloads for 'go'"
    # Expect at least one payload with kind set to 'A' or 'B'
    kinds = {p.get("kind") for p in payloads if isinstance(p, dict)}
    assert any(k in {"A", "B"} for k in kinds)


def test_payload_heuristics_chained_range() -> None:
    ctx = DocumentContext.from_xml_string(_chart_chained_range(), execution_mode=ExecutionMode.LAX)
    hints = extract_payload_heuristics(ctx)
    payloads = hints.get("go") or []
    assert payloads
    # Expect at least one numeric n within (0, 5)
    ns = [p.get("n") for p in payloads if isinstance(p, dict)]
    assert any(isinstance(v, (int, float)) and 0 < v < 5 for v in ns)


def test_payload_heuristics_reversed_membership() -> None:
    ctx = DocumentContext.from_xml_string(_chart_reversed_membership(), execution_mode=ExecutionMode.LAX)
    hints = extract_payload_heuristics(ctx)
    payloads = hints.get("go") or []
    assert payloads
    # Expect list container with 'items' including 'A'
    found = False
    for p in payloads:
        if isinstance(p, dict) and isinstance(p.get("items"), list) and 'A' in p.get("items"):
            found = True
            break
    assert found


def test_minimizer_removes_redundant_event(tmp_path: Path) -> None:
    xml = (
        """
        <scxml initial="s0" xmlns="http://www.w3.org/2005/07/scxml">
          <state id="s0">
            <transition event="go" target="s1"/>
          </state>
          <state id="s1"/>
        </scxml>
        """
    ).strip()
    chart = tmp_path / "mini.scxml"
    chart.write_text(xml, encoding="utf-8")
    ctx_factory = lambda: DocumentContext.from_xml_file(chart, execution_mode=ExecutionMode.LAX)
    seq = [{"event": "go"}, {"event": "go"}]
    minimized = _minimize_sequence(ctx_factory, list(seq))
    assert minimized == [{"event": "go"}]


def test_payload_heuristics_variable_membership() -> None:
    ctx = DocumentContext.from_xml_string(_chart_variable_membership(), execution_mode=ExecutionMode.LAX)
    hints = extract_payload_heuristics(ctx)
    payloads = hints.get("go") or []
    assert payloads
    kinds = {p.get("kind") for p in payloads if isinstance(p, dict)}
    assert any(k in {"A", "B"} for k in kinds)


def test_payload_variant_limit() -> None:
    ctx = DocumentContext.from_xml_string(_chart_fusion_two_fields(), execution_mode=ExecutionMode.LAX)
    hints1 = extract_payload_heuristics(ctx, max_variants=1)
    assert len(hints1.get("go", [])) == 1
    hints3 = extract_payload_heuristics(ctx, max_variants=3)
    assert 1 <= len(hints3.get("go", [])) <= 3


def test_payload_fusion_merges_distinct_fields() -> None:
    ctx = DocumentContext.from_xml_string(_chart_fusion_two_fields(), execution_mode=ExecutionMode.LAX)
    hints = extract_payload_heuristics(ctx, max_variants=4)
    payloads = hints.get("go") or []
    assert payloads
    # At least one payload contains both fields
    assert any(isinstance(p, dict) and p.get("a") == 1 and p.get("b") == 2 for p in payloads)


def test_payload_fusion_one_hot_variants() -> None:
    ctx = DocumentContext.from_xml_string(_chart_fusion_two_fields(), execution_mode=ExecutionMode.LAX)
    hints = extract_payload_heuristics(ctx, max_variants=4)
    payloads = [p for p in (hints.get("go") or []) if isinstance(p, dict)]
    assert payloads
    # Check for one-hot: a==1 and b != 2
    has_a1_b_not2 = any(p.get("a") == 1 and ("b" in p and p.get("b") != 2) for p in payloads)
    # Or a != 1 and b == 2
    has_a_not1_b2 = any(p.get("b") == 2 and ("a" in p and p.get("a") != 1) for p in payloads)
    assert has_a1_b_not2 or has_a_not1_b2


def test_payload_fusion_avoids_conflicts() -> None:
    ctx = DocumentContext.from_xml_string(_chart_fusion_conflict(), execution_mode=ExecutionMode.LAX)
    hints = extract_payload_heuristics(ctx)
    payloads = hints.get("go") or []
    # Ensure we represent distinct possibilities, not a merged conflicting value
    vals = {p.get("a") for p in payloads if isinstance(p, dict) and "a" in p}
    assert 1 in vals and 2 in vals
    # And do not encode conflicting composite types for 'a'
    for p in payloads:
        if isinstance(p, dict) and "a" in p:
            assert not isinstance(p["a"], (list, dict))


def test_vector_gen_writes_data_payload(tmp_path: Path) -> None:
    xml = _chart_cond_flag()
    chart = tmp_path / "flag.scxml"
    chart.write_text(xml, encoding="utf-8")
    out_dir = tmp_path / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    events_path = generate_vectors(chart, treat_as_xml=True, out_dir=out_dir, max_depth=1)
    # Ensure an events.jsonl file exists and contains at least one object with data
    lines = (out_dir / f"{chart.stem}.events.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert lines
    first = json.loads(lines[0])
    assert first.get("event") == "go"
    # A data field is present due to heuristics
    assert "data" in first and isinstance(first["data"], dict)


def test_vector_meta_recommends_advance_time(tmp_path: Path) -> None:
    xml = _chart_delayed_send()
    chart = tmp_path / "timer.scxml"
    chart.write_text(xml, encoding="utf-8")
    out_dir = tmp_path / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    _ = generate_vectors(chart, treat_as_xml=True, out_dir=out_dir, max_depth=1)
    meta_path = out_dir / "timer.vector.json"
    assert meta_path.exists()
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    assert float(meta.get("advanceTime", 0.0)) >= 0.0
    # For this chart specifically, we should detect the 1s delay and recommend > 0
    assert float(meta.get("advanceTime", 0.0)) > 0.0
