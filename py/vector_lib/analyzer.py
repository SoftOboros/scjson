"""
Agent Name: python-vector-analyzer

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Analyzer utilities for vector generation.

This module extracts:
- A simple event alphabet from transition ``event`` attributes
- Lightweight invoke hints
- Phase 2 payload heuristics: suggested ``_event.data`` shapes per event
  name, derived from scanning transition ``cond`` expressions for common
  patterns (truthiness, equality, numeric thresholds).
"""

from __future__ import annotations

import re
import json
from typing import Any, Dict, List, Set, Tuple

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


def _parse_literal(token: str) -> Any:
    """Parse a simple Python-like literal from a token.

    Supports single/double quoted strings, integers, floats, and
    ``True``/``False``/``None``. Returns the original token on failure.

    Parameters
    ----------
    token: str
        Raw token text to parse.

    Returns
    -------
    Any
        Parsed value or the original string if parsing fails.
    """
    t = token.strip()
    if len(t) >= 2 and ((t[0] == t[-1] == '"') or (t[0] == t[-1] == "'")):
        return t[1:-1]
    if t in {"True", "False"}:
        return t == "True"
    if t == "None":
        return None
    try:
        if "." in t:
            return float(t)
        return int(t)
    except Exception:
        return token


def _set_deep(mapping: Dict[str, Any], dotted: str, value: Any) -> None:
    """Set a nested ``mapping`` value given a dotted path.

    Parameters
    ----------
    mapping: dict
        Destination mapping to update.
    dotted: str
        Dotted key path (e.g., ``"user.id"``).
    value: Any
        Value to assign at the path.
    """
    parts = [p for p in dotted.split(".") if p]
    cur: Dict[str, Any] = mapping
    for i, part in enumerate(parts):
        if i == len(parts) - 1:
            cur[part] = value
            return
        nxt = cur.get(part)
        if not isinstance(nxt, dict):
            nxt = {}
            cur[part] = nxt
        cur = nxt


def extract_payload_heuristics(ctx: DocumentContext, max_variants: int = 3) -> Dict[str, List[Dict[str, Any]]]:
    """Infer simple event payload variants from transition conditions.

    This scans each transition ``cond`` expression for references to
    ``_event.data.<path>`` (or ``event.data.<path>``) and common comparator
    patterns, then proposes a small set of payload dictionaries for the
    associated concrete event names.

    Heuristics covered:
    - Truthiness: ``_event.data.x`` or ``not _event.data.x`` → x=True/False
    - Equality: ``_event.data.x == <literal>`` → x=<literal>
    - Inequality: ``_event.data.n >= 3`` → n=3 and n=4
    - ``is None`` and ``is not None`` → x=None and x=1

    Parameters
    ----------
    ctx : DocumentContext
        Initialized runtime context used to iterate transitions and events.

    Returns
    -------
    dict[str, list[dict]]
        Mapping from event name to a short list of payload shapes. The first
        payload aims to satisfy "positive" branches; the second flips them
        where reasonable. Payload dictionaries can be merged by the caller to
        compose per-event candidates.
    """
    hints: Dict[str, List[Dict[str, Any]]] = {}
    # Track per-event positive/negative pairs to enable one-hot fusion later
    per_event_pairs: Dict[str, List[tuple[Dict[str, Any], Dict[str, Any]]]] = {}

    # Regex to capture event.data paths and nearby comparators
    path_re = re.compile(r"(?:(?:_event|event)\.data\.)((?:[A-Za-z_][A-Za-z0-9_]*)(?:\.[A-Za-z_][A-Za-z0-9_]*)*)")

    def _record(evt: str, positive: Dict[str, Any], negative: Dict[str, Any]) -> None:
        cur = hints.setdefault(evt, [])
        # Keep variants short; append positive/negative if non-empty and not duplicates
        for variant in (positive, negative):
            if not variant:
                continue
            if variant not in cur:
                cur.append(variant)
            if len(cur) >= 3:
                break

    for sid in sorted(ctx.activations.keys(), key=ctx._activation_order_key):
        act = ctx.activations.get(sid)
        if not act:
            continue
        for trans in getattr(act, "transitions", []) or []:
            raw_events = (trans.event or "").split()
            # Skip wildcard/prefix rules; generation targets concrete names
            ev_names = [t for t in raw_events if t and t != "*" and not t.endswith(".*")]
            if not ev_names or not trans.cond:
                continue
            cond = str(trans.cond)
            # Find all event.data paths referenced in the condition
            paths = list(path_re.finditer(cond))
            if not paths:
                continue

            positive: Dict[str, Any] = {}
            negative: Dict[str, Any] = {}

            def _resolve_var(path_expr: str) -> Any:
                # Resolve dotted variable from global datamodel only (best-effort)
                cur: Any = ctx.data_model
                for part in [p for p in path_expr.split(".") if p]:
                    if isinstance(cur, dict) and part in cur:
                        cur = cur[part]
                    else:
                        return None
                return cur

            for m in paths:
                path = m.group(1)
                # Look around the match to find a comparator/value
                start, end = m.span(0)
                window = cond[max(0, start - 48) : min(len(cond), end + 48)]
                # Equality/inequality
                eq = re.search(r"==\s*([^\s\)\]\}]+|'.*?'|\".*?\")", window)
                ne = re.search(r"!=\s*([^\s\)\]\}]+|'.*?'|\".*?\")", window)
                ge = re.search(r">=\s*([0-9]+(?:\.[0-9]+)?)", window)
                le = re.search(r"<=\s*([0-9]+(?:\.[0-9]+)?)", window)
                gt = re.search(r">\s*([0-9]+(?:\.[0-9]+)?)", window)
                lt = re.search(r"<\s*([0-9]+(?:\.[0-9]+)?)", window)
                is_none = re.search(r"\bis\s+None\b", window)
                not_none = re.search(r"\bis\s+not\s+None\b", window)
                not_prefix = re.search(r"\bnot\s+(?:(?:_event|event)\.data\.)", window)
                # Membership tests
                # Forms handled:
                #   <path> [not] in [list literal]
                #   [literal] in <path> (treat path as container)
                path_expr = re.escape(m.group(0))  # full matched prefix and path
                mem_in = re.search(rf"{path_expr}\s+in\s*(\[[^\]]+\]|\([^\)]+\))", cond)
                mem_not_in = re.search(rf"{path_expr}\s+not\s+in\s*(\[[^\]]+\]|\([^\)]+\))", cond)
                rev_in = re.search(rf"('.*?'|\".*?\"|\S+)\s+in\s*{path_expr}", cond)
                rev_not_in = re.search(rf"('.*?'|\".*?\"|\S+)\s+not\s+in\s*{path_expr}", cond)
                var_in = re.search(rf"{path_expr}\s+in\s+([A-Za-z_][A-Za-z0-9_\.]+)", cond)
                var_not_in = re.search(rf"{path_expr}\s+not\s+in\s+([A-Za-z_][A-Za-z0-9_\.]+)", cond)
                mem_values: List[Any] = []
                if mem_in or mem_not_in:
                    seq_text = (mem_in or mem_not_in).group(1)
                    try:
                        # Simple safe literal eval for lists/tuples
                        if seq_text.startswith("(") and seq_text.endswith(")"):
                            raw_list = seq_text[1:-1]
                        elif seq_text.startswith("[") and seq_text.endswith("]"):
                            raw_list = seq_text[1:-1]
                        else:
                            raw_list = seq_text
                        parts = [p.strip() for p in raw_list.split(",") if p.strip()]
                        for tok in parts:
                            mem_values.append(_parse_literal(tok))
                    except Exception:
                        mem_values = []

                if eq:
                    val = _parse_literal(eq.group(1))
                    _set_deep(positive, path, val)
                    # Pick a flipped value for negative branch
                    flipped = None if val is not None else 1
                    if isinstance(val, bool):
                        flipped = not val
                    elif isinstance(val, (int, float)):
                        flipped = val + 1
                    elif isinstance(val, str):
                        flipped = val + "_x"
                    _set_deep(negative, path, flipped)
                elif ge or le or gt or lt:
                    num_s = (ge or le or gt or lt).group(1)
                    try:
                        num = float(num_s) if "." in num_s else int(num_s)
                    except Exception:
                        num = 0
                    # Satisfy threshold and flip over/under
                    _set_deep(positive, path, num)
                    _set_deep(negative, path, (num + 1) if isinstance(num, (int, float)) else 1)
                elif is_none:
                    _set_deep(positive, path, None)
                    _set_deep(negative, path, 1)
                elif not_none:
                    _set_deep(positive, path, 1)
                    _set_deep(negative, path, None)
                elif mem_in and mem_values:
                    # Choose first member as positive, a distinct value as negative
                    _set_deep(positive, path, mem_values[0])
                    flipped = None
                    for candidate in (False, True, None, 0, 1, "__none__"):
                        if candidate not in mem_values:
                            flipped = candidate
                            break
                    _set_deep(negative, path, flipped)
                elif mem_not_in and mem_values:
                    # Choose a non-member for positive, and member for negative
                    positive_val = None
                    for candidate in (False, True, None, 0, 1, "__none__"):
                        if candidate not in mem_values:
                            positive_val = candidate
                            break
                    _set_deep(positive, path, positive_val)
                    _set_deep(negative, path, mem_values[0])
                elif rev_in:
                    # Reverse orientation: literal in <path> (container)
                    lit = _parse_literal(rev_in.group(1))
                    _set_deep(positive, path, [lit])
                    _set_deep(negative, path, [])
                elif rev_not_in:
                    lit = _parse_literal(rev_not_in.group(1))
                    _set_deep(positive, path, [])
                    _set_deep(negative, path, [lit])
                elif var_in:
                    varname = var_in.group(1)
                    # Skip _event.data var; handled earlier
                    if not varname.startswith("_event.") and not varname.startswith("event."):
                        container = _resolve_var(varname)
                        if isinstance(container, (list, tuple)) and container:
                            _set_deep(positive, path, container[0])
                            flipped = None
                            for candidate in (False, True, None, 0, 1, "__none__"):
                                if candidate not in container:
                                    flipped = candidate
                                    break
                            _set_deep(negative, path, flipped)
                elif var_not_in:
                    varname = var_not_in.group(1)
                    if not varname.startswith("_event.") and not varname.startswith("event."):
                        container = _resolve_var(varname)
                        if isinstance(container, (list, tuple)) and container:
                            _set_deep(positive, path, None)
                            _set_deep(negative, path, container[0])
                else:
                    # Truthiness or negation
                    if not_prefix:
                        _set_deep(positive, path, False)
                        _set_deep(negative, path, True)
                    else:
                        _set_deep(positive, path, True)
                        _set_deep(negative, path, False)

            # Chained comparisons around the same path
            path_full = re.escape(m.group(0))
            chain = re.search(rf"([0-9]+(?:\.[0-9]+)?)\s*([<>]=?)\s*{path_full}\s*([<>]=?)\s*([0-9]+(?:\.[0-9]+)?)", cond)
            if chain:
                try:
                    left_num = float(chain.group(1))
                    right_num = float(chain.group(4))
                    mid = (left_num + right_num) / 2.0
                    pos = int(mid) if mid.is_integer() else mid
                    neg = int(right_num + 1) if right_num.is_integer() else right_num + 1.0
                    _set_deep(positive, path, pos)
                    _set_deep(negative, path, neg)
                except Exception:
                    pass
            else:
                # Try split comparisons: path > a and path < b
                try:
                    lowers = [
                        float(m2.group(2))
                        for m2 in re.finditer(rf"{path_full}\s*>\s*([0-9]+(?:\.[0-9]+)?)", cond)
                    ] + [
                        float(m2.group(1))
                        for m2 in re.finditer(rf"([0-9]+(?:\.[0-9]+)?)\s*<\s*{path_full}", cond)
                    ]
                    uppers = [
                        float(m2.group(2))
                        for m2 in re.finditer(rf"{path_full}\s*<\s*([0-9]+(?:\.[0-9]+)?)", cond)
                    ] + [
                        float(m2.group(1))
                        for m2 in re.finditer(rf"([0-9]+(?:\.[0-9]+)?)\s*>\s*{path_full}", cond)
                    ]
                    if lowers and uppers:
                        lo = max(lowers)
                        hi = min(uppers)
                        if lo < hi:
                            mid = (lo + hi) / 2.0
                            pos = int(mid) if mid.is_integer() else mid
                            neg = int(hi + 1) if hi.is_integer() else hi + 1.0
                            _set_deep(positive, path, pos)
                            _set_deep(negative, path, neg)
                except Exception:
                    pass

            for ev in ev_names:
                _record(ev, positive, negative)
                per_event_pairs.setdefault(ev, []).append((dict(positive), dict(negative)))

    # Fuse payloads across transitions for the same event to form richer shapes
    def _deep_merge(a: Dict[str, Any], b: Dict[str, Any]) -> tuple[bool, Dict[str, Any]]:
        out: Dict[str, Any] = {}
        keys = set(a.keys()) | set(b.keys())
        for k in keys:
            if k in a and k in b:
                va, vb = a[k], b[k]
                if isinstance(va, dict) and isinstance(vb, dict):
                    ok, merged = _deep_merge(va, vb)
                    if not ok:
                        return False, {}
                    out[k] = merged
                else:
                    if va != vb:
                        return False, {}
                    out[k] = va
            elif k in a:
                out[k] = a[k]
            else:
                out[k] = b[k]
        return True, out

    def _dedup(payloads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen: set[str] = set()
        out: List[Dict[str, Any]] = []
        for p in payloads:
            try:
                key = json.dumps(p, sort_keys=True)
            except Exception:
                key = str(p)
            if key in seen:
                continue
            seen.add(key)
            out.append(p)
        return out

    fused: Dict[str, List[Dict[str, Any]]] = {}
    for ev, variants in hints.items():
        base = _dedup([v for v in variants if isinstance(v, dict) and v])
        # Greedy pairwise fusion to limit combinatorics; keep up to 3
        results: List[Dict[str, Any]] = []
        # Prefer richer seeds first
        seeds = sorted(base, key=lambda d: (-len(d), json.dumps(d, sort_keys=True)))
        for i, a in enumerate(seeds):
            # Add the seed itself first
            if len(results) < 3:
                results.append(a)
            for j in range(i + 1, len(seeds)):
                b = seeds[j]
                ok, merged = _deep_merge(a, b)
                if ok:
                    results.append(merged)
                    if len(results) >= 3:
                        break
            if len(results) >= 3:
                break
        # One-hot fusion: for each condition, combine its positive with negatives of others
        one_hot: List[Dict[str, Any]] = []
        pairs = per_event_pairs.get(ev, [])
        for k, (pos_k, neg_k) in enumerate(pairs):
            payload = dict(pos_k)
            for m_idx, (pos_m, neg_m) in enumerate(pairs):
                if m_idx == k:
                    continue
                ok, merged = _deep_merge(payload, neg_m)
                if ok:
                    payload = merged
            one_hot.append(payload)

        # Prepend one-hot variants to prioritize branch-flipping sequences
        prioritized = one_hot + results
        fused[ev] = _dedup(prioritized)[:max(1, int(max_variants))] if prioritized else base[:max(1, int(max_variants))]

    return fused
