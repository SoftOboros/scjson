"""Verify the SCXML mixed wildcard from conversion through event delivery.

Agent Name: mixed-payload-regression

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.
"""

import json
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError
from xsdata.exceptions import ParserError

from scjson.SCXMLDocumentHandler import SCXMLDocumentHandler
from scjson.context import DocumentContext
from scjson.pydantic import Scxml
from scjson.pydantic_strict import Scxml as StrictScxml


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = Draft202012Validator(json.loads((ROOT / "scjson.schema.json").read_text(encoding="utf-8")))
CHARTS = [
    f"{dialect}/W3C/{category}/Auto/test{number}.scxml"
    for dialect in ("ecma", "python")
    for category, numbers in (("Mandatory", [179, 354, 529]), ("Optional", [520, 532, 562, 578]))
    for number in numbers
] + [
    "ecma/W3C/Mandatory/Auto/test294.scxml",
    "ecma/Custom/types/testConditionalExpressions.scxml",
    "ecma/Custom/types/testConditionalExpressionsContent.scxml",
]
NS = "{http://www.w3.org/2005/07/scxml}"


def _original(relative):
    tests = ROOT / "tutorial" / "Tests"
    if not tests.is_dir():
        pytest.skip("Initialize the tutorial submodule to run the original charts.")
    return (tests / relative).read_text(encoding="utf-8-sig")


def _literal(xml):
    return [
        node.text for node in ET.fromstring(xml).iter(NS + "content")
        if len(node) == 0 and node.text is not None
    ]


@pytest.mark.parametrize("relative", CHARTS)
def test_original_payload_round_trip(relative, tmp_path):
    """Check the exact unmodified corpus literal in both model families and round trip."""
    xml = _original(relative)
    codec = SCXMLDocumentHandler()
    encoded = codec.xml_to_json(xml)
    for model in (Scxml, StrictScxml):
        model.model_validate_json(encoded)
    SCHEMA.validate(json.loads(encoded))
    assert len(_literal(xml)) == 1
    assert _literal(codec.json_to_xml(encoded)) == _literal(xml)
    converted_path = tmp_path / "original.scjson"
    converted_path.write_text(encoded, encoding="utf-8")
    for loaded in (
        DocumentContext.from_xml_file(ROOT / "tutorial" / "Tests" / relative),
        DocumentContext.from_json_file(converted_path),
    ):
        stored = loaded.doc.model_dump_json(exclude_unset=True)
        assert _literal(codec.json_to_xml(stored)) == _literal(xml)


def test_existing_intake_refusals():
    """Preserve the independent invalid assignment and root transition diagnostics."""
    codec = SCXMLDocumentHandler()
    encoded = codec.xml_to_json(_original("python/W3C/Mandatory/Auto/test401.scxml"))
    for model in (Scxml, StrictScxml):
        with pytest.raises(ValidationError) as error:
            model.model_validate_json(encoded)
        assert any(e["loc"][-2:] == (0, "location") for e in error.value.errors())
    with pytest.raises(ParserError, match="transition"):
        codec.xml_to_json(_original("ecma/Custom/uscxml/test-enc-UTF8.scxml"))


@pytest.mark.parametrize("item", [42, {"qname": 7}, {"qname": "bad", "children": [12]}])
def test_invalid_mixed_item_is_rejected(item):
    """Invalid XML nodes and bare numbers cannot masquerade as nested charts."""
    chart = {"state": [{"id": "s", "onentry": [{"send": [
        {"event": "message", "content": [{"content": [item]}]}
    ]}]}]}
    for model in (Scxml, StrictScxml):
        with pytest.raises(ValidationError):
            model.model_validate(chart)
    assert not SCHEMA.is_valid(chart)


def _load_pair(tmp_path, xml):
    xml_path = tmp_path / "fixture.scxml"
    xml_path.write_text(xml, encoding="utf-8")
    codec = SCXMLDocumentHandler(pretty=False)
    encoded = codec.xml_to_json(xml)
    assert json.loads(codec.xml_to_json(codec.json_to_xml(encoded))) == json.loads(encoded)
    SCHEMA.validate(json.loads(encoded))
    for model in (Scxml, StrictScxml):
        model.model_validate_json(encoded)
    json_path = tmp_path / "fixture.scjson"
    json_path.write_text(encoded, encoding="utf-8")
    return (DocumentContext.from_xml_file(xml_path), DocumentContext.from_json_file(json_path))


@pytest.mark.parametrize(("payload", "expected"), [
    ("<content>  42\n</content>", "  42\n"),
    ("<content>   \n </content>", "   \n "),
    ("<content>[1, 2]</content>", "[1, 2]"),
    ("<content/>", ""),
    ('<content expr="6 * 7"/>', 42),
    ('<content>before <state id="payload" xmlns="http://www.w3.org/2005/07/scxml">'
     '<leaf xmlns="urn:fixture">body</leaf>after</state> end</content>',
     ["before ", {"qname": NS + "state", "attributes": {"id": "payload"}, "text": "",
                  "tail": " end", "children": [{"qname": "{urn:fixture}leaf", "text": "body", "tail": "after"}]}]),
])
def test_send_and_done_deliver_mixed_payload(tmp_path, payload, expected):
    """Read both files and inspect the actual queued send and done.state data."""
    xml = f"""<scxml xmlns="http://www.w3.org/2005/07/scxml" version="1.0" initial="s">
      <state id="s" initial="f"><onentry><send event="message">{payload}</send></onentry>
        <final id="f"><donedata>{payload}</donedata></final>
      </state></scxml>"""
    for context in _load_pair(tmp_path, xml):
        events = {event.name: event.data for event in iter(context.events.pop, None)}
        assert events["message"] == {"content": expected}
        assert events["done.state.s"] == expected


def test_invoked_chart_remains_executable(tmp_path):
    """Execute a typed inline child and observe its completion in the parent."""
    xml = """<scxml xmlns="http://www.w3.org/2005/07/scxml" version="1.0" initial="parent">
      <state id="parent"><invoke id="child" type="scxml"><content>
        <scxml version="1.0" initial="finished"><final id="finished"/></scxml>
      </content></invoke><transition event="done.invoke.child" target="pass"/></state>
      <final id="pass"/></scxml>"""
    for context in _load_pair(tmp_path, xml):
        context.run(steps=20)
        assert "pass" in context.configuration
