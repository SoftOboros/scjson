"""
Agent Name: ecmascript-normalizer-tests

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Unit tests for the constrained ECMAScript normalizer (M1P6 D-M1P6-2).
Each admitted form is tested for correct Python output; each inadmissible
form is tested to confirm ECMAScriptNormalizationError is raised.
"""

import pytest

from scjson.ecmascript_normalizer import (
    ECMAScriptNormalizationError,
    normalize,
    normalize_script,
)


# ---------------------------------------------------------------------------
# Admitted operator forms
# ---------------------------------------------------------------------------


def test_logical_and() -> None:
    """&& is rewritten to 'and'."""
    assert normalize("a && b") == "a  and  b"


def test_logical_or() -> None:
    """|| is rewritten to 'or'."""
    assert normalize("a || b") == "a  or  b"


def test_logical_not_simple() -> None:
    """! is rewritten to 'not '."""
    result = normalize("!x")
    assert "not " in result and "x" in result


def test_logical_not_complex() -> None:
    """!expr in a parenthesized condition."""
    result = normalize("!(x === 0)")
    # Should contain 'not' and '==' (=== -> ==)
    assert "not " in result
    assert "==" in result


def test_strict_equality() -> None:
    """=== is rewritten to ==."""
    result = normalize("a === b")
    assert "==" in result
    assert "===" not in result


def test_strict_inequality() -> None:
    """!== is rewritten to !=."""
    result = normalize("a !== b")
    assert "!=" in result
    assert "!==" not in result


def test_loose_equality_passthrough() -> None:
    """Plain == passes through unchanged."""
    result = normalize("a == b")
    assert result == "a == b"


def test_loose_inequality_passthrough() -> None:
    """Plain != passes through unchanged."""
    result = normalize("a != b")
    assert result == "a != b"


def test_comparison_operators() -> None:
    """< <= > >= pass through unchanged."""
    for op in ("<", "<=", ">", ">="):
        result = normalize("a {} b".format(op))
        assert op in result


def test_arithmetic_passthrough() -> None:
    """Arithmetic operators pass through."""
    result = normalize("x + y * z - w / 2")
    assert result == "x + y * z - w / 2"


# ---------------------------------------------------------------------------
# Literal forms
# ---------------------------------------------------------------------------


def test_true_literal() -> None:
    """'true' is rewritten to 'True'."""
    result = normalize("true")
    assert result == "True"


def test_false_literal() -> None:
    """'false' is rewritten to 'False'."""
    result = normalize("false")
    assert result == "False"


def test_null_literal() -> None:
    """'null' is rewritten to 'None'."""
    result = normalize("null")
    assert result == "None"


def test_undefined_literal() -> None:
    """'undefined' is rewritten to 'None'."""
    result = normalize("undefined")
    assert result == "None"


def test_number_literal() -> None:
    """Number literals pass through unchanged."""
    result = normalize("42")
    assert result == "42"
    result2 = normalize("3.14")
    assert result2 == "3.14"


def test_string_literal_single_quotes_preserved() -> None:
    """Single-quoted strings are preserved as-is."""
    result = normalize("'hello'")
    assert result == "'hello'"


def test_string_literal_content_not_mutated() -> None:
    """String literals containing JS keywords are not substituted inside."""
    result = normalize("'true && false || null'")
    # The literal content must not be changed
    assert result == "'true && false || null'"


def test_true_in_string_not_replaced() -> None:
    """'true' inside a string literal is not replaced with 'True'."""
    result = normalize("x === 'true'")
    # x === 'true' -> x == 'true'  (string content unchanged)
    assert "==" in result
    assert "'true'" in result
    assert "True" not in result


# ---------------------------------------------------------------------------
# Built-in function rewrites
# ---------------------------------------------------------------------------


def test_parse_int_no_radix() -> None:
    """parseInt(x) is rewritten to int(x)."""
    result = normalize("parseInt(x)")
    assert result == "int(x)"


def test_parse_int_with_radix() -> None:
    """parseInt(x, r) is rewritten to int(x, r)."""
    result = normalize("parseInt(x, 10)")
    assert result == "int(x, 10)"


def test_parse_int_with_expression() -> None:
    """parseInt with a method call expression (DP machine pattern)."""
    result = normalize("parseInt(_event.name.replace('taken.',''))")
    # replace method is Python-compatible, parseInt -> int
    assert result.startswith("int(")
    assert "_event.name.replace" in result


def test_string_coerce() -> None:
    """String(x) is rewritten to str(x)."""
    result = normalize("String(x)")
    assert result == "str(x)"


def test_number_coerce() -> None:
    """Number(x) is rewritten to float(x)."""
    result = normalize("Number(x)")
    assert result == "float(x)"


def test_replace_passthrough() -> None:
    """str.replace is already Python-compatible and passes through."""
    result = normalize("name.replace('taken.', '')")
    assert "replace" in result


# ---------------------------------------------------------------------------
# System variable access
# ---------------------------------------------------------------------------


def test_event_name_passthrough() -> None:
    """_event.name passes through unchanged."""
    result = normalize("_event.name")
    assert result == "_event.name"


def test_event_data_passthrough() -> None:
    """_event.data passes through unchanged."""
    result = normalize("_event.data")
    assert result == "_event.data"


def test_computed_dict_access() -> None:
    """dict[key] computed access passes through."""
    result = normalize("t_INPUTS[_event.name]")
    assert result == "t_INPUTS[_event.name]"


# ---------------------------------------------------------------------------
# Object / array literals
# ---------------------------------------------------------------------------


def test_object_literal_unquoted_keys() -> None:
    """JS object literal with unquoted keys is converted to Python dict."""
    result = normalize("{ foo: 1, bar: 2 }")
    assert '"foo"' in result or "'foo'" in result
    assert '"bar"' in result or "'bar'" in result


def test_object_literal_already_quoted_keys() -> None:
    """Object literal with already-quoted keys passes through."""
    result = normalize("{ 'foo': 1 }")
    # Should not double-quote
    assert "'foo'" in result or '"foo"' in result


def test_array_literal_passthrough() -> None:
    """Array literals pass through unchanged."""
    result = normalize("[1, 2, 3]")
    assert result == "[1, 2, 3]"


def test_array_of_arrays_passthrough() -> None:
    """Array-of-array literals pass through unchanged."""
    result = normalize("[[1, 5], [2, 1]]")
    assert result == "[[1, 5], [2, 1]]"


# ---------------------------------------------------------------------------
# Comment stripping
# ---------------------------------------------------------------------------


def test_line_comment_stripped() -> None:
    """// comments are removed before evaluation."""
    result = normalize("x > 0 // check positive")
    assert "//" not in result
    assert "x > 0" in result


def test_block_comment_stripped() -> None:
    """/* ... */ comments are removed."""
    result = normalize("x /* the value */ > 0")
    assert "/*" not in result
    assert "x" in result
    assert "> 0" in result


# ---------------------------------------------------------------------------
# Complex compound expressions (DP machine patterns)
# ---------------------------------------------------------------------------


def test_dp_condition_or() -> None:
    """DP machine condition: (_event.name == expr) || (_event.name == expr2)."""
    expr = "(_event.name == ('taken.' + i_ID_LEFT)) || (_event.name == ('taken.' + i_ID_RIGHT))"
    result = normalize(expr)
    assert " or " in result
    assert "_event.name" in result


def test_dp_delay_concatenation() -> None:
    """DP machine delay: i_DELAY_THINK_EAT + 'ms'."""
    result = normalize("i_DELAY_THINK_EAT + 'ms'")
    assert "i_DELAY_THINK_EAT" in result
    assert "'ms'" in result


def test_dp_event_name_send() -> None:
    """DP machine eventexpr: 'eat.' + i_ID."""
    result = normalize("'eat.' + i_ID")
    assert "'eat.'" in result
    assert "i_ID" in result


def test_dp_not_condition() -> None:
    """DP machine: ! (_event.data==1) -> not (_event.data==1)."""
    result = normalize("! (_event.data==1)")
    assert "not " in result
    assert "_event.data" in result


def test_dp_target_expr() -> None:
    """DP machine targetexpr: '#_ID_P_' + (complianceIndex + 1)."""
    result = normalize("'#_ID_P_' + (complianceIndex + 1)")
    assert "'#_ID_P_'" in result


# ---------------------------------------------------------------------------
# Inadmissible forms (must raise ECMAScriptNormalizationError)
# ---------------------------------------------------------------------------


def test_unsupported_arrow_function() -> None:
    """Arrow functions raise ECMAScriptNormalizationError."""
    with pytest.raises(ECMAScriptNormalizationError) as exc_info:
        normalize("x => x + 1")
    assert exc_info.value.diagnostic == "unsupported-ecmascript"
    assert "arrow function" in str(exc_info.value)


def test_unsupported_new() -> None:
    """'new' expression raises ECMAScriptNormalizationError."""
    with pytest.raises(ECMAScriptNormalizationError) as exc_info:
        normalize("new Object()")
    assert exc_info.value.diagnostic == "unsupported-ecmascript"


def test_unsupported_typeof() -> None:
    """typeof operator raises ECMAScriptNormalizationError."""
    with pytest.raises(ECMAScriptNormalizationError) as exc_info:
        normalize("typeof x === 'number'")
    assert exc_info.value.diagnostic == "unsupported-ecmascript"


def test_unsupported_instanceof() -> None:
    """instanceof operator raises ECMAScriptNormalizationError."""
    with pytest.raises(ECMAScriptNormalizationError) as exc_info:
        normalize("x instanceof Array")
    assert exc_info.value.diagnostic == "unsupported-ecmascript"


def test_unsupported_for_loop() -> None:
    """for loop raises ECMAScriptNormalizationError."""
    with pytest.raises(ECMAScriptNormalizationError) as exc_info:
        normalize("for (let i = 0; i < 10; i++) {}")
    assert exc_info.value.diagnostic == "unsupported-ecmascript"


def test_unsupported_while_loop() -> None:
    """while loop raises ECMAScriptNormalizationError."""
    with pytest.raises(ECMAScriptNormalizationError) as exc_info:
        normalize("while (x > 0) { x-- }")
    assert exc_info.value.diagnostic == "unsupported-ecmascript"


def test_unsupported_template_literal() -> None:
    """Template literals raise ECMAScriptNormalizationError."""
    with pytest.raises(ECMAScriptNormalizationError) as exc_info:
        normalize("`hello ${name}`")
    assert exc_info.value.diagnostic == "unsupported-ecmascript"


def test_unsupported_delete() -> None:
    """delete operator raises ECMAScriptNormalizationError."""
    with pytest.raises(ECMAScriptNormalizationError) as exc_info:
        normalize("delete obj.key")
    assert exc_info.value.diagnostic == "unsupported-ecmascript"


def test_unsupported_void() -> None:
    """void operator raises ECMAScriptNormalizationError."""
    with pytest.raises(ECMAScriptNormalizationError) as exc_info:
        normalize("void 0")
    assert exc_info.value.diagnostic == "unsupported-ecmascript"


def test_unsupported_yield() -> None:
    """yield raises ECMAScriptNormalizationError."""
    with pytest.raises(ECMAScriptNormalizationError) as exc_info:
        normalize("yield x")
    assert exc_info.value.diagnostic == "unsupported-ecmascript"


def test_unsupported_await() -> None:
    """await raises ECMAScriptNormalizationError."""
    with pytest.raises(ECMAScriptNormalizationError) as exc_info:
        normalize("await somePromise")
    assert exc_info.value.diagnostic == "unsupported-ecmascript"


# ---------------------------------------------------------------------------
# Script body normalization
# ---------------------------------------------------------------------------


def test_script_assignment() -> None:
    """Simple assignment in a script body normalizes correctly."""
    result = normalize_script("t_INPUTS[_event.name] = _event.data")
    assert "t_INPUTS[_event.name]" in result
    assert "_event.data" in result


def test_script_if_statement() -> None:
    """if (cond) { body } is converted to Python if form."""
    result = normalize_script("if (i_ID !== 0) {\n    x = 1\n}")
    assert result.startswith("if ")
    assert "!=" in result  # !== -> !=
    assert "x = 1" in result


def test_script_if_with_assignments() -> None:
    """Multi-line if body with assignments (DP machine pattern)."""
    body = """if (i_ID !== 0) {
    i_ID_LEFT = t_HAND_COMPLIANCE[i_ID - 1][0]
    i_ID_RIGHT = t_HAND_COMPLIANCE[i_ID - 1][1]
}

t_INPUTS['taken.' + i_ID_LEFT] = 0
t_INPUTS['taken.' + i_ID_RIGHT] = 0"""
    result = normalize_script(body)
    assert "if " in result
    assert "i_ID_LEFT" in result
    assert "i_ID_RIGHT" in result
    assert "t_INPUTS" in result


def test_script_unsupported_form_raises() -> None:
    """Inadmissible form in a script body raises ECMAScriptNormalizationError."""
    with pytest.raises(ECMAScriptNormalizationError):
        normalize_script("for (let i = 0; i < 10; i++) { x += i }")
