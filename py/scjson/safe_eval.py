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
import math
from typing import Any, Dict, Iterable, Mapping, Sequence

try:  # pragma: no cover - exercised in environments with sandbox extras
    # Prefer the in-repo managed sandbox package name
    from py_sandboxed import SandboxViolation  # type: ignore
    from py_sandboxed.sandbox import (  # type: ignore
        _prepare_modules,
        filter_globals,
        guard_code,
    )
except Exception:  # pragma: no cover - simplified sandbox fallback
    import ast
    import fnmatch

    class SandboxViolation(RuntimeError):
        """Raised when the fallback sandbox detects an unsafe construct."""

    _SANDBOX_MODULES = {"math": math}

    def _matches(name: str, patterns: Sequence[str]) -> bool:
        for pattern in patterns:
            if not pattern:
                continue
            if pattern.endswith(".*"):
                root = pattern[:-2]
                if name == root or name.startswith(root + "."):
                    return True
            if fnmatch.fnmatchcase(name, pattern):
                return True
        return False

    def _is_allowed(name: str, rules: Mapping[str, Any]) -> bool:
        allow: Sequence[str] = tuple(rules.get("allow", []))
        deny: Sequence[str] = tuple(rules.get("deny", []))
        block_dunder = bool(rules.get("block_dunder"))
        if block_dunder and name.startswith("__"):
            return False
        if deny and _matches(name, deny):
            return False
        if not allow:
            return True
        return _matches(name, allow)

    def filter_globals(source: Mapping[str, Any], rules: Mapping[str, Any]) -> Dict[str, Any]:
        safe: Dict[str, Any] = {}
        for name, value in source.items():
            if _is_allowed(name, rules):
                safe[name] = value
        return safe

    def _prepare_modules(rules: Mapping[str, Any]) -> Dict[str, Any]:
        safe: Dict[str, Any] = {}
        for name, module in _SANDBOX_MODULES.items():
            if _is_allowed(name, rules):
                safe[name] = module
        return safe

    def guard_code(expr: str, rules: Mapping[str, Any]) -> None:
        if not expr:
            raise SandboxViolation("Expression is empty")
        try:
            tree = ast.parse(expr, mode="eval")
        except SyntaxError as exc:
            raise SandboxViolation(str(exc)) from exc

        deny: Sequence[str] = tuple(rules.get("deny", []))
        block_dunder = bool(rules.get("block_dunder"))
        block_import = bool(rules.get("block_import"))

        class _Visitor(ast.NodeVisitor):
            def visit_Name(self, node: ast.Name) -> None:  # noqa: D401
                if block_dunder and node.id.startswith("__"):
                    raise SandboxViolation("Double underscore names are restricted")
                self.generic_visit(node)

            def visit_Attribute(self, node: ast.Attribute) -> None:  # noqa: D401
                if block_dunder and getattr(node, "attr", "").startswith("__"):
                    raise SandboxViolation("Double underscore attribute access is restricted")
                self.generic_visit(node)

            def visit_Call(self, node: ast.Call) -> None:  # noqa: D401
                func = node.func
                name: str | None = None
                if isinstance(func, ast.Name):
                    name = func.id
                elif isinstance(func, ast.Attribute):
                    name = func.attr
                if name and deny and _matches(name, deny):
                    raise SandboxViolation(f"Call to disallowed name '{name}'")
                if block_dunder and name and name.startswith("__"):
                    raise SandboxViolation("Double underscore call targets are restricted")
                self.generic_visit(node)

            def visit_Import(self, node: ast.Import) -> None:  # noqa: D401
                if block_import:
                    raise SandboxViolation("Import statements are not permitted")
                self.generic_visit(node)

            def visit_ImportFrom(self, node: ast.ImportFrom) -> None:  # noqa: D401
                if block_import:
                    raise SandboxViolation("Import statements are not permitted")
                self.generic_visit(node)

        _Visitor().visit(tree)

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
