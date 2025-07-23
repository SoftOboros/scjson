"""
Agent Name: python-engine-tests

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.
"""

from decimal import Decimal
from scjson.pydantic import Scxml, State, Transition, Datamodel, Data
from scjson.context import DocumentContext


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
