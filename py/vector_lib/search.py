"""
Agent Name: python-vector-search

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Coverage-guided vector search (bounded) for SCXML charts.

Phase 2 extends the alphabet to support data-bearing stimuli: each symbol in
the alphabet can be either a plain event name (``str``) or a mapping with
``{"event": name, "data": payload}`` (or ``{"name": name, "data": ...}``).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable, List, Sequence, Tuple

from scjson.context import DocumentContext, ExecutionMode
from scjson.events import Event
from .coverage import CoverageTracker
import json


CtxFactory = Callable[[], DocumentContext]


def _simulate(ctx: DocumentContext, seq: Sequence[Any]) -> CoverageTracker:
    """Run ``seq`` through context ``ctx`` and compute coverage.

    Sequence items can be:
    - ``str``: event name, no payload
    - ``dict``: keys ``event|name`` (required) and optional ``data``
    """
    cov = CoverageTracker()
    for item in seq:
        if isinstance(item, dict):
            name = item.get("event") or item.get("name")
            data = item.get("data") if "data" in item else None
        else:
            name = str(item)
            data = None
        trace = ctx.trace_step(Event(name=name, data=data))
        cov.add_step(trace)
    return cov


def generate_sequences(
    ctx_factory: CtxFactory,
    alphabet: Sequence[Any],
    *,
    max_depth: int = 2,
    limit: int = 1,
) -> List[List[Any]]:
    """Generate up to ``limit`` sequences using BFS with coverage pruning.

    Parameters
    ----------
    ctx_factory : Callable[[], DocumentContext]
        Factory to create a fresh context per simulation.
    alphabet : Sequence[str]
        Candidate event names to append when expanding sequences.
    max_depth : int
        Maximum sequence length to explore.
    limit : int
        Maximum number of sequences to return.

    Returns
    -------
    list[list[str]]
        Sequences ordered by descending coverage size and stable tiebreak.
    """

    if not alphabet:
        return [[]]

    best: List[Tuple[int, List[Any]]] = []
    frontier: List[List[Any]] = [[]]
    seen: set[Tuple[Any, ...]] = set()

    while frontier:
        seq = frontier.pop(0)
        if len(seq) >= max_depth:
            continue
        for ev in alphabet:
            cand = seq + [ev]
            # Stabilize dict stimuli for dedup keys
            def _key_of(x: Any) -> Any:
                return json.dumps(x, sort_keys=True) if isinstance(x, dict) else x
            key = tuple(_key_of(x) for x in cand)
            if key in seen:
                continue
            seen.add(key)
            ctx = ctx_factory()
            cov = _simulate(ctx, cand)
            score = cov.size()
            best.append((score, cand))
            # Keep frontier breadth-limited: expand new candidate if it added anything.
            if score > 0:
                frontier.append(cand)

    # Sort best by coverage score desc, then by length asc, then by stable repr
    def _stable_key(seq: List[Any]) -> str:
        return ",".join(
            json.dumps(item, sort_keys=True) if isinstance(item, dict) else str(item)
            for item in seq
        )
    best.sort(key=lambda x: (-x[0], len(x[1]), _stable_key(x[1])))
    # Deduplicate by sequence key retaining order
    out: List[List[Any]] = []
    used: set[Tuple[Any, ...]] = set()
    for _, seq in best:
        def _key_of(x: Any) -> Any:
            return json.dumps(x, sort_keys=True) if isinstance(x, dict) else x
        key = tuple(_key_of(x) for x in seq)
        if key in used:
            continue
        used.add(key)
        out.append(seq)
        if len(out) >= max(limit, 1):
            break
    return out or [[]]
