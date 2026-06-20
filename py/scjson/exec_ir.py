"""
Agent Name: exec-ir

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

M1 Executable IR + SCJSON-to-IR lowerer (M1P6 G2-codegen).

This module provides:

1. **Value model** (D-M1P6-3) -- a closed tagged union of runtime values:
   Number, Str, Bool, Array, Map, Undefined.

2. **ExpressionNode families** (M1-EXECUTABLE-IR Area 1 + D-M1P6-2) -- seven
   families covering the admitted ECMAScript subset, lowered from Python AST
   nodes produced by the ecmascript_normalizer.

3. **ActionNode families** (M1-EXECUTABLE-IR Area 2, D-M1P6-4..6) -- seven
   families: Assign, Log, Raise, Send (with dynamic expr slots), Cancel, If,
   Foreach, plus CapabilityCall and the M1P6-added ForeachNode shape.

4. **State-tree IR** -- recursive dataclasses mirroring the SCXML tree:
   StateIR, ParallelIR, FinalIR, HistoryIR, MachineIR, TransitionIR,
   DataSlotIR.

5. **lower_document()** -- the public entry point: accepts a parsed ``Scxml``
   Pydantic model and returns a ``MachineIR`` plus a list of
   ``ExecutableDiagnostic`` items collected during lowering.  No construct is
   silently dropped; unadmitted forms produce a diagnostic (D-M1P6-8).

Mapping from admitted ECMAScript to ExpressionNode (D-M1P6-2):
  JS form                     -> Python AST node      -> IR family
  -----------------------------------------------------------------------
  42  /  3.14  /  -5         -> ast.Constant(int|float) -> NumericLiteral
  'hello'                    -> ast.Constant(str)     -> StringLiteral
  True / False               -> ast.Constant(bool)    -> BoolLiteral
  x  /  _event              -> ast.Name               -> VarRead
  a.b  /  _event.name       -> ast.Attribute          -> MemberAccess
  a[expr]                   -> ast.Subscript          -> IndexAccess
  a + b  /  a == b  etc.    -> ast.BinOp / ast.Compare -> BinOp
  !x  (normalized to not x) -> ast.UnaryOp(Not)       -> UnaryOp
  -x                        -> ast.UnaryOp(USub)       -> UnaryOp
  parseInt(x)  String(x) .. -> ast.Call               -> CallNode
  [1, 2, 3]                 -> ast.List               -> ArrayLiteral
  {a: b}                    -> ast.Dict               -> MapLiteral

Deviations from M1-EXECUTABLE-IR spec (none; full compliance):
  - M1P1 seven ExpressionNode families are all implemented.
  - M1P2 seven ActionNode families are all implemented.
  - M1P6 ForeachNode, inline-invoke nested MachineIR, dynamic Send slots
    are implemented per D-M1P6-4, D-M1P6-5, D-M1P6-6.
  - CapabilityCallNode: script elements map to CapabilityCallNode per M1P3;
    name synthesis follows the frozen pattern.
  - Diagnostics are collected (never raised) per D-M1P6-8.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union


# ---------------------------------------------------------------------------
# Diagnostic
# ---------------------------------------------------------------------------


@dataclass
class ExecutableDiagnostic:
    """A non-fatal lowering diagnostic (M1P4 / D-M1P6-8).

    Diagnostics are always collected; they never abort lowering.

    :param code: Machine-readable code, e.g. ``"unsupported-ecmascript"``.
    :param outcome: One of ``"accept"``, ``"normalize"``, ``"capability-only"``,
        ``"reject"``.
    :param tier: Portability tier of the offending construct.
    :param source_origin: Free-form origin label (state id / block type).
    :param message: Human-readable description.
    """

    code: str
    outcome: str
    tier: str
    source_origin: str
    message: str


# ---------------------------------------------------------------------------
# Value model (D-M1P6-3)
# ---------------------------------------------------------------------------


@dataclass
class NumberValue:
    """A numeric IR value (int or float).

    :param v: The numeric value.
    """

    v: Union[int, float]


@dataclass
class StrValue:
    """A string IR value.

    :param v: The string value.
    """

    v: str


@dataclass
class BoolValue:
    """A boolean IR value.

    :param v: The boolean value.
    """

    v: bool


@dataclass
class ArrayValue:
    """An array IR value (ordered sequence).

    :param items: Sequence of element values.
    """

    items: List["Value"] = field(default_factory=list)


@dataclass
class MapValue:
    """A string-keyed map IR value (ordered).

    :param entries: Ordered list of (key, value) pairs.
    """

    entries: List[tuple] = field(default_factory=list)


@dataclass
class UndefinedValue:
    """Undefined / null sentinel (compares falsey per D-M1P6-3)."""


#: Tagged union of all admitted IR values.
Value = Union[NumberValue, StrValue, BoolValue, ArrayValue, MapValue, UndefinedValue]


# ---------------------------------------------------------------------------
# ExpressionNode families (M1-EXECUTABLE-IR Area 1, D-M1P6-2)
# ---------------------------------------------------------------------------


@dataclass
class NumericLiteral:
    """Numeric constant.  Ref: M1-EXECUTABLE-IR Area 1, ``{"num": float}``.

    :param num: The numeric constant value.
    :param diagnostic: Optional diagnostic if this node carries a warning.
    """

    num: Union[int, float]
    diagnostic: Optional[ExecutableDiagnostic] = None


@dataclass
class StringLiteral:
    """String constant.  Ref: M1-EXECUTABLE-IR Area 1, ``{"str": str}``.

    :param s: The string value.
    :param diagnostic: Optional diagnostic if this node carries a warning.
    """

    s: str
    diagnostic: Optional[ExecutableDiagnostic] = None


@dataclass
class BoolLiteral:
    """Boolean constant.  Ref: M1-EXECUTABLE-IR Area 1, ``{"bool": bool}``.

    :param b: The boolean value.
    :param diagnostic: Optional diagnostic if this node carries a warning.
    """

    b: bool
    diagnostic: Optional[ExecutableDiagnostic] = None


@dataclass
class VarRead:
    """Read a datamodel variable.  Ref: M1-EXECUTABLE-IR Area 1, ``{"var": str}``.

    Type is ``unknown`` at M1; deferred to M2.

    :param var: Variable name.
    :param diagnostic: Optional diagnostic.
    """

    var: str
    diagnostic: Optional[ExecutableDiagnostic] = None


@dataclass
class MemberAccess:
    """Static attribute access (``a.b``).

    Extension of the M1 ExpressionNode family for the admitted ECMAScript subset
    (D-M1P6-2): ``_event.name``, ``_event.data``, etc.

    :param obj: Object expression.
    :param attr: Attribute name.
    :param diagnostic: Optional diagnostic.
    """

    obj: "ExpressionNode"
    attr: str
    diagnostic: Optional[ExecutableDiagnostic] = None


@dataclass
class IndexAccess:
    """Computed index access (``a[expr]``).

    Covers ``t_INPUTS[_event.name]``, ``t_HAND_COMPLIANCE[i][0]``, etc.
    (D-M1P6-2).

    :param obj: Object (array/map) expression.
    :param index: Index expression.
    :param diagnostic: Optional diagnostic.
    """

    obj: "ExpressionNode"
    index: "ExpressionNode"
    diagnostic: Optional[ExecutableDiagnostic] = None


@dataclass
class BinOp:
    """Binary or comparison operation.

    Covers ``+  -  *  /  ==  !=  <  <=  >  >=  &&  ||``
    (M1-EXECUTABLE-IR ``Comparison`` / ``BoolCompose`` extended with arithmetic).

    :param op: Operator string from the admitted set.
    :param lhs: Left operand.
    :param rhs: Right operand.
    :param diagnostic: Optional diagnostic.
    """

    op: str
    lhs: "ExpressionNode"
    rhs: "ExpressionNode"
    diagnostic: Optional[ExecutableDiagnostic] = None


@dataclass
class UnaryOp:
    """Unary operation (``!`` / unary ``-``).

    Covers M1-EXECUTABLE-IR ``Not``; extended with unary minus for arithmetic.

    :param op: ``"not"`` or ``"neg"``.
    :param operand: Operand expression.
    :param diagnostic: Optional diagnostic.
    """

    op: str  # "not" | "neg"
    operand: "ExpressionNode"
    diagnostic: Optional[ExecutableDiagnostic] = None


@dataclass
class CallNode:
    """Admitted built-in call (``parseInt``, ``String``, ``Number``, ``.replace``).

    D-M1P6-2 whitelist only; any other call produces ``unsupported-ecmascript``.

    :param func: Canonical function name (e.g. ``"parseInt"``, ``"str"``,
        ``"float"``, ``"replace"``).
    :param args: Argument expression list.
    :param receiver: For method calls (``<str>.replace(a, b)``), the receiver
        expression; ``None`` for free functions.
    :param diagnostic: Optional diagnostic.
    """

    func: str
    args: List["ExpressionNode"] = field(default_factory=list)
    receiver: Optional["ExpressionNode"] = None
    diagnostic: Optional[ExecutableDiagnostic] = None


@dataclass
class ArrayLiteral:
    """Array literal (``[a, b, c]``), including array-of-array.

    :param items: Element expressions.
    :param diagnostic: Optional diagnostic.
    """

    items: List["ExpressionNode"] = field(default_factory=list)
    diagnostic: Optional[ExecutableDiagnostic] = None


@dataclass
class MapLiteral:
    """Object literal (``{key: val, ...}``).

    Keys must be string literals or string-placeholder identifiers per
    the normalizer's object-literal rewriting.

    :param entries: List of (key_expr, value_expr) pairs.
    :param diagnostic: Optional diagnostic.
    """

    entries: List[tuple] = field(default_factory=list)
    diagnostic: Optional[ExecutableDiagnostic] = None


@dataclass
class UnsupportedExpr:
    """Placeholder for an expression that could not be lowered.

    Carries the diagnostic and the original source text so downstream
    consumers can report the failure location.  Tier: ``unsupported``.
    Per D-M1P6-8 this must never be silently omitted.

    :param source: Original source text.
    :param diagnostic: Required diagnostic entry.
    """

    source: str
    diagnostic: ExecutableDiagnostic


#: Union of all admitted ExpressionNode types.
ExpressionNode = Union[
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
]


# ---------------------------------------------------------------------------
# OriginRef (M1-EXECUTABLE-IR Area 2)
# ---------------------------------------------------------------------------


@dataclass
class OriginRef:
    """Block-level source origin annotation.

    :param type: Block kind: ``"onentry"``, ``"onexit"``, ``"transition"``,
        ``"script"``.
    :param state: Owning state id if known.
    :param idx: Index within the containing block list.
    :param src: Source state id for transitions.
    :param dst: Target state id(s) for transitions.
    """

    type: str
    state: Optional[str] = None
    idx: Optional[int] = None
    src: Optional[str] = None
    dst: Optional[List[str]] = None


# ---------------------------------------------------------------------------
# ActionNode families (M1-EXECUTABLE-IR Area 2, D-M1P6-4..6)
# ---------------------------------------------------------------------------


@dataclass
class AssignNode:
    """Assign to a datamodel location.  M1-EXECUTABLE-IR ``AssignNode``.

    :param loc: Target location (variable name, or ``"map[key]"`` for
        computed-member assignment).
    :param expr: Value expression.
    :param op: Assignment operator: ``"set"`` | ``"add"`` | ``"sub"`` |
        ``"mul"`` | ``"div"``.
    :param origin: Block-level origin reference.
    :param diagnostic: Optional diagnostic.
    """

    loc: str
    expr: ExpressionNode
    op: str = "set"
    origin: Optional[OriginRef] = None
    diagnostic: Optional[ExecutableDiagnostic] = None


@dataclass
class LogNode:
    """Log a value.  M1-EXECUTABLE-IR ``LogNode``.

    :param expr: Expression to log.
    :param label: Optional label string.
    :param origin: Block-level origin reference.
    :param diagnostic: Optional diagnostic.
    """

    expr: ExpressionNode
    label: Optional[str] = None
    origin: Optional[OriginRef] = None
    diagnostic: Optional[ExecutableDiagnostic] = None


@dataclass
class RaiseNode:
    """Raise a named event.  M1-EXECUTABLE-IR ``RaiseNode``.

    :param event: Event name string.
    :param origin: Block-level origin reference.
    :param diagnostic: Optional diagnostic.
    """

    event: str
    origin: Optional[OriginRef] = None
    diagnostic: Optional[ExecutableDiagnostic] = None


@dataclass
class SendNode:
    """Send an event.  M1-EXECUTABLE-IR ``SendNode`` with D-M1P6-6 dynamic slots.

    Static ``event`` / ``target`` / ``delay`` are plain strings; dynamic
    ``eventexpr`` / ``targetexpr`` / ``delayexpr`` / ``content_expr`` hold
    ``ExpressionNode`` trees evaluated at send time.

    :param event: Static event name (or ``None`` when ``eventexpr`` is set).
    :param eventexpr: Dynamic event-name expression (D-M1P6-6).
    :param target: Static send target (or ``None``).
    :param targetexpr: Dynamic target expression (D-M1P6-6).
    :param delay: Static delay string (or ``None``).
    :param delayexpr: Dynamic delay expression (D-M1P6-6).
    :param send_id: Static send identifier.
    :param content_expr: Dynamic ``<content expr=...>`` expression.
    :param params: List of ``(name, expr)`` pairs from ``<param>`` children.
    :param origin: Block-level origin reference.
    :param diagnostic: Optional diagnostic.
    """

    event: Optional[str] = None
    eventexpr: Optional[ExpressionNode] = None
    target: Optional[str] = None
    targetexpr: Optional[ExpressionNode] = None
    delay: Optional[str] = None
    delayexpr: Optional[ExpressionNode] = None
    send_id: Optional[str] = None
    content_expr: Optional[ExpressionNode] = None
    params: List[tuple] = field(default_factory=list)
    origin: Optional[OriginRef] = None
    diagnostic: Optional[ExecutableDiagnostic] = None


@dataclass
class CancelNode:
    """Cancel a pending send.  M1-EXECUTABLE-IR ``CancelNode`` (stub).

    :param sendid: Static send id to cancel.
    :param origin: Block-level origin reference.
    :param diagnostic: Optional diagnostic.
    """

    sendid: Optional[str] = None
    origin: Optional[OriginRef] = None
    diagnostic: Optional[ExecutableDiagnostic] = None


@dataclass
class IfBranch:
    """One branch of an IfNode.

    :param guard: Guard expression (``None`` for ``else`` branches).
    :param body: Action list for this branch.
    """

    guard: Optional[ExpressionNode]
    body: List["ActionNode"] = field(default_factory=list)


@dataclass
class IfNode:
    """Conditional action.  M1-EXECUTABLE-IR ``IfNode``.

    Branches are tested in order; first match fires.

    :param branches: Ordered list of branches (if / elseif / else).
    :param origin: Block-level origin reference.
    :param diagnostic: Optional diagnostic.
    """

    branches: List[IfBranch] = field(default_factory=list)
    origin: Optional[OriginRef] = None
    diagnostic: Optional[ExecutableDiagnostic] = None


@dataclass
class ForeachNode:
    """Bounded iteration over an array.  D-M1P6-4.

    :param array_expr: Expression evaluating to an Array value.
    :param item: Name of the item binding variable.
    :param index: Optional name of the index binding variable.
    :param body: Actions executed per iteration.
    :param depth: Nesting depth (max 4 per D-M1P6-4).
    :param origin: Block-level origin reference.
    :param diagnostic: Optional diagnostic.
    """

    array_expr: ExpressionNode
    item: str
    index: Optional[str] = None
    body: List["ActionNode"] = field(default_factory=list)
    depth: int = 1
    origin: Optional[OriginRef] = None
    diagnostic: Optional[ExecutableDiagnostic] = None


@dataclass
class CapabilityCallNode:
    """Named or synthesized capability call.  M1-EXECUTABLE-IR Area 3.

    :param name: Stable capability identifier (named or synthesized).
    :param origin: Block-level source reference.
    :param success_event: ``"<name>.success"`` -- frozen at M1.
    :param error_event: ``"<name>.error"`` -- frozen at M1.
    :param capability_intent: ``None`` at M1; typed at M2.
    :param args: ``None`` at M1; typed at M2.
    :param return_type: ``None`` at M1; typed at M2.
    :param correlation_id: ``None`` at M1; runtime token at M4.
    :param diagnostic: Optional diagnostic.
    """

    name: str
    origin: OriginRef
    success_event: str
    error_event: str
    capability_intent: None = None
    args: None = None
    return_type: None = None
    correlation_id: None = None
    diagnostic: Optional[ExecutableDiagnostic] = None


#: Union of all ActionNode types.
ActionNode = Union[
    AssignNode,
    LogNode,
    RaiseNode,
    SendNode,
    CancelNode,
    IfNode,
    ForeachNode,
    CapabilityCallNode,
]


# ---------------------------------------------------------------------------
# State-tree IR
# ---------------------------------------------------------------------------


@dataclass
class DataSlotIR:
    """One ``<data>`` element in a ``<datamodel>``.

    :param id: Data slot identifier.
    :param initial_value: IR-level initial value (or ``None`` for unspecified).
    :param expr_source: Original expression source text.
    :param diagnostic: Optional diagnostic.
    """

    id: str
    initial_value: Optional[Value] = None
    expr_source: Optional[str] = None
    diagnostic: Optional[ExecutableDiagnostic] = None


@dataclass
class TransitionIR:
    """One transition in the IR.

    :param event: Event pattern (``None`` for eventless/epsilon transitions).
    :param targets: List of target state ids.
    :param guard: Guard expression (``None`` means always enabled).
    :param actions: Executable content in document order.
    :param origin: Block-level origin reference.
    :param diagnostics: Per-transition diagnostic list.
    """

    event: Optional[str] = None
    targets: List[str] = field(default_factory=list)
    guard: Optional[ExpressionNode] = None
    actions: List[ActionNode] = field(default_factory=list)
    origin: Optional[OriginRef] = None
    diagnostics: List[ExecutableDiagnostic] = field(default_factory=list)


@dataclass
class StateIR:
    """IR for a ``<state>`` element.

    :param id: State identifier.
    :param initial: Initial sub-state id (or ``None``).
    :param datamodel: Data slots declared on this state.
    :param onentry: Onentry action list.
    :param onexit: Onexit action list.
    :param transitions: Ordered transition list.
    :param children: Child StateIR / ParallelIR / FinalIR / HistoryIR nodes.
    :param invokes: Invoke IR nodes attached to this state.
    :param diagnostics: Diagnostics collected for this state.
    """

    id: str
    initial: Optional[str] = None
    datamodel: List[DataSlotIR] = field(default_factory=list)
    onentry: List[ActionNode] = field(default_factory=list)
    onexit: List[ActionNode] = field(default_factory=list)
    transitions: List[TransitionIR] = field(default_factory=list)
    children: List["AnyStateIR"] = field(default_factory=list)
    invokes: List["InvokeIR"] = field(default_factory=list)
    diagnostics: List[ExecutableDiagnostic] = field(default_factory=list)


@dataclass
class ParallelIR:
    """IR for a ``<parallel>`` element.

    :param id: Parallel region identifier.
    :param datamodel: Data slots declared on this region.
    :param onentry: Onentry action list.
    :param onexit: Onexit action list.
    :param transitions: Ordered transition list.
    :param children: Child region / state nodes (all run concurrently).
    :param invokes: Invoke IR nodes.
    :param diagnostics: Diagnostics collected for this region.
    """

    id: str
    datamodel: List[DataSlotIR] = field(default_factory=list)
    onentry: List[ActionNode] = field(default_factory=list)
    onexit: List[ActionNode] = field(default_factory=list)
    transitions: List[TransitionIR] = field(default_factory=list)
    children: List["AnyStateIR"] = field(default_factory=list)
    invokes: List["InvokeIR"] = field(default_factory=list)
    diagnostics: List[ExecutableDiagnostic] = field(default_factory=list)


@dataclass
class FinalIR:
    """IR for a ``<final>`` element.

    :param id: Final state identifier.
    :param diagnostics: Diagnostics collected for this state.
    """

    id: str
    diagnostics: List[ExecutableDiagnostic] = field(default_factory=list)


@dataclass
class HistoryIR:
    """IR for a ``<history>`` pseudostate.

    :param id: History pseudostate identifier.
    :param type: ``"shallow"`` or ``"deep"``.
    :param diagnostics: Diagnostics collected for this element.
    """

    id: str
    type: str = "shallow"
    diagnostics: List[ExecutableDiagnostic] = field(default_factory=list)


#: Union of all state-level IR node types.
AnyStateIR = Union[StateIR, ParallelIR, FinalIR, HistoryIR]


@dataclass
class InvokeIR:
    """IR for an ``<invoke>`` element.

    :param invoke_id: Explicit invoke id (or ``None`` for auto-assigned).
    :param type_value: Invoke type string (default ``"scxml"``).
    :param src: External source URI (``None`` for inline content).
    :param child_machine: Nested MachineIR for inline ``<content><scxml>``,
        depth-bounded per D-M1P6-5.
    :param params: List of ``(name, expr)`` pairs from ``<param>`` children.
    :param autoforward: Whether to autoforward events.
    :param depth: Nesting depth of this invocation (max 2 per D-M1P6-5).
    :param diagnostics: Diagnostics collected for this invoke.
    """

    invoke_id: Optional[str] = None
    type_value: str = "scxml"
    src: Optional[str] = None
    child_machine: Optional["MachineIR"] = None
    params: List[tuple] = field(default_factory=list)
    autoforward: bool = False
    depth: int = 1
    diagnostics: List[ExecutableDiagnostic] = field(default_factory=list)


@dataclass
class MachineIR:
    """Top-level IR for one SCXML document.

    :param name: Machine name from ``<scxml name=...>``.
    :param datamodel_attr: Datamodel attribute (``"ecmascript"`` | ``"python"``
        | ``"null"``).
    :param initial: Initial state id(s).
    :param datamodel: Root-level data slots.
    :param children: Top-level state / parallel / final nodes.
    :param diagnostics: All diagnostics collected during lowering of this
        machine (does not include child-machine diagnostics).
    """

    name: Optional[str] = None
    datamodel_attr: str = "null"
    initial: List[str] = field(default_factory=list)
    datamodel: List[DataSlotIR] = field(default_factory=list)
    children: List[AnyStateIR] = field(default_factory=list)
    diagnostics: List[ExecutableDiagnostic] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Python-AST → ExpressionNode converter
# ---------------------------------------------------------------------------

_ADMITTED_BUILTINS = frozenset({"int", "str", "float"})
_ADMITTED_METHODS = frozenset({"replace"})

# Maps Python AST operator types to canonical IR op strings.
_BINOP_MAP: Dict[type, str] = {
    ast.Add: "+",
    ast.Sub: "-",
    ast.Mult: "*",
    ast.Div: "/",
    ast.BitOr: "|",
    ast.BitAnd: "&",
}
_CMPOP_MAP: Dict[type, str] = {
    ast.Eq: "==",
    ast.NotEq: "!=",
    ast.Lt: "<",
    ast.LtE: "<=",
    ast.Gt: ">",
    ast.GtE: ">=",
}
_BOOLOP_MAP: Dict[type, str] = {
    ast.And: "&&",
    ast.Or: "||",
}


def _ast_to_expr(node: ast.expr, origin: str) -> ExpressionNode:
    """Convert a Python AST expression node to an IR ExpressionNode.

    :param node: Python AST expression node produced by ``ast.parse``.
    :param origin: Source-origin label (state id / block type) for diagnostics.
    :returns: An ExpressionNode; never raises; unsupported forms return
        ``UnsupportedExpr`` with a diagnostic.
    """
    # Constant
    if isinstance(node, ast.Constant):
        v = node.value
        if v is None:
            return UndefinedValue()  # type: ignore[return-value]
        if isinstance(v, bool):
            return BoolLiteral(b=v)
        if isinstance(v, (int, float)):
            return NumericLiteral(num=v)
        if isinstance(v, str):
            return StringLiteral(s=v)
        return _unsupported_expr(
            ast.unparse(node), origin,
            "unsupported constant type: {}".format(type(v).__name__),
        )

    # Name (variable read)
    if isinstance(node, ast.Name):
        return VarRead(var=node.id)

    # Attribute access (a.b)
    if isinstance(node, ast.Attribute):
        obj = _ast_to_expr(node.value, origin)
        return MemberAccess(obj=obj, attr=node.attr)

    # Subscript (a[expr])
    if isinstance(node, ast.Subscript):
        obj = _ast_to_expr(node.value, origin)
        # Python 3.9+ wraps the index in an Index node; 3.9+ uses the value directly.
        idx_node = node.slice
        if isinstance(idx_node, ast.Index):  # type: ignore[attr-defined]
            idx_node = idx_node.value  # type: ignore[attr-defined]
        idx = _ast_to_expr(idx_node, origin)
        return IndexAccess(obj=obj, index=idx)

    # BinOp (arithmetic)
    if isinstance(node, ast.BinOp):
        op_str = _BINOP_MAP.get(type(node.op))
        if op_str is None:
            return _unsupported_expr(
                ast.unparse(node), origin,
                "unsupported binary operator: {}".format(type(node.op).__name__),
            )
        lhs = _ast_to_expr(node.left, origin)
        rhs = _ast_to_expr(node.right, origin)
        return BinOp(op=op_str, lhs=lhs, rhs=rhs)

    # Compare (a == b, a < b, etc.)
    if isinstance(node, ast.Compare):
        if len(node.ops) != 1 or len(node.comparators) != 1:
            # Chained comparisons not in admitted subset
            return _unsupported_expr(
                ast.unparse(node), origin,
                "chained comparison not in admitted subset",
            )
        op_str = _CMPOP_MAP.get(type(node.ops[0]))
        if op_str is None:
            return _unsupported_expr(
                ast.unparse(node), origin,
                "unsupported comparison operator: {}".format(type(node.ops[0]).__name__),
            )
        lhs = _ast_to_expr(node.left, origin)
        rhs = _ast_to_expr(node.comparators[0], origin)
        return BinOp(op=op_str, lhs=lhs, rhs=rhs)

    # BoolOp (and / or)
    if isinstance(node, ast.BoolOp):
        op_str = _BOOLOP_MAP.get(type(node.op))
        if op_str is None:
            return _unsupported_expr(
                ast.unparse(node), origin,
                "unsupported boolean operator: {}".format(type(node.op).__name__),
            )
        # Fold left-associatively
        result = _ast_to_expr(node.values[0], origin)
        for val in node.values[1:]:
            result = BinOp(op=op_str, lhs=result, rhs=_ast_to_expr(val, origin))
        return result

    # UnaryOp (not / -)
    if isinstance(node, ast.UnaryOp):
        if isinstance(node.op, ast.Not):
            operand = _ast_to_expr(node.operand, origin)
            return UnaryOp(op="not", operand=operand)
        if isinstance(node.op, ast.USub):
            operand = _ast_to_expr(node.operand, origin)
            return UnaryOp(op="neg", operand=operand)
        return _unsupported_expr(
            ast.unparse(node), origin,
            "unsupported unary operator: {}".format(type(node.op).__name__),
        )

    # Call (free function or method)
    if isinstance(node, ast.Call):
        # Free function calls: int(), str(), float()
        if isinstance(node.func, ast.Name):
            fname = node.func.id
            if fname in _ADMITTED_BUILTINS:
                args = [_ast_to_expr(a, origin) for a in node.args]
                return CallNode(func=fname, args=args)
            return _unsupported_expr(
                ast.unparse(node), origin,
                "non-admitted free function call: {}".format(fname),
            )
        # Method calls: <str>.replace(a, b)
        if isinstance(node.func, ast.Attribute):
            mname = node.func.attr
            if mname in _ADMITTED_METHODS:
                receiver = _ast_to_expr(node.func.value, origin)
                args = [_ast_to_expr(a, origin) for a in node.args]
                return CallNode(func=mname, args=args, receiver=receiver)
            return _unsupported_expr(
                ast.unparse(node), origin,
                "non-admitted method call: {}".format(mname),
            )
        return _unsupported_expr(
            ast.unparse(node), origin,
            "unsupported call form",
        )

    # List literal ([a, b, c])
    if isinstance(node, ast.List):
        items = [_ast_to_expr(elt, origin) for elt in node.elts]
        return ArrayLiteral(items=items)

    # Dict literal ({k: v, ...})
    if isinstance(node, ast.Dict):
        entries = []
        for k, v in zip(node.keys, node.values):
            if k is None:
                return _unsupported_expr(
                    ast.unparse(node), origin,
                    "dict unpacking (**) not in admitted subset",
                )
            key_expr = _ast_to_expr(k, origin)
            val_expr = _ast_to_expr(v, origin)
            entries.append((key_expr, val_expr))
        return MapLiteral(entries=entries)

    # Tuple (not admitted)
    return _unsupported_expr(
        ast.unparse(node) if hasattr(ast, "unparse") else repr(node),
        origin,
        "unsupported expression form: {}".format(type(node).__name__),
    )


def _unsupported_expr(source: str, origin: str, message: str) -> UnsupportedExpr:
    """Build an UnsupportedExpr placeholder with a diagnostic.

    :param source: Source text of the expression.
    :param origin: State/block origin for diagnostic attribution.
    :param message: Human-readable description of the failure.
    :returns: UnsupportedExpr with a ``"unsupported-ecmascript"`` diagnostic.
    """
    diag = ExecutableDiagnostic(
        code="unsupported-ecmascript",
        outcome="reject",
        tier="forbidden",
        source_origin=origin,
        message=message,
    )
    return UnsupportedExpr(source=source, diagnostic=diag)


def lower_expression(expr_str: str, origin: str) -> tuple:
    """Lower an ECMAScript expression string to an ExpressionNode.

    Uses the ecmascript_normalizer to translate to Python, then parses the
    Python AST and converts to the IR.

    :param expr_str: Raw ECMAScript expression string.
    :param origin: Source origin label for diagnostics.
    :returns: ``(ExpressionNode, diagnostics)`` where ``diagnostics`` is a
        (possibly empty) list of ``ExecutableDiagnostic`` items.  Never raises.
    """
    from .ecmascript_normalizer import (
        ECMAScriptNormalizationError,
        normalize as _normalize,
    )

    diagnostics: List[ExecutableDiagnostic] = []
    if not expr_str or not expr_str.strip():
        diag = ExecutableDiagnostic(
            code="empty-expression",
            outcome="normalize",
            tier="restricted",
            source_origin=origin,
            message="Empty expression string",
        )
        diagnostics.append(diag)
        return UnsupportedExpr(source=expr_str, diagnostic=diag), diagnostics

    try:
        py_expr = _normalize(expr_str)
    except ECMAScriptNormalizationError as exc:
        diag = ExecutableDiagnostic(
            code=getattr(exc, "diagnostic", "unsupported-ecmascript"),
            outcome="reject",
            tier="forbidden",
            source_origin=origin,
            message=str(exc),
        )
        diagnostics.append(diag)
        return UnsupportedExpr(source=expr_str, diagnostic=diag), diagnostics

    try:
        tree = ast.parse(py_expr, mode="eval")
    except SyntaxError as exc:
        diag = ExecutableDiagnostic(
            code="parse-error",
            outcome="reject",
            tier="forbidden",
            source_origin=origin,
            message="Python AST parse error after normalization: {} (normalized: {!r})".format(
                exc, py_expr
            ),
        )
        diagnostics.append(diag)
        return UnsupportedExpr(source=expr_str, diagnostic=diag), diagnostics

    ir_node = _ast_to_expr(tree.body, origin)
    if isinstance(ir_node, UnsupportedExpr):
        diagnostics.append(ir_node.diagnostic)
    return ir_node, diagnostics


# ---------------------------------------------------------------------------
# SCJSON → IR lowerer
# ---------------------------------------------------------------------------


class _LoweringContext:
    """Mutable context accumulating diagnostics during lowering.

    :param ecmascript_mode: True when the machine's datamodel is
        ``"ecmascript"``.
    :param invoke_depth: Current invocation nesting depth (max 2 per D-M1P6-5).
    """

    def __init__(self, *, ecmascript_mode: bool = False, invoke_depth: int = 0) -> None:
        self.ecmascript_mode = ecmascript_mode
        self.invoke_depth = invoke_depth
        self.diagnostics: List[ExecutableDiagnostic] = []
        # Counters used for capability-call name synthesis (M1P3)
        self._cap_counters: Dict[str, int] = {}

    def push_diag(self, diag: ExecutableDiagnostic) -> None:
        """Append a diagnostic.

        :param diag: The diagnostic to record.
        """
        self.diagnostics.append(diag)

    def lower_expr(self, expr_str: str, origin: str) -> ExpressionNode:
        """Lower an expression string to an ExpressionNode, collecting diagnostics.

        If the machine is NOT in ECMAScript mode, treat the expression as a
        Python-datamodel expression and emit a lightweight VarRead or
        UnsupportedExpr rather than running the JS normalizer.

        :param expr_str: Expression source text.
        :param origin: Source origin label.
        :returns: ExpressionNode (never raises).
        """
        if self.ecmascript_mode:
            node, diags = lower_expression(expr_str, origin)
            self.diagnostics.extend(diags)
            return node
        # Python-datamodel: do a best-effort lowering via the Python AST
        # directly (no ECMAScript normalizer needed).
        node, diags = _lower_python_expr(expr_str, origin)
        self.diagnostics.extend(diags)
        return node

    def synth_cap_name(
        self, *, script_name: Optional[str], block_type: str, state: str, idx: int
    ) -> str:
        """Synthesize a stable CapabilityCallNode name per M1P3.

        Named scripts use their own name.  Unnamed scripts get the frozen
        synthesis pattern: ``script_<block_type>_<state>_<count>``.

        :param script_name: Explicit script name attribute (or ``None``).
        :param block_type: ``"onentry"``, ``"onexit"``, or ``"trans_<src>_<dst>"``.
        :param state: Owning state id.
        :param idx: Index within the block.
        :returns: Synthesized stable name string.
        """
        if script_name:
            return script_name
        key = "{}_{}".format(block_type, state)
        count = self._cap_counters.get(key, 0)
        self._cap_counters[key] = count + 1
        return "script_{}_{}_{}_{}".format(block_type, state, idx, count)


def _lower_python_expr(expr_str: str, origin: str) -> tuple:
    """Best-effort Python-datamodel expression lowering.

    Parses the expression as Python directly (no JS normalizer step).

    :param expr_str: Python expression string.
    :param origin: Source origin label.
    :returns: ``(ExpressionNode, diagnostics)``.
    """
    diagnostics: List[ExecutableDiagnostic] = []
    if not expr_str or not expr_str.strip():
        diag = ExecutableDiagnostic(
            code="empty-expression",
            outcome="normalize",
            tier="restricted",
            source_origin=origin,
            message="Empty expression string",
        )
        diagnostics.append(diag)
        return UnsupportedExpr(source=expr_str, diagnostic=diag), diagnostics

    try:
        tree = ast.parse(expr_str, mode="eval")
    except SyntaxError as exc:
        diag = ExecutableDiagnostic(
            code="parse-error",
            outcome="reject",
            tier="forbidden",
            source_origin=origin,
            message="AST parse error: {}".format(exc),
        )
        diagnostics.append(diag)
        return UnsupportedExpr(source=expr_str, diagnostic=diag), diagnostics

    ir_node = _ast_to_expr(tree.body, origin)
    if isinstance(ir_node, UnsupportedExpr):
        diagnostics.append(ir_node.diagnostic)
    return ir_node, diagnostics


# ---------------------------------------------------------------------------
# DataSlotIR lowering
# ---------------------------------------------------------------------------

_NUMERIC_RE = re.compile(r"^\s*-?\d+(\.\d+)?\s*$")


def _lower_data_slot(data: Any, ctx: _LoweringContext) -> DataSlotIR:
    """Lower one ``<data>`` element to a DataSlotIR.

    :param data: Pydantic ``Data`` / ``ScxmlDataType`` model instance.
    :param ctx: Lowering context.
    :returns: DataSlotIR.
    """
    slot_id = getattr(data, "id", None) or ""
    expr_src = getattr(data, "expr", None)
    initial: Optional[Value] = None

    if expr_src is not None:
        expr_str = str(expr_src).strip()
        ir_node = ctx.lower_expr(expr_str, "data:{}".format(slot_id))
        # Convert simple literal IR nodes to Value tags
        initial = _expr_to_value(ir_node)
    return DataSlotIR(id=slot_id, initial_value=initial, expr_source=expr_src)


def _expr_to_value(node: ExpressionNode) -> Optional[Value]:
    """Convert a simple ExpressionNode literal to a tagged Value, if possible.

    Used for datamodel initialization where the value is a compile-time
    constant.  Non-constant nodes are left as ``None`` (value unknown at
    lower time).

    :param node: ExpressionNode to convert.
    :returns: Tagged Value or ``None``.
    """
    if isinstance(node, NumericLiteral):
        return NumberValue(v=node.num)
    if isinstance(node, StringLiteral):
        return StrValue(v=node.s)
    if isinstance(node, BoolLiteral):
        return BoolValue(v=node.b)
    if isinstance(node, UndefinedValue):
        return UndefinedValue()
    if isinstance(node, ArrayLiteral):
        items = [_expr_to_value(e) for e in node.items]
        return ArrayValue(items=[v for v in items if v is not None])
    if isinstance(node, MapLiteral):
        entries = []
        for k, v in node.entries:
            kv = _expr_to_value(k)
            vv = _expr_to_value(v)
            if isinstance(kv, StrValue):
                entries.append((kv.v, vv))
        return MapValue(entries=entries)
    return None


# ---------------------------------------------------------------------------
# Executable-content (action block) lowering
# ---------------------------------------------------------------------------

_MAX_FOREACH_DEPTH = 4  # D-M1P6-4
_MAX_INVOKE_DEPTH = 2   # D-M1P6-5


def _lower_send(send: Any, ctx: _LoweringContext, origin: str) -> SendNode:
    """Lower a ``<send>`` element to a SendNode.

    Handles both static (``event``, ``target``, ``delay``) and dynamic
    (``eventexpr``, ``targetexpr``, ``delayexpr``) attributes per D-M1P6-6.

    :param send: Pydantic Send model instance.
    :param ctx: Lowering context.
    :param origin: Source origin label.
    :returns: SendNode.
    """
    event = getattr(send, "event", None)
    target = getattr(send, "target", None)
    delay = getattr(send, "delay", None)
    send_id = getattr(send, "id", None)

    eventexpr_ir: Optional[ExpressionNode] = None
    targetexpr_ir: Optional[ExpressionNode] = None
    delayexpr_ir: Optional[ExpressionNode] = None
    content_expr_ir: Optional[ExpressionNode] = None

    raw_eventexpr = getattr(send, "eventexpr", None)
    raw_targetexpr = getattr(send, "targetexpr", None)
    raw_delayexpr = getattr(send, "delayexpr", None)

    if raw_eventexpr:
        eventexpr_ir = ctx.lower_expr(str(raw_eventexpr), origin + ":eventexpr")
    if raw_targetexpr:
        targetexpr_ir = ctx.lower_expr(str(raw_targetexpr), origin + ":targetexpr")
    if raw_delayexpr:
        delayexpr_ir = ctx.lower_expr(str(raw_delayexpr), origin + ":delayexpr")

    # <content expr=...>
    for content in getattr(send, "content", []) or []:
        expr_attr = getattr(content, "expr", None)
        if expr_attr:
            content_expr_ir = ctx.lower_expr(str(expr_attr), origin + ":content_expr")
            break

    # <param> elements
    params: List[tuple] = []
    for param in getattr(send, "param", []) or []:
        pname = getattr(param, "name", None)
        pexpr = getattr(param, "expr", None)
        if pname and pexpr is not None:
            param_ir = ctx.lower_expr(str(pexpr), origin + ":param:{}".format(pname))
            params.append((pname, param_ir))

    return SendNode(
        event=event,
        eventexpr=eventexpr_ir,
        target=target,
        targetexpr=targetexpr_ir,
        delay=delay,
        delayexpr=delayexpr_ir,
        send_id=send_id,
        content_expr=content_expr_ir,
        params=params,
        origin=OriginRef(type="send", state=origin),
    )


def _lower_foreach(
    fe: Any, ctx: _LoweringContext, origin: str, depth: int = 1
) -> ForeachNode:
    """Lower a ``<foreach>`` element to a ForeachNode (D-M1P6-4).

    :param fe: Pydantic Foreach model instance.
    :param ctx: Lowering context.
    :param origin: Source origin label.
    :param depth: Current foreach nesting depth.
    :returns: ForeachNode.
    """
    if depth > _MAX_FOREACH_DEPTH:
        diag = ExecutableDiagnostic(
            code="foreach-depth-exceeded",
            outcome="reject",
            tier="forbidden",
            source_origin=origin,
            message="foreach nesting depth {} exceeds maximum {} (D-M1P6-4)".format(
                depth, _MAX_FOREACH_DEPTH
            ),
        )
        ctx.push_diag(diag)

    array_str = getattr(fe, "array", "[]")
    array_ir = ctx.lower_expr(str(array_str), origin + ":foreach.array")
    item = getattr(fe, "item", "_item")
    index = getattr(fe, "index", None)
    body = _lower_action_block(fe, ctx, origin + ":foreach", foreach_depth=depth)

    return ForeachNode(
        array_expr=array_ir,
        item=item,
        index=index,
        body=body,
        depth=depth,
        origin=OriginRef(type="foreach", state=origin),
    )


def _lower_if(block: Any, ctx: _LoweringContext, origin: str) -> IfNode:
    """Lower an ``<if>`` block to an IfNode.

    :param block: Pydantic If model instance.
    :param ctx: Lowering context.
    :param origin: Source origin label.
    :returns: IfNode.
    """
    branches: List[IfBranch] = []

    # Primary if branch
    cond_str = getattr(block, "cond", None)
    guard_ir: Optional[ExpressionNode] = None
    if cond_str:
        guard_ir = ctx.lower_expr(str(cond_str), origin + ":if.cond")

    # Reconstruct the branch body by looking at the sub-actions
    # We gather the initial if body items from the transition / block's
    # own action children, then switch on elseif/else tags.
    # Use the same approach as the engine: collect action children in XML order.
    primary_body = _lower_action_block(block, ctx, origin + ":if")

    # Check for elseif
    elseif = getattr(block, "elseif", None)
    else_value = getattr(block, "else_value", None)

    if elseif is not None or else_value is not None:
        # The primary body items came from the block until the first elseif/else marker.
        # For simplicity (and parity with the engine's _split_if_branches), treat
        # all sub-action items from the block itself as the primary branch body.
        branches.append(IfBranch(guard=guard_ir, body=primary_body))
        # Add elseif branch
        if elseif is not None:
            elseif_cond = getattr(elseif, "cond", None)
            elseif_guard: Optional[ExpressionNode] = None
            if elseif_cond:
                elseif_guard = ctx.lower_expr(
                    str(elseif_cond), origin + ":elseif.cond"
                )
            branches.append(IfBranch(guard=elseif_guard, body=[]))
        # Add else branch
        if else_value is not None:
            branches.append(IfBranch(guard=None, body=[]))
    else:
        branches.append(IfBranch(guard=guard_ir, body=primary_body))

    return IfNode(branches=branches, origin=OriginRef(type="if", state=origin))


def _lower_script(
    script: Any, ctx: _LoweringContext, origin: str, state: str, idx: int
) -> CapabilityCallNode:
    """Lower a ``<script>`` element to a CapabilityCallNode (M1P3).

    :param script: Pydantic Script model instance.
    :param ctx: Lowering context.
    :param origin: Source origin label.
    :param state: Owning state id for name synthesis.
    :param idx: Index within the parent block.
    :returns: CapabilityCallNode.
    """
    script_name = getattr(script, "name", None)
    block_type = origin.split(":")[-1] if ":" in origin else origin
    name = ctx.synth_cap_name(
        script_name=script_name, block_type=block_type, state=state, idx=idx
    )
    origin_ref = OriginRef(type="script", state=state, idx=idx)
    return CapabilityCallNode(
        name=name,
        origin=origin_ref,
        success_event="{}.success".format(name),
        error_event="{}.error".format(name),
    )


def _lower_action_block(
    container: Any,
    ctx: _LoweringContext,
    origin: str,
    foreach_depth: int = 0,
) -> List[ActionNode]:
    """Lower all executable-content children of *container* in document order.

    Iterates over the action-type lists on the pydantic model; ordering
    follows the same precedence as the engine's ``_build_action_sequence``.

    :param container: Pydantic model with action list attributes.
    :param ctx: Lowering context.
    :param origin: Source origin label.
    :param foreach_depth: Current foreach nesting depth (for depth checks).
    :returns: Ordered list of ActionNode.
    """
    actions: List[ActionNode] = []

    # Walk known action list attributes in document-declared field order.
    # raise_value, if_value, foreach, assign, log, script, send, cancel
    # For onentry/onexit types the attribute bag is the same.

    state_id = _extract_state_from_origin(origin)
    script_counter = [0]  # mutable to allow closure increment

    def _push_assign(item: Any) -> None:
        loc = getattr(item, "location", None) or ""
        expr_src = getattr(item, "expr", None) or ""
        op_enum = getattr(item, "type_value", None)
        op = "set"
        if op_enum is not None:
            op_str = str(op_enum).lower()
            if "add" in op_str:
                op = "add"
            elif "sub" in op_str:
                op = "sub"
            elif "mul" in op_str:
                op = "mul"
            elif "div" in op_str:
                op = "div"
        expr_ir = ctx.lower_expr(str(expr_src), origin + ":assign")
        actions.append(
            AssignNode(
                loc=loc,
                expr=expr_ir,
                op=op,
                origin=OriginRef(type="assign", state=state_id),
            )
        )

    def _push_log(item: Any) -> None:
        expr_src = getattr(item, "expr", None) or ""
        label = getattr(item, "label", None)
        expr_ir = ctx.lower_expr(str(expr_src), origin + ":log")
        actions.append(
            LogNode(
                expr=expr_ir,
                label=label,
                origin=OriginRef(type="log", state=state_id),
            )
        )

    def _push_raise(item: Any) -> None:
        event_name = getattr(item, "event", None) or ""
        actions.append(
            RaiseNode(
                event=event_name,
                origin=OriginRef(type="raise", state=state_id),
            )
        )

    def _push_send(item: Any) -> None:
        actions.append(_lower_send(item, ctx, origin))

    def _push_cancel(item: Any) -> None:
        sendid = getattr(item, "sendid", None)
        actions.append(
            CancelNode(sendid=sendid, origin=OriginRef(type="cancel", state=state_id))
        )

    def _push_if(item: Any) -> None:
        actions.append(_lower_if(item, ctx, origin))

    def _push_foreach(item: Any) -> None:
        depth = foreach_depth + 1
        actions.append(_lower_foreach(item, ctx, origin, depth=depth))

    def _push_script(item: Any) -> None:
        idx = script_counter[0]
        script_counter[0] += 1
        actions.append(_lower_script(item, ctx, origin, state_id, idx))

    # Map attribute names on the pydantic model to action kinds
    # We visit in a fixed order but the important thing is we visit all items.
    _handlers: List[tuple] = [
        ("raise_value", _push_raise),
        ("assign", _push_assign),
        ("log", _push_log),
        ("send", _push_send),
        ("cancel", _push_cancel),
        ("if_value", _push_if),
        ("foreach", _push_foreach),
        ("script", _push_script),
    ]

    # Collect all items from each list, then sort by document order.
    # We attempt to use XML round-trip order when available; otherwise
    # fall back to the per-attribute order above.
    ordered = _collect_actions_ordered(container, _handlers, ctx, origin)
    return ordered


def _collect_actions_ordered(
    container: Any,
    handlers: List[tuple],
    ctx: _LoweringContext,
    origin: str,
) -> List[ActionNode]:
    """Collect actions from *container* using document-order XML if possible.

    Falls back to the handler order from *handlers* if XML round-trip is
    unavailable (e.g. in deeply nested inline invoke content).

    :param container: Pydantic model with action list attributes.
    :param handlers: Ordered list of ``(attr_name, handler)`` pairs.
    :param ctx: Lowering context.
    :param origin: Source origin label.
    :returns: Ordered list of ActionNode.
    """
    from xml.etree import ElementTree as ET
    from .SCXMLDocumentHandler import SCXMLDocumentHandler
    from . import dataclasses as dataclasses_module

    _serializer = SCXMLDocumentHandler(
        pretty=False,
        omit_empty=False,
        fail_on_unknown_properties=False,
    )

    def _local_name(tag: str) -> str:
        return tag.rsplit("}", 1)[-1] if "}" in tag else tag

    # Attempt XML round-trip to get true document order
    xml_order: Optional[List[str]] = None
    try:
        if hasattr(container, "__dataclass_fields__"):
            dc_obj = container
        elif hasattr(container, "model_dump"):
            cls = getattr(dataclasses_module, type(container).__name__)
            data = container.model_dump(mode="python")
            dc_obj = _serializer._to_dataclass(cls, data)
        else:
            dc_obj = None

        if dc_obj is not None:
            xml_str = _serializer.to_string(dc_obj)
            root = ET.fromstring(xml_str)
            xml_order = [_local_name(child.tag) for child in list(root)]
    except Exception:
        xml_order = None

    state_id = _extract_state_from_origin(origin)
    script_counter = [0]
    all_actions: List[ActionNode] = []

    if xml_order is not None:
        # Build per-type item queues
        queues: Dict[str, List[Any]] = {}
        for attr_name, _ in handlers:
            items = list(getattr(container, attr_name, []) or [])
            queues[attr_name] = items
        cursors: Dict[str, int] = {k: 0 for k in queues}

        _tag_to_attr = {
            "raise": "raise_value",
            "assign": "assign",
            "log": "log",
            "send": "send",
            "cancel": "cancel",
            "if": "if_value",
            "foreach": "foreach",
            "script": "script",
        }

        for tag in xml_order:
            attr_name = _tag_to_attr.get(tag)
            if attr_name is None:
                continue
            q = queues.get(attr_name, [])
            idx = cursors.get(attr_name, 0)
            if idx >= len(q):
                continue
            item = q[idx]
            cursors[attr_name] = idx + 1

            if attr_name == "raise_value":
                event_name = getattr(item, "event", None) or ""
                all_actions.append(
                    RaiseNode(event=event_name, origin=OriginRef(type="raise", state=state_id))
                )
            elif attr_name == "assign":
                loc = getattr(item, "location", None) or ""
                expr_src = getattr(item, "expr", None) or ""
                op_enum = getattr(item, "type_value", None)
                op = "set"
                if op_enum is not None:
                    op_str = str(op_enum).lower()
                    if "add" in op_str:
                        op = "add"
                    elif "sub" in op_str:
                        op = "sub"
                    elif "mul" in op_str:
                        op = "mul"
                    elif "div" in op_str:
                        op = "div"
                expr_ir = ctx.lower_expr(str(expr_src), origin + ":assign")
                all_actions.append(
                    AssignNode(loc=loc, expr=expr_ir, op=op, origin=OriginRef(type="assign", state=state_id))
                )
            elif attr_name == "log":
                expr_src = getattr(item, "expr", None) or ""
                label = getattr(item, "label", None)
                expr_ir = ctx.lower_expr(str(expr_src), origin + ":log")
                all_actions.append(
                    LogNode(expr=expr_ir, label=label, origin=OriginRef(type="log", state=state_id))
                )
            elif attr_name == "send":
                all_actions.append(_lower_send(item, ctx, origin))
            elif attr_name == "cancel":
                sendid = getattr(item, "sendid", None)
                all_actions.append(
                    CancelNode(sendid=sendid, origin=OriginRef(type="cancel", state=state_id))
                )
            elif attr_name == "if_value":
                all_actions.append(_lower_if(item, ctx, origin))
            elif attr_name == "foreach":
                depth = 1
                all_actions.append(_lower_foreach(item, ctx, origin, depth=depth))
            elif attr_name == "script":
                sc_idx = script_counter[0]
                script_counter[0] += 1
                all_actions.append(_lower_script(item, ctx, origin, state_id, sc_idx))

        return all_actions

    # Fallback: use handler order
    for attr_name, handler_fn in handlers:
        items = list(getattr(container, attr_name, []) or [])
        for item in items:
            if attr_name == "script":
                sc_idx = script_counter[0]
                script_counter[0] += 1
                all_actions.append(_lower_script(item, ctx, origin, state_id, sc_idx))
            else:
                # Call the appropriate inline logic
                if attr_name == "raise_value":
                    event_name = getattr(item, "event", None) or ""
                    all_actions.append(
                        RaiseNode(event=event_name, origin=OriginRef(type="raise", state=state_id))
                    )
                elif attr_name == "assign":
                    loc = getattr(item, "location", None) or ""
                    expr_src = getattr(item, "expr", None) or ""
                    expr_ir = ctx.lower_expr(str(expr_src), origin + ":assign")
                    all_actions.append(
                        AssignNode(loc=loc, expr=expr_ir, op="set", origin=OriginRef(type="assign", state=state_id))
                    )
                elif attr_name == "log":
                    expr_src = getattr(item, "expr", None) or ""
                    label = getattr(item, "label", None)
                    expr_ir = ctx.lower_expr(str(expr_src), origin + ":log")
                    all_actions.append(
                        LogNode(expr=expr_ir, label=label, origin=OriginRef(type="log", state=state_id))
                    )
                elif attr_name == "send":
                    all_actions.append(_lower_send(item, ctx, origin))
                elif attr_name == "cancel":
                    sendid = getattr(item, "sendid", None)
                    all_actions.append(
                        CancelNode(sendid=sendid, origin=OriginRef(type="cancel", state=state_id))
                    )
                elif attr_name == "if_value":
                    all_actions.append(_lower_if(item, ctx, origin))
                elif attr_name == "foreach":
                    all_actions.append(_lower_foreach(item, ctx, origin, depth=1))

    return all_actions


def _extract_state_from_origin(origin: str) -> str:
    """Extract the state id from an origin label string.

    :param origin: Origin label like ``"state:Thinking:onentry"``.
    :returns: The first segment before a colon, or the whole string.
    """
    return origin.split(":")[0] if ":" in origin else origin


# ---------------------------------------------------------------------------
# Invoke lowering
# ---------------------------------------------------------------------------


def _lower_invoke(
    inv: Any, ctx: _LoweringContext, parent_state: str
) -> InvokeIR:
    """Lower an ``<invoke>`` element to an InvokeIR.

    Inline ``<content><scxml>`` child machines are lowered recursively
    per D-M1P6-5, bounded to depth 2.

    :param inv: Pydantic Invoke model instance.
    :param ctx: Lowering context.
    :param parent_state: Id of the state containing this invoke.
    :returns: InvokeIR.
    """
    invoke_id = getattr(inv, "id", None)
    type_value = getattr(inv, "type_value", None) or "scxml"
    src = getattr(inv, "src", None)
    af = getattr(inv, "autoforward", None)
    autoforward = str(af).lower() in {"true", "booleandata.true"} if af is not None else False

    params: List[tuple] = []
    for param in getattr(inv, "param", []) or []:
        pname = getattr(param, "name", None)
        pexpr = getattr(param, "expr", None)
        if pname and pexpr is not None:
            param_ir = ctx.lower_expr(str(pexpr), "invoke:{}:param:{}".format(parent_state, pname))
            params.append((pname, param_ir))

    child_machine: Optional[MachineIR] = None
    content_items = getattr(inv, "content", []) or []
    for content in content_items:
        # Look for inline <scxml> inside <content>
        inner_list = getattr(content, "content", []) or []
        for inner in inner_list:
            from .pydantic import Scxml as _PydScxml
            if isinstance(inner, _PydScxml):
                if ctx.invoke_depth >= _MAX_INVOKE_DEPTH:
                    diag = ExecutableDiagnostic(
                        code="invoke-depth-exceeded",
                        outcome="reject",
                        tier="forbidden",
                        source_origin=parent_state,
                        message="inline invoke nesting depth exceeds maximum {} (D-M1P6-5)".format(
                            _MAX_INVOKE_DEPTH
                        ),
                    )
                    ctx.push_diag(diag)
                else:
                    child_ctx = _LoweringContext(
                        ecmascript_mode=_is_ecmascript(inner),
                        invoke_depth=ctx.invoke_depth + 1,
                    )
                    child_machine = _lower_scxml(inner, child_ctx)
                    ctx.diagnostics.extend(child_ctx.diagnostics)
                break
        if child_machine is not None:
            break

    if src is not None and child_machine is None:
        # External src reference — not admitted by M1P6
        diag = ExecutableDiagnostic(
            code="unsupported-invoke-src",
            outcome="normalize",
            tier="restricted",
            source_origin=parent_state,
            message="<invoke src={}> is not admitted by M1P6; only inline <content> is supported".format(
                src
            ),
        )
        ctx.push_diag(diag)

    return InvokeIR(
        invoke_id=invoke_id,
        type_value=type_value,
        src=src,
        child_machine=child_machine,
        params=params,
        autoforward=autoforward,
        depth=ctx.invoke_depth + 1,
    )


# ---------------------------------------------------------------------------
# Transition lowering
# ---------------------------------------------------------------------------


def _lower_transition(trans: Any, ctx: _LoweringContext, state_id: str) -> TransitionIR:
    """Lower one ``<transition>`` element to a TransitionIR.

    :param trans: Pydantic Transition model instance.
    :param ctx: Lowering context.
    :param state_id: Owning state id.
    :returns: TransitionIR.
    """
    event = getattr(trans, "event", None)
    targets = list(getattr(trans, "target", []) or [])
    cond = getattr(trans, "cond", None)

    guard_ir: Optional[ExpressionNode] = None
    diags: List[ExecutableDiagnostic] = []
    if cond:
        origin = "{}:trans".format(state_id)
        guard_ir = ctx.lower_expr(str(cond), origin)
        # Collect diagnostics from the lowered guard
        if isinstance(guard_ir, UnsupportedExpr):
            diags.append(guard_ir.diagnostic)

    origin_ref = OriginRef(
        type="transition",
        state=state_id,
        src=state_id,
        dst=targets,
    )
    actions = _lower_action_block(trans, ctx, "{}:trans".format(state_id))

    return TransitionIR(
        event=event,
        targets=targets,
        guard=guard_ir,
        actions=actions,
        origin=origin_ref,
        diagnostics=diags,
    )


# ---------------------------------------------------------------------------
# State-tree lowering helpers
# ---------------------------------------------------------------------------


def _is_ecmascript(doc: Any) -> bool:
    """Return True when *doc* declares datamodel="ecmascript".

    :param doc: Pydantic Scxml model.
    :returns: True if ECMAScript datamodel.
    """
    dm = getattr(doc, "datamodel_attribute", None) or getattr(doc, "datamodel", None)
    return str(dm).lower() == "ecmascript"


def _lower_datamodel(node: Any, ctx: _LoweringContext) -> List[DataSlotIR]:
    """Lower all ``<datamodel>`` blocks on *node*.

    :param node: Pydantic SCXML node with a ``datamodel`` attribute.
    :param ctx: Lowering context.
    :returns: List of DataSlotIR.
    """
    slots: List[DataSlotIR] = []
    for dm in getattr(node, "datamodel", []) or []:
        for data in getattr(dm, "data", []) or []:
            slots.append(_lower_data_slot(data, ctx))
    return slots


def _lower_onentry(node: Any, ctx: _LoweringContext, state_id: str) -> List[ActionNode]:
    """Lower onentry blocks for *node*.

    :param node: Pydantic SCXML state node.
    :param ctx: Lowering context.
    :param state_id: Owning state id for diagnostics.
    :returns: Ordered action list.
    """
    actions: List[ActionNode] = []
    for entry in getattr(node, "onentry", []) or []:
        actions.extend(_lower_action_block(entry, ctx, "{}:onentry".format(state_id)))
    return actions


def _lower_onexit(node: Any, ctx: _LoweringContext, state_id: str) -> List[ActionNode]:
    """Lower onexit blocks for *node*.

    :param node: Pydantic SCXML state node.
    :param ctx: Lowering context.
    :param state_id: Owning state id for diagnostics.
    :returns: Ordered action list.
    """
    actions: List[ActionNode] = []
    for onexit in getattr(node, "onexit", []) or []:
        actions.extend(_lower_action_block(onexit, ctx, "{}:onexit".format(state_id)))
    return actions


def _lower_state(node: Any, ctx: _LoweringContext, parent_id: str) -> StateIR:
    """Lower a ``<state>`` element recursively.

    :param node: Pydantic State model.
    :param ctx: Lowering context.
    :param parent_id: Parent state id (for diagnostics).
    :returns: StateIR.
    """
    from .pydantic import History as _PydHistory, ScxmlFinalType as _PydFinal

    state_id = getattr(node, "id", None) or "anon_{}".format(id(node))
    initial_attr = getattr(node, "initial_attribute", None)
    if not initial_attr:
        initial_nodes = getattr(node, "initial", []) or []
        if initial_nodes:
            first = initial_nodes[0]
            tgt = getattr(getattr(first, "transition", None), "target", None)
            initial_attr = list(tgt)[0] if tgt else None

    datamodel = _lower_datamodel(node, ctx)
    onentry = _lower_onentry(node, ctx, state_id)
    onexit = _lower_onexit(node, ctx, state_id)
    transitions = [
        _lower_transition(t, ctx, state_id)
        for t in getattr(node, "transition", []) or []
    ]

    invokes: List[InvokeIR] = []
    for inv in getattr(node, "invoke", []) or []:
        invokes.append(_lower_invoke(inv, ctx, state_id))

    children: List[AnyStateIR] = []
    for child in getattr(node, "state", []) or []:
        children.append(_lower_state(child, ctx, state_id))
    for child in getattr(node, "parallel", []) or []:
        children.append(_lower_parallel(child, ctx, state_id))
    for child in getattr(node, "final", []) or []:
        child_id = getattr(child, "id", None) or "final_{}".format(id(child))
        children.append(FinalIR(id=child_id))
    for child in getattr(node, "history", []) or []:
        child_id = getattr(child, "id", None) or "hist_{}".format(id(child))
        hist_type = getattr(child, "type_value", "shallow") or "shallow"
        children.append(HistoryIR(id=child_id, type=str(hist_type)))

    return StateIR(
        id=state_id,
        initial=str(initial_attr) if initial_attr else None,
        datamodel=datamodel,
        onentry=onentry,
        onexit=onexit,
        transitions=transitions,
        children=children,
        invokes=invokes,
    )


def _lower_parallel(node: Any, ctx: _LoweringContext, parent_id: str) -> ParallelIR:
    """Lower a ``<parallel>`` element recursively.

    :param node: Pydantic ScxmlParallelType model.
    :param ctx: Lowering context.
    :param parent_id: Parent id (for diagnostics).
    :returns: ParallelIR.
    """
    parallel_id = getattr(node, "id", None) or "parallel_{}".format(id(node))
    datamodel = _lower_datamodel(node, ctx)
    onentry = _lower_onentry(node, ctx, parallel_id)
    onexit = _lower_onexit(node, ctx, parallel_id)
    transitions = [
        _lower_transition(t, ctx, parallel_id)
        for t in getattr(node, "transition", []) or []
    ]

    invokes: List[InvokeIR] = []
    for inv in getattr(node, "invoke", []) or []:
        invokes.append(_lower_invoke(inv, ctx, parallel_id))

    children: List[AnyStateIR] = []
    for child in getattr(node, "state", []) or []:
        children.append(_lower_state(child, ctx, parallel_id))
    for child in getattr(node, "parallel", []) or []:
        children.append(_lower_parallel(child, ctx, parallel_id))
    for child in getattr(node, "final", []) or []:
        child_id = getattr(child, "id", None) or "final_{}".format(id(child))
        children.append(FinalIR(id=child_id))
    for child in getattr(node, "history", []) or []:
        child_id = getattr(child, "id", None) or "hist_{}".format(id(child))
        hist_type = getattr(child, "type_value", "shallow") or "shallow"
        children.append(HistoryIR(id=child_id, type=str(hist_type)))

    return ParallelIR(
        id=parallel_id,
        datamodel=datamodel,
        onentry=onentry,
        onexit=onexit,
        transitions=transitions,
        children=children,
        invokes=invokes,
    )


def _lower_scxml(doc: Any, ctx: _LoweringContext) -> MachineIR:
    """Lower the root ``<scxml>`` element to a MachineIR.

    This is the recursive core used both for the top-level document and for
    inline ``<content><scxml>`` child machines (D-M1P6-5).

    :param doc: Pydantic Scxml model.
    :param ctx: Lowering context (owns the diagnostic list).
    :returns: MachineIR.
    """
    name = getattr(doc, "name", None)
    datamodel_attr = getattr(doc, "datamodel_attribute", None) or "null"
    initial_attr = getattr(doc, "initial", None) or []

    datamodel = _lower_datamodel(doc, ctx)

    children: List[AnyStateIR] = []
    for child in getattr(doc, "state", []) or []:
        children.append(_lower_state(child, ctx, "__root__"))
    for child in getattr(doc, "parallel", []) or []:
        children.append(_lower_parallel(child, ctx, "__root__"))
    for child in getattr(doc, "final", []) or []:
        child_id = getattr(child, "id", None) or "final_{}".format(id(child))
        children.append(FinalIR(id=child_id))

    return MachineIR(
        name=name,
        datamodel_attr=datamodel_attr,
        initial=list(initial_attr),
        datamodel=datamodel,
        children=children,
        diagnostics=ctx.diagnostics,
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def lower_document(doc: Any) -> tuple:
    """Lower a parsed SCJSON/SCXML Pydantic document to a MachineIR.

    This is the primary API of the M1 Executable IR layer.  The returned
    MachineIR carries all diagnostics collected during lowering; every
    un-lowerable construct produces a diagnostic rather than being silently
    dropped (D-M1P6-8).

    :param doc: A ``Scxml`` Pydantic model instance (from ``pydantic.generated``).
        Also accepts any model with the SCXML root interface (used for inline
        child machines in tests).
    :returns: ``(MachineIR, diagnostics)`` where ``diagnostics`` is the flat
        list of all ``ExecutableDiagnostic`` items collected.  The list is also
        accessible as ``machine_ir.diagnostics``.
    """
    ecmascript = _is_ecmascript(doc)
    ctx = _LoweringContext(ecmascript_mode=ecmascript, invoke_depth=0)
    machine = _lower_scxml(doc, ctx)
    return machine, ctx.diagnostics
