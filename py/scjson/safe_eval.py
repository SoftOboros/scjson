"""
Agent Name: python-safe-evaluator

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Deterministic and side-effect free expression evaluation utilities used by the
runtime engine.
"""

from __future__ import annotations

import builtins
from typing import Any, Dict, Iterable, Mapping, Sequence

try:
    # Prefer the in-repo managed sandbox package name
    from py_sandboxed import SandboxViolation  # type: ignore
    from py_sandboxed.sandbox import _prepare_modules, filter_globals, guard_code  # type: ignore
except Exception:  # pragma: no cover - fallback for alternate import name
    from py_sandboxer import SandboxViolation
    from py_sandboxer.sandbox import _prepare_modules, filter_globals, guard_code

__all__ = ["SafeEvaluationError", "SafeExpressionEvaluator"]


_DEFAULT_ALLOW_PATTERNS: Sequence[str] = (
    "True",
    "False",
    "None",
    "abs",
    "all",
    "any",
    "bool",
    "dict",
    "divmod",
    "enumerate",
    "filter",
    "float",
    "int",
    "len",
    "list",
    "map",
    "max",
    "min",
    "next",
    "pow",
    "range",
    "repr",
    "round",
    "set",
    "sorted",
    "str",
    "sum",
    "tuple",
    "zip",
    "math.*",
)

_DEFAULT_DENY_PATTERNS: Sequence[str] = ("__import__",)


class SafeEvaluationError(RuntimeError):
    """Raised when an expression attempts an unsafe operation."""


class SafeExpressionEvaluator:
    """Evaluate SCXML datamodel expressions within a sandboxed environment.

    Parameters
    ----------
    allow_patterns:
        Optional iterable of glob-style patterns for builtin names exposed to
        the expression. Patterns supplement the default safe allow list.
    deny_patterns:
        Optional iterable of glob-style patterns that should be explicitly
        blocked in addition to the defaults.
    """

    def __init__(
        self,
        *,
        allow_patterns: Iterable[str] | None = None,
        deny_patterns: Iterable[str] | None = None,
    ) -> None:
        default_allow = set(_DEFAULT_ALLOW_PATTERNS)
        if allow_patterns:
            default_allow.update(allow_patterns)
        self._allow_patterns = tuple(sorted(default_allow))

        default_deny = set(_DEFAULT_DENY_PATTERNS)
        if deny_patterns:
            default_deny.update(deny_patterns)
        self._deny_patterns = tuple(sorted(default_deny))

    def evaluate(
        self,
        expr: str,
        env: Mapping[str, Any],
        *,
        extra_globals: Mapping[str, Any] | None = None,
    ) -> Any:
        """Evaluate ``expr`` using sandboxed semantics.

        Parameters
        ----------
        expr:
            Expression string to evaluate.
        env:
            Mapping of variable names to values exposed as locals during
            evaluation.
        extra_globals:
            Optional mapping of helper callables injected as additional globals.

        Returns
        -------
        Any
            Result of evaluating ``expr``.

        Raises
        ------
        SafeEvaluationError
            If the expression violates sandbox policies or triggers a runtime
            error.
        """

        if not expr:
            raise SafeEvaluationError("Expression is empty")

        rules = {
            "allow": list(self._allow_patterns),
            "deny": list(self._deny_patterns),
            "block_import": True,
            "block_dunder": True,
        }
        try:
            guard_code(expr, rules)
        except SandboxViolation as exc:  # pragma: no cover - guard failures
            raise SafeEvaluationError(str(exc)) from exc

        safe_globals: Dict[str, Any] = filter_globals(vars(builtins), rules)
        safe_globals.update(_prepare_modules(rules))

        if extra_globals:
            for name in extra_globals:
                if name.startswith("__"):
                    raise SafeEvaluationError(
                        "Global helpers must not begin with double underscore"
                    )
            safe_globals.update(extra_globals)

        locals_ns = dict(env)
        try:
            return eval(expr, {"__builtins__": safe_globals}, locals_ns)
        except SandboxViolation as exc:  # pragma: no cover - wrapped immediately
            raise SafeEvaluationError(str(exc)) from exc
        except Exception as exc:  # noqa: BLE001
            raise SafeEvaluationError(str(exc)) from exc
