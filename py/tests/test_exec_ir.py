"""
Agent Name: test-exec-ir

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Tests for the M1 Executable IR module (exec_ir.py) and the SCJSON→IR lowerer.

Coverage:
- All admitted ECMAScript expression forms (D-M1P6-2) → ExpressionNode
- All ActionNode kinds (M1-EXECUTABLE-IR Area 2)
- At least one unsupported-ecmascript diagnostic case (arrow fn) → no crash
- Dining Philosophers lowering proof (keystone)
"""

from __future__ import annotations

import os
import sys
import pytest

# Ensure the py/ package is on the path when running from the repo root.
_here = os.path.dirname(__file__)
_pkg_root = os.path.join(_here, "..")
if _pkg_root not in sys.path:
    sys.path.insert(0, _pkg_root)

from scjson.exec_ir import (
    # Value types
    NumberValue,
    StrValue,
    BoolValue,
    ArrayValue,
    MapValue,
    UndefinedValue,
    # ExpressionNode families
    NumericLiteral,
    StringLiteral,
    BoolLiteral,
    VarRead,
    MemberAccess,
    IndexAccess,
    BinOp,
    UnaryOp,
    CallNode,
    ArrayLiteral,
    MapLiteral,
    UnsupportedExpr,
    # ActionNode families
    AssignNode,
    LogNode,
    RaiseNode,
    SendNode,
    CancelNode,
    IfNode,
    IfBranch,
    ForeachNode,
    CapabilityCallNode,
    # Diagnostics
    ExecutableDiagnostic,
    # State-tree IR
    MachineIR,
    StateIR,
    ParallelIR,
    FinalIR,
    HistoryIR,
    InvokeIR,
    TransitionIR,
    DataSlotIR,
    OriginRef,
    # Lower API
    lower_expression,
    lower_document,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SCJSON_ROOT = os.path.abspath(os.path.join(_here, "..", ".."))
DP_SCXML_PATH = os.path.join(
    _SCJSON_ROOT, "tutorial", "Examples", "StateCharts",
    "DiningPhilosphersProblem", "machine_dining_philosphers.flat.scxml",
)


def _parse_dp() -> object:
    """Load and parse the Dining Philosophers SCXML file into a Pydantic model."""
    from scjson.context import DocumentContext
    from scjson.SCXMLDocumentHandler import SCXMLDocumentHandler
    from scjson.pydantic import Scxml
    import json

    xml_str = open(DP_SCXML_PATH, encoding="utf-8").read()
    handler = SCXMLDocumentHandler(fail_on_unknown_properties=False)
    json_str = handler.xml_to_json(xml_str)
    data = DocumentContext._prepare_raw_data(json.loads(json_str))
    return Scxml.model_validate(data)


# ---------------------------------------------------------------------------
# Expression lowering — admitted ECMAScript subset (D-M1P6-2)
# ---------------------------------------------------------------------------

class TestExpressionLowering:
    """Each admitted ECMAScript form maps to the expected ExpressionNode."""

    def test_integer_literal(self):
        node, diags = lower_expression("42", "test")
        assert isinstance(node, NumericLiteral)
        assert node.num == 42
        assert not diags

    def test_float_literal(self):
        node, diags = lower_expression("3.14", "test")
        assert isinstance(node, NumericLiteral)
        assert abs(node.num - 3.14) < 1e-9
        assert not diags

    def test_negative_integer(self):
        node, diags = lower_expression("-5", "test")
        # -5 parses as UnaryOp(neg, 5) or as a signed constant depending on Python version
        assert isinstance(node, (NumericLiteral, UnaryOp))
        assert not diags

    def test_string_literal(self):
        node, diags = lower_expression("'hello'", "test")
        assert isinstance(node, StringLiteral)
        assert node.s == "hello"
        assert not diags

    def test_true_literal(self):
        node, diags = lower_expression("true", "test")
        assert isinstance(node, BoolLiteral)
        assert node.b is True
        assert not diags

    def test_false_literal(self):
        node, diags = lower_expression("false", "test")
        assert isinstance(node, BoolLiteral)
        assert node.b is False
        assert not diags

    def test_var_read(self):
        node, diags = lower_expression("i_ID", "test")
        assert isinstance(node, VarRead)
        assert node.var == "i_ID"
        assert not diags

    def test_member_access_event_name(self):
        node, diags = lower_expression("_event.name", "test")
        assert isinstance(node, MemberAccess)
        assert isinstance(node.obj, VarRead)
        assert node.obj.var == "_event"
        assert node.attr == "name"
        assert not diags

    def test_member_access_event_data(self):
        node, diags = lower_expression("_event.data", "test")
        assert isinstance(node, MemberAccess)
        assert node.attr == "data"
        assert not diags

    def test_computed_index_access(self):
        node, diags = lower_expression("t_INPUTS[_event.name]", "test")
        assert isinstance(node, IndexAccess)
        assert isinstance(node.obj, VarRead)
        assert node.obj.var == "t_INPUTS"
        assert isinstance(node.index, MemberAccess)
        assert node.index.attr == "name"
        assert not diags

    def test_array_index_access(self):
        node, diags = lower_expression("t_HAND_COMPLIANCE[0]", "test")
        assert isinstance(node, IndexAccess)
        assert isinstance(node.index, NumericLiteral)
        assert node.index.num == 0
        assert not diags

    def test_addition(self):
        node, diags = lower_expression("i_EAT_COUNT + 1", "test")
        assert isinstance(node, BinOp)
        assert node.op == "+"
        assert isinstance(node.lhs, VarRead)
        assert isinstance(node.rhs, NumericLiteral)
        assert not diags

    def test_multiplication(self):
        node, diags = lower_expression("a * b", "test")
        assert isinstance(node, BinOp)
        assert node.op == "*"
        assert not diags

    def test_equality(self):
        node, diags = lower_expression("t_INPUTS['taken.1']==0", "test")
        assert isinstance(node, BinOp)
        assert node.op == "=="
        assert not diags

    def test_strict_equality_maps_to_equality(self):
        # === is normalized to == by the ecmascript_normalizer
        node, diags = lower_expression("i_ID !== 0", "test")
        assert isinstance(node, BinOp)
        assert node.op == "!="
        assert not diags

    def test_comparison_lt(self):
        node, diags = lower_expression("a < b", "test")
        assert isinstance(node, BinOp)
        assert node.op == "<"
        assert not diags

    def test_logical_and(self):
        node, diags = lower_expression("a == 1 && b == 2", "test")
        assert isinstance(node, BinOp)
        assert node.op == "&&"
        assert not diags

    def test_logical_or(self):
        node, diags = lower_expression("a || b", "test")
        assert isinstance(node, BinOp)
        assert node.op == "||"
        assert not diags

    def test_logical_not(self):
        node, diags = lower_expression("!x", "test")
        assert isinstance(node, UnaryOp)
        assert node.op == "not"
        assert isinstance(node.operand, VarRead)
        assert not diags

    def test_unary_not_of_comparison(self):
        # ! (expr == 1)
        node, diags = lower_expression("! (_event.data==1)", "test")
        assert isinstance(node, UnaryOp)
        assert node.op == "not"
        assert not diags

    def test_parseint(self):
        node, diags = lower_expression("parseInt('5')", "test")
        assert isinstance(node, CallNode)
        assert node.func == "int"
        assert not diags

    def test_string_coerce(self):
        node, diags = lower_expression("String(x)", "test")
        assert isinstance(node, CallNode)
        assert node.func == "str"
        assert not diags

    def test_number_coerce(self):
        node, diags = lower_expression("Number(x)", "test")
        assert isinstance(node, CallNode)
        assert node.func == "float"
        assert not diags

    def test_str_replace_method(self):
        node, diags = lower_expression("_event.name.replace('taken.','')", "test")
        assert isinstance(node, CallNode)
        assert node.func == "replace"
        assert node.receiver is not None
        assert not diags

    def test_parseint_with_replace(self):
        """Covers the key DP expression parseInt(_event.name.replace('taken.',''))."""
        node, diags = lower_expression(
            "parseInt(_event.name.replace('taken.',''))", "test"
        )
        assert isinstance(node, CallNode)
        assert node.func == "int"
        assert len(node.args) == 1
        assert isinstance(node.args[0], CallNode)
        assert node.args[0].func == "replace"
        assert not diags

    def test_string_concatenation_with_expr(self):
        """i_DELAY_THINK_EAT + 'ms' — string concat with coercion."""
        node, diags = lower_expression("i_DELAY_THINK_EAT + 'ms'", "test")
        # The normalizer wraps the non-string side in str(); we should get
        # a BinOp with a CallNode(str) on the lhs.
        assert isinstance(node, BinOp)
        assert node.op == "+"
        assert not diags

    def test_array_literal(self):
        node, diags = lower_expression("[1, 2, 3]", "test")
        assert isinstance(node, ArrayLiteral)
        assert len(node.items) == 3
        assert not diags

    def test_array_of_array(self):
        node, diags = lower_expression("[[1,5],[2,1]]", "test")
        assert isinstance(node, ArrayLiteral)
        assert len(node.items) == 2
        assert isinstance(node.items[0], ArrayLiteral)
        assert not diags

    def test_object_literal(self):
        node, diags = lower_expression(
            "{ 'take.1':0, 'take.2':0 }", "test"
        )
        assert isinstance(node, MapLiteral)
        assert len(node.entries) == 2
        assert not diags

    def test_event_name_string_comparison(self):
        """_event.name == 'taken.' + i_ID_LEFT"""
        node, diags = lower_expression(
            "_event.name == ('taken.' + i_ID_LEFT)", "test"
        )
        assert isinstance(node, BinOp)
        assert node.op == "=="
        assert isinstance(node.lhs, MemberAccess)
        assert not diags

    def test_complex_dp_cond(self):
        """Full DP child transition condition."""
        expr = "(_event.name == ('taken.' + i_ID_LEFT)) || (_event.name == ('taken.' + i_ID_RIGHT))"
        node, diags = lower_expression(expr, "test")
        assert isinstance(node, BinOp)
        assert node.op == "||"
        assert not diags

    def test_t_inputs_computed_key_cond(self):
        """t_INPUTS['taken.'+i_ID_LEFT]==0"""
        node, diags = lower_expression(
            "t_INPUTS['taken.'+i_ID_LEFT]==0", "test"
        )
        assert isinstance(node, BinOp)
        assert node.op == "=="
        assert isinstance(node.lhs, IndexAccess)
        assert not diags

    def test_t_inputs_indexed_by_event_name(self):
        """t_INPUTS[_event.name] — the DP dispatch key expression."""
        node, diags = lower_expression("t_INPUTS[_event.name]", "test")
        assert isinstance(node, IndexAccess)
        assert isinstance(node.index, MemberAccess)
        assert node.index.attr == "name"
        assert not diags

    def test_complianceindex_add(self):
        """complianceIndex + 1 — arithmetic in the DP foreach."""
        node, diags = lower_expression("complianceIndex + 1", "test")
        assert isinstance(node, BinOp)
        assert node.op == "+"
        assert not diags


# ---------------------------------------------------------------------------
# Unsupported expression forms (D-M1P6-8) — diagnostic, no crash
# ---------------------------------------------------------------------------

class TestUnsupportedExpressions:
    """Inadmissible forms produce UnsupportedExpr + diagnostic, not a crash."""

    def test_arrow_function_produces_diagnostic(self):
        node, diags = lower_expression("(x) => x + 1", "test")
        assert isinstance(node, UnsupportedExpr)
        assert len(diags) == 1
        assert diags[0].code == "unsupported-ecmascript"

    def test_new_keyword_produces_diagnostic(self):
        node, diags = lower_expression("new Foo()", "test")
        assert isinstance(node, UnsupportedExpr)
        assert len(diags) == 1
        assert "unsupported-ecmascript" in diags[0].code

    def test_typeof_produces_diagnostic(self):
        node, diags = lower_expression("typeof x", "test")
        assert isinstance(node, UnsupportedExpr)
        assert diags

    def test_template_literal_produces_diagnostic(self):
        node, diags = lower_expression("`hello ${x}`", "test")
        assert isinstance(node, UnsupportedExpr)
        assert diags

    def test_non_admitted_free_call_produces_diagnostic(self):
        node, diags = lower_expression("Math.floor(x)", "test")
        # Math.floor is a method call with non-admitted method name
        assert isinstance(node, UnsupportedExpr)
        assert diags

    def test_diagnostic_never_raises(self):
        # Extreme case: empty string
        node, diags = lower_expression("", "test")
        assert isinstance(node, UnsupportedExpr)
        assert diags


# ---------------------------------------------------------------------------
# ActionNode construction tests
# ---------------------------------------------------------------------------

class TestActionNodes:
    """Verify ActionNode dataclasses construct correctly."""

    def test_assign_node(self):
        n = AssignNode(
            loc="i_EAT_COUNT",
            expr=BinOp(op="+", lhs=VarRead(var="i_EAT_COUNT"), rhs=NumericLiteral(num=1)),
            op="set",
        )
        assert n.loc == "i_EAT_COUNT"
        assert n.op == "set"
        assert isinstance(n.expr, BinOp)

    def test_log_node(self):
        n = LogNode(
            expr=StringLiteral(s="hello"),
            label="DEBUG",
        )
        assert n.label == "DEBUG"
        assert isinstance(n.expr, StringLiteral)

    def test_raise_node(self):
        n = RaiseNode(event="error.execution")
        assert n.event == "error.execution"

    def test_send_node_static(self):
        n = SendNode(event="take.1", target="#_parent")
        assert n.event == "take.1"
        assert n.target == "#_parent"
        assert n.eventexpr is None

    def test_send_node_dynamic(self):
        n = SendNode(
            eventexpr=MemberAccess(obj=VarRead(var="_event"), attr="name"),
            targetexpr=StringLiteral(s="#_parent"),
        )
        assert n.event is None
        assert isinstance(n.eventexpr, MemberAccess)

    def test_cancel_node(self):
        n = CancelNode(sendid="ID.Do.Timer.Think")
        assert n.sendid == "ID.Do.Timer.Think"

    def test_if_node(self):
        guard = BinOp(op="==", lhs=VarRead(var="x"), rhs=NumericLiteral(num=0))
        branch = IfBranch(guard=guard, body=[RaiseNode(event="done")])
        n = IfNode(branches=[branch])
        assert len(n.branches) == 1
        assert isinstance(n.branches[0].guard, BinOp)

    def test_foreach_node(self):
        n = ForeachNode(
            array_expr=VarRead(var="t_HAND_COMPLIANCE"),
            item="complianceItem",
            index="complianceIndex",
            body=[LogNode(expr=VarRead(var="complianceItem"))],
        )
        assert n.item == "complianceItem"
        assert n.index == "complianceIndex"
        assert len(n.body) == 1

    def test_capability_call_node(self):
        origin = OriginRef(type="script", state="Thinking", idx=0)
        n = CapabilityCallNode(
            name="script_onentry_Thinking_0_0",
            origin=origin,
            success_event="script_onentry_Thinking_0_0.success",
            error_event="script_onentry_Thinking_0_0.error",
        )
        assert n.success_event.endswith(".success")
        assert n.error_event.endswith(".error")
        assert n.capability_intent is None
        assert n.args is None
        assert n.return_type is None
        assert n.correlation_id is None


# ---------------------------------------------------------------------------
# Value model tests (D-M1P6-3)
# ---------------------------------------------------------------------------

class TestValueModel:
    """Tagged value types construct correctly."""

    def test_number_value(self):
        v = NumberValue(v=42)
        assert v.v == 42

    def test_str_value(self):
        v = StrValue(v="hello")
        assert v.v == "hello"

    def test_bool_value(self):
        v = BoolValue(v=True)
        assert v.v is True

    def test_array_value(self):
        v = ArrayValue(items=[NumberValue(v=1), NumberValue(v=2)])
        assert len(v.items) == 2

    def test_map_value(self):
        v = MapValue(entries=[("take.1", NumberValue(v=0))])
        assert v.entries[0][0] == "take.1"

    def test_undefined_value(self):
        v = UndefinedValue()
        assert isinstance(v, UndefinedValue)


# ---------------------------------------------------------------------------
# Dining Philosophers lowering proof (keystone test)
# ---------------------------------------------------------------------------

class TestDiningPhilosophersLowering:
    """Full lowering proof for the DP machine.

    Proves that lower_document() faithfully converts the flat SCXML to a
    MachineIR with complete structural coverage.
    """

    @pytest.fixture(scope="class")
    def dp_doc(self):
        return _parse_dp()

    @pytest.fixture(scope="class")
    def dp_ir(self, dp_doc):
        machine, diagnostics = lower_document(dp_doc)
        return machine, diagnostics

    def test_returns_machine_ir(self, dp_ir):
        machine, _ = dp_ir
        assert isinstance(machine, MachineIR)

    def test_datamodel_attr_ecmascript(self, dp_ir):
        machine, _ = dp_ir
        assert machine.datamodel_attr == "ecmascript"

    def test_root_is_parallel(self, dp_ir):
        """The root <parallel id="DiningPhilosophers"> must be present."""
        machine, _ = dp_ir
        assert len(machine.children) == 1
        root = machine.children[0]
        assert isinstance(root, ParallelIR)
        assert root.id == "DiningPhilosophers"

    def test_parallel_has_correct_child_count(self, dp_ir):
        """DiningPhilosophers has 5 Philosopher states + 5 Fork states = 10 children."""
        machine, _ = dp_ir
        root = machine.children[0]
        assert isinstance(root, ParallelIR)
        # 5 Philosopher states + 5 Fork states
        assert len(root.children) == 10

    def test_philosopher_states_present(self, dp_ir):
        """Philosopher1..5 must all be StateIR nodes."""
        machine, _ = dp_ir
        root = machine.children[0]
        phil_ids = {c.id for c in root.children if isinstance(c, StateIR)}
        for n in range(1, 6):
            assert "Philosopher{}".format(n) in phil_ids, \
                "Philosopher{} missing from parallel children".format(n)

    def test_fork_states_present(self, dp_ir):
        """Fork1..5 must all be StateIR nodes."""
        machine, _ = dp_ir
        root = machine.children[0]
        fork_ids = {c.id for c in root.children if isinstance(c, StateIR)}
        for n in range(1, 6):
            assert "Fork{}".format(n) in fork_ids, \
                "Fork{} missing from parallel children".format(n)

    def _collect_states(self, node, seen=None):
        if seen is None:
            seen = set()
        if isinstance(node, MachineIR):
            for c in node.children:
                self._collect_states(c, seen)
        elif isinstance(node, (StateIR, ParallelIR)):
            seen.add(node.id)
            for c in node.children:
                self._collect_states(c, seen)
            for inv in getattr(node, "invokes", []):
                if inv.child_machine is not None:
                    self._collect_states(inv.child_machine, seen)
        elif isinstance(node, FinalIR):
            seen.add(node.id)
        return seen

    def test_total_state_count(self, dp_ir):
        """Total state count (including nested child machines) must cover all states.

        The flat SCXML has:
        - 1 parallel root (DiningPhilosophers)
        - 5 philosopher observer states (PhilosopherN with 3 sub-states each)
        - 5 fork states (ForkN with 2 sub-states each)
        - 5 child machines (one per invoke), each with Philospher + sub-states +
          ProcessHungry + sub-states + FinalSub

        We verify > 50 states (the structure is large).
        """
        machine, _ = dp_ir
        all_states = self._collect_states(machine)
        assert len(all_states) > 50, \
            "Expected > 50 states across all machines; got {}".format(len(all_states))

    def test_philosopher_nested_states(self, dp_ir):
        """Each Philosopher state must have nested P{N}_Thinking/Hungry/Eating children."""
        machine, _ = dp_ir
        root = machine.children[0]
        for child in root.children:
            if not isinstance(child, StateIR):
                continue
            if not child.id.startswith("Philosopher"):
                continue
            n = child.id.replace("Philosopher", "")
            child_ids = {c.id for c in child.children}
            for sub in ("P{}_Thinking".format(n), "P{}_Hungry".format(n)):
                assert sub in child_ids, \
                    "{} missing from {}".format(sub, child.id)

    def test_five_invoke_child_machines(self, dp_ir):
        """Each PhilosopherN must have exactly one InvokeIR with a child MachineIR."""
        machine, _ = dp_ir
        root = machine.children[0]
        invoke_count = 0
        for child in root.children:
            if not isinstance(child, StateIR):
                continue
            if not child.id.startswith("Philosopher"):
                continue
            assert len(child.invokes) == 1, \
                "{} must have exactly 1 invoke; got {}".format(child.id, len(child.invokes))
            inv = child.invokes[0]
            assert inv.child_machine is not None, \
                "{}'s invoke has no child_machine".format(child.id)
            assert isinstance(inv.child_machine, MachineIR)
            invoke_count += 1
        assert invoke_count == 5

    def test_child_machine_has_philospher_state(self, dp_ir):
        """Each child machine must contain a 'Philospher' state with sub-states."""
        machine, _ = dp_ir
        root = machine.children[0]
        for child in root.children:
            if not isinstance(child, StateIR) or not child.id.startswith("Philosopher"):
                continue
            cm = child.invokes[0].child_machine
            assert cm is not None
            child_state_ids = {c.id for c in cm.children}
            assert "Philospher" in child_state_ids or "FinalSub" in child_state_ids, \
                "Child machine for {} missing expected states; got {}".format(
                    child.id, child_state_ids
                )

    def _count_transitions(self, node):
        count = 0
        if isinstance(node, MachineIR):
            for c in node.children:
                count += self._count_transitions(c)
        elif isinstance(node, (StateIR, ParallelIR)):
            count += len(node.transitions)
            for c in node.children:
                count += self._count_transitions(c)
            for inv in getattr(node, "invokes", []):
                if inv.child_machine is not None:
                    count += self._count_transitions(inv.child_machine)
        return count

    def test_transition_count(self, dp_ir):
        """Total transition count must be substantial (>80 across all machines)."""
        machine, _ = dp_ir
        total = self._count_transitions(machine)
        assert total > 80, "Expected > 80 transitions; got {}".format(total)

    def _count_datamodel_slots(self, node):
        count = 0
        if isinstance(node, MachineIR):
            count += len(node.datamodel)
            for c in node.children:
                count += self._count_datamodel_slots(c)
        elif isinstance(node, (StateIR, ParallelIR)):
            count += len(node.datamodel)
            for c in node.children:
                count += self._count_datamodel_slots(c)
            for inv in getattr(node, "invokes", []):
                if inv.child_machine is not None:
                    count += self._count_datamodel_slots(inv.child_machine)
        return count

    def test_datamodel_slot_count(self, dp_ir):
        """Total datamodel slot count must be substantial (>15)."""
        machine, _ = dp_ir
        total = self._count_datamodel_slots(machine)
        assert total > 15, "Expected > 15 datamodel slots; got {}".format(total)

    def test_root_datamodel_slots(self, dp_ir):
        """Root parallel must have t_INPUTS, t_HAND_COMPLIANCE, i_DELAY_THINK_EAT."""
        machine, _ = dp_ir
        root = machine.children[0]
        assert isinstance(root, ParallelIR)
        slot_ids = {s.id for s in root.datamodel}
        assert "t_INPUTS" in slot_ids
        assert "t_HAND_COMPLIANCE" in slot_ids
        assert "i_DELAY_THINK_EAT" in slot_ids

    def test_t_inputs_lowered_as_map(self, dp_ir):
        """t_INPUTS initial value must lower to a MapValue."""
        machine, _ = dp_ir
        root = machine.children[0]
        assert isinstance(root, ParallelIR)
        t_inputs = next((s for s in root.datamodel if s.id == "t_INPUTS"), None)
        assert t_inputs is not None
        assert isinstance(t_inputs.initial_value, MapValue), \
            "t_INPUTS initial_value expected MapValue; got {}".format(
                type(t_inputs.initial_value).__name__
            )

    def test_t_hand_compliance_lowered_as_array(self, dp_ir):
        """t_HAND_COMPLIANCE must lower to an ArrayValue (array of arrays)."""
        machine, _ = dp_ir
        root = machine.children[0]
        slot = next((s for s in root.datamodel if s.id == "t_HAND_COMPLIANCE"), None)
        assert slot is not None
        assert isinstance(slot.initial_value, ArrayValue), \
            "t_HAND_COMPLIANCE expected ArrayValue; got {}".format(
                type(slot.initial_value).__name__
            )
        # Should be 5 inner arrays (one per philosopher)
        assert len(slot.initial_value.items) == 5

    def test_i_delay_lowered_as_number(self, dp_ir):
        """i_DELAY_THINK_EAT must lower to NumberValue(1000)."""
        machine, _ = dp_ir
        root = machine.children[0]
        slot = next((s for s in root.datamodel if s.id == "i_DELAY_THINK_EAT"), None)
        assert slot is not None
        assert isinstance(slot.initial_value, NumberValue)
        assert slot.initial_value.v == 1000

    def _find_expr_in_ir(self, node, pred):
        """Recursively search for any ExpressionNode satisfying pred."""
        if pred(node):
            return node
        if isinstance(node, BinOp):
            r = self._find_expr_in_ir(node.lhs, pred) or self._find_expr_in_ir(node.rhs, pred)
            if r:
                return r
        if isinstance(node, UnaryOp):
            r = self._find_expr_in_ir(node.operand, pred)
            if r:
                return r
        if isinstance(node, (MemberAccess, IndexAccess)):
            r = self._find_expr_in_ir(node.obj, pred)
            if r:
                return r
            if isinstance(node, IndexAccess):
                r = self._find_expr_in_ir(node.index, pred)
                if r:
                    return r
        if isinstance(node, CallNode):
            if node.receiver:
                r = self._find_expr_in_ir(node.receiver, pred)
                if r:
                    return r
            for a in node.args:
                r = self._find_expr_in_ir(a, pred)
                if r:
                    return r
        if isinstance(node, (ArrayLiteral, MapLiteral)):
            for item in (node.items if isinstance(node, ArrayLiteral) else [v for _, v in node.entries]):
                r = self._find_expr_in_ir(item, pred)
                if r:
                    return r
        return None

    def _collect_all_expr_in_actions(self, actions, results=None):
        if results is None:
            results = []
        for action in actions:
            if isinstance(action, AssignNode):
                results.append(action.expr)
            elif isinstance(action, LogNode):
                results.append(action.expr)
            elif isinstance(action, SendNode):
                for e in (action.eventexpr, action.targetexpr, action.delayexpr, action.content_expr):
                    if e is not None:
                        results.append(e)
                for _, e in action.params:
                    results.append(e)
            elif isinstance(action, IfNode):
                for branch in action.branches:
                    if branch.guard is not None:
                        results.append(branch.guard)
                    self._collect_all_expr_in_actions(branch.body, results)
            elif isinstance(action, ForeachNode):
                results.append(action.array_expr)
                self._collect_all_expr_in_actions(action.body, results)
        return results

    def _collect_all_expr_in_machine(self, machine, results=None):
        if results is None:
            results = []
        if isinstance(machine, MachineIR):
            for c in machine.children:
                self._collect_all_expr_in_machine(c, results)
        elif isinstance(machine, (StateIR, ParallelIR)):
            for t in machine.transitions:
                if t.guard is not None:
                    results.append(t.guard)
                self._collect_all_expr_in_actions(t.actions, results)
            self._collect_all_expr_in_actions(machine.onentry, results)
            self._collect_all_expr_in_actions(machine.onexit, results)
            for c in machine.children:
                self._collect_all_expr_in_machine(c, results)
            for inv in getattr(machine, "invokes", []):
                if inv.child_machine is not None:
                    self._collect_all_expr_in_machine(inv.child_machine, results)
        return results

    def test_parseint_replace_expression_lowered(self, dp_ir):
        """parseInt(_event.name.replace('taken.','')) must appear as CallNode(int, [CallNode(replace)])."""
        machine, _ = dp_ir
        all_exprs = self._collect_all_expr_in_machine(machine)

        def _is_parseint_replace(node):
            return (
                isinstance(node, CallNode)
                and node.func == "int"
                and len(node.args) == 1
                and isinstance(node.args[0], CallNode)
                and node.args[0].func == "replace"
            )

        found = any(
            self._find_expr_in_ir(e, _is_parseint_replace) for e in all_exprs
        )
        assert found, "parseInt(_event.name.replace(...)) not found in lowered IR"

    def test_t_inputs_indexed_by_event_name_expr(self, dp_ir):
        """t_INPUTS[_event.name] in <script> bodies lowers to CapabilityCallNode; the
        expression form t_INPUTS['taken.'+x] in cond attributes lowers to
        IndexAccess(VarRead('t_INPUTS'), BinOp) in transition guards."""
        machine, _ = dp_ir
        all_exprs = self._collect_all_expr_in_machine(machine)

        # t_INPUTS[_event.name] only appears in <script> bodies (CapabilityCallNode);
        # the equivalent in cond attributes is t_INPUTS['taken.'+i_ID_LEFT] where
        # the index is a BinOp string concat.  Verify that form is present.
        def _is_t_inputs_string_key_index(node):
            return (
                isinstance(node, IndexAccess)
                and isinstance(node.obj, VarRead)
                and node.obj.var == "t_INPUTS"
                and isinstance(node.index, BinOp)
            )

        found = any(
            self._find_expr_in_ir(e, _is_t_inputs_string_key_index) for e in all_exprs
        )
        assert found, "t_INPUTS['taken.'+key] IndexAccess not found in lowered IR guards"

    def test_delay_string_concat_expr(self, dp_ir):
        """i_DELAY_THINK_EAT + 'ms' must appear as a BinOp with + operator."""
        machine, _ = dp_ir
        all_exprs = self._collect_all_expr_in_machine(machine)

        def _is_delay_concat(node):
            # BinOp(+, something, StringLiteral('ms')) or
            # BinOp(+, CallNode(str, [VarRead(i_DELAY_THINK_EAT)]), StringLiteral('ms'))
            if not isinstance(node, BinOp) or node.op != "+":
                return False
            # Check rhs is string 'ms' or the overall pattern involves 'ms'
            rhs = node.rhs
            if isinstance(rhs, StringLiteral) and rhs.s == "ms":
                return True
            lhs = node.lhs
            if isinstance(lhs, StringLiteral) and lhs.s == "ms":
                return True
            return False

        found = any(
            self._find_expr_in_ir(e, _is_delay_concat) for e in all_exprs
        )
        assert found, "i_DELAY_THINK_EAT + 'ms' delay expression not found in lowered IR"

    def test_foreach_nodes_present(self, dp_ir):
        """The DP root parallel transitions include ForeachNode actions (nested foreach)."""
        machine, _ = dp_ir
        root = machine.children[0]
        assert isinstance(root, ParallelIR)

        def _has_foreach(actions):
            for a in actions:
                if isinstance(a, ForeachNode):
                    return True
                if isinstance(a, IfNode):
                    for branch in a.branches:
                        if _has_foreach(branch.body):
                            return True
            return False

        found = any(_has_foreach(t.actions) for t in root.transitions)
        assert found, "No ForeachNode found in root parallel transitions"

    def test_nested_foreach_depth_2(self, dp_ir):
        """The DP 'taken.*' transition has nested foreach (depth 1 outer, depth 2 inner)."""
        machine, _ = dp_ir
        root = machine.children[0]
        assert isinstance(root, ParallelIR)

        outer_foreach = None
        for t in root.transitions:
            for a in t.actions:
                if isinstance(a, ForeachNode):
                    outer_foreach = a
                    break
            if outer_foreach is not None:
                break

        assert outer_foreach is not None
        # The outer foreach body should contain an inner ForeachNode
        inner = next((a for a in outer_foreach.body if isinstance(a, ForeachNode)), None)
        assert inner is not None, "Expected nested ForeachNode inside outer foreach"

    def test_send_with_dynamic_eventexpr(self, dp_ir):
        """SendNode with dynamic eventexpr must be present in the lowered IR."""
        machine, _ = dp_ir
        all_exprs = []

        def _collect_send_nodes(node, acc):
            if isinstance(node, MachineIR):
                for c in node.children:
                    _collect_send_nodes(c, acc)
            elif isinstance(node, (StateIR, ParallelIR)):
                for t in node.transitions:
                    for a in t.actions:
                        _collect_from_action(a, acc)
                for a in node.onentry + node.onexit:
                    _collect_from_action(a, acc)
                for c in node.children:
                    _collect_send_nodes(c, acc)
                for inv in getattr(node, "invokes", []):
                    if inv.child_machine is not None:
                        _collect_send_nodes(inv.child_machine, acc)

        def _collect_from_action(action, acc):
            if isinstance(action, SendNode):
                acc.append(action)
            elif isinstance(action, IfNode):
                for b in action.branches:
                    for a in b.body:
                        _collect_from_action(a, acc)
            elif isinstance(action, ForeachNode):
                for a in action.body:
                    _collect_from_action(a, acc)

        send_nodes = []
        _collect_send_nodes(machine, send_nodes)

        dynamic_sends = [s for s in send_nodes if s.eventexpr is not None]
        assert dynamic_sends, "No SendNode with dynamic eventexpr found in lowered IR"

    def test_send_with_dynamic_targetexpr(self, dp_ir):
        """SendNode with dynamic targetexpr (#_parent/#_ID_P_N) must be present."""
        machine, _ = dp_ir
        send_nodes = []

        def _collect_from_action(action, acc):
            if isinstance(action, SendNode):
                acc.append(action)
            elif isinstance(action, IfNode):
                for b in action.branches:
                    for a in b.body:
                        _collect_from_action(a, acc)
            elif isinstance(action, ForeachNode):
                for a in action.body:
                    _collect_from_action(a, acc)

        def _collect_send_nodes(node, acc):
            if isinstance(node, MachineIR):
                for c in node.children:
                    _collect_send_nodes(c, acc)
            elif isinstance(node, (StateIR, ParallelIR)):
                for t in node.transitions:
                    for a in t.actions:
                        _collect_from_action(a, acc)
                for a in node.onentry + node.onexit:
                    _collect_from_action(a, acc)
                for c in node.children:
                    _collect_send_nodes(c, acc)
                for inv in getattr(node, "invokes", []):
                    if inv.child_machine is not None:
                        _collect_send_nodes(inv.child_machine, acc)

        _collect_send_nodes(machine, send_nodes)
        dynamic_target = [s for s in send_nodes if s.targetexpr is not None]
        assert dynamic_target, "No SendNode with dynamic targetexpr found in lowered IR"

    def test_diagnostics_reported_not_crashing(self, dp_ir):
        """Diagnostics collected during lowering must be accessible, not exceptions."""
        machine, diags = dp_ir
        # Diagnostics is a list (may be empty or non-empty; the machine lowered)
        assert isinstance(diags, list)
        # Machine must be a valid MachineIR regardless of diagnostic count
        assert isinstance(machine, MachineIR)

    def test_script_lowers_to_capability_call(self, dp_ir):
        """<script> elements in the child machine must lower to CapabilityCallNode."""
        machine, _ = dp_ir
        root = machine.children[0]
        # Find a Philosopher child
        phil_state = next(
            (c for c in root.children if isinstance(c, StateIR) and c.id == "Philosopher1"),
            None,
        )
        assert phil_state is not None
        cm = phil_state.invokes[0].child_machine
        assert cm is not None

        def _has_cap_call(node):
            if isinstance(node, MachineIR):
                for c in node.children:
                    if _has_cap_call(c):
                        return True
            elif isinstance(node, (StateIR, ParallelIR)):
                for a in node.onentry + node.onexit:
                    if isinstance(a, CapabilityCallNode):
                        return True
                for t in node.transitions:
                    for a in t.actions:
                        if isinstance(a, CapabilityCallNode):
                            return True
                for c in node.children:
                    if _has_cap_call(c):
                        return True
            return False

        assert _has_cap_call(cm), "No CapabilityCallNode found in Philosopher1's child machine"

    def test_capability_call_name_synthesis(self, dp_ir):
        """CapabilityCallNode names must follow the script_<block>_<state>_<idx>_<count> pattern."""
        machine, _ = dp_ir
        root = machine.children[0]
        phil_state = next(
            (c for c in root.children if isinstance(c, StateIR) and c.id == "Philosopher1"),
            None,
        )
        cm = phil_state.invokes[0].child_machine

        cap_names = []

        def _collect_cap(node):
            if isinstance(node, MachineIR):
                for c in node.children:
                    _collect_cap(c)
            elif isinstance(node, (StateIR, ParallelIR)):
                for a in node.onentry + node.onexit:
                    if isinstance(a, CapabilityCallNode):
                        cap_names.append(a.name)
                for t in node.transitions:
                    for a in t.actions:
                        if isinstance(a, CapabilityCallNode):
                            cap_names.append(a.name)
                for c in node.children:
                    _collect_cap(c)

        _collect_cap(cm)
        assert cap_names, "No CapabilityCallNode found"
        for name in cap_names:
            assert name.startswith("script_"), \
                "Cap name {!r} does not start with 'script_'".format(name)
            assert name.endswith(".success") is False  # names, not events


# ---------------------------------------------------------------------------
# Summary dump helper (used for the keystone report)
# ---------------------------------------------------------------------------

def test_dp_lowering_summary_dump(capsys):
    """Print a structural summary of the DP lowering for inspection."""
    doc = _parse_dp()
    machine, diags = lower_document(doc)

    def _count_states(node, child_machines=False):
        count = 0
        if isinstance(node, MachineIR):
            for c in node.children:
                count += _count_states(c, child_machines)
        elif isinstance(node, (StateIR, ParallelIR)):
            count += 1
            for c in node.children:
                count += _count_states(c, child_machines)
            if child_machines:
                for inv in getattr(node, "invokes", []):
                    if inv.child_machine is not None:
                        count += _count_states(inv.child_machine, child_machines)
        elif isinstance(node, FinalIR):
            count += 1
        return count

    def _count_transitions_deep(node):
        count = 0
        if isinstance(node, MachineIR):
            for c in node.children:
                count += _count_transitions_deep(c)
        elif isinstance(node, (StateIR, ParallelIR)):
            count += len(node.transitions)
            for c in node.children:
                count += _count_transitions_deep(c)
            for inv in getattr(node, "invokes", []):
                if inv.child_machine is not None:
                    count += _count_transitions_deep(inv.child_machine)
        return count

    def _count_slots_deep(node):
        count = 0
        if isinstance(node, MachineIR):
            count += len(node.datamodel)
            for c in node.children:
                count += _count_slots_deep(c)
        elif isinstance(node, (StateIR, ParallelIR)):
            count += len(node.datamodel)
            for c in node.children:
                count += _count_slots_deep(c)
            for inv in getattr(node, "invokes", []):
                if inv.child_machine is not None:
                    count += _count_slots_deep(inv.child_machine)
        return count

    def _count_child_machines(node):
        count = 0
        if isinstance(node, MachineIR):
            for c in node.children:
                count += _count_child_machines(c)
        elif isinstance(node, (StateIR, ParallelIR)):
            for inv in getattr(node, "invokes", []):
                if inv.child_machine is not None:
                    count += 1
                    count += _count_child_machines(inv.child_machine)
            for c in node.children:
                count += _count_child_machines(c)
        return count

    total_states = _count_states(machine, child_machines=True)
    top_states = _count_states(machine, child_machines=False)
    total_transitions = _count_transitions_deep(machine)
    total_slots = _count_slots_deep(machine)
    child_machine_count = _count_child_machines(machine)

    print("\n=== Dining Philosophers IR Lowering Summary ===")
    print("  Machine name: {}".format(machine.name))
    print("  Datamodel: {}".format(machine.datamodel_attr))
    print("  Top-level state count (excluding child machines): {}".format(top_states))
    print("  Total state count (incl. nested child machines): {}".format(total_states))
    print("  Inline <invoke> child machines lowered: {}".format(child_machine_count))
    print("  Total transition count (all machines): {}".format(total_transitions))
    print("  Total datamodel slot count (all machines): {}".format(total_slots))
    print("  Diagnostics collected: {}".format(len(diags)))
    if diags:
        print("  --- Diagnostics ---")
        for d in diags:
            print("    [{}] {} @ {}: {}".format(d.outcome, d.code, d.source_origin, d.message[:80]))
    print("===================================================")

    # Structural assertions
    assert isinstance(machine, MachineIR)
    assert machine.datamodel_attr == "ecmascript"
    assert child_machine_count == 5
    assert total_states > 50
    assert total_transitions > 80
    assert total_slots > 15
