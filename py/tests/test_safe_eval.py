"""
Agent Name: python-safe-eval-tests

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.
"""

from decimal import Decimal

from scjson.context import DocumentContext
from scjson.pydantic import Data, Datamodel, Scxml, State
from scjson.safe_eval import SafeEvaluationError, SafeExpressionEvaluator


def test_safe_evaluator_basic_math() -> None:
    """Ensure basic arithmetic works in the sandbox."""
    evaluator = SafeExpressionEvaluator()
    assert evaluator.evaluate("1 + 2 * 3", {}) == 7


def test_safe_evaluator_env_access() -> None:
    """Variables supplied via ``env`` must be available."""
    evaluator = SafeExpressionEvaluator()
    assert evaluator.evaluate("value + 1", {"value": 4}) == 5


def test_safe_evaluator_blocks_imports() -> None:
    """Attempting to import should raise a sandbox violation."""
    evaluator = SafeExpressionEvaluator()
    try:
        evaluator.evaluate("__import__('os')", {})
    except SafeEvaluationError:
        pass
    else:  # pragma: no cover - sanity guard
        raise AssertionError("unsafe import was permitted")


def test_assign_falls_back_when_sandbox_blocks() -> None:
    """Assignments with disallowed expressions fall back to the raw string."""
    doc = Scxml(
        id="root",
        datamodel=[Datamodel(data=[Data(id="danger", expr="0")])],
        initial=["s"],
        state=[
            State(
                id="s",
                onentry=[{"assign": [{"location": "danger", "expr": "__import__('os')"}]}],
            )
        ],
        version=Decimal("1.0"),
    )
    ctx = DocumentContext.from_doc(doc)
    assert ctx.data_model["danger"] == "__import__('os')"
