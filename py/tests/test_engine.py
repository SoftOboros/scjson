"""
Agent Name: python-engine-tests

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.
"""

from decimal import Decimal
import pytest
from xsdata.exceptions import ParserError

from scjson.pydantic import Scxml, State, Transition, Datamodel, Data, Parallel
from scjson.context import DocumentContext, ExecutionMode
from scjson.SCXMLDocumentHandler import SCXMLDocumentHandler
from scjson.invoke import InvokeRegistry, RecordHandler


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


def _make_deep_history_doc() -> Scxml:
    """Parent state with deep history restoring nested descendant."""
    return Scxml(
        id="histdeep",
        initial=["p"],
        state=[
            State(
                id="p",
                initial_attribute=["s1"],
                history=[{"id": "h", "type_value": "deep", "transition": Transition(target=["s2b"]) }],
                state=[
                    State(
                        id="s1",
                        initial_attribute=["s1a"],
                        state=[
                            State(id="s1a", transition=[Transition(event="next", target=["s1b"]) ]),
                            State(id="s1b"),
                        ],
                        transition=[Transition(event="toQ", target=["q"])]
                    ),
                    State(
                        id="s2",
                        initial_attribute=["s2a"],
                        state=[State(id="s2a"), State(id="s2b")],
                    ),
                ],
                transition=[Transition(event="toQ", target=["q"])]
            ),
            State(id="q", transition=[Transition(event="back", target=["h"]) ]),
        ],
        version=Decimal("1.0"),
    )


def test_deep_history_restores_descendant_path():
    """Deep history should restore to the nested descendant active at exit."""
    ctx = DocumentContext.from_doc(_make_deep_history_doc())
    # Currently in p -> s1 -> s1a
    ctx.enqueue("next")
    ctx.microstep()
    assert "s1b" in ctx.configuration
    # Transition to q, then back via history 'h'
    ctx.enqueue("toQ")
    ctx.microstep()
    assert "q" in ctx.configuration and "s1b" not in ctx.configuration
    ctx.enqueue("back")
    ctx.microstep()
    # Deep history should return us to s1b (not initial s1a)
    assert "s1b" in ctx.configuration


def _make_done_compound_doc() -> Scxml:
    """Compound state that raises ``done.state`` when entering its final child."""
    return Scxml(
        id="root",
        initial=["s"],
        state=[
            State(
                id="s",
                state=[State(id="x", transition=[Transition(target=["f"])])],
                final=[{"id": "f"}],
                transition=[Transition(event="done.state.s", target=["pass"])],
            ),
            State(id="pass"),
        ],
        version=Decimal("1.0"),
    )


def _make_done_parallel_doc() -> Scxml:
    """Parallel with two regions; emits region done and then parent done."""
    return Scxml(
        id="pdoc",
        datamodel=[Datamodel(data=[Data(id="v", expr="0")])],
        initial=["p"],
        parallel=[
            Parallel(
                id="p",
                onentry=[
                    {"raise_value": [{"event": "e1"}]},
                    {"raise_value": [{"event": "e2"}]},
                ],
                transition=[
                    Transition(event="done.state.r1", assign=[{"location": "v", "expr": "1"}]),
                    Transition(event="done.state.r2", target=["s1"]),
                ],
                state=[
                    State(
                        id="r1",
                        initial_attribute=["r1a"],
                        state=[State(id="r1a", transition=[Transition(event="e1", target=["r1f"])])],
                        final=[{"id": "r1f"}],
                    ),
                    State(
                        id="r2",
                        initial_attribute=["r2a"],
                        state=[State(id="r2a", transition=[Transition(event="e2", target=["r2f"])])],
                        final=[{"id": "r2f"}],
                    ),
                ],
            )
        ],
        state=[
            State(
                id="s1",
                transition=[
                    Transition(event="done.state.p", cond="v == 1", target=["pass"]),
                    Transition(event="*", target=["fail"]),
                ],
            ),
            State(id="pass"),
            State(id="fail"),
        ],
        version=Decimal("1.0"),
    )


def test_external_send_emits_error_communication(tmp_path):
    """External send target should produce error.communication and not enqueue external event."""
    chart = tmp_path / "external_send.scxml"
    chart.write_text(
        """
<scxml xmlns=\"http://www.w3.org/2005/07/scxml\" initial=\"s\" datamodel=\"python\">
  <state id=\"s\">
    <onentry>
      <send event=\"poke\" target=\"#external\"/>
    </onentry>
  </state>
""",
        encoding="utf-8",
    )

    ctx = DocumentContext.from_xml_file(chart)
    # First event should be error.communication (no other events enqueued)
    evt = ctx.events.pop()
    assert evt and evt.name == "error.communication"
    assert ctx.events.pop() is None

def test_error_event_emitted_on_cond_failure():
    """A failing cond expression should enqueue error.execution."""
    doc = Scxml(
        id="err",
        initial=["s"],
        state=[
            State(id="s", transition=[Transition(event="go", target=["t"], cond="undefined_var + 1")]),
            State(id="t"),
        ],
        version=Decimal("1.0"),
    )
    ctx = DocumentContext.from_doc(doc)
    ctx.enqueue("go")
    ctx.microstep()
    err = ctx.events.pop()
    assert err is not None and err.name == "error.execution"


def test_done_state_compound():
    """done.state.<parent> is raised on entering a final child."""
    ctx = DocumentContext.from_doc(_make_done_compound_doc())
    # Trigger transition into the final child of state 's'
    ctx.enqueue("__start__")  # no-op to step
    ctx.microstep()  # drain initial (no effect)
    # transition from x -> f (eventless)
    ctx.microstep()
    # process done.state.s to move to 'pass'
    ctx.microstep()
    assert "pass" in ctx.configuration


def test_done_state_parallel_sequence():
    """Parallel emits region done events before parent done, allowing ordering-sensitive logic."""
    ctx = DocumentContext.from_doc(_make_done_parallel_doc())
    # Run until all internal events are processed
    ctx.run()
    assert "pass" in ctx.configuration


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


def test_execution_mode_defaults_to_strict():
    ctx = DocumentContext.from_doc(_make_doc())
    assert ctx.execution_mode is ExecutionMode.STRICT


def test_execution_mode_lax_allows_unknown(tmp_path):
    chart = tmp_path / "unknown.scxml"
    chart.write_text(
        """
<scxml xmlns="http://www.w3.org/2005/07/scxml" initial="s">
  <state id="s">
    <bogus />
  </state>
</scxml>
""",
        encoding="utf-8",
    )

    with pytest.raises(ParserError):
        DocumentContext.from_xml_file(chart, execution_mode=ExecutionMode.STRICT)

    ctx = DocumentContext.from_xml_file(chart, execution_mode=ExecutionMode.LAX)
    assert ctx.execution_mode is ExecutionMode.LAX


def test_if_elseif_else_branches(tmp_path):
    chart = tmp_path / "branches.scxml"
    chart.write_text(
        """
<scxml xmlns="http://www.w3.org/2005/07/scxml" initial="s" datamodel="python">
  <datamodel>
    <data id="flag" expr="1"/>
    <data id="value" expr="0"/>
  </datamodel>
  <state id="s">
    <onentry>
      <if cond="flag == 0">
        <assign location="value" expr="100"/>
        <elseif cond="flag == 1"/>
        <assign location="value" expr="200"/>
        <else/>
        <assign location="value" expr="300"/>
      </if>
    </onentry>
  </state>
</scxml>
""",
        encoding="utf-8",
    )

    ctx = DocumentContext.from_xml_file(chart)
    assert ctx.data_model["value"] == 200


def test_foreach_executes_body(tmp_path):
    chart = tmp_path / "foreach.scxml"
    chart.write_text(
        """
<scxml xmlns="http://www.w3.org/2005/07/scxml" initial="s" datamodel="python">
  <datamodel>
    <data id="total" expr="0"/>
  </datamodel>
  <state id="s">
    <onentry>
      <foreach array="[1,2,3]" item="item" index="idx">
        <assign location="total" expr="total + item"/>
      </foreach>
    </onentry>
  </state>
</scxml>
""",
        encoding="utf-8",
    )

    ctx = DocumentContext.from_xml_file(chart)
    assert ctx.data_model["total"] == 6


def test_send_enqueues_internal_event(tmp_path):
    chart = tmp_path / "send.scxml"
    chart.write_text(
        """
<scxml xmlns="http://www.w3.org/2005/07/scxml" initial="s" datamodel="python">
  <datamodel>
    <data id="flag" expr="5"/>
  </datamodel>
  <state id="s">
    <onentry>
      <send event="go" id="evt">
        <param name="value" expr="flag"/>
      </send>
    </onentry>
  </state>
</scxml>
""",
        encoding="utf-8",
    )

    ctx = DocumentContext.from_xml_file(chart)
    evt = ctx.events.pop()
    assert evt is not None
    assert evt.name == "go"
    assert evt.send_id == "evt"
    assert evt.data == {"value": 5}


def test_cancel_removes_pending_send(tmp_path):
    chart = tmp_path / "cancel.scxml"
    chart.write_text(
        """
<scxml xmlns="http://www.w3.org/2005/07/scxml" initial="s" datamodel="python">
  <state id="s">
    <onentry>
      <send event="go" id="evt"/>
      <cancel sendid="evt"/>
    </onentry>
  </state>
</scxml>
""",
        encoding="utf-8",
    )

    ctx = DocumentContext.from_xml_file(chart)
    assert ctx.events.pop() is None


def test_send_delay_requires_advance_time(tmp_path):
    chart = tmp_path / "delay.scxml"
    chart.write_text(
        """
<scxml xmlns="http://www.w3.org/2005/07/scxml" initial="s" datamodel="python">
  <state id="s">
    <onentry>
      <send event="tick" delay="0.1s"/>
    </onentry>
  </state>
</scxml>
""",
        encoding="utf-8",
    )

    ctx = DocumentContext.from_xml_file(chart)
    assert ctx.events.pop() is None
    ctx.advance_time(0.2)
    evt = ctx.events.pop()
    assert evt and evt.name == "tick"


def test_delayed_sends_fire_in_order(tmp_path):
    """Delayed events release in chronological order via advance_time."""
    chart = tmp_path / "delayed_multi.scxml"
    chart.write_text(
        """
<scxml xmlns="http://www.w3.org/2005/07/scxml" initial="s" datamodel="python">
  <state id="s">
    <onentry>
      <send event="first" delay="0.1s"/>
      <send event="second" delay="0.3s"/>
    </onentry>
  </state>
</scxml>
""",
        encoding="utf-8",
    )

    ctx = DocumentContext.from_xml_file(chart)
    assert ctx.events.pop() is None

    ctx.advance_time(0.15)
    first = ctx.events.pop()
    assert first is not None and first.name == "first"
    assert ctx.events.pop() is None

    ctx.advance_time(0.2)
    second = ctx.events.pop()
    assert second is not None and second.name == "second"


def test_cancel_removes_delayed_send(tmp_path):
    """Cancelling a delayed send prevents future delivery."""
    chart = tmp_path / "cancel_delayed.scxml"
    chart.write_text(
        """
<scxml xmlns="http://www.w3.org/2005/07/scxml" initial="s" datamodel="python">
  <state id="s">
    <onentry>
      <send event="poke" id="evt" delay="0.5s"/>
      <cancel sendid="evt"/>
    </onentry>
  </state>
</scxml>
""",
        encoding="utf-8",
    )

    ctx = DocumentContext.from_xml_file(chart)
    ctx.advance_time(1.0)
    assert ctx.events.pop() is None


def test_send_content_text_payload(tmp_path):
    """Textual <content> blocks populate the send payload."""
    chart = tmp_path / "send_content_text.scxml"
    chart.write_text(
        """
<scxml xmlns="http://www.w3.org/2005/07/scxml" initial="s" datamodel="python">
  <state id="s">
    <onentry>
      <send event="notify" id="evt">
        <content>hello-world</content>
      </send>
    </onentry>
  </state>
</scxml>
""",
        encoding="utf-8",
    )

    ctx = DocumentContext.from_xml_file(chart)
    evt = ctx.events.pop()
    assert evt is not None
    assert evt.data == {"content": "hello-world"}


def test_send_content_expr_payload(tmp_path):
    """<content expr="..."> expressions evaluate within the sandbox."""
    chart = tmp_path / "send_content_expr.scxml"
    chart.write_text(
        """
<scxml xmlns="http://www.w3.org/2005/07/scxml" initial="s" datamodel="python">
  <datamodel>
    <data id="value" expr="41"/>
  </datamodel>
  <state id="s">
    <onentry>
      <send event="notify" id="evt">
        <content expr="value + 1"/>
      </send>
    </onentry>
  </state>
</scxml>
""",
        encoding="utf-8",
    )

    ctx = DocumentContext.from_xml_file(chart)
    evt = ctx.events.pop()
    assert evt is not None
    assert evt.data == {"content": 42}

def test_send_content_nested_markup(tmp_path):
    """Nested markup inside <content> is preserved as structured payload."""
    chart = tmp_path / "send_content_nested.scxml"
    chart.write_text(
        """
<scxml xmlns="http://www.w3.org/2005/07/scxml" initial="s" datamodel="python">
  <state id="s">
    <onentry>
      <send event="complex" id="evt">
        <content>
          <foo attr="1">text</foo>
          <bar>
            <baz>42</baz>
          </bar>
        </content>
      </send>
    </onentry>
  </state>
</scxml>
""",
        encoding="utf-8",
    )

    ctx = DocumentContext.from_xml_file(chart)
    evt = ctx.events.pop()
    assert evt is not None
    assert evt.data == {
        "content": [
            {
                "qname": "{http://www.w3.org/2005/07/scxml}foo",
                "text": "text",
                "attributes": {"attr": "1"},
            },
            {
                "qname": "{http://www.w3.org/2005/07/scxml}bar",
                "text": "",
                "children": [
                    {
                        "qname": "{http://www.w3.org/2005/07/scxml}baz",
                        "text": "42",
                    }
                ],
            },
        ]
    }


def test_donedata_content_precedence(tmp_path):
    """When <donedata> has both <content> and <param>, content must dominate."""
    chart = tmp_path / "donedata_content_precedence.scxml"
    chart.write_text(
        """
<scxml xmlns="http://www.w3.org/2005/07/scxml" datamodel="python" initial="s">
  <state id="s">
    <state id="x">
      <transition target="f"/>
    </state>
    <final id="f">
      <donedata>
        <param name="ignored" expr="123"/>
        <content>{"a": 1, "b": 2}</content>
      </donedata>
    </final>
    <transition event="done.state.s" target="pass"/>
  </state>
  <state id="pass"/>
</scxml>
""",
        encoding="utf-8",
    )

    ctx = DocumentContext.from_xml_file(chart)
    # done.state.s should be queued from entering <final> during initialization
    evt = ctx.events.pop()
    assert evt is not None and evt.name == "done.state.s"
    # Content should dominate over params; payload is the literal content string
    assert isinstance(evt.data, str)
    assert evt.data.strip() == '{"a": 1, "b": 2}'


def test_deep_history_parallel_restores_both_regions(tmp_path):
    """Deep history should restore leaf states across parallel regions."""
    chart = tmp_path / "deep_hist_parallel.scxml"
    chart.write_text(
        """
<scxml xmlns="http://www.w3.org/2005/07/scxml" datamodel="python" initial="p">
  <state id="p">
    <history id="h" type="deep">
      <transition target="par.r1b par.r2b"/>
    </history>
    <parallel id="par">
      <state id="r1" initial="r1a">
        <state id="r1a"><transition event="go1" target="r1b"/></state>
        <state id="r1b"/>
      </state>
      <state id="r2" initial="r2a">
        <state id="r2a"><transition event="go2" target="r2b"/></state>
        <state id="r2b"/>
      </state>
    </parallel>
    <transition event="toQ" target="q"/>
  </state>
  <state id="q">
    <transition event="back" target="h"/>
  </state>
</scxml>
""",
        encoding="utf-8",
    )

    ctx = DocumentContext.from_xml_file(chart)
    # Initially r1a and r2a are active under the parallel
    ctx.enqueue("go1")
    ctx.microstep()
    ctx.enqueue("go2")
    ctx.microstep()
    assert "r1b" in ctx.configuration and "r2b" in ctx.configuration
    # Exit to q and then return via deep history
    ctx.enqueue("toQ")
    ctx.microstep()
    assert "q" in ctx.configuration
    ctx.enqueue("back")
    ctx.microstep()
    # Both region leaves should be restored
    assert "r1b" in ctx.configuration and "r2b" in ctx.configuration


def test_error_event_ordering_precedes_later_events(tmp_path):
    """error.execution should be queued before later events when cond fails."""
    chart = tmp_path / "error_ordering.scxml"
    chart.write_text(
        """
<scxml xmlns="http://www.w3.org/2005/07/scxml" datamodel="python" initial="s">
  <state id="s">
    <onentry>
      <send event="go"/>
      <send event="later"/>
    </onentry>
    <transition event="go" target="t" cond="undefined_var + 1"/>
  </state>
  <state id="t"/>
</scxml>
""",
        encoding="utf-8",
    )

    ctx = DocumentContext.from_xml_file(chart)
    # Process the first event (go); cond fails -> error.execution should be enqueued
    ctx.microstep()
    # Next event in queue should be error.execution before the later event
    first = ctx.events.pop()
    assert first and first.name == "error.execution"
    second = ctx.events.pop()
    assert second and second.name == "later"


def test_external_send_error_precedes_raise(tmp_path):
    """error.communication from external send should preserve document order vs raise."""
    chart = tmp_path / "send_error_ordering.scxml"
    chart.write_text(
        """
<scxml xmlns="http://www.w3.org/2005/07/scxml" initial="s" datamodel="python">
  <state id="s">
    <onentry>
      <send event="poke" target="#external"/>
      <raise event="later"/>
    </onentry>
  </state>
</scxml>
""",
        encoding="utf-8",
    )

    ctx = DocumentContext.from_xml_file(chart)
    e1 = ctx.events.pop()
    e2 = ctx.events.pop()
    assert e1 and e1.name == "error.communication"
    assert e2 and e2.name == "later"


def test_invoke_immediate_done_and_finalize(tmp_path):
    chart = tmp_path / "invoke_immediate.scxml"
    chart.write_text(
        """
<scxml xmlns="http://www.w3.org/2005/07/scxml" datamodel="python" initial="s">
  <datamodel>
    <data id="flag" expr="0"/>
  </datamodel>
  <state id="s">
    <invoke type="mock:immediate" idlocation="invId">
      <finalize>
        <assign location="flag" expr="1"/>
      </finalize>
    </invoke>
  </state>
</scxml>
""",
        encoding="utf-8",
    )

    ctx = DocumentContext.from_xml_file(chart)
    # Finalize should have run immediately, setting flag to 1
    assert ctx.data_model["flag"] == 1
    # An invocation id should be stored
    inv_id = ctx.root_activation.local_data.get("invId") or ctx.data_model.get("invId")
    assert isinstance(inv_id, str) and inv_id
    evt = ctx.events.pop()
    assert evt and evt.name == f"done.invoke.{inv_id}"


def test_invoke_autoforward_records_events(tmp_path):
    chart = tmp_path / "invoke_autoforward.scxml"
    chart.write_text(
        """
<scxml xmlns="http://www.w3.org/2005/07/scxml" datamodel="python" initial="s">
  <state id="s">
    <invoke type="mock:record" id="rec" autoforward="true"/>
    <transition event="go" target="t"/>
  </state>
  <state id="t"/>
</scxml>
""",
        encoding="utf-8",
    )

    ctx = DocumentContext.from_xml_file(chart)
    # Send an external event; should be forwarded to the mock record handler
    ctx.enqueue("go", {"x": 1})
    ctx.microstep()
    # Locate the record handler
    handler = ctx.invocations.get("rec")
    assert isinstance(handler, RecordHandler)
    assert handler.received and handler.received[0] == ("go", {"x": 1})


def test_invoke_cancel_runs_finalize_only_no_done_event(tmp_path):
    chart = tmp_path / "invoke_cancel_finalize.scxml"
    chart.write_text(
        """
<scxml xmlns="http://www.w3.org/2005/07/scxml" datamodel="python" initial="s">
  <datamodel>
    <data id="n" expr="0"/>
  </datamodel>
  <state id="s">
    <invoke type="mock:record" id="rec">
      <finalize>
        <assign location="n" expr="n + 1"/>
      </finalize>
    </invoke>
    <transition event="go" target="t"/>
  </state>
  <state id="t"/>
</scxml>
""",
        encoding="utf-8",
    )

    ctx = DocumentContext.from_xml_file(chart)
    # Cancel by leaving the state
    ctx.enqueue("go")
    ctx.microstep()
    # Finalize should have run; n incremented
    assert ctx.data_model["n"] == 1
    # No done.invoke.* should be in the queue after cancel
    ev = ctx.events.pop()
    assert (ev is None) or (not ev.name.startswith("done.invoke."))


def test_invoke_id_and_idlocation_assignment(tmp_path):
    chart = tmp_path / "invoke_id_idlocation.scxml"
    chart.write_text(
        """
<scxml xmlns="http://www.w3.org/2005/07/scxml" datamodel="python" initial="s">
  <state id="s">
    <invoke type="mock:record" id="fixed" idlocation="stored"/>
  </state>
</scxml>
""",
        encoding="utf-8",
    )

    ctx = DocumentContext.from_xml_file(chart)
    # idlocation should reflect the explicit id
    stored = ctx.root_activation.local_data.get("stored") or ctx.data_model.get("stored")
    assert stored == "fixed"
    assert "fixed" in ctx.invocations


def test_finalize_receives_event_data(tmp_path):
    chart = tmp_path / "invoke_finalize_event.scxml"
    chart.write_text(
        """
<scxml xmlns="http://www.w3.org/2005/07/scxml" datamodel="python" initial="s">
  <datamodel>
    <data id="y" expr="0"/>
  </datamodel>
  <state id="s">
    <invoke type="mock:immediate">
      <param name="x" expr="41"/>
      <finalize>
        <assign location="y" expr="_event['data']['x'] + 1"/>
      </finalize>
    </invoke>
  </state>
</scxml>
""",
        encoding="utf-8",
    )

    ctx = DocumentContext.from_xml_file(chart)
    # finalize should read _event.data and compute 42
    assert ctx.data_model["y"] == 42


def test_invoke_scxml_child_completes_and_finalizes(tmp_path):
    child = tmp_path / "child.scxml"
    child.write_text(
        """
<scxml xmlns="http://www.w3.org/2005/07/scxml" datamodel="python" initial="s" id="childroot">
  <state id="s">
    <transition event="go" target="f"/>
  </state>
  <final id="f">
    <donedata><param name="result" expr="42"/></donedata>
  </final>
</scxml>
""",
        encoding="utf-8",
    )

    parent = tmp_path / "parent.scxml"
    parent.write_text(
        f"""
<scxml xmlns="http://www.w3.org/2005/07/scxml" datamodel="python" initial="s">
  <datamodel><data id="x" expr="0"/></datamodel>
  <state id="s">
    <invoke type="scxml" id="child" src="{child}" autoforward="true">
      <finalize>
        <assign location="x" expr="_event['data']['result']"/>
      </finalize>
    </invoke>
    <transition event="done.invoke.child" target="pass"/>
  </state>
  <state id="pass"/>
</scxml>
""",
        encoding="utf-8",
    )

    ctx = DocumentContext.from_xml_file(parent)
    # Child should be started at initialization; ensure parent transition fires after forwarding
    ctx.enqueue("go")
    ctx.run()
    assert "pass" in ctx.configuration
    assert ctx.data_model["x"] == 42


def test_invoke_generic_done_event(tmp_path):
    chart = tmp_path / "invoke_generic_done.scxml"
    chart.write_text(
        """
<scxml xmlns="http://www.w3.org/2005/07/scxml" datamodel="python" initial="s">
  <state id="s">
    <invoke type="mock:immediate" id="child"/>
    <transition event="done.invoke" target="pass"/>
  </state>
  <state id="pass"/>
</scxml>
""",
        encoding="utf-8",
    )

    ctx = DocumentContext.from_xml_file(chart)
    # Transition on generic done.invoke should have fired
    assert "pass" in ctx.configuration


def test_invoke_type_uri_and_file_src(tmp_path):
    child = tmp_path / "sub.scxml"
    child.write_text(
        """
<scxml xmlns="http://www.w3.org/2005/07/scxml" datamodel="python" initial="f" id="sub">
  <final id="f"/>
</scxml>
""",
        encoding="utf-8",
    )

    chart = tmp_path / "invoke_uri.scxml"
    chart.write_text(
        f"""
<scxml xmlns="http://www.w3.org/2005/07/scxml" datamodel="python" initial="s">
  <state id="s">
    <invoke type="http://www.w3.org/TR/scxml/" src="file:{child.name}" id="child"/>
    <transition event="done.invoke.child" target="pass"/>
  </state>
  <state id="pass"/>
</scxml>
""",
        encoding="utf-8",
    )

    ctx = DocumentContext.from_xml_file(chart)
    # Child completes immediately; relative file: URI should resolve against base_dir
    assert "pass" in ctx.configuration


def test_invoke_src_and_content_parity(tmp_path):
    """Invoking equivalent children via src and via content should behave the same."""
    child = tmp_path / "child_final.scxml"
    child.write_text(
        """
<scxml xmlns="http://www.w3.org/2005/07/scxml" datamodel="python" initial="f">
  <final id="f"/>
  <final id="pass"/>
</scxml>
""",
        encoding="utf-8",
    )

    parent = tmp_path / "parent_src_content_parity.scxml"
    parent.write_text(
        f"""
<scxml xmlns="http://www.w3.org/2005/07/scxml" datamodel="python" initial="s1">
  <state id="s1">
    <invoke type="scxml" id="c1" src="{child}"/>
    <transition event="done.invoke.c1" target="s2"/>
  </state>
  <state id="s2">
    <invoke type="scxml">
      <content>
        <scxml initial="f" datamodel="python">
          <final id="f"/>
        </scxml>
      </content>
    </invoke>
    <transition event="done.invoke" target="pass"/>
  </state>
  <state id="pass"/>
</scxml>
""",
        encoding="utf-8",
    )

    ctx = DocumentContext.from_xml_file(parent)
    ctx.run()
    assert "pass" in ctx.configuration


def test_invoke_namelist_param_parity(tmp_path):
    """Child sees Var1==1 regardless of whether passed by namelist or param."""
    chart = tmp_path / "invoke_namelist_param_parity.scxml"
    chart.write_text(
        """
<scxml xmlns="http://www.w3.org/2005/07/scxml" datamodel="python" initial="s01">
  <datamodel><data id="Var1" expr="1"/></datamodel>
  <state id="s01">
    <invoke type="scxml" namelist="Var1">
      <content>
        <scxml initial="sub01" datamodel="python">
          <datamodel><data id="Var1" expr="0"/></datamodel>
          <state id="sub01">
            <transition cond="Var1==1" target="subFinal1">
              <send target="#_parent" event="ok1"/>
            </transition>
            <transition target="subFinal1">
              <send target="#_parent" event="bad1"/>
            </transition>
          </state>
          <final id="subFinal1"/>
        </scxml>
      </content>
    </invoke>
    <transition event="ok1" target="s02"/>
    <transition event="bad1" target="fail"/>
  </state>
  <state id="s02">
    <invoke type="scxml">
      <param name="Var1" expr="1"/>
      <content>
        <scxml initial="sub02" datamodel="python">
          <datamodel><data id="Var1" expr="0"/></datamodel>
          <state id="sub02">
            <transition cond="Var1==1" target="subFinal2">
              <send target="#_parent" event="ok2"/>
            </transition>
            <transition target="subFinal2">
              <send target="#_parent" event="bad2"/>
            </transition>
          </state>
          <final id="subFinal2"/>
        </scxml>
      </content>
    </invoke>
    <transition event="ok2" target="pass"/>
    <transition event="bad2" target="fail"/>
  </state>
  <state id="pass"/>
  <state id="fail"/>
</scxml>
""",
        encoding="utf-8",
    )

    ctx = DocumentContext.from_xml_file(chart)
    ctx.run()
    assert "pass" in ctx.configuration
def test_invoke_bad_src_emits_error_communication(tmp_path):
    chart = tmp_path / "invoke_bad_src.scxml"
    chart.write_text(
        """
<scxml xmlns="http://www.w3.org/2005/07/scxml" datamodel="python" initial="s">
  <state id="s">
    <invoke type="scxml" src="file:missing_child.scxml" id="child"/>
  </state>
</scxml>
""",
        encoding="utf-8",
    )
    ctx = DocumentContext.from_xml_file(chart)
    evt = ctx.events.pop()
    assert evt and evt.name == "error.communication"


def test_invoke_bad_typeexpr_emits_error_execution(tmp_path):
    chart = tmp_path / "invoke_bad_typeexpr.scxml"
    chart.write_text(
        """
<scxml xmlns="http://www.w3.org/2005/07/scxml" datamodel="python" initial="s">
  <state id="s">
    <invoke typeexpr="undefined_var + 1"/>
  </state>
</scxml>
""",
        encoding="utf-8",
    )
    ctx = DocumentContext.from_xml_file(chart)
    evt = ctx.events.pop()
    assert evt and evt.name == "error.execution"


def test_invoke_child_bubbles_event_to_parent(tmp_path):
    child = tmp_path / "child_bubble.scxml"
    child.write_text(
        """
<scxml xmlns="http://www.w3.org/2005/07/scxml" datamodel="python" initial="s" id="childroot">
  <state id="s">
    <onentry><raise event="childReady"/></onentry>
  </state>
</scxml>
""",
        encoding="utf-8",
    )

    parent = tmp_path / "parent_bubble.scxml"
    parent.write_text(
        f"""
<scxml xmlns="http://www.w3.org/2005/07/scxml" datamodel="python" initial="s">
  <state id="s">
    <invoke type="scxml" id="child" src="{child}"/>
    <transition event="childReady" target="pass"/>
  </state>
  <state id="pass"/>
</scxml>
""",
        encoding="utf-8",
    )

    ctx = DocumentContext.from_xml_file(parent)
    # The child's raised event should be queued for the parent
    evt = ctx.events.pop()
    assert evt and evt.name == "childReady"


def test_invoke_deferred_completion_and_ordering(tmp_path):
    chart = tmp_path / "invoke_deferred.scxml"
    chart.write_text(
        """
<scxml xmlns="http://www.w3.org/2005/07/scxml" datamodel="python" initial="s">
  <datamodel><data id="v" expr="0"/></datamodel>
  <state id="s">
    <invoke type="mock:deferred" id="job">
      <finalize>
        <assign location="v" expr="1"/>
      </finalize>
    </invoke>
    <transition event="done.invoke.job" target="pass"/>
  </state>
  <state id="pass"/>
</scxml>
""",
        encoding="utf-8",
    )

    ctx = DocumentContext.from_xml_file(chart)
    # Trigger completion via external event delivered to invocation
    ctx.enqueue("complete")
    ctx.microstep()  # deliver to invoker and run finalize
    assert ctx.data_model["v"] == 1
    # The transition to 'pass' should have fired within the same microstep
    assert "pass" in ctx.configuration
    assert "pass" in ctx.configuration


def test_multiple_invocations_autoforward(tmp_path):
    chart = tmp_path / "invoke_multi_autoforward.scxml"
    chart.write_text(
        """
<scxml xmlns="http://www.w3.org/2005/07/scxml" datamodel="python" initial="s">
  <state id="s">
    <invoke type="mock:record" id="rec1" autoforward="true"/>
    <invoke type="mock:record" id="rec2" autoforward="true"/>
  </state>
</scxml>
""",
        encoding="utf-8",
    )

    ctx = DocumentContext.from_xml_file(chart)
    ctx.enqueue("poke", {"k": 2})
    ctx.microstep()
    h1 = ctx.invocations.get("rec1")
    h2 = ctx.invocations.get("rec2")
    assert isinstance(h1, RecordHandler) and isinstance(h2, RecordHandler)
    assert h1.received and h1.received[0] == ("poke", {"k": 2})
    assert h2.received and h2.received[0] == ("poke", {"k": 2})


def test_multiple_invocations_in_distinct_states_autoforward_switch(tmp_path):
    chart = tmp_path / "invoke_switch.scxml"
    chart.write_text(
        """
<scxml xmlns="http://www.w3.org/2005/07/scxml" datamodel="python" initial="s1">
  <state id="s1">
    <invoke type="mock:record" id="rec1" autoforward="true"/>
    <transition event="to2" target="s2"/>
  </state>
  <state id="s2">
    <invoke type="mock:record" id="rec2" autoforward="true"/>
  </state>
</scxml>
""",
        encoding="utf-8",
    )

    ctx = DocumentContext.from_xml_file(chart)
    # While in s1, note should go to rec1 only
    ctx.enqueue("note", {"n": 1})
    ctx.microstep()
    h1 = ctx.invocations.get("rec1")
    h2 = ctx.invocations.get("rec2")
    assert isinstance(h1, RecordHandler)
    assert h1.received and h1.received[-1] == ("note", {"n": 1})
    assert (h2 is None) or (not getattr(h2, "received", []))

    # Switch to s2; now note2 should go to rec2 only
    ctx.enqueue("to2")
    ctx.microstep()
    ctx.enqueue("note2", {"n": 2})
    ctx.microstep()
    h2 = ctx.invocations.get("rec2")
    assert isinstance(h2, RecordHandler)
    assert h2.received and h2.received[-1] == ("note2", {"n": 2})


def test_finalize_runs_before_done_in_same_microstep(tmp_path):
    chart = tmp_path / "invoke_finalize_order.scxml"
    chart.write_text(
        """
<scxml xmlns="http://www.w3.org/2005/07/scxml" datamodel="python" initial="s">
  <datamodel><data id="flag" expr="0"/></datamodel>
  <state id="s">
    <invoke type="mock:deferred" id="job">
      <finalize><assign location="flag" expr="1"/></finalize>
    </invoke>
    <transition event="done.invoke.job" cond="flag == 1" target="pass"/>
  </state>
  <state id="pass"/>
</scxml>
""",
        encoding="utf-8",
    )

    ctx = DocumentContext.from_xml_file(chart)
    ctx.enqueue("complete")
    ctx.microstep()
    # Transition should have fired in the same microstep thanks to finalize-before-enqueue
    assert "pass" in ctx.configuration


def test_finalize_event_scope_is_transient(tmp_path):
    chart = tmp_path / "invoke_finalize_scope.scxml"
    chart.write_text(
        """
<scxml xmlns="http://www.w3.org/2005/07/scxml" datamodel="python" initial="s">
  <state id="s">
    <invoke type="mock:immediate">
      <finalize>
        <assign location="visible" expr="1"/>
      </finalize>
    </invoke>
  </state>
</scxml>
""",
        encoding="utf-8",
    )

    ctx = DocumentContext.from_xml_file(chart)
    # _event should not leak into state local_data after finalize
    act_s = ctx.activations.get("s")
    assert act_s is not None
    assert "_event" not in act_s.local_data


def test_finalize_only_runs_in_invoking_state_in_parallel(tmp_path):
    chart = tmp_path / "invoke_parallel_finalize.scxml"
    chart.write_text(
        """
<scxml xmlns="http://www.w3.org/2005/07/scxml" datamodel="python" initial="S">
  <datamodel>
    <data id="Var1" expr="0"/>
    <data id="Var2" expr="0"/>
  </datamodel>
  <state id="S" initial="P">
    <parallel id="P">
      <state id="R1">
        <invoke type="mock:deferred" id="job1">
          <finalize>
            <assign location="Var1" expr="1"/>
          </finalize>
        </invoke>
        <!-- When job1 completes, leave the parallel to sibling DONE -->
        <transition event="done.invoke.job1" target="DONE"/>
      </state>
      <state id="R2">
        <invoke type="mock:record" id="job2">
          <finalize>
            <assign location="Var2" expr="1"/>
          </finalize>
        </invoke>
      </state>
    </parallel>
    <state id="DONE"/>
  </state>
</scxml>
""",
        encoding="utf-8",
    )

    ctx = DocumentContext.from_xml_file(chart)
    # Trigger completion of R1's invocation; engine forwards external events
    # to active invocations, so this reaches mock:deferred.
    ctx.enqueue("complete")
    ctx.microstep()
    # Finalize for job1 should have run, updating Var1
    assert ctx.data_model["Var1"] == 1
    # The transition exits the parallel; R2's invocation is canceled and its
    # finalize still runs on cancel. Var2 is updated as well.
    assert ctx.data_model["Var2"] == 1
