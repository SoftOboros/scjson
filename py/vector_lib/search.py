"""
Agent Name: python-vector-search

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Coverage-guided vector search (bounded) for SCXML charts.

Phase 2 extends the alphabet to support data-bearing stimuli: each symbol in
the alphabet can be either a plain event name (``str``) or a mapping with
``{"event": name, "data": payload}`` (or ``{"name": name, "data": ...}``).

Phase 3 (EXEC-E-D1..D4) adds a candidate-count cap (``max_candidates``) and a
wall-clock budget (``time_budget_ms``) to guarantee termination on large
machines.  Charts containing ``<parallel>`` and/or ``<invoke>`` elements
receive a construct-aware depth/alphabet reduction (EXEC-E-D2).  When the
budget is exhausted the search returns partial results with ``truncated=True``
(EXEC-E-D4).
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, List, Optional, Sequence, Tuple

from scjson.context import DocumentContext, ExecutionMode
from scjson.events import Event
from .coverage import CoverageTracker
import json


logger = logging.getLogger(__name__)

CtxFactory = Callable[[], DocumentContext]


@dataclass
class SearchResult:
    """Result returned by ``generate_sequences``.

    Attributes
    ----------
    sequences : list[list[Any]]
        Ordered list of sequences (descending coverage, then length asc, then
        stable repr tiebreak).  Always non-empty: contains at least ``[[]]``
        when the alphabet is empty or the budget triggers immediately.
    truncated : bool
        ``True`` when the ``while frontier:`` loop was terminated early because
        ``max_candidates`` was reached or ``time_budget_ms`` elapsed
        (EXEC-E-D4).  Callers MUST propagate this flag as a ``limited``
        terminal outcome rather than treating the result as a full-coverage
        success.
    candidates_evaluated : int
        Number of BFS candidates evaluated before the search stopped.
    elapsed_ms : float
        Wall-clock time spent inside ``generate_sequences``, in milliseconds.
    """

    sequences: List[List[Any]]
    truncated: bool = False
    candidates_evaluated: int = 0
    elapsed_ms: float = 0.0


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


def _detect_complex_constructs(ctx_factory: CtxFactory) -> Tuple[bool, bool]:
    """Detect whether the chart contains ``<parallel>`` and/or ``<invoke>``.

    Called once before the BFS loop.  Returns ``(has_parallel, has_invoke)``.
    Detection is static (reads ``ctx.doc`` and ``ctx.activations``); it does
    not drive any state transitions, so it cannot block.

    Parameters
    ----------
    ctx_factory : CtxFactory
        Factory for a fresh DocumentContext.

    Returns
    -------
    tuple[bool, bool]
        ``(has_parallel, has_invoke)``
    """
    try:
        ctx = ctx_factory()
        has_parallel = bool(getattr(ctx.doc, "parallel", None))
        has_invoke = False
        for _sid, act in ctx.activations.items():
            if getattr(act, "invokes", None):
                has_invoke = True
                break
        return has_parallel, has_invoke
    except Exception:
        # If detection itself fails, default to conservative treatment
        return False, False


def generate_sequences(
    ctx_factory: CtxFactory,
    alphabet: Sequence[Any],
    *,
    max_depth: int = 2,
    limit: int = 1,
    max_candidates: int = 2000,
    time_budget_ms: int = 30000,
) -> SearchResult:
    """Generate up to ``limit`` sequences using BFS with coverage pruning.

    The search is bounded by both a candidate-count cap and a wall-clock
    budget (EXEC-E-D1).  When either limit is reached the loop exits and
    returns a ``SearchResult`` with ``truncated=True`` (EXEC-E-D4).  Charts
    containing ``<parallel>`` or ``<invoke>`` elements receive a
    construct-aware reduction: effective depth is capped at
    ``min(max_depth, 2)`` and only top-level transition events are used as the
    stimulus alphabet (EXEC-E-D2).

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
    max_candidates : int
        Maximum cumulative frontier entries to evaluate before stopping.
        Checked at the top of the ``while frontier:`` loop, before popping.
        Default: 2000 (EXEC-E-D1 Standards Action).
    time_budget_ms : int
        Wall-clock budget in milliseconds measured from function entry.
        Checked immediately after the ``max_candidates`` check.
        Default: 30000 (30 s) (EXEC-E-D1 Standards Action).

    Returns
    -------
    SearchResult
        ``sequences``: list ordered by descending coverage, then length asc,
        then stable repr tiebreak.  Always has at least one entry (``[[]]``
        when alphabet is empty or budget fires immediately).
        ``truncated``: ``True`` when budget or candidate cap was hit.
    """

    if not alphabet:
        return SearchResult(sequences=[[]], truncated=False)

    # EXEC-E-D2: Construct-aware reduction.
    # When the chart contains <parallel> and/or <invoke>, the per-candidate
    # ctx_factory() cost is O(parallel-regions × inline-invoke-child-machine-
    # init), making depth > 2 effectively non-terminating on complex machines
    # (ERRATA-002 root cause).  Cap effective depth at min(max_depth, 2) and
    # restrict the search alphabet to the top-level transition events already
    # in `alphabet` (which extract_event_alphabet already provides in
    # document order — no further reduction is needed here beyond depth).
    # This reduction is applied statically before the loop.
    has_parallel, has_invoke = _detect_complex_constructs(ctx_factory)
    effective_depth = max_depth
    if has_parallel or has_invoke:
        effective_depth = min(max_depth, 2)
        if effective_depth < max_depth:
            logger.debug(
                "EXEC-E-D2 construct-aware reduction: chart has parallel=%s invoke=%s; "
                "capping effective depth %d -> %d (max_candidates=%d, time_budget_ms=%d)",
                has_parallel,
                has_invoke,
                max_depth,
                effective_depth,
                max_candidates,
                time_budget_ms,
            )

    best: List[Tuple[int, List[Any]]] = []
    frontier: List[List[Any]] = [[]]
    seen: set[Tuple[Any, ...]] = set()
    candidates_evaluated = 0
    truncated = False

    # EXEC-E-D1: Record entry time for wall-clock budget.
    t_start = time.monotonic()

    while frontier:
        # EXEC-E-D1: Check candidate-count cap before popping.
        if candidates_evaluated >= max_candidates:
            logger.warning(
                "EXEC-E-D1 budget: max_candidates=%d reached after %.1f ms; "
                "returning %d partial sequences (truncated)",
                max_candidates,
                (time.monotonic() - t_start) * 1000,
                len(best),
            )
            truncated = True
            break
        # EXEC-E-D1: Check wall-clock budget immediately after candidate cap.
        elapsed_ms = (time.monotonic() - t_start) * 1000
        if elapsed_ms >= time_budget_ms:
            logger.warning(
                "EXEC-E-D1 budget: time_budget_ms=%d ms elapsed (%.1f ms actual); "
                "returning %d partial sequences (truncated)",
                time_budget_ms,
                elapsed_ms,
                len(best),
            )
            truncated = True
            break

        seq = frontier.pop(0)
        if len(seq) >= effective_depth:
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
            candidates_evaluated += 1
            ctx = ctx_factory()
            cov = _simulate(ctx, cand)
            score = cov.size()
            best.append((score, cand))
            # Keep frontier breadth-limited: expand new candidate if it added anything.
            if score > 0:
                frontier.append(cand)

    elapsed_ms = (time.monotonic() - t_start) * 1000

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

    # EXEC-E-D3 (memoization): TODO — ctx_factory memoization by sequence-prefix
    # is deferred per spec (optional for first EXEC-E landing; MUST land before
    # the EXEC-E-D2 depth cap is relaxed for parallel-only charts).  The
    # candidate-count + wall-clock budget (EXEC-E-D1) is the primary safety net.
    # Reference: SCJSON-EXEC-00-CONCEPTS.md §EXEC-E-D3 (Specification Required).

    return SearchResult(
        sequences=out or [[]],
        truncated=truncated,
        candidates_evaluated=candidates_evaluated,
        elapsed_ms=elapsed_ms,
    )
