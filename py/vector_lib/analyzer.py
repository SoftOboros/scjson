"""
Agent Name: python-vector-analyzer

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Analyzer for extracting a simple event alphabet and hints from a chart.
"""

from __future__ import annotations

from typing import Dict, List, Set, Tuple

from scjson.context import DocumentContext


def extract_event_alphabet(ctx: DocumentContext) -> List[str]:
    """Extract a de-duplicated, ordered event alphabet from transitions.

    Parameters
    ----------
    ctx : DocumentContext
        Initialized context containing the activation graph and transitions.

    Returns
    -------
    list[str]
        Event names discovered in document order; ignores wildcard tokens and
        empty strings.
    """

    seen: Set[str] = set()
    ordered: List[str] = []
    for sid in sorted(ctx.activations.keys(), key=ctx._activation_order_key):
        act = ctx.activations.get(sid)
        if not act:
            continue
        for trans in getattr(act, "transitions", []) or []:
            raw = trans.event or ""
            for token in (t.strip() for t in raw.split() if t.strip()):
                # Skip wildcard/prefix patterns for generation; generator only
                # emits concrete event names.
                if token == "*" or token.endswith(".*"):
                    continue
                if token not in seen:
                    seen.add(token)
                    ordered.append(token)
    return ordered


def extract_invoke_hints(ctx: DocumentContext) -> Dict[str, bool]:
    """Return simple invocation hints.

    Parameters
    ----------
    ctx : DocumentContext
        Initialized chart context.

    Returns
    -------
    dict
        Mapping of hint flags:
        - ``has_deferred``: True if an invocation with type mock:deferred is present.
    """
    has_deferred = False
    for sid, act in ctx.activations.items():
        for inv in getattr(act, "invokes", []) or []:
            t = (getattr(inv, "type_value", None) or "").strip().lower()
            if t == "mock:deferred":
                has_deferred = True
                break
        if has_deferred:
            break
    return {"has_deferred": has_deferred}

