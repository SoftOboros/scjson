"""
Agent Name: executable-order-regressions

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

SCJSON-CONV-00 executable-child order across XML, JSON, execution and IR.
"""

from copy import deepcopy
import json
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from scjson import pydantic, pydantic_strict
from scjson.SCXMLDocumentHandler import SCXMLDocumentHandler
from scjson.context import DocumentContext
from scjson.exec_ir import AssignNode, IfNode, lower_document


NS = "http://www.w3.org/2005/07/scxml"
HANDLER = SCXMLDocumentHandler()
REPO = Path(__file__).resolve().parents[2]


def chart(body):
    return (f'<scxml xmlns="{NS}" xmlns:x="urn:ext" version="1.0" initial="s" datamodel="python">'
            '<datamodel><data id="v" expr="0"/></datamodel>'
            f'<state id="s"><onentry>{body}</onentry></state></scxml>')


def assigned(value):
    return f'<assign location="v" expr="{value}"/>'


def entry(raw):
    return raw["state"][0]["onentry"][0]


def test_previous_json_collision_is_distinguishable_and_selects_the_authored_branch():
    before = chart('<if cond="False">' + assigned(1) + '<else/>' + assigned(2) + '</if>')
    after = chart('<if cond="False">' + assigned(1) + assigned(2) + '<else/></if>')
    a, b = [json.loads(HANDLER.xml_to_json(x)) for x in (before, after)]
    for raw, order, expected in [(a, ["assign", "else", "assign"], 2),
                                 (b, ["assign", "assign", "else"], 0)]:
        block = entry(raw)["if_value"][0]
        assert block["execution_order"] == order
        machine = pydantic.Scxml.model_validate(raw)
        assert DocumentContext.from_doc(machine).data_model["v"] == expected
        block.pop("execution_order")
    assert a == b


def test_repeated_guards_and_foreign_names_keep_their_individual_payloads_and_comments(tmp_path):
    xml = chart('<if cond="False">' + assigned(10) + '<elseif cond="False"/>'
                + assigned(20) + '<elseif cond="True"/><x:assign code="a">opaque</x:assign>'
                + '<!-- chosen -->' + assigned(30) + '<x:assign code="b"/>'
                + '<else/>' + assigned(40) + '</if><log expr="v"/>')
    raw = json.loads(HANDLER.xml_to_json(xml))
    block = entry(raw)["if_value"][0]
    assert entry(raw)["execution_order"] == ["if", "log"]
    assert block["execution_order"] == [
        "assign", "elseif", "assign", "elseif", "{urn:ext}assign", "assign",
        "{urn:ext}assign", "else", "assign",
    ]
    assert block["elseif"] == [{"cond": "False"}, {"cond": "True"}]
    assert block["other_element"][0]["text"] == "opaque"
    assert [a.get("help_text") for a in block["assign"]] == [None, None, ["chosen"], None]
    exported = HANDLER.json_to_xml(json.dumps(raw))
    assert "execution_order" not in exported and "executionOrder" not in exported
    assert [e.get("code") for e in ET.fromstring(exported).iter("{urn:ext}assign")] == ["a", "b"]
    assert json.loads(HANDLER.xml_to_json(exported)) == raw
    path = tmp_path / "chart.scxml"
    path.write_text(xml, encoding="utf-8")
    native = HANDLER.load(str(path))
    HANDLER.dump(native, str(path))
    assert [e.tag for e in ET.parse(path).find(".//{" + NS + "}if")] == [
        ("{" + NS + "}" + k) if not k.startswith("{") else k for k in block["execution_order"]
    ]
    doc = pydantic.Scxml.model_validate(raw)
    assert DocumentContext.from_doc(doc).data_model["v"] == 30
    ir, diagnostics = lower_document(doc)
    assert diagnostics == []
    conditional = ir.children[0].onentry[0]
    assert isinstance(conditional, IfNode)
    assert [[node.expr.num for node in branch.body if isinstance(node, AssignNode)]
            for branch in conditional.branches] == [[10], [20], [30], [40]]


@pytest.mark.parametrize("model", [pydantic, pydantic_strict])
def test_model_export_omits_absent_orders_at_each_depth_and_preserves_explicit_empty(model):
    """The Python export contract is the same on the pinned Pydantic 2.11 runtime."""
    raw = json.loads(HANDLER.xml_to_json(chart(
        '<if cond="True"><foreach array="[1]" item="v">' + assigned(1) + '</foreach></if>'
        '<log expr="v"/>')))
    raw["state"][0]["onexit"] = [{"execution_order": []}]
    doc = model.Scxml.model_validate(raw)
    for exported in (doc.model_dump(), doc.model_dump(mode="json"), json.loads(doc.model_dump_json())):
        outer = entry(exported)
        assert outer["execution_order"] == ["if", "log"]
        assert exported["state"][0]["onexit"][0]["execution_order"] == []
        assert "execution_order" not in outer["if_value"][0]
        assert "execution_order" not in outer["if_value"][0]["foreach"][0]
        wire = model.Scxml.model_validate(exported).model_dump_json()
        assert DocumentContext.from_doc(pydantic.Scxml.model_validate_json(wire)).data_model["v"] == 1


@pytest.mark.parametrize("model", [pydantic, pydantic_strict])
def test_legacy_input_and_canonical_singleton_elseif(model):
    raw = json.loads(HANDLER.xml_to_json(chart('<if cond="False"><elseif cond="True"/>'
                                               + assigned(5) + '</if>')))
    block = entry(raw)["if_value"][0]
    assert block["elseif"] == {"cond": "True"}
    block["elseif"] = [block["elseif"]]
    assert model.Scxml.model_validate(raw).model_dump()["state"][0]["onentry"][0]["if_value"][0]["elseif"]["cond"] == "True"
    block["elseif"] = block["elseif"][0]
    del block["execution_order"]
    doc = model.Scxml.model_validate(raw)
    assert '"execution_order"' not in doc.model_dump_json()
    assert "<ns0:elseif " in HANDLER.json_to_xml(json.dumps(raw))


@pytest.mark.parametrize("order", [
    None, "assign", {}, [7], [], ["assign", "else"], ["assign", "else", "assign", "assign"],
    ["assign", "other_element", "assign"], ["assign", "else", "unknown"],
    ["else", "else", "assign"], ["else", "elseif", "assign", "assign"],
])
def test_malformed_explicit_order_is_rejected_at_both_model_and_converter(order):
    raw = json.loads(HANDLER.xml_to_json(chart('<if cond="True">' + assigned(1)
                                               + '<else/>' + assigned(2) + '</if>')))
    block = entry(raw)["if_value"][0]
    if order == ["else", "elseif", "assign", "assign"]:
        block["elseif"] = {"cond": "False"}
    block["execution_order"] = order
    for factory in (pydantic.Scxml.model_validate, pydantic_strict.Scxml.model_validate,
                    lambda data: HANDLER.json_to_xml(json.dumps(data))):
        with pytest.raises(ValueError, match="execution_order"):
            factory(raw)


def test_no_order_for_homogeneous_children_and_valid_explicit_empty():
    raw = json.loads(HANDLER.xml_to_json(chart(assigned(1) + assigned(2))))
    assert "execution_order" not in entry(raw)
    entry(raw)["execution_order"] = ["assign", "assign"]
    assert len(pydantic.Scxml.model_validate(raw).state[0].onentry[0].assign) == 2
    entry(raw).clear()
    entry(raw)["execution_order"] = []
    assert pydantic.Scxml.model_validate(raw).state[0].onentry[0].execution_order == []
    assert ET.fromstring(HANDLER.json_to_xml(json.dumps(raw))).find(".//{" + NS + "}onentry") is not None
    entry(raw)["execution_order"] = ["else"]
    with pytest.raises(ValueError, match="outside if"):
        HANDLER.json_to_xml(json.dumps(raw))


def test_nested_foreach_transition_finalize_and_onexit_order_round_trip():
    children = assigned(1) + '<log expr="v"/>' + assigned(2)
    xml = (f'<scxml xmlns="{NS}" version="1.0"><state id="s">'
           f'<onexit>{children}</onexit><transition event="go" target="s">{children}</transition>'
           f'<onentry><foreach array="a" item="v">{children}</foreach></onentry>'
           f'<invoke><finalize>{children}</finalize></invoke></state></scxml>')
    raw = json.loads(HANDLER.xml_to_json(xml))
    state = raw["state"][0]
    for group in [state["onexit"][0], state["transition"][0], entry(raw)["foreach"][0],
                  state["invoke"][0]["finalize"][0]]:
        assert group["execution_order"] == ["assign", "log", "assign"]
    assert json.loads(HANDLER.xml_to_json(HANDLER.json_to_xml(json.dumps(raw)))) == raw


@pytest.mark.parametrize("dialect", ["ecma", "python"])
@pytest.mark.parametrize("mode", ["strict", "lax"])
@pytest.mark.parametrize(("case", "key", "value"), [(153, "Var4", 1), (457, "Var6", 6), (459, "Var5", 1)])
def test_original_alex_z_xml_and_scjson_trace_parity(dialect, case, key, value, mode, tmp_path):
    tier = "Mandatory" if case == 153 else "Optional"
    path = REPO / "tutorial" / "Tests" / dialect / "W3C" / tier / "Auto" / f"test{case}.scxml"
    if not path.is_file():
        pytest.skip("Alex Z tutorial submodule unavailable")
    converted = tmp_path / "converted.scjson"
    converted.write_text(HANDLER.xml_to_json(path.read_text(encoding="utf-8")), encoding="utf-8")
    xml_context = DocumentContext.from_xml_file(path, execution_mode=mode)
    json_context = DocumentContext.from_json_file(converted, execution_mode=mode)
    for _ in range(12):
        assert deepcopy(xml_context.trace_step()) == json_context.trace_step()
        if "pass" in xml_context.configuration or "fail" in xml_context.configuration:
            break
    assert xml_context.configuration == json_context.configuration
    assert "pass" in xml_context.configuration
    assert xml_context.data_model == json_context.data_model
    assert xml_context.data_model[key] == value


def test_canonical_schemas_declare_the_field_and_both_marker_forms():
    paths = [REPO / "scjson.schema.json", REPO / "js/scjson.schema.json",
             REPO / "java/src/main/resources/scjson.schema.json"]
    content = [path.read_bytes() for path in paths]
    assert content[0] == content[1] == content[2]
    definitions = json.loads(content[0])["$defs"]
    comparable = pydantic.Scxml.model_json_schema()["$defs"]
    for name in ("Onentry", "Onexit", "Transition", "Finalize", "Foreach", "If"):
        spec = definitions[name]["properties"]["execution_order"]
        assert spec == comparable[name]["properties"]["execution_order"]
        assert spec["type"] == "array" and spec["items"] == {"type": "string"}
    assert definitions["If"]["properties"]["elseif"] == comparable["If"]["properties"]["elseif"]


@pytest.mark.parametrize("schema", ["scxml.xsd", "scxml-strict.xsd"])
def test_xml_schema_permits_several_elseif_then_one_else(schema):
    import xmlschema

    reader = xmlschema.XMLSchema11 if schema == "scxml-strict.xsd" else xmlschema.XMLSchema
    validator = reader(REPO / "xsd" / schema)
    assert validator.is_valid(chart('<if cond="True"><elseif cond="False"/><elseif cond="True"/><else/></if>'))
    assert not validator.is_valid(chart('<if cond="True"><else/><elseif cond="False"/></if>'))
