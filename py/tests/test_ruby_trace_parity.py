"""Pin the Python side of the three-engine release trace regressions.

Agent Name: scjson-trace-parity
Part of the scjson project. Licensed under the BSD 1-Clause License.
"""

from pathlib import Path

import pytest

from scjson.context import DocumentContext
from scjson.events import Event


CHARTS = Path(__file__).resolve().parents[2] / "tests" / "exec"


@pytest.mark.parametrize(("key", "data", "target"), [
    (3, [1, 2, 3], "fail"), (0, [42], "pass"), ("01", [42, 43], "fail"),
    ("length", [], "pass"), ("map", [], "pass"), ("x", {"x": None}, "pass"),
])
def test_ecmascript_property_guard(key, data, target):
    ctx = DocumentContext.from_xml_file(CHARTS / "membership.scxml")
    frame = ctx.trace_step(Event(name="check", data={"val": key, "arr": data}))
    assert frame["configuration"] == [target]


def test_scion_snapshot_preserves_queued_child_completion():
    ctx = DocumentContext.from_xml_file(CHARTS / "parallel_history_invoke.scxml", ordering_mode="scion")
    assert {"LS", "RS"} <= ctx.configuration
    assert ctx.trace_step(Event(name="start"))["configuration"] == ["LS", "RS"]
    events = []
    while ctx.events:
        events.append(ctx.trace_step()["event"]["name"])
    assert "done.invoke.childL" in events and "done.invoke.childR" in events
    assert "Done" in ctx.configuration


def test_parallel_completion_waits_for_both_regions(tmp_path):
    xml = (CHARTS / "conflict_parallel.scxml").read_text(encoding="utf-8")
    path = tmp_path / "split.scxml"
    path.write_text(xml.replace('event="tick"', 'event="left"', 1)
                       .replace('event="tick"', 'event="right"', 1), encoding="utf-8")
    ctx = DocumentContext.from_xml_file(path, ordering_mode="scion")
    assert ctx.trace_step(Event(name="left"))["configuration"] == ["LF", "RReady"]
    assert ctx.trace_step(Event(name="right"))["configuration"] == ["done"]
