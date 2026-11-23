"""Public interpreter and IR behavior for default and explicit entry."""

import itertools
import json
from pathlib import Path

import pytest

from scjson.SCXMLDocumentHandler import SCXMLDocumentHandler
from scjson.activation import ActivationStatus
from scjson.context import DocumentContext
from scjson.events import Event
from scjson.exec_ir import lower_document
from scjson.pydantic import Scxml


FIXTURE = Path(__file__).with_name("fixtures") / "compound_initial.scxml"
ROUTES = ["xml", "model", "scjson", "returned", "legacy"]


def chart(body, attributes=""):
    return f'<scxml xmlns="http://www.w3.org/2005/07/scxml" version="1.0" datamodel="ecmascript" {attributes}>{body}</scxml>'


def load(xml, route, directory):
    handler = SCXMLDocumentHandler()
    if route != "xml":
        raw = json.loads(handler.xml_to_json(xml))
        if route == "legacy":
            def unmark(node):
                if isinstance(node, dict):
                    node.pop("state_order", None)
                    for child in node.values():
                        unmark(child)
                elif isinstance(node, list):
                    for child in node:
                        unmark(child)
            unmark(raw)
        model = Scxml.model_validate(DocumentContext._prepare_raw_data(raw))
        if route == "model":
            return DocumentContext.from_doc(model), model
        if route != "returned":
            path = directory / "test.scjson"
            path.write_text(json.dumps(raw), encoding="utf-8")
            return DocumentContext.from_json_file(path), model
        xml = handler.json_to_xml(json.dumps(raw))
    path = directory / "test.scxml"
    path.write_text(xml, encoding="utf-8")
    return DocumentContext.from_xml_file(path), handler.load(str(path))


@pytest.mark.parametrize("order", itertools.permutations(("s", "p", "f")))
@pytest.mark.parametrize("compound", [False, True])
@pytest.mark.parametrize("route", ROUTES)
def test_first_real_child_determines_entry_and_completion(order, compound, route, tmp_path):
    children = {"s": '<state id="s"/>', "p": '<parallel id="p"><state id="leaf"/></parallel>', "f": '<final id="f"/>'}
    body = "".join(children[kind] for kind in order)
    if compound:
        body = f'<state id="owner">{body}</state>'
    ctx, model = load(chart(body), route, tmp_path)
    ir, diagnostics = lower_document(model)
    assert diagnostics == []
    container = ir.children[0] if compound else ir
    expected = ["s", "p", "f"] if route == "legacy" else list(order)
    assert [child.id for child in container.children] == expected
    first = expected[0]
    assert ctx.configuration & ctx.leaf_state_ids() == {"leaf" if first == "p" else first}
    assert (ctx.root_activation.status is ActivationStatus.FINAL) == (first == "f" and not compound)
    if compound:
        assert (ctx.activations["owner"].status is ActivationStatus.FINAL) == (first == "f")


@pytest.mark.parametrize("route", ROUTES)
def test_explicit_initial_orders_actions_and_preserves_all_targets_on_reentry(route, tmp_path):
    ctx, model = load(FIXTURE.read_text(encoding="utf-8"), route, tmp_path)
    ir, diagnostics = lower_document(model)
    assert diagnostics == []
    owner = next(child for child in ir.children if child.id == "owner")
    assert owner.initial == "b d"
    assert [type(a).__name__ for a in owner.initial_actions] == ["AssignNode", "AssignNode", "RaiseNode"]
    for visits in (1, 2):
        assert ctx.configuration & ctx.leaf_state_ids() == {"b", "d"}
        assert ctx.data_model["phase"] == 1234
        assert ctx.data_model["initialRuns"] == visits
        assert ctx.trace_step()["event"]["name"] == "observe"
        assert ctx.data_model["observed"] == 1234
        ctx.trace_step(Event(name="leave"))
        assert ctx.configuration & ctx.leaf_state_ids() == {"outside"}
        ctx.trace_step(Event(name="again" if visits == 1 else "deep"))
    assert ctx.configuration & ctx.leaf_state_ids() == {"b", "d"}
    assert ctx.data_model["phase"] == 134
    assert ctx.data_model["initialRuns"] == 2
    assert ctx.events.pop() is None


@pytest.mark.parametrize("route", ROUTES)
def test_explicit_attribute_and_completion_on_reentry(route, tmp_path):
    ctx, model = load(chart('''
      <state id="owner" initial="choice">
        <parallel id="unused"><state id="unusedLeaf"/></parallel>
        <state id="choice"><transition event="finish" target="selected"/></state>
        <final id="selected"/>
        <transition event="again" target="owner"/>
        <transition event="stop" target="terminal"/>
      </state><final id="terminal"/>''', 'initial="owner"'), route, tmp_path)
    ir, _ = lower_document(model)
    owner = next(child for child in ir.children if child.id == "owner")
    assert owner.initial == "choice" and owner.initial_actions == []
    for event in ("again", "stop"):
        assert ctx.activations["owner"].status is ActivationStatus.ACTIVE
        assert ctx.configuration & ctx.leaf_state_ids() == {"choice"}
        ctx.trace_step(Event(name="finish"))
        assert ctx.trace_step()["event"]["name"] == "done.state.owner"
        assert ctx.activations["owner"].status is ActivationStatus.FINAL
        assert ctx.root_activation.status is ActivationStatus.ACTIVE
        ctx.trace_step(Event(name=event))
    assert ctx.root_activation.status is ActivationStatus.FINAL
    assert ctx.configuration & ctx.leaf_state_ids() == {"terminal"}


@pytest.mark.parametrize("route", ROUTES)
def test_unnamed_siblings_have_stable_distinct_identities(route, tmp_path):
    xml = chart('''<state id="owner"><final/><state/><state id="anon"/></state>''')
    ctx, model = load(xml, route, tmp_path)
    ir, _ = lower_document(model)
    again, reloaded = load(xml, route, tmp_path)
    assert ir == lower_document(reloaded)[0]
    assert len(ir.anonymous_ids) == len(set(ir.anonymous_ids)) == 2
    assert "anon" not in ir.anonymous_ids
    first = ir.children[0].children[0].id
    assert first in ir.anonymous_ids and first in ctx.configuration and first in again.configuration
    assert not ctx._in_state(first) and not ctx._in_state("anon")
    assert (ctx.activations["owner"].status is ActivationStatus.FINAL) == (route != "legacy")
    # The lone unnamed node retains its existing interpreter ID, and still has no authored ID.
    single, model = load(chart("<state/>"), route, tmp_path)
    assert lower_document(model)[0].anonymous_ids == ["anon"]
    assert "anon" in single.configuration and not single._in_state("anon")
