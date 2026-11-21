"""Verify the processor location and relative invocation in original Alex Z charts."""

import shutil
from pathlib import Path

import pytest

from scjson.context import DocumentContext, SCXML_PROCESSOR
from scjson.ecmascript_normalizer import normalize, normalize_script
from scjson.invoke import SCXMLChildHandler
from scjson.SCXMLDocumentHandler import SCXMLDocumentHandler


@pytest.mark.parametrize("route", ["xml", "scjson"])
@pytest.mark.parametrize("dialect", ["ecma", "python"])
@pytest.mark.parametrize("number", [216, 500])
def test_original_processor_and_relative_child(route, dialect, number, tmp_path, monkeypatch):
    originals = Path(__file__).resolve().parents[2] / "tutorial/Tests" / dialect / "W3C/Mandatory/Auto"
    if not originals.is_dir():
        pytest.skip("Alex Z tutorial submodule is unavailable")
    original = originals / f"test{number}.scxml"
    source = tmp_path / original.name
    shutil.copyfile(original, source)
    child = tmp_path / "test216sub1.scxml"
    opened = []
    if number == 216:
        shutil.copyfile(originals / child.name, child)
        start = SCXMLChildHandler.start

        def record_child(handler):
            opened.append(handler.src)
            return start(handler)

        monkeypatch.setattr(SCXMLChildHandler, "start", record_child)
    if route == "xml":
        ctx = DocumentContext.from_xml_file(source)
    else:
        converted = SCXMLDocumentHandler().xml_to_json(source.read_text(encoding="utf-8-sig"))
        source = source.with_suffix(".scjson")
        source.write_text(converted, encoding="utf-8")
        ctx = DocumentContext.from_json_file(source)
    assert "pass" in ctx.configuration
    pending = [e.name for e in iter(ctx.events.pop, None)]
    assert not any(name.startswith("error") for name in pending)
    if number == 216:
        assert opened == [child.resolve()]
        assert any(name.startswith("done.invoke") for name in pending)
        assert [event.name for _, event in ctx.delayed_events] == ["timeout"]
    else:
        env = ctx._scope_env(ctx.root_activation)
        assert ctx.data_model["Var1"] == env["_ioprocessors"][SCXML_PROCESSOR]["location"]
        assert ctx.data_model["Var1"] == "#_scxml_" + env["_sessionid"]


def test_processor_locations_are_per_session_and_deliver_self_addressed_events():
    chart = f"""<scxml xmlns="http://www.w3.org/2005/07/scxml" initial="s" datamodel="ecmascript">
        <state id="s"><onentry>
          <send event="hello" targetexpr="_ioprocessors['{SCXML_PROCESSOR}'].location"/>
        </onentry></state></scxml>"""
    contexts = [DocumentContext.from_xml_string(chart) for _ in range(2)]
    origins = []
    for ctx in contexts:
        event = ctx.events.pop()
        assert (event.name, event.origintype) == ("hello", SCXML_PROCESSOR)
        origins.append(event.origin)
        assert event.origin == "#_scxml_" + ctx._scope_env(ctx.root_activation)["_sessionid"]
    assert origins[0] != origins[1]


def test_javascript_comments_respect_quoted_delimiters():
    literal = "'http://example.org/path/*inside*/new'"
    assert normalize(literal + " /* comment's quote */ // trailing").strip() == literal
    assert normalize_script("x = " + literal + " // trailing").strip() == "x = " + literal
