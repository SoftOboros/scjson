"""
Agent Name: python-root-activation-regression-tests

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Regression coverage for root activation identity and user state visibility.
"""

from scjson.context import DocumentContext
from scjson.events import Event


def _chart_root_name_collides_with_state_id() -> str:
    """Return a chart whose root name collides with a user state id.

    Returns
    -------
    str
        SCXML chart text containing ``<scxml name="menu">`` and
        ``<state id="menu">``.
    """
    return (
        """
        <scxml name="menu" initial="menu" xmlns="http://www.w3.org/2005/07/scxml">
          <state id="menu">
            <transition event="select" target="selected"/>
          </state>
          <final id="selected"/>
        </scxml>
        """
    ).strip()


def test_root_activation_name_collision_keeps_user_state_visible() -> None:
    """Configuration and trace output keep a state named like the root chart."""
    ctx = DocumentContext.from_xml_string(_chart_root_name_collides_with_state_id())

    assert "menu" in ctx.configuration

    initial_trace = ctx.trace_step()
    assert "menu" in initial_trace["configuration"]

    select_trace = ctx.trace_step(Event(name="select"))
    assert select_trace["firedTransitions"] == [
        {"source": "menu", "targets": ["selected"], "event": "select", "cond": None}
    ]
    assert "menu" in select_trace["exitedStates"]
    assert "selected" in select_trace["configuration"]
    assert "menu" not in ctx.configuration
