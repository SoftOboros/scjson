"""
Agent Name: state-membership-tests

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

ERRATA-003 portable guard admission and active-configuration timing controls.
"""
import json
from pathlib import Path
from xml.sax.saxutils import quoteattr

import pytest

from scjson.context import DocumentContext
from scjson.events import Event
from scjson.exec_ir import BinOp, CallNode, CapabilityCallNode, StringLiteral, UnaryOp, UnsupportedExpr, lower_document
from scjson.pydantic import Scxml
from scjson.SCXMLDocumentHandler import SCXMLDocumentHandler


def chart(body, dialect="ecmascript", initial="a"):
    return (f'<scxml xmlns="http://www.w3.org/2005/07/scxml" version="1.0" '
            f'datamodel="{dialect}" initial="{initial}">{body}</scxml>')


def lower(xml):
    data = json.loads(SCXMLDocumentHandler().xml_to_json(xml))
    return lower_document(Scxml.model_validate(DocumentContext._prepare_raw_data(data)))


@pytest.mark.parametrize("dialect,condition", [
    ("ecmascript", """In('a') && !In("missing")"""),
    ("python", """In('a') and not In("missing")"""),
])
def test_guards_reuse_call_family_in_transition_if_and_elseif(dialect, condition):
    xml = chart(f"""<state id="a"><transition cond={quoteattr(condition)} target="b"/>
      <onentry><if cond="In('a')"><raise event="first"/><elseif cond="In('other')"/>
      <raise event="second"/></if></onentry></state><final id="b"/>""", dialect)
    machine, diagnostics = lower(xml)
    assert diagnostics == []
    root = machine.children[0]
    assert root.transitions[0].guard == BinOp("&&", CallNode("In", [StringLiteral("a")]),
                                             UnaryOp("not", CallNode("In", [StringLiteral("missing")])))
    assert [b.guard for b in root.onentry[0].branches] == [
        CallNode("In", [StringLiteral("a")]), CallNode("In", [StringLiteral("other")])]


@pytest.mark.parametrize("dialect", ["ecmascript", "python"])
@pytest.mark.parametrize("source", [
    "In()", "In('a', 'b')", "In(name)", "In(1)", "In('a' + 'b')", "In('a' 'b')",
    "In(state='a')", "str(In('a'))", "In('a') == bogus()", "In('a') == [bogus()]",
])
def test_unsupported_guard_is_blocked_as_a_whole(dialect, source):
    negation = "!" if dialect == "ecmascript" else "not "
    guard = f"{negation}({source})"
    machine, diagnostics = lower(chart(f'<state id="a"><transition cond={quoteattr(guard)}/></state>', dialect))
    node = machine.children[0].transitions[0].guard
    assert isinstance(node, UnsupportedExpr)
    assert node.source == guard
    assert diagnostics == [node.diagnostic]
    assert node.diagnostic.outcome == "reject"


@pytest.mark.parametrize("source", ['In(r"a")', "In('''a''')"])
def test_python_string_spellings_refused_in_ecmascript(source):
    machine, diagnostics = lower(chart(f'<state id="a"><transition cond={quoteattr(source)}/></state>'))
    assert diagnostics and isinstance(machine.children[0].transitions[0].guard, UnsupportedExpr)


@pytest.mark.parametrize("dialect", ["python", "ecmascript"])
def test_value_and_script_membership_never_become_portable(dialect):
    xml = chart("""<datamodel><data id="x" expr="In('a')"/></datamodel>
        <state id="a"><onentry><assign location="x" expr="In('a')"/>
          <script>x = In('a')</script>
        </onentry></state>""", dialect)
    machine, diagnostics = lower(xml)
    assign, script = machine.children[0].onentry
    assert isinstance(assign.expr, UnsupportedExpr)
    assert isinstance(script, CapabilityCallNode)
    assert [d.outcome for d in diagnostics] == ["reject", "reject", "capability-only"]


def test_entry_exit_and_both_orthogonal_transitions_share_one_microstep(tmp_path):
    xml = chart("""<parallel id="p"><state id="left" initial="L">
      <state id="L"><onexit><if cond="In('L')"><log label="phase" expr="'left exit'"/></if></onexit>
        <transition event="go" cond="In('R')" target="L2">
          <if cond="!In('L') &amp;&amp; !In('R') &amp;&amp; !In('R2')"><log label="phase" expr="'left body'"/></if>
        </transition>
      </state>
      <state id="L2"><onentry><if cond="In('L2') &amp;&amp; !In('R2')"><log label="phase" expr="'left entry'"/></if></onentry></state>
      </state><state id="right" initial="R">
      <state id="R"><onexit><if cond="In('L') &amp;&amp; In('R')"><log label="phase" expr="'right exit'"/></if></onexit>
        <transition event="go" cond="In('L')" target="R2"><if cond="In('p')"><log label="phase" expr="'right body'"/></if></transition>
      </state>
      <final id="R2"><onentry><if cond="In('L2') &amp;&amp; In('R2')"><log label="phase" expr="'right entry'"/>
        <elseif cond="In('p')"/><log label="phase" expr="'wrong second branch'"/></if></onentry></final>
      </state></parallel>""", initial="p")
    src = tmp_path / "chart.scxml"
    src.write_text(xml, encoding="utf8")
    converted = tmp_path / "chart.scjson"
    converted.write_text(SCXMLDocumentHandler().xml_to_json(xml), encoding="utf8")
    for engine in (DocumentContext.from_xml_file(src), DocumentContext.from_json_file(converted)):
        step = engine.trace_step(Event(name="go"))
        assert step["configuration"] == ["L2", "R2"]
        assert [t["source"] for t in step["firedTransitions"]] == ["L", "R"]
        assert step["actionLog"] == [f"phase:{action}" for action in
            ["right exit", "left exit", "left body", "right body", "left entry", "right entry"]]
    machine, diags = lower(xml)
    assert diags == []
    final = machine.children[0].children[1].children[1]
    assert final.onentry[0].branches[0].guard.lhs == CallNode("In", [StringLiteral("L2")])


def test_entry_path_skips_default_sibling_and_tracks_ancestors():
    xml = chart("""<state id="p" initial="wrong"><onentry>
      <if cond="In('p') &amp;&amp; !In('leaf')"><log label="entry" expr="'parent'"/></if></onentry>
      <state id="wrong"/><state id="nested" initial="wrong2">
        <state id="wrong2"/><state id="leaf"><onentry><if cond="In('p') &amp;&amp; In('nested') &amp;&amp; In('leaf')">
        <log label="entry" expr="'leaf'"/></if></onentry></state>
      </state></state>""", initial="leaf")
    engine = DocumentContext.from_xml_string(xml)
    assert engine.action_log == ["entry:parent", "entry:leaf"]
    assert engine.configuration - {engine.root_activation.id} == {"p", "nested", "leaf"}
    assert not any(engine._in_state(s) for s in ("wrong", "wrong2", "missing", "__scxml_root__"))


def test_authored_root_sentinel_name_is_an_ordinary_state():
    xml = chart("""<state id="a"><transition cond="In('__scxml_root__')" target="bad"/>
      <transition event="go" target="__scxml_root__"/></state>
      <state id="__scxml_root__"><onentry><if cond="In('__scxml_root__')">
      <log label="entry" expr="'authored'"/></if></onentry></state><state id="bad"/>""")
    engine = DocumentContext.from_xml_string(xml)
    assert not engine._in_state("__scxml_root__")
    step = engine.trace_step(Event(name="go"))
    assert step["configuration"] == ["__scxml_root__"] and step["actionLog"] == ["entry:authored"]


def test_inline_invoke_observes_its_own_configuration():
    child = chart("""<state id="start"><transition cond="In('shared')" target="bad"/>
       <transition cond="In('start')" target="childGood"/></state><state id="childGood"/><state id="bad"/>
       <state id="shared"/>""", initial="start")
    parent = DocumentContext.from_xml_string(chart(f"""<state id="shared"><invoke id="job" type="scxml">
        <content>{child}</content></invoke><transition event="probe" cond="In('childGood')" target="bad"/>
        <transition event="probe" cond="In('shared')" target="pass"/></state>
        <state id="bad"/><final id="pass"/>""", initial="shared"))
    invoked = parent.invocations["job"].child
    assert invoked.configuration - {invoked.root_activation.id} == {"childGood"}
    assert parent.trace_step(Event(name="probe"))["configuration"] == ["pass"]


@pytest.mark.parametrize("descriptor,event,expected", [
    ("foo.*", "foo", "yes"), ("foo.*", "foo.bar", "yes"), ("foo.*", "foobar", "no"),
    ("foo", "foo", "yes"), ("foo", "foo.bar", "no"), ("other foo.*", "foo", "yes"),
])
def test_event_matching_preserves_exact_and_wildcard_descriptors(descriptor, event, expected):
    xml = chart(f'<state id="a"><transition event="{descriptor}" target="yes"/>'
                '<transition event="*" target="no"/></state><final id="yes"/><final id="no"/>')
    ctx = DocumentContext.from_xml_string(xml)
    assert ctx.trace_step(Event(name=event))["configuration"] == [expected]


def test_history_and_transition_type_preserve_canonical_ir():
    machine, diagnostics = lower(chart("""<state id="a"><history id="h" type="deep">
      <transition target="leaf"><if cond="In('a')"><raise event="restored"/></if></transition></history>
      <state id="leaf"/><transition type="internal" target="leaf"/><transition event="reset" target="a"/>
      </state>"""))
    assert diagnostics == []
    state = machine.children[0]
    assert [t.type for t in state.transitions] == ["internal", "external"]
    history = state.children[-1]
    assert history.type == "deep" and history.transition.targets == ["leaf"]
    assert history.transition.actions[0].branches[0].guard == CallNode("In", [StringLiteral("a")])


_CORPUS = Path(__file__).resolve().parents[2] / "tutorial" / "Tests"
_ORIGINALS = [f"{dialect}/W3C/{'Optional' if n == 451 else 'Mandatory'}/Auto/test{n}.scxml"
              for dialect in ("ecma", "python") for n in (310, 409, 411, 413, 451, 580)]
_ORIGINALS.extend("ecma/Custom/uscxml/" + name + ".scxml" for name in (
    "testIssue176_DoneStateParallelNotBeforeFinal", "testIssue176_DoneStateParallelNotBeforeFinal2",
    "testIssue203_MultipleTransitionsOnSameEvent",
))


@pytest.mark.parametrize("path", _ORIGINALS)
def test_original_alex_membership_outcome(path):
    source = _CORPUS / path
    if not _CORPUS.is_dir():
        pytest.skip("Alex Z tutorial submodule unavailable")
    engine = DocumentContext.from_xml_file(source)
    for _ in range(30):
        if {"pass", "fail"} & engine.configuration:
            break
        if not engine.events:
            engine.advance_time(3000)
        engine.trace_step()
    assert engine.configuration - {engine.root_activation.id} == {"pass"}
    assert "Outcome:pass" in engine.action_log
