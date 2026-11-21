"""Document and compound-state child order on the Python interchange surface.

Part of the scjson project. Licensed under the BSD 1-Clause License.
"""

import json
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from scjson import dataclasses, dataclasses_strict, pydantic, pydantic_strict
from scjson.SCXMLDocumentHandler import SCXMLDocumentHandler
from scjson.execution_order import iter_state_children


SCXML = "http://www.w3.org/2005/07/scxml"
DOC = SCXMLDocumentHandler()


def chart(body, attributes=""):
    return f'<scxml xmlns="{SCXML}" xmlns:x="urn:test" version="1.0" {attributes}>{body}</scxml>'


def child_ids(node):
    tags = {f"{{{SCXML}}}{kind}" for kind in ("state", "parallel", "final")}
    return [child.get("id") for child in node if child.tag in tags]


def reject(raw):
    for reader in (pydantic.Scxml.model_validate, pydantic_strict.Scxml.model_validate,
                   lambda data: DOC.json_to_xml(json.dumps(data))):
        with pytest.raises(ValueError, match="state_order"):
            reader(raw)


@pytest.mark.parametrize("family", [dataclasses, dataclasses_strict])
@pytest.mark.parametrize("initial", ["", 'initial="outer"'])
def test_mixed_root_nested_state_and_parallel_preserve_independent_orders(family, initial):
    xml = chart("""
        <final id="first"/>
        <state id="outer" initial="s">
          <final id="f1"/><state id="s"/><history id="h"><transition target="s"/></history>
          <onentry><raise event="a"/><log label="b"/></onentry>
          <parallel id="p"><parallel id="p1"/><state id="p2"/></parallel>
          <final id="f2"/><!-- next state name omitted --><state/>
        </state>
        <parallel id="last"/>
    """, initial)
    handler = SCXMLDocumentHandler(model_class=family.Scxml)
    raw = json.loads(handler.xml_to_json(xml))
    assert raw["state_order"] == ["final", "state", "parallel"]
    outer = raw["state"][0]
    assert outer["state_order"] == ["final", "state", "parallel", "final", "state"]
    assert outer["parallel"][0]["region_order"] == ["parallel", "state"]
    assert outer["onentry"][0]["execution_order"] == ["raise", "log"]
    assert outer["state"][1]["help_text"] == ["next state name omitted"]
    for models in (pydantic, pydantic_strict):
        root = models.Scxml.model_validate(raw)
        assert [c.id for _, c in iter_state_children(root)] == ["first", "outer", "last"]
        assert [c.id for _, c in iter_state_children(root.state[0])] == ["f1", "s", "p", "f2", None]
    rebuilt = handler.json_to_xml(json.dumps(raw))
    assert "state_order" not in rebuilt
    root = ET.fromstring(rebuilt)
    assert child_ids(root) == ["first", "outer", "last"]
    assert child_ids(root.find("{*}state")) == ["f1", "s", "p", "f2", None]
    assert json.loads(handler.xml_to_json(rebuilt)) == raw


def test_opposite_mixed_orders_are_distinguishable_and_legacy_ignores_key_order():
    bodies = ['<final id="d"/><parallel id="p"/><state id="s"/><state id="t"/>',
              '<state id="s"/><state id="t"/><parallel id="p"/><final id="d"/>']
    records = [json.loads(DOC.xml_to_json(chart(body))) for body in bodies]
    assert records[0].pop("state_order") == ["final", "parallel", "state", "state"]
    assert records[1].pop("state_order") == ["state", "state", "parallel", "final"]
    assert records[0] == records[1]
    records[0]["state"] = records[0].pop("state")
    for models in (pydantic, pydantic_strict):
        legacy = models.Scxml.model_validate(records[0])
        assert "state_order" not in legacy.model_dump()
        assert "state_order" not in json.loads(legacy.model_dump_json())
        assert [c.id for _, c in iter_state_children(legacy)] == ["s", "t", "p", "d"]
    assert child_ids(ET.fromstring(DOC.json_to_xml(json.dumps(records[0])))) == ["s", "t", "p", "d"]


@pytest.mark.parametrize("body,kinds", [("", []), ("<final/><final/>", ["final", "final"])])
def test_present_complete_arrays_and_absent_metadata_for_homogeneous_owners(body, kinds):
    raw = json.loads(SCXMLDocumentHandler(omit_empty=False).xml_to_json(chart(body)))
    assert "state_order" not in raw
    raw = json.loads(DOC.xml_to_json(chart(body)))
    raw["state_order"] = kinds
    for models in (pydantic, pydantic_strict):
        assert json.loads(models.Scxml.model_validate_json(json.dumps(raw)).model_dump_json())["state_order"] == kinds
    assert len(child_ids(ET.fromstring(DOC.json_to_xml(json.dumps(raw))))) == len(kinds)


def test_foreign_elements_and_explicit_initial_transitions_do_not_consume_slots():
    xml = chart('<state id="s"><initial><transition target="p"/></initial><final/><x:state/>'
                '<parallel id="p"/><x:final state_order="foreign"/></state>')
    raw = json.loads(DOC.xml_to_json(xml))
    assert "state_order" not in raw
    assert raw["state"][0]["state_order"] == ["final", "parallel"]
    raw["state"][0]["other_attributes"] = {"{urn:test}state_order": "author data"}
    assert json.loads(DOC.xml_to_json(DOC.json_to_xml(json.dumps(raw)))) == raw


@pytest.mark.parametrize("order", [None, [], {}, "state", ["state"], ["final", "final"], ["final", "state", "final"],
                                   ["history", "state"], ["parallel", "state"], [1, "state"], [["final"], "state"]])
def test_invalid_complete_order_rejected_on_root_and_state(order):
    raw = json.loads(DOC.xml_to_json(chart('<state id="s"><final/><state/></state><final/>')))
    for owner in (raw, raw["state"][0]):
        saved, owner["state_order"] = owner["state_order"], order
        reject(raw)
        owner["state_order"] = saved


def test_order_rejected_on_wrong_owners_and_in_invalid_embedded_chart():
    inner = chart('<parallel id="p"/><final id="f"/>')
    xml = chart(f'<state><invoke><content>{inner}</content></invoke></state><parallel/><final/>')
    raw = json.loads(DOC.xml_to_json(xml))
    embedded = raw["state"][0]["invoke"][0]["content"][0]["content"][0]
    assert embedded["state_order"] == ["parallel", "final"]
    assert json.loads(DOC.xml_to_json(DOC.json_to_xml(json.dumps(raw)))) == raw
    for owner in (embedded, raw["parallel"][0], raw["final"][0]):
        owner["state_order"] = None
        reject(raw)
        if owner is embedded:
            owner["state_order"] = ["parallel", "final"]
        else:
            del owner["state_order"]


def test_schemas_project_state_order_only_on_valid_owners():
    repo = Path(__file__).resolve().parents[2]
    canonical = (repo / "scjson.schema.json").read_bytes()
    assert all(p.read_bytes() == canonical for p in
               (repo / "js/scjson.schema.json", repo / "java/src/main/resources/scjson.schema.json"))
    schema = json.loads(canonical)
    target = schema["properties"]["state_order"]
    assert target["items"]["enum"] == ["state", "parallel", "final"]
    assert target["type"] == "array"
    assert {kind for kind, node in schema["$defs"].items()
            if "state_order" in node.get("properties", {})} == {"State", "Scxml"}
    for kind in ("State", "Scxml"):
        assert "state_order" not in schema["$defs"][kind].get("required", ())
        assert schema["$defs"][kind]["properties"]["state_order"] == target
        for models in (pydantic, pydantic_strict):
            assert models.Scxml.model_json_schema()["$defs"][kind]["properties"]["state_order"] == target
