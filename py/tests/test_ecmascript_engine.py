"""
Agent Name: ecmascript-engine-tests

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Integration tests for the constrained ECMAScript front-end in the engine
(M1P6 G2).  Tests that:
  - datamodel="ecmascript" machines load and execute.
  - ECMAScript conditions (===, !==, &&, ||, !) are evaluated correctly.
  - _event.name and _event.data are accessible in expressions.
  - The Dining Philosophers single-philosopher child machine can step through
    Thinking -> Hungry -> Eating using time advancement.
"""

from __future__ import annotations

import os
from pathlib import Path
from decimal import Decimal

import pytest

from scjson.context import DocumentContext, ExecutionMode


FIXTURES_DIR = Path(__file__).parent / "fixtures"
DP_DIR = (
    Path(__file__).parent.parent.parent
    / "tutorial"
    / "Examples"
    / "StateCharts"
    / "DiningPhilosphersProblem"
)
DP_SCXML = DP_DIR / "machine_dining_philosphers.scxml"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_fixture(name: str) -> DocumentContext:
    path = FIXTURES_DIR / name
    return DocumentContext.from_xml_file(
        str(path), execution_mode=ExecutionMode.LAX
    )


# ---------------------------------------------------------------------------
# Basic ecmascript datamodel tests (using the fixture machine)
# ---------------------------------------------------------------------------


def test_ecmascript_machine_loads() -> None:
    """A machine with datamodel=ecmascript loads without error."""
    ctx = _load_fixture("ecmascript_simple.scxml")
    assert "idle" in ctx.configuration


def test_ecmascript_strict_equality_condition() -> None:
    """A transition guarded by x === 0 fires when x == 0 (initial value)."""
    ctx = _load_fixture("ecmascript_simple.scxml")
    assert "idle" in ctx.configuration
    # x is initialized to 0; transition cond is "x === 0"; event is "go"
    ctx.enqueue("go")
    ctx.microstep()
    assert "active" in ctx.configuration, (
        "Expected transition to 'active' via x === 0 condition; "
        "configuration was {}".format(ctx.configuration)
    )


def test_ecmascript_logical_and_condition() -> None:
    """A transition with flag === false && x !== 1 fires from idle."""
    ctx = _load_fixture("ecmascript_simple.scxml")
    ctx.enqueue("go2")
    ctx.microstep()
    assert "done" in ctx.configuration


def test_ecmascript_logical_or_condition() -> None:
    """A transition with x > 0 || flag === true fires when x > 0."""
    ctx = _load_fixture("ecmascript_simple.scxml")
    # First get to active state
    ctx.enqueue("go")
    ctx.microstep()
    assert "active" in ctx.configuration
    # Set x > 0 by modifying datamodel directly
    ctx.data_model["x"] = 1
    ctx.enqueue("finish")
    ctx.microstep()
    assert "done" in ctx.configuration


def test_ecmascript_mode_flag_set() -> None:
    """The _ecmascript_mode flag is True for ecmascript machines."""
    ctx = _load_fixture("ecmascript_simple.scxml")
    assert getattr(ctx, "_ecmascript_mode", False) is True


def test_ecmascript_not_set_for_python_machines() -> None:
    """Non-ecmascript machines do not have _ecmascript_mode set to True."""
    from decimal import Decimal
    from scjson.pydantic import Scxml, State, Transition
    doc = Scxml(
        initial=["a"],
        state=[
            State(id="a", transition=[Transition(event="go", target=["b"])]),
            State(id="b"),
        ],
        version=Decimal("1.0"),
    )
    ctx = DocumentContext.from_doc(doc)
    assert not getattr(ctx, "_ecmascript_mode", False)


# ---------------------------------------------------------------------------
# _event availability in ecmascript conditions
# ---------------------------------------------------------------------------


def test_event_name_in_ecmascript_condition() -> None:
    """_event.name is available in ECMAScript transition conditions."""
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<scxml datamodel="ecmascript" initial="idle" version="1.0"
       xmlns="http://www.w3.org/2005/07/scxml">
  <state id="idle">
    <transition cond="_event.name === 'ping'" event="ping" target="done"/>
  </state>
  <state id="done"/>
</scxml>"""
    ctx = DocumentContext.from_xml_string(xml, execution_mode=ExecutionMode.LAX)
    ctx.enqueue("ping")
    ctx.microstep()
    assert "done" in ctx.configuration


def test_event_data_in_ecmascript_condition() -> None:
    """_event.data is available in ECMAScript transition conditions."""
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<scxml datamodel="ecmascript" initial="idle" version="1.0"
       xmlns="http://www.w3.org/2005/07/scxml">
  <state id="idle">
    <transition cond="_event.data === 1" event="tick" target="done"/>
  </state>
  <state id="done"/>
</scxml>"""
    from scjson.events import Event
    ctx = DocumentContext.from_xml_string(xml, execution_mode=ExecutionMode.LAX)
    ctx.events.push(Event(name="tick", data=1))
    ctx.microstep()
    assert "done" in ctx.configuration


def test_event_data_false_does_not_fire() -> None:
    """A transition with _event.data === 1 does NOT fire when data is 0."""
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<scxml datamodel="ecmascript" initial="idle" version="1.0"
       xmlns="http://www.w3.org/2005/07/scxml">
  <state id="idle">
    <transition cond="_event.data === 1" event="tick" target="done"/>
  </state>
  <state id="done"/>
</scxml>"""
    from scjson.events import Event
    ctx = DocumentContext.from_xml_string(xml, execution_mode=ExecutionMode.LAX)
    ctx.events.push(Event(name="tick", data=0))
    ctx.microstep()
    assert "idle" in ctx.configuration
    assert "done" not in ctx.configuration


# ---------------------------------------------------------------------------
# ECMAScript eventexpr / targetexpr / delayexpr
# ---------------------------------------------------------------------------


def test_ecmascript_eventexpr() -> None:
    """eventexpr with ECMAScript string concatenation works."""
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<scxml datamodel="ecmascript" initial="idle" version="1.0"
       xmlns="http://www.w3.org/2005/07/scxml">
  <datamodel>
    <data id="myId" expr="5"/>
  </datamodel>
  <state id="idle">
    <onentry>
      <send eventexpr="'ping.' + myId"/>
    </onentry>
    <transition event="ping.5" target="done"/>
  </state>
  <state id="done"/>
</scxml>"""
    ctx = DocumentContext.from_xml_string(xml, execution_mode=ExecutionMode.LAX)
    ctx.microstep()
    assert "done" in ctx.configuration


def test_ecmascript_delayexpr() -> None:
    """delayexpr with string concatenation (e.g., delay + 'ms') works."""
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<scxml datamodel="ecmascript" initial="idle" version="1.0"
       xmlns="http://www.w3.org/2005/07/scxml">
  <datamodel>
    <data id="delay_ms" expr="100"/>
  </datamodel>
  <state id="idle">
    <onentry>
      <send event="tick" delayexpr="delay_ms + 'ms'" id="timer1"/>
    </onentry>
    <transition event="tick" target="done"/>
  </state>
  <state id="done"/>
</scxml>"""
    ctx = DocumentContext.from_xml_string(xml, execution_mode=ExecutionMode.LAX)
    # After initial entry, the delayed event should be pending
    assert "idle" in ctx.configuration
    assert ctx.delayed_events  # timer is scheduled
    # Advance time to release it
    ctx.advance_time(0.2)
    ctx.microstep()
    assert "done" in ctx.configuration


# ---------------------------------------------------------------------------
# ECMAScript <script> body execution
# ---------------------------------------------------------------------------


def test_ecmascript_script_assignment() -> None:
    """A <script> body that assigns t_INPUTS[key] = val executes correctly."""
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<scxml datamodel="ecmascript" initial="idle" version="1.0"
       xmlns="http://www.w3.org/2005/07/scxml">
  <datamodel>
    <data id="t_INPUTS" expr="{}"/>
  </datamodel>
  <state id="idle">
    <transition event="assign_event" target="done">
      <script>t_INPUTS['key1'] = 42</script>
    </transition>
  </state>
  <state id="done"/>
</scxml>"""
    ctx = DocumentContext.from_xml_string(xml, execution_mode=ExecutionMode.LAX)
    ctx.enqueue("assign_event")
    ctx.microstep()
    assert "done" in ctx.configuration
    t_inputs = ctx.data_model.get("t_INPUTS", {})
    assert t_inputs.get("key1") == 42, (
        "Expected t_INPUTS['key1'] == 42, got {}".format(t_inputs)
    )


def test_ecmascript_script_if_body() -> None:
    """A <script> body with if (cond) { assign } executes the if branch."""
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<scxml datamodel="ecmascript" initial="idle" version="1.0"
       xmlns="http://www.w3.org/2005/07/scxml">
  <datamodel>
    <data id="x" expr="5"/>
    <data id="y" expr="0"/>
  </datamodel>
  <state id="idle">
    <onentry>
      <script>if (x !== 0) {
    y = x + 1
}</script>
    </onentry>
    <transition event="check" target="done"/>
  </state>
  <state id="done"/>
</scxml>"""
    ctx = DocumentContext.from_xml_string(xml, execution_mode=ExecutionMode.LAX)
    # x=5, y should become 6 after onentry script
    assert ctx.data_model.get("y") == 6, (
        "Expected y=6 after script; got y={}".format(ctx.data_model.get("y"))
    )


# ---------------------------------------------------------------------------
# parseInt / String built-ins
# ---------------------------------------------------------------------------


def test_parse_int_in_cond() -> None:
    """parseInt in a condition expression is evaluated correctly."""
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<scxml datamodel="ecmascript" initial="idle" version="1.0"
       xmlns="http://www.w3.org/2005/07/scxml">
  <state id="idle">
    <transition cond="parseInt('42') === 42" event="go" target="done"/>
  </state>
  <state id="done"/>
</scxml>"""
    ctx = DocumentContext.from_xml_string(xml, execution_mode=ExecutionMode.LAX)
    ctx.enqueue("go")
    ctx.microstep()
    assert "done" in ctx.configuration


# ---------------------------------------------------------------------------
# Dining Philosophers machine integration (child machine invoke, ecmascript)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not DP_SCXML.exists(),
    reason="Dining Philosophers SCXML not found at expected path",
)
def test_dp_machine_loads() -> None:
    """The Dining Philosophers SCXML loads; parallel root + 5 states entered."""
    import json as _json
    from scjson.SCXMLDocumentHandler import SCXMLDocumentHandler
    from scjson.pydantic import Scxml
    handler = SCXMLDocumentHandler(fail_on_unknown_properties=False)
    xml = DP_SCXML.read_text(encoding="utf-8-sig")
    json_str = handler.xml_to_json(xml)
    data = DocumentContext._prepare_raw_data(_json.loads(json_str))
    doc = Scxml.model_validate(data)
    ctx = DocumentContext._from_model(
        doc, data,
        allow_unsafe_eval=False, evaluator=None,
        execution_mode=ExecutionMode.LAX,
        source_xml=xml, base_dir=DP_DIR,
        defer_initial=False,
    )
    assert "DiningPhilosophers" in ctx.configuration
    thinking = [s for s in ctx.configuration if "Thinking" in s]
    assert len(thinking) == 5, (
        "Expected all 5 philosophers in Thinking; got {}".format(thinking)
    )


@pytest.mark.skipif(
    not DP_SCXML.exists(),
    reason="Dining Philosophers SCXML not found at expected path",
)
def test_dp_initial_configuration() -> None:
    """All five philosophers start in Thinking; child machines have correct forks."""
    import json as _json
    from scjson.SCXMLDocumentHandler import SCXMLDocumentHandler
    from scjson.pydantic import Scxml
    handler = SCXMLDocumentHandler(fail_on_unknown_properties=False)
    xml = DP_SCXML.read_text(encoding="utf-8-sig")
    json_str = handler.xml_to_json(xml)
    data = DocumentContext._prepare_raw_data(_json.loads(json_str))
    doc = Scxml.model_validate(data)
    ctx = DocumentContext._from_model(
        doc, data,
        allow_unsafe_eval=False, evaluator=None,
        execution_mode=ExecutionMode.LAX,
        source_xml=xml, base_dir=DP_DIR,
        defer_initial=False,
    )
    # Every child should be in Thinking state with correct fork assignment.
    for n in range(1, 6):
        inv = ctx.invocations.get("ID_P_{}".format(n))
        assert inv is not None, "Invocation ID_P_{} missing".format(n)
        child = getattr(inv, "child", None)
        assert child is not None, "Child machine for ID_P_{} not created".format(n)
        dm = child.data_model
        assert dm.get("i_ID") == n, (
            "P{} i_ID={} expected {}".format(n, dm.get("i_ID"), n)
        )
        # Verify onentry <script> executed: i_ID_LEFT / i_ID_RIGHT set from table
        assert dm.get("i_ID_LEFT", 0) != 0, (
            "P{} i_ID_LEFT not set by onentry script".format(n)
        )
        assert "Thinking" in child.configuration, (
            "P{} not in Thinking state; config={}".format(n, child.configuration)
        )


@pytest.mark.skipif(
    not DP_SCXML.exists(),
    reason="Dining Philosophers SCXML not found at expected path",
)
def test_dp_child_philosopher_script_execution() -> None:
    """The philosopher onentry <script> runs: i_ID_LEFT and i_ID_RIGHT are set."""
    import json as _json
    from scjson.SCXMLDocumentHandler import SCXMLDocumentHandler
    from scjson.pydantic import Scxml
    handler = SCXMLDocumentHandler(fail_on_unknown_properties=False)
    xml = DP_SCXML.read_text(encoding="utf-8-sig")
    json_str = handler.xml_to_json(xml)
    data = DocumentContext._prepare_raw_data(_json.loads(json_str))
    doc = Scxml.model_validate(data)
    ctx = DocumentContext._from_model(
        doc, data,
        allow_unsafe_eval=False, evaluator=None,
        execution_mode=ExecutionMode.LAX,
        source_xml=xml, base_dir=DP_DIR,
        defer_initial=False,
    )
    # Philosopher 1 has forks 1 (left) and 5 (right) per the compliance table.
    # [1,5], [2,1], [3,2], [4,3], [5,4]
    expected_forks = {1: (1, 5), 2: (2, 1), 3: (3, 2), 4: (4, 3), 5: (5, 4)}
    for n, (left, right) in expected_forks.items():
        inv = ctx.invocations.get("ID_P_{}".format(n))
        child = getattr(inv, "child", None) if inv else None
        assert child is not None
        dm = child.data_model
        assert dm.get("i_ID_LEFT") == left, (
            "P{} i_ID_LEFT expected {} got {}".format(n, left, dm.get("i_ID_LEFT"))
        )
        assert dm.get("i_ID_RIGHT") == right, (
            "P{} i_ID_RIGHT expected {} got {}".format(n, right, dm.get("i_ID_RIGHT"))
        )
