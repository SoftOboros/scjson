"""
Agent Name: python-engine-tests

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.
"""

from decimal import Decimal
from scjson.pydantic import Scxml, State, Transition, Datamodel, Data
from scjson.context import DocumentContext
from scjson.SCXMLDocumentHandler import SCXMLDocumentHandler


def _make_doc():
    """Create a minimal state machine for tests."""
    return Scxml(
        id="root",
        initial=["a"],
        state=[
            State(id="a", transition=[Transition(event="go", target=["b"])]),
            State(id="b"),
        ],
        version=Decimal("1.0"),
    )


def _make_cond_doc() -> Scxml:
    """State machine with a conditional transition."""
    return Scxml(
        id="cond",
        initial=["a"],
        datamodel=[Datamodel(data=[Data(id="flag", expr="1")])],
        state=[
            State(id="a", transition=[Transition(event="go", target=["b"], cond="flag == 1")]),
            State(id="b"),
        ],
        version=Decimal("1.0"),
    )


def _make_local_data_doc() -> Scxml:
    """Root data overridden by state-scoped <data> entry."""
    return Scxml(
        id="shadow",
        initial=["s"],
        datamodel=[Datamodel(data=[Data(id="flag", expr="0")])],
        state=[
            State(
                id="s",
                datamodel=[Datamodel(data=[Data(id="flag", expr="1")])],
                transition=[Transition(event="go", target=["t"], cond="flag == 1")],
            ),
            State(id="t"),
        ],
        version=Decimal("1.0"),
    )


def _make_entry_exit_doc() -> Scxml:
    """State machine with onentry/onexit assignments."""
    return Scxml(
        id="actions",
        datamodel=[Datamodel(data=[Data(id="count", expr="0")])],
        initial=["a"],
        state=[
            State(
                id="a",
                onentry=[{"assign": [{"location": "count", "expr": "count + 1"}]}],
                onexit=[{"assign": [{"location": "count", "expr": "count + 2"}]}],
                transition=[Transition(event="go", target=["b"])],
            ),
            State(id="b"),
        ],
        version=Decimal("1.0"),
    )


def _make_history_doc() -> Scxml:
    """Parent state with history."""
    return Scxml(
        id="hist",
        initial=["p"],
        state=[
            State(
                id="p",
                initial_attribute=["s1"],
                history=[{"id": "h", "transition": Transition(target=["s1"])}],
                state=[
                    State(id="s1", transition=[Transition(event="next", target=["s2"])]),
                    State(id="s2")
                ],
                transition=[Transition(event="toQ", target=["q"])]
            ),
            State(id="q", transition=[Transition(event="back", target=["h"])]),
        ],
        version=Decimal("1.0"),
    )


def test_initial_configuration():
    """Ensure initial states are entered on context creation."""
    ctx = DocumentContext.from_doc(_make_doc())
    assert "a" in ctx.configuration


def test_transition_microstep():
    """Verify that transitions update the configuration."""
    ctx = DocumentContext.from_doc(_make_doc())
    ctx.enqueue("go")
    ctx.microstep()
    assert "b" in ctx.configuration and "a" not in ctx.configuration


def test_transition_condition():
    """Transitions fire only when conditions evaluate truthy."""
    doc = _make_cond_doc()
    ctx = DocumentContext.from_doc(doc)
    ctx.enqueue("go")
    ctx.microstep()
    assert "b" in ctx.configuration

    ctx2 = DocumentContext.from_doc(doc)
    ctx2.data_model["flag"] = 0
    ctx2.root_activation.local_data["flag"] = 0
    ctx2.enqueue("go")
    ctx2.microstep()
    assert "b" not in ctx2.configuration


def test_state_scoped_datamodel():
    """State-level <data> should shadow global variables."""
    ctx = DocumentContext.from_doc(_make_local_data_doc())
    ctx.enqueue("go")
    ctx.microstep()
    assert "t" in ctx.configuration


def _make_logic_doc() -> Scxml:
    """State machine exercising boolean operators."""
    return Scxml(
        id="logic",
        initial=["s"],
        datamodel=[Datamodel(data=[
            Data(id="a", expr="1"),
            Data(id="b", expr="0"),
            Data(id="c", expr="1"),
        ])],
        state=[
            State(
                id="s",
                transition=[
                    Transition(event="to1", target=["t1"], cond="a == 1 and b == 0"),
                    Transition(event="to2", target=["t2"], cond="a == 1 or b == 1"),
                    Transition(event="to3", target=["t3"], cond="not b"),
                    Transition(event="to4", target=["t4"], cond="a == 1 and (b == 0 or c == 1)"),
                ],
            ),
            State(id="t1"),
            State(id="t2"),
            State(id="t3"),
            State(id="t4"),
        ],
        version=Decimal("1.0"),
    )


def _make_nested_doc() -> Scxml:
    """Two-step machine for nested condition checks."""
    return Scxml(
        id="nested",
        initial=["a"],
        datamodel=[Datamodel(data=[
            Data(id="x", expr="1"),
            Data(id="y", expr="0"),
        ])],
        state=[
            State(id="a", transition=[Transition(event="step", target=["b"], cond="x == 1")]),
            State(id="b", transition=[Transition(event="finish", target=["c"], cond="y == 0")]),
            State(id="c"),
        ],
        version=Decimal("1.0"),
    )


def test_and_condition():
    """Handle boolean AND conditions."""
    ctx = DocumentContext.from_doc(_make_logic_doc())
    ctx.enqueue("to1")
    ctx.microstep()
    assert "t1" in ctx.configuration


def test_or_condition():
    """Handle boolean OR conditions."""
    doc = _make_logic_doc()
    ctx = DocumentContext.from_doc(doc)
    ctx.data_model["b"] = 1
    ctx.root_activation.local_data["b"] = 1
    ctx.enqueue("to2")
    ctx.microstep()
    assert "t2" in ctx.configuration


def test_not_condition():
    """Handle boolean NOT conditions."""
    ctx = DocumentContext.from_doc(_make_logic_doc())
    ctx.enqueue("to3")
    ctx.microstep()
    assert "t3" in ctx.configuration


def test_nested_boolean_condition():
    """Evaluate nested boolean expressions."""
    ctx = DocumentContext.from_doc(_make_logic_doc())
    ctx.enqueue("to4")
    ctx.microstep()
    assert "t4" in ctx.configuration


def test_nested_conditional_transitions():
    """Transitions chained across multiple states."""
    ctx = DocumentContext.from_doc(_make_nested_doc())
    ctx.enqueue("step")
    ctx.microstep()
    assert "b" in ctx.configuration
    ctx.enqueue("finish")
    ctx.microstep()
    assert "c" in ctx.configuration

    
def test_eval_condition_bad_syntax():
    """Invalid syntax should not raise exceptions."""
    ctx = DocumentContext.from_doc(_make_doc())
    result = ctx._eval_condition("flag ==", ctx.root_activation)
    assert result is False


def test_eval_condition_missing_variable():
    """Undefined variables are treated as false."""
    ctx = DocumentContext.from_doc(_make_doc())
    result = ctx._eval_condition("unknown", ctx.root_activation)
    assert result is False

    
def test_onentry_onexit_actions():
    """onentry/onexit assign actions should update variables."""
    ctx = DocumentContext.from_doc(_make_entry_exit_doc())
    assert ctx.data_model["count"] == 1
    ctx.enqueue("go")
    ctx.microstep()
    assert ctx.data_model["count"] == 3


def test_history_state_restore():
    """History states restore last active child."""
    ctx = DocumentContext.from_doc(_make_history_doc())
    ctx.enqueue("next")
    ctx.microstep()
    assert "s2" in ctx.configuration
    ctx.enqueue("toQ")
    ctx.microstep()
    assert "q" in ctx.configuration and "p" not in ctx.configuration
    ctx.enqueue("back")
    ctx.microstep()
    assert "p" in ctx.configuration and "s2" in ctx.configuration


def test_xml_skip_unknown(tmp_path):
    """Unknown elements are ignored when configured."""
    xml = (
        "<scxml xmlns='http://www.w3.org/2005/07/scxml'>"
        "<state id='a'/><bogus/></scxml>"
    )
    path = tmp_path / "bad.scxml"
    path.write_text(xml)
    handler = SCXMLDocumentHandler(fail_on_unknown_properties=False)
    json_str = handler.xml_to_json(xml)
    assert "bogus" not in json_str
