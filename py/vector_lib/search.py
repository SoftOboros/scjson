"""
Agent Name: python-vector-search

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Coverage-guided vector search (bounded) for SCXML charts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, List, Sequence, Tuple

from scjson.context import DocumentContext, ExecutionMode
from scjson.events import Event
from .coverage import CoverageTracker


CtxFactory = Callable[[], DocumentContext]


def _simulate(ctx: DocumentContext, seq: Sequence[str]) -> CoverageTracker:
    """Run ``seq`` through context ``ctx`` and compute coverage."""
    cov = CoverageTracker()
    for name in seq:
        trace = ctx.trace_step(Event(name=name))
        cov.add_step(trace)
    return cov


def generate_sequences(
    ctx_factory: CtxFactory,
    alphabet: Sequence[str],
    *,
    max_depth: int = 2,
    limit: int = 1,
) -> List[List[str]]:
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

    best: List[Tuple[int, List[str]]] = []
    frontier: List[List[str]] = [[]]
    seen: set[Tuple[str, ...]] = set()

    while frontier:
        seq = frontier.pop(0)
        if len(seq) >= max_depth:
            continue
        for ev in alphabet:
            cand = seq + [ev]
            key = tuple(cand)
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

    # Sort best by coverage score desc, then by length asc
    best.sort(key=lambda x: (-x[0], len(x[1]), x[1]))
    # Deduplicate by sequence key retaining order
    out: List[List[str]] = []
    used: set[Tuple[str, ...]] = set()
    for _, seq in best:
        key = tuple(seq)
        if key in used:
            continue
        used.add(key)
        out.append(seq)
        if len(out) >= max(limit, 1):
            break
    return out or [[]]

