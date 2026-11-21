"""SCJSON-CONV-00 parallel region order at the Python interchange boundary.

Agent Name: parallel-region-interchange-tests

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.
"""

import json
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from scjson import dataclasses, dataclasses_strict, pydantic, pydantic_strict
from scjson.SCXMLDocumentHandler import SCXMLDocumentHandler
from scjson.execution_order import iter_regions


NS = "http://www.w3.org/2005/07/scxml"
DOC = SCXMLDocumentHandler()


def chart(children):
    return f'<scxml xmlns="{NS}" xmlns:x="urn:foreign" version="1.0" initial="outer">' \
           f'<parallel id="outer">{children}</parallel></scxml>'


def region_ids(element):
    return [n.get("id") for n in element if n.tag in {f"{{{NS}}}state", f"{{{NS}}}parallel"}]


@pytest.mark.parametrize("family", [dataclasses, dataclasses_strict])
def test_opposite_orders_roundtrip_distinctly_with_the_same_payloads(family):
    handler = SCXMLDocumentHandler(model_class=family.Scxml)
    first, second = '<parallel id="first"><state id="leaf"/></parallel>', '<state id="second"/>'
    records = []
    for children, sequence, ids in ((first + second, ["parallel", "state"], ["first", "second"]),
                                    (second + first, ["state", "parallel"], ["second", "first"])):
        raw = json.loads(handler.xml_to_json(chart(children)))
        assert raw["parallel"][0]["region_order"] == sequence
        xml = handler.json_to_xml(json.dumps(raw))
        assert region_ids(ET.fromstring(xml).find("{*}parallel")) == ids
        assert "region_order" not in xml
        assert json.loads(handler.xml_to_json(xml)) == raw
        raw["parallel"][0].pop("region_order")
        records.append(raw)
    assert records[0] == records[1]


def test_nested_parallel_queues_preserve_occurrences_and_ignore_nonregions(tmp_path):
    xml = chart("""
      <onentry><raise event="one"/><log label="two"/></onentry>
      <state id="a"/><parallel id="inner"><state id="i1"/><parallel id="i2"/><state id="i3"/></parallel>
      <!-- keep this comment with b --><state id="b"/><x:parallel region_order="foreign"/>
      <parallel id="inner2"/><history id="past"><transition target="a"/></history><state id="c"/>
    """)
    file = tmp_path / "chart.scxml"
    file.write_text(xml, encoding="utf-8")
    saved = tmp_path / "result.scxml"
    model = DOC.load(file)
    assert [child.id for _, child in iter_regions(model.parallel[0])] == ["a", "inner", "b", "inner2", "c"]
    DOC.dump(model, saved)
    assert region_ids(ET.parse(saved).getroot().find("{*}parallel")) == ["a", "inner", "b", "inner2", "c"]
    raw = json.loads(DOC.xml_to_json(xml))
    outer = raw["parallel"][0]
    assert outer["region_order"] == ["state", "parallel", "state", "parallel", "state"]
    assert outer["parallel"][0]["region_order"] == ["state", "parallel", "state"]
    assert "region_order" not in outer["parallel"][1]
    assert outer["onentry"][0]["execution_order"] == ["raise", "log"]
    assert outer["state"][1]["help_text"] == ["keep this comment with b"]
    rebuilt = DOC.json_to_xml(json.dumps(raw))
    assert json.loads(DOC.xml_to_json(rebuilt)) == raw
    assert region_ids(ET.fromstring(rebuilt).find(".//{*}parallel[@id='inner']")) == ["i1", "i2", "i3"]


def test_parallel_in_an_invoked_chart_owns_its_sequence():
    embedded = chart('<parallel id="inner"/><state id="s"/><parallel id="last"/>')
    parent = chart(f'<state id="host"><invoke><content>{embedded}</content></invoke></state>')
    raw = json.loads(DOC.xml_to_json(parent))
    block = raw["parallel"][0]["state"][0]["invoke"][0]["content"][0]["content"][0]["parallel"][0]
    assert block["region_order"] == ["parallel", "state", "parallel"]
    assert json.loads(DOC.xml_to_json(DOC.json_to_xml(json.dumps(raw)))) == raw
    block["region_order"] = ["parallel", "state"]
    for read in (pydantic.Scxml.model_validate, pydantic_strict.Scxml.model_validate,
                 lambda value: DOC.json_to_xml(json.dumps(value))):
        with pytest.raises(ValueError, match="region_order"):
            read(raw)


@pytest.mark.parametrize("legacy", [False, True])
def test_legacy_grouping_and_present_region_arrays(legacy):
    raw = json.loads(DOC.xml_to_json(chart('<parallel id="p"/><state id="s1"/><state id="s2"/>')))
    outer = raw["parallel"][0]
    # Reorder the JSON fields. Each kind's array keeps its authored occurrence order.
    outer["state"] = outer.pop("state")
    if legacy:
        del outer["region_order"]
    for family in (pydantic, pydantic_strict):
        model = family.Scxml.model_validate(raw)
        result = model.model_dump(mode="json")["parallel"][0]
        assert ("region_order" in result) == (not legacy)
        assert ("region_order" in json.loads(model.model_dump_json())["parallel"][0]) == (not legacy)
        expected = ["s1", "s2", "p"] if legacy else ["p", "s1", "s2"]
        assert [n.id for _, n in iter_regions(model.parallel[0])] == expected
    assert region_ids(ET.fromstring(DOC.json_to_xml(json.dumps(raw))).find("{*}parallel")) == expected


@pytest.mark.parametrize("kinds,order", [((), []), (("state",), ["state"]),
                                        (("parallel", "parallel"), ["parallel", "parallel"])])
def test_homogeneous_explicit_arrays_and_omitted_canonical_form(kinds, order):
    xml = chart("".join(f'<{kind} id="r{i}"/>' for i, kind in enumerate(kinds)))
    raw = json.loads(SCXMLDocumentHandler(omit_empty=False).xml_to_json(xml))
    assert "region_order" not in raw["parallel"][0]
    # Canonical XML intake may omit homogeneous region metadata. Readers still
    # accept an author-provided complete array, including an explicit empty one.
    raw = json.loads(DOC.xml_to_json(xml))
    raw["parallel"][0]["region_order"] = order
    assert json.loads(pydantic.Scxml.model_validate(raw).model_dump_json())["parallel"][0]["region_order"] == order
    assert region_ids(ET.fromstring(DOC.json_to_xml(json.dumps(raw))).find("{*}parallel")) == [
        f"r{i}" for i in range(len(kinds))]


@pytest.mark.parametrize("order", [None, [], "parallel", {}, ["parallel"], ["state", "state"],
                                  ["state", "parallel", "state"], ["foreign", "parallel"],
                                  ["history", "state"], [1, "parallel"], [{"kind": "state"}, "parallel"]])
def test_invalid_order_is_refused_by_both_models_and_the_converter(order):
    raw = json.loads(DOC.xml_to_json(chart('<parallel id="p"/><state id="s"/>')))
    raw["parallel"][0]["region_order"] = order
    for read in (pydantic.Scxml.model_validate, pydantic_strict.Scxml.model_validate,
                 lambda value: DOC.json_to_xml(json.dumps(value))):
        with pytest.raises(ValueError, match="region_order"):
            read(raw)


def test_reserved_field_on_other_typed_nodes_but_opaque_foreign_attributes():
    raw = json.loads(DOC.xml_to_json(chart('<state id="a"/><x:mark region_order="user metadata"/>')))
    outer = raw["parallel"][0]
    outer["other_attributes"] = {"{urn:foreign}region_order": "user metadata"}
    assert json.loads(DOC.xml_to_json(DOC.json_to_xml(json.dumps(raw)))) == raw
    for target in (raw, outer["state"][0]):
        target["region_order"] = []
        for read in (pydantic.Scxml.model_validate, pydantic_strict.Scxml.model_validate,
                     lambda value: DOC.json_to_xml(json.dumps(value))):
            with pytest.raises(ValueError, match="region_order"):
                read(raw)
        del target["region_order"]


def test_canonical_schema_and_vendored_copies_share_the_enum():
    repo = Path(__file__).resolve().parents[2]
    schema = (repo / "scjson.schema.json").read_bytes()
    assert all(p.read_bytes() == schema for p in
               (repo / "js/scjson.schema.json", repo / "java/src/main/resources/scjson.schema.json"))
    defs = json.loads(schema)["$defs"]
    expected = defs["Parallel"]["properties"]["region_order"]
    assert expected == pydantic.Scxml.model_json_schema()["$defs"]["Parallel"]["properties"]["region_order"]
    assert expected["items"]["enum"] == ["state", "parallel"]
    assert "region_order" not in defs["State"]["properties"]
