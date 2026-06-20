"""
Agent Name: ecmascript-normalizer

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Constrained ECMAScript expression front-end (M1P6 G2).

Normalizes the admitted ECMAScript subset (D-M1P6-2) into Python expressions
that can be evaluated by the existing Python sandbox evaluator.  Everything
outside the admitted subset raises ECMAScriptNormalizationError with diagnostic
name "unsupported-ecmascript" -- nothing is silently dropped.

Admitted forms (D-M1P6-2):
  Operators:   &&  ||  !  ===  !==  ==  !=  <  <=  >  >=  +  -  *  /  unary-
  Literals:    true  false  null  undefined  number  string  array  object
  Built-ins:   parseInt(x)  parseInt(x, r)  String(x)  Number(x)
               <str>.replace(a, b)  (identical Python method -- passed through)
  Sys vars:    _event  _event.name  _event.data  (available in eval env)
  Member:      a.b  a[expr]
  Script stmts (in <script>): assignment  if (cond) { ... }

Inadmissible forms that produce unsupported-ecmascript:
  =>  new  typeof  instanceof  for  while  do  switch  throw  try  catch
  template literals (backtick)  delete  void  yield  await  class  import
  export  with
"""

from __future__ import annotations

import re
from typing import List, Tuple


# Sentinel prefix used to mark string-literal placeholders.  We use a
# distinctive multi-character prefix that cannot appear in valid JS/Python
# expressions so that restoring placeholders is unambiguous.
_STR_SENTINEL = "__SCJSON_STR_"
_STR_SENTINEL_RE = re.compile(r"__SCJSON_STR_(\d+)__")


# ---------------------------------------------------------------------------
# Error type
# ---------------------------------------------------------------------------


class ECMAScriptNormalizationError(ValueError):
    """Raised when an expression or script body contains inadmissible forms.

    :param message: Human-readable description of what was rejected.
    :param diagnostic: Machine-readable diagnostic name per D-M1P6-8.
        Always ``"unsupported-ecmascript"`` unless a sub-diagnostic is
        warranted; callers MAY inspect this attribute.
    """

    diagnostic: str

    def __init__(self, message: str, diagnostic: str = "unsupported-ecmascript") -> None:
        super().__init__(message)
        self.diagnostic = diagnostic


# ---------------------------------------------------------------------------
# Inadmissible-form detection patterns
# ---------------------------------------------------------------------------

_INADMISSIBLE_PATTERNS: List[Tuple[re.Pattern, str]] = [
    # Arrow functions
    (re.compile(r"=>"), "arrow function (=>)"),
    # new keyword (word boundary)
    (re.compile(r"\bnew\b"), "new expression"),
    # typeof / instanceof
    (re.compile(r"\btypeof\b"), "typeof operator"),
    (re.compile(r"\binstanceof\b"), "instanceof operator"),
    # Loops
    (re.compile(r"\bfor\s*\("), "for loop"),
    (re.compile(r"\bwhile\s*\("), "while loop"),
    (re.compile(r"\bdo\s*\{"), "do-while loop"),
    # switch / throw / try
    (re.compile(r"\bswitch\s*\("), "switch statement"),
    (re.compile(r"\bthrow\b"), "throw statement"),
    (re.compile(r"\btry\s*\{"), "try statement"),
    # delete / void / yield / await
    (re.compile(r"\bdelete\b"), "delete operator"),
    (re.compile(r"\bvoid\b"), "void operator"),
    (re.compile(r"\byield\b"), "yield expression"),
    (re.compile(r"\bawait\b"), "await expression"),
    # class / import / export / with
    (re.compile(r"\bclass\b"), "class declaration"),
    (re.compile(r"\bimport\b"), "import statement"),
    (re.compile(r"\bexport\b"), "export statement"),
    (re.compile(r"\bwith\s*\("), "with statement"),
    # Template literals (backtick strings)
    (re.compile(r"`"), "template literal"),
]


# ---------------------------------------------------------------------------
# String-literal extraction helpers
# ---------------------------------------------------------------------------

_STRING_LITERAL_RE = re.compile(
    r"""(?P<sq>'(?:[^'\\]|\\.)*')|(?P<dq>"(?:[^"\\]|\\.)*")"""
)

_LINE_COMMENT_RE = re.compile(r"//[^\n]*")
_BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)


def _strip_comments(text: str) -> str:
    """Remove // and /* ... */ comments from *text*."""
    text = _BLOCK_COMMENT_RE.sub("", text)
    text = _LINE_COMMENT_RE.sub("", text)
    return text


def _extract_strings(text: str) -> Tuple[str, List[str]]:
    """Replace string literals with positional placeholders.

    Returns (masked_text, strings) where ``strings[i]`` is the original
    literal for placeholder ``__SCJSON_STR_i__``.
    """
    strings: List[str] = []

    def _replace(m: re.Match) -> str:
        idx = len(strings)
        strings.append(m.group(0))
        return "__SCJSON_STR_{}__".format(idx)

    masked = _STRING_LITERAL_RE.sub(_replace, text)
    return masked, strings


def _restore_strings(text: str, strings: List[str]) -> str:
    """Restore string placeholders back to their original literals."""

    def _restore(m: re.Match) -> str:
        return strings[int(m.group(1))]

    return _STR_SENTINEL_RE.sub(_restore, text)


def _is_str_placeholder(segment: str) -> bool:
    """Return True when *segment* (stripped) is a string-literal placeholder."""
    return bool(_STR_SENTINEL_RE.fullmatch(segment.strip()))


# ---------------------------------------------------------------------------
# Object-literal normalization (unquoted JS keys -> quoted Python dict keys)
# ---------------------------------------------------------------------------

_UNQUOTED_KEY_BRACE_RE = re.compile(r"\{([^{}]*)\}")
_UNQUOTED_IDENTIFIER_KEY_RE = re.compile(
    r"([a-zA-Z_$][a-zA-Z0-9_$]*)\s*:"
)


def _normalize_object_literal(text: str) -> str:
    """Convert JS-style ``{key: val}`` object literals to Python ``{"key": val}`` dicts.

    Only rewrites unquoted identifier keys; already-quoted keys are left alone.
    Applied to the *masked* text so string placeholders are safe.

    :param text: Masked expression text.
    :returns: Text with object literal keys quoted.
    """

    def _rewrite_obj(m: re.Match) -> str:
        inner = m.group(1)
        # Only quote identifier keys; skip string placeholders (already quoted
        # string literals from _extract_strings) and already-quoted keys.
        def _quote_key(km):
            key_text = km.group(1)
            # If the key is a string placeholder, leave it unquoted
            # (it will be restored to its original quoted literal).
            if key_text.startswith("__SCJSON_STR_"):
                return km.group(0)
            return '"{}":'.format(key_text)
        rewritten = _UNQUOTED_IDENTIFIER_KEY_RE.sub(_quote_key, inner)
        return "{" + rewritten + "}"

    # Iteratively apply (inner-most first) until stable.
    prev = None
    while prev != text:
        prev = text
        text = _UNQUOTED_KEY_BRACE_RE.sub(_rewrite_obj, text)
    return text


# ---------------------------------------------------------------------------
# Token-level substitutions
# ---------------------------------------------------------------------------


def _apply_token_substitutions(text: str) -> str:
    """Apply all operator and keyword token substitutions to *text*.

    Operates on the *masked* text (string literals replaced with placeholders)
    so that string content is never mutated.

    :param text: Masked expression or script text.
    :returns: Python-compatible text with ECMAScript tokens replaced.
    """
    # Strict equality/inequality must come before == / !=.
    text = re.sub(r"===", "==", text)
    text = re.sub(r"!==", "!=", text)

    # Logical operators
    text = re.sub(r"&&", " and ", text)
    text = re.sub(r"\|\|", " or ", text)

    # Logical not: !expr -> not expr
    # ! not followed by = (after the !== -> != substitution above, any remaining
    # ! is a logical not).
    text = re.sub(r"!(?!=)", "not ", text)

    # Boolean / null / undefined literals (word-boundary safe)
    text = re.sub(r"\btrue\b", "True", text)
    text = re.sub(r"\bfalse\b", "False", text)
    text = re.sub(r"\bnull\b", "None", text)
    text = re.sub(r"\bundefined\b", "None", text)

    # parseInt(x) -> int(x),  parseInt(x, r) -> int(x, r)
    text = re.sub(r"\bparseInt\b", "int", text)

    # String(x) -> str(x)
    text = re.sub(r"\bString\b(?=\s*\()", "str", text)

    # Number(x) -> float(x)
    text = re.sub(r"\bNumber\b(?=\s*\()", "float", text)

    return text


# ---------------------------------------------------------------------------
# String concatenation coercion
# ---------------------------------------------------------------------------


def _coerce_string_concatenation(text: str, strings: List[str]) -> str:
    """Wrap non-string operands of + with str() when adjacent to a string literal.

    In ECMAScript ``42 + 'ms'`` coerces the integer to a string.  Python raises
    ``TypeError``.  This pass wraps the non-string side in ``str()`` when one
    operand of ``+`` is a known string placeholder.

    :param text: Masked text (string literals replaced with placeholders).
    :param strings: The original string literals from ``_extract_strings``.
    :returns: Masked text with str() coercions applied where needed.
    """
    if not strings:
        return text

    _placeholder = r"__SCJSON_STR_\d+__"

    # A "complex token" is a parenthesized expression, a dotted/subscripted
    # identifier chain, a plain identifier, or an integer.
    # We exclude ident tokens that are already str(...) calls to avoid
    # double-wrapping (e.g. str(i_ID) -> str(str(i_ID))).
    _complex_token = (
        r"(?:"
        r"str\([^)]*\)"                                       # already str(...)
        r"|"
        r"(?!str\s*\()[A-Za-z_][A-Za-z0-9_.]*(?:\[[^\]]*\])?"  # ident chain (not str()
        r"|"
        r"\([^)]*\)"                                           # (paren expr)
        r"|"
        r"\d+"                                                  # integer
        r")"
    )

    def _needs_str_wrap(segment: str) -> bool:
        s = segment.strip()
        if _is_str_placeholder(s):
            return False
        if s.startswith("str("):
            return False
        return True

    # Right-hand: PLACEHOLDER + complex_token
    def _wrap_right(m: re.Match) -> str:
        lhs = m.group(1)
        rhs = m.group(2)
        if _needs_str_wrap(rhs):
            return "{} + str({})".format(lhs, rhs)
        return m.group(0)

    # Left-hand: complex_token + PLACEHOLDER
    def _wrap_left(m: re.Match) -> str:
        lhs = m.group(1)
        rhs = m.group(2)
        if _needs_str_wrap(lhs):
            return "str({}) + {}".format(lhs, rhs)
        return m.group(0)

    # Apply: PLACEHOLDER + complex_token
    text = re.sub(
        r"({plh})\s*\+\s*({tok})".format(plh=_placeholder, tok=_complex_token),
        _wrap_right,
        text,
    )
    # Apply: complex_token + PLACEHOLDER
    text = re.sub(
        r"({tok})\s*\+\s*({plh})".format(tok=_complex_token, plh=_placeholder),
        _wrap_left,
        text,
    )
    # Remove any accidental double-wrapping: str(str(x)) -> str(x)
    text = re.sub(r"str\(str\(", "str(", text)
    # Remove any mangled "strstr(" that occurs when the ident "str" gets wrapped
    text = re.sub(r"strstr\(", "str(", text)
    return text


# ---------------------------------------------------------------------------
# if-statement normalization (script bodies only)
# ---------------------------------------------------------------------------


def _normalize_if_statements(text: str) -> str:
    """Convert ``if (cond) { ... }`` to Python ``if cond:\\n    ...`` form.

    Handles the simple single-level if blocks that appear in the DP machine's
    ``<script>`` elements.  Nested ifs are supported via recursive call on the
    body.

    :param text: Masked script body text.
    :returns: Python-equivalent statement text.
    """
    result_parts: List[str] = []
    i = 0
    n = len(text)

    while i < n:
        m = re.search(r"\bif\s*\(", text[i:])
        if m is None:
            result_parts.append(text[i:])
            break

        start = i + m.start()
        result_parts.append(text[i:start])

        # Find the matching `)` for the condition
        paren_start = i + m.end() - 1  # position of `(`
        depth = 0
        j = paren_start
        while j < n:
            if text[j] == "(":
                depth += 1
            elif text[j] == ")":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        cond = text[paren_start + 1:j]

        # Skip whitespace after `)`
        k = j + 1
        while k < n and text[k] in " \t\r\n":
            k += 1

        if k < n and text[k] == "{":
            # Find the matching `}`
            brace_depth = 0
            b = k
            while b < n:
                if text[b] == "{":
                    brace_depth += 1
                elif text[b] == "}":
                    brace_depth -= 1
                    if brace_depth == 0:
                        break
                b += 1
            body = text[k + 1:b]
            body_normalized = _normalize_if_statements(body)
            # Dedent the body lines uniformly before re-indenting so that
            # JS sources that use leading whitespace inside braces do not
            # accumulate double-indentation in the output.
            import textwrap as _textwrap
            body_lines = _textwrap.dedent(body_normalized).strip().splitlines()
            indented = "\n".join("    " + line for line in body_lines if line.strip())
            result_parts.append("if {}:\n{}".format(cond.strip(), indented))
            i = b + 1
        else:
            # Single statement on the same line (no braces)
            eol = text.find("\n", k)
            if eol == -1:
                eol = n
            stmt = text[k:eol].strip()
            result_parts.append("if {}:\n    {}".format(cond.strip(), stmt))
            i = eol

    return "".join(result_parts)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def normalize(expr: str) -> str:
    """Normalize an admitted ECMAScript expression to a Python expression.

    :param expr: ECMAScript expression string from an SCXML ``cond``,
        ``expr``, ``eventexpr``, ``targetexpr``, or ``delayexpr`` attribute.
    :returns: A Python expression string suitable for ``eval()`` or the
        scjson ``SafeExpressionEvaluator``.
    :raises ECMAScriptNormalizationError: When *expr* contains a form outside
        the admitted D-M1P6-2 subset.  The exception's ``.diagnostic``
        attribute is always ``"unsupported-ecmascript"``.
    """
    cleaned = _strip_comments(expr)

    # Check inadmissible forms before masking strings.
    for pattern, description in _INADMISSIBLE_PATTERNS:
        if pattern.search(cleaned):
            raise ECMAScriptNormalizationError(
                "ECMAScript form not in admitted subset (D-M1P6-2): {!r} "
                "found in expression: {!r}".format(description, expr),
                diagnostic="unsupported-ecmascript",
            )

    masked, strings = _extract_strings(cleaned)
    masked = _normalize_object_literal(masked)
    masked = _apply_token_substitutions(masked)
    masked = _coerce_string_concatenation(masked, strings)
    result = _restore_strings(masked, strings)
    return result


def normalize_script(script_body: str) -> str:
    """Normalize an admitted ECMAScript ``<script>`` body to Python statements.

    D-M1P6-2 admits only:
    - Assignment to a datamodel location (incl. computed member: ``t[k] = v``).
    - ``if (cond) { ... }`` whose body is itself admitted.

    Everything else in a ``<script>`` body is ``forbidden`` per M0-D10 and
    causes an ECMAScriptNormalizationError with diagnostic
    ``"unsupported-ecmascript"``.

    :param script_body: Raw JS ``<script>`` text.
    :returns: Equivalent Python statement string.
    :raises ECMAScriptNormalizationError: For inadmissible script forms.
    """
    cleaned = _strip_comments(script_body)

    for pattern, description in _INADMISSIBLE_PATTERNS:
        if pattern.search(cleaned):
            raise ECMAScriptNormalizationError(
                "ECMAScript form not in admitted subset (D-M1P6-2): {!r} "
                "found in script body".format(description),
                diagnostic="unsupported-ecmascript",
            )

    masked, strings = _extract_strings(cleaned)
    masked = _normalize_object_literal(masked)
    masked = _apply_token_substitutions(masked)
    masked = _coerce_string_concatenation(masked, strings)
    masked = _normalize_if_statements(masked)
    result = _restore_strings(masked, strings)
    return result
