"""Exercise authored and legacy parallel region order through public execution APIs."""

import json
from pathlib import Path

import pytest

from scjson.SCXMLDocumentHandler import SCXMLDocumentHandler
from scjson.context import DocumentContext
from scjson.events import Event
from scjson.exec_ir import lower_document
from scjson.pydantic import Scxml


FIXTURE = Path(__file__).with_name("fixtures") / "parallel_region_order.scxml"


def remove_region_order(node):
    if isinstance(node, dict):
        node.pop("region_order", None)
        for child in node.values():
            remove_region_order(child)
    elif isinstance(node, list):
        for child in node:
            remove_region_order(child)


def load_models(route, xml, tmp_path):
    """Return the execution context and the public lowerer's source model."""
    handler = SCXMLDocumentHandler()
    if route == "xml":
        source = tmp_path / "input.scxml"
        source.write_text(xml, encoding="utf-8")
        return DocumentContext.from_xml_file(source), handler.load(str(source))
    raw = json.loads(handler.xml_to_json(xml))
    if route == "legacy":
        remove_region_order(raw)
    model = Scxml.model_validate(DocumentContext._prepare_raw_data(raw))
    if route == "model":
        return DocumentContext.from_doc(model), model
    source = tmp_path / "input.scjson"
    source.write_text(json.dumps(raw), encoding="utf-8")
    return DocumentContext.from_json_file(source), model


@pytest.mark.parametrize("route", ["xml", "scjson", "model", "legacy"])
def test_mixed_regions_control_entry_queue_conflict_and_exit(route, tmp_path):
    ctx, model = load_models(route, FIXTURE.read_text(encoding="utf-8"), tmp_path)
    ir, diagnostics = lower_document(model)
    assert diagnostics == []
    authored = route != "legacy"
    assert [region.id for region in ir.children[0].children] == (
        ["z", "a", "q", "b"] if authored else ["a", "b", "z", "q"]
    )
    ids = ["zLeaf", "a", "qLeaf", "b"] if authored else ["a", "b", "zLeaf", "qLeaf"]
    assert ctx.configuration & ctx.leaf_state_ids() == {"a", "b", "qLeaf", "zLeaf"}
    assert [ctx.trace_step()["event"]["name"] for _ in range(4)] == [
        f"record{n}" for n in ("1234" if authored else "2413")
    ]
    ordered = 1234 if authored else 2413
    assert ctx.data_model["entry"] == ctx.data_model["queued"] == ordered
    assert ctx.data_model["sawFirst"] == int(authored)
    step = ctx.trace_step(Event(name="visit"))
    assert step["configuration"] == ids
    assert [t["source"] for t in step["firedTransitions"]] == ids
    assert ctx.data_model["actions"] == ordered
    chosen = ctx.trace_step(Event(name="choose"))
    assert chosen["configuration"] == ["zWon" if authored else "aWon"]
    assert ctx.data_model["exitOrder"] == (4321 if authored else 3142)


@pytest.mark.parametrize("route", ["xml", "scjson", "model", "legacy"])
def test_inline_child_and_its_sibling_invocation(route, tmp_path):
    child = FIXTURE.read_text(encoding="utf-8").split("?>", 1)[1]
    child = child.replace('<raise event="record', '<send target="#_parent" event="record')
    xml = f"""<scxml xmlns="http://www.w3.org/2005/07/scxml" version="1.0" datamodel="ecmascript" initial="before">
      <state id="before"><transition event="start" target="outer"/></state>
      <parallel id="outer">
        <parallel id="first"><state id="inner"><invoke id="session"><content>{child}</content></invoke></state></parallel>
        <state id="second"><invoke id="sibling"><content>
          <scxml version="1.0" datamodel="ecmascript"><state id="only"/></scxml>
        </content></invoke></state>
      </parallel></scxml>"""
    parent, model = load_models(route, xml, tmp_path)
    parent.ordering_mode = "strict"
    parent.trace_step(Event(name="start"))
    ir, diagnostics = lower_document(model)
    assert diagnostics == []
    outer = next(node for node in ir.children if node.id == "outer")
    regions = {region.id: region for region in outer.children}
    session_ir = regions["first"].children[0].invokes[0].child_machine
    sibling_ir = regions["second"].invokes[0].child_machine
    assert sibling_ir.children[0].id == "only"
    child_ids = [r.id for r in session_ir.children[0].children]
    assert child_ids == (["a", "b", "z", "q"] if route == "legacy" else ["z", "a", "q", "b"])
    if route != "legacy":
        assert list(parent.invocations) == ["session", "sibling"]
    session = parent.invocations["session"].child
    assert parent.invocations["sibling"].child.configuration & {"only"} == {"only"}
    numbers = "2413" if route == "legacy" else "1234"
    assert session.data_model["entry"] == int(numbers)
    assert [evt.name for evt in iter(parent.events.pop, None)] == [f"record{n}" for n in numbers]
