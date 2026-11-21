"""
Agent Name: parallel-exit-order-tests

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Observe SCXML exit order through actual raised events and transition actions.
"""

from pathlib import Path

import pytest

from scjson.SCXMLDocumentHandler import SCXMLDocumentHandler
from scjson.context import DocumentContext
from scjson.events import Event


@pytest.mark.parametrize("dialect", ["ecma", "python"])
@pytest.mark.parametrize("route", ["xml", "scjson"])
def test_original_case404_raises_four_events_in_exit_then_transition_order(dialect, route, tmp_path):
    """Require each of the four transitions selected by the original chart."""
    source = Path(__file__).resolve().parents[2] / "tutorial" / "Tests" / dialect / "W3C" / "Mandatory" / "Auto" / "test404.scxml"
    if not source.is_file():
        pytest.skip("Alex Z tutorial submodule unavailable")
    if route == "xml":
        ctx = DocumentContext.from_xml_file(source)
    else:
        saved = tmp_path / "case404.scjson"
        saved.write_text(SCXMLDocumentHandler().xml_to_json(source.read_text("utf-8")), encoding="utf-8")
        ctx = DocumentContext.from_json_file(saved)
    traces = [ctx.trace_step() for _ in range(4)]
    assert [step["event"]["name"] for step in traces] == ["event1", "event2", "event3", "event4"]
    assert [step["firedTransitions"][0]["targets"] for step in traces] == [["s03"], ["s04"], ["s05"], ["pass"]]


def test_exiting_parallel_from_one_leaf_exits_the_opposite_region_first():
    """A transition from the earlier region includes both active sibling subtrees."""
    xml = '''<scxml xmlns="http://www.w3.org/2005/07/scxml" version="1.0" datamodel="python" initial="parallel">
        <parallel id="parallel">
            <onexit><raise event="parent"/></onexit>
            <state id="left" initial="leftLeaf">
                <onexit><raise event="left"/></onexit>
                <state id="leftLeaf">
                    <onexit><raise event="leftLeaf"/></onexit>
                    <transition event="observe"><raise event="observed"/></transition>
                    <transition event="exit" target="finished"><raise event="transition"/></transition>
                </state>
            </state>
            <state id="right" initial="rightLeaf">
                <onexit><raise event="right"/></onexit>
                <state id="rightLeaf"><onexit><raise event="rightLeaf"/></onexit></state>
            </state>
        </parallel>
        <state id="finished"/>
    </scxml>'''
    ctx = DocumentContext.from_xml_string(xml)
    assert ctx.trace_step(Event(name="observe"))["exitedStates"] == []
    assert [event.name for event in iter(ctx.events.pop, None)] == ["observed"]
    step = ctx.trace_step(Event(name="exit"))
    assert set(step["exitedStates"]) == {"leftLeaf", "rightLeaf"}
    assert ctx.configuration - {"__scxml_root__"} == {"finished"}
    assert [event.name for event in iter(ctx.events.pop, None)] == [
        "rightLeaf", "right", "leftLeaf", "left", "parent", "transition"
    ]
