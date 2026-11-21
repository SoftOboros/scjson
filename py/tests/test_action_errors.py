"""Verify the boundary of a failing SCXML executable block.

Agent Name: python-engine-action-errors

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.
"""

from pathlib import Path
from xml.etree import ElementTree

import pytest

from scjson.context import DocumentContext, ExecutionMode
from scjson.events import Event
from scjson.SCXMLDocumentHandler import SCXMLDocumentHandler


TUTORIAL = Path(__file__).resolve().parents[2] / "tutorial" / "Tests"


def _load(path, route, tmp_path):
    if route == "xml":
        return DocumentContext.from_xml_file(path, execution_mode=ExecutionMode.STRICT)
    converted = SCXMLDocumentHandler().xml_to_json(path.read_text(encoding="utf-8-sig"))
    saved = tmp_path / "original.scjson"
    saved.write_text(converted, encoding="utf-8")
    return DocumentContext.from_json_file(saved, execution_mode=ExecutionMode.STRICT)


def _errors(ctx):
    return [event.name for event in iter(ctx.events.pop, None) if event.name.startswith("error")]


def _original(dialect, number):
    path = TUTORIAL / dialect / "W3C" / "Mandatory" / "Auto" / f"test{number}.scxml"
    if not path.is_file():
        pytest.skip("Alex Z tutorial submodule is unavailable")
    return path


@pytest.mark.parametrize("dialect", ["ecma", "python"])
@pytest.mark.parametrize("route", ["xml", "scjson"])
@pytest.mark.parametrize("number", [156, 159])
def test_original_action_error(dialect, route, number, tmp_path):
    """Exercise the original foreach evaluation or send communication failure."""
    ctx = _load(_original(dialect, number), route, tmp_path)
    assert ctx.configuration - {"__scxml_root__"} == {"pass"}
    if number == 156:
        assert [ctx.data_model[name] for name in ("Var1", "Var2", "Var3")] == [1, 1, [1, 2, 3]]
        assert "Var5" not in ctx.data_model
        assert _errors(ctx) == ["error.execution", "error"]
    else:
        assert ctx.data_model["Var1"] == 0
        assert _errors(ctx) == ["error.communication"]


@pytest.mark.parametrize("dialect", ["ecma", "python"])
@pytest.mark.parametrize("route", ["xml", "scjson"])
def test_valid_assignment_visits_every_original_item(dialect, route, tmp_path):
    """Replace the invalid assignment and verify all three iterations."""
    tree = ElementTree.parse(_original(dialect, 156))
    assignment = tree.find('.//{*}foreach/{*}assign[@location="Var5"]')
    assignment.attrib.update(location="Var1", expr="Var1")
    tree.find('.//{*}transition[@target="pass"]').set("cond", "Var1==3")
    path = tmp_path / "valid.scxml"
    tree.write(path, encoding="utf-8", xml_declaration=True)
    ctx = _load(path, route, tmp_path)
    assert ctx.configuration - {"__scxml_root__"} == {"pass"}
    assert [ctx.data_model[name] for name in ("Var1", "Var2")] == [3, 3]
    assert _errors(ctx) == []


@pytest.mark.parametrize("dialect", ["ecma", "python"])
@pytest.mark.parametrize("route", ["xml", "scjson"])
def test_successful_send_in_original_159_continues(dialect, route, tmp_path):
    """An internal destination allows the following increment to run."""
    tree = ElementTree.parse(_original(dialect, 159))
    tree.find(".//{*}send").set("target", "#_internal")
    path = tmp_path / "internal.scxml"
    tree.write(path, encoding="utf-8", xml_declaration=True)
    ctx = _load(path, route, tmp_path)
    assert ctx.data_model["Var1"] == 1
    assert ctx.configuration - {"__scxml_root__"} == {"fail"}
    events = [event.name for event in iter(ctx.events.pop, None)]
    assert "thisWillFail" in events
    assert not any(name.startswith("error") for name in events)


@pytest.mark.parametrize("route", ["xml", "scjson"])
def test_only_the_failing_handler_or_transition_stops(route, tmp_path):
    """Preserve independent handlers and enter the failing transition's target."""
    path = tmp_path / "handlers.scxml"
    path.write_text("""<scxml xmlns="http://www.w3.org/2005/07/scxml" version="1.0"
                               initial="start" datamodel="ecmascript">
      <datamodel><data id="value" expr="0"/><data id="keep" expr="7"/></datamodel>
      <state id="start">
        <onentry>
          <foreach array="[1,2,3]" item="i"><if cond="true">
            <assign location="value" expr="value + 1"/>
            <assign location="keep" expr="return"/>
            <assign location="value" expr="900"/>
          </if></foreach>
          <foreach array="[1]" item="i"><assign location="value" expr="800"/></foreach>
        </onentry>
        <onentry><assign location="value" expr="value * 10"/></onentry>
        <onexit><assign location="value" expr="value + 2"/><assign location="unknown" expr="1"/>
                <assign location="value" expr="700"/></onexit>
        <onexit><assign location="value" expr="value * 10"/></onexit>
        <transition event="go" target="end">
          <assign location="value" expr="value + 3"/><assign location="keep" expr="return"/>
          <assign location="value" expr="600"/>
        </transition>
      </state>
      <state id="end"><onentry><assign location="value" expr="value * 10"/></onentry></state>
    </scxml>""", encoding="utf-8")
    ctx = _load(path, route, tmp_path)
    assert ctx.data_model["value"] == 10
    assert _errors(ctx) == ["error.execution", "error"]
    ctx.trace_step(Event(name="go"))
    assert ctx.configuration - {"__scxml_root__"} == {"end"}
    assert (ctx.data_model["value"], ctx.data_model["keep"]) == (1230, 7)
    assert _errors(ctx).count("error.execution") == 2


@pytest.mark.parametrize("route", ["xml", "scjson"])
def test_authored_error_named_event_does_not_abort_the_block(route, tmp_path):
    """An authored event name does not signal an action failure."""
    path = tmp_path / "raise.scxml"
    path.write_text("""<scxml xmlns="http://www.w3.org/2005/07/scxml" version="1.0" initial="s">
      <datamodel><data id="ran" expr="0"/></datamodel>
      <state id="s"><onentry><raise event="error.execution"/><assign location="ran" expr="1"/></onentry></state>
    </scxml>""", encoding="utf-8")
    ctx = _load(path, route, tmp_path)
    assert ctx.data_model["ran"] == 1
    assert _errors(ctx) == ["error.execution"]
