"""
Agent Name: python-vector-gen

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Vector generator with coverage-guided search.

Phase 1 implemented alphabet extraction and depth-limited BFS. Phase 2 adds
payload heuristics derived from transition conditions and auto-detection of
delayed sends during initialization to choose a recommended ``advance_time``.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Iterable, List, Set

from scjson.context import DocumentContext, ExecutionMode
from scjson.events import Event
from vector_lib.analyzer import (
    extract_event_alphabet,
    extract_invoke_hints,
    extract_payload_heuristics,
)
from vector_lib.search import generate_sequences
from vector_lib.coverage import CoverageTracker
import json


def _ctx_factory(chart: Path, treat_as_xml: bool, advance_time: float) -> callable:
    """Return a factory that creates a fresh context for the chart."""

    def make() -> DocumentContext:
        mode = ExecutionMode.LAX if treat_as_xml else ExecutionMode.STRICT
        ctx = (
            DocumentContext.from_xml_file(chart, execution_mode=mode)
            if treat_as_xml
            else DocumentContext.from_json_file(chart, execution_mode=mode)
        )
        if advance_time and advance_time > 0:
            ctx.advance_time(advance_time)
        return ctx

    return make


def _simulate_sequence(ctx: DocumentContext, seq: list[Any]) -> CoverageTracker:
    """Simulate a sequence of stimuli against the given context.

    Parameters
    ----------
    ctx: DocumentContext
        Initialized runtime context.
    seq: list[Any]
        Sequence of event names (str) or objects with ``event|name`` and ``data``.

    Returns
    -------
    CoverageTracker
        Accumulated coverage across the sequence.
    """
    cov = CoverageTracker()
    for ev in seq:
        if isinstance(ev, dict):
            name = ev.get("event") or ev.get("name")
            data = ev.get("data") if "data" in ev else None
        else:
            name = str(ev)
            data = None
        trace = ctx.trace_step(Event(name=str(name), data=data))
        cov.add_step(trace)
    return cov


def _minimize_sequence(ctx_factory: callable, seq: list[Any]) -> list[Any]:
    """Greedily remove events that do not increase coverage.

    Parameters
    ----------
    ctx_factory: callable
        Factory creating a fresh DocumentContext.
    seq: list[Any]
        Candidate sequence to minimize.

    Returns
    -------
    list[Any]
        Minimized sequence with equal coverage size.
    """
    if not seq:
        return seq
    base_cov = _simulate_sequence(ctx_factory(), seq)
    base_size = base_cov.size()
    out = list(seq)
    i = len(out) - 1
    while i >= 0 and len(out) > 1:
        cand = out[:i] + out[i + 1 :]
        cov = _simulate_sequence(ctx_factory(), cand)
        # Preserve exact coverage sets
        equal_sets = (
            cov.entered_states == base_cov.entered_states
            and cov.fired_transitions == base_cov.fired_transitions
            and cov.done_events == base_cov.done_events
            and cov.error_events == base_cov.error_events
        )
        if equal_sets and cov.size() >= base_size:
            out = cand
            base_cov = cov
            base_size = cov.size()
        i -= 1
    return out


def generate_vectors(
    chart: Path,
    *,
    treat_as_xml: bool,
    out_dir: Path,
    max_depth: int = 1,
    advance_time: float = 0.0,
    limit: int = 1,
    auto_advance: bool = True,
    variants_per_event: int = 3,
) -> Path:
    """Generate minimal vectors for ``chart`` and write to ``out_dir``.

    Parameters
    ----------
    chart : Path
        Path to SCXML or SCJSON chart.
    treat_as_xml : bool
        When ``True``, parse as SCXML; otherwise treat input as SCJSON.
    out_dir : Path
        Destination directory for emitted vector files.
    max_depth : int
        Maximum sequence depth (events per vector); Phase 1 uses depth 1.
    advance_time : float
        Optional time advancement prior to starting the sequence (for delayed
        sends scheduled during init).
    limit : int
        Maximum number of vectors to emit; Phase 1 uses a single vector.

    Returns
    -------
    Path
        Path to the emitted ``.events.jsonl`` file.
    """

    out_dir.mkdir(parents=True, exist_ok=True)
    execution_mode = ExecutionMode.LAX if treat_as_xml else ExecutionMode.STRICT
    ctx = (
        DocumentContext.from_xml_file(chart, execution_mode=execution_mode)
        if treat_as_xml
        else DocumentContext.from_json_file(chart, execution_mode=execution_mode)
    )
    # Auto-detect initial delayed sends when no explicit advance_time provided
    used_advance = advance_time or 0.0
    if (not advance_time or advance_time <= 0) and auto_advance:
        try:
            now = float(getattr(ctx, "_timer_now", 0.0))
            deltas = [float(due) - now for (due, _evt) in getattr(ctx, "delayed_events", [])]
            if deltas:
                # Pick the earliest due and step slightly beyond
                min_delta = max(0.0, min(deltas))
                used_advance = max(used_advance, float(min_delta) + 1e-6)
        except Exception:
            pass
    if used_advance and used_advance > 0:
        try:
            ctx.advance_time(used_advance)
        except Exception:
            pass

    alphabet = extract_event_alphabet(ctx)
    hints = extract_invoke_hints(ctx)
    payload_hints = extract_payload_heuristics(ctx, max_variants=max(1, int(variants_per_event)))
    # Include a generic "complete" stimulus when a deferred invocation is present.
    if hints.get("has_deferred") and "complete" not in alphabet:
        alphabet = list(alphabet) + ["complete"]
    # Phase 1: generate sequences from alphabet only.
    # Build stimuli alphabet: include heuristically suggested payload shapes
    stimuli: List[Any] = []
    seen_stim: Set[str] = set()
    for name in alphabet:
        # Always include a bare event symbol (no payload)
        base = {"event": name}
        key = json.dumps(base, sort_keys=True)
        if key not in seen_stim:
            stimuli.append(base)
            seen_stim.add(key)
        for payload in payload_hints.get(name, [])[: max(1, int(variants_per_event))]:
            item = {"event": name, "data": payload}
            k = json.dumps(item, sort_keys=True)
            if k in seen_stim:
                continue
            seen_stim.add(k)
            stimuli.append(item)
    # Include a generic "complete" stimulus when a deferred invocation is present.
    if hints.get("has_deferred") and not any(
        (isinstance(s, dict) and s.get("event") == "complete") or s == "complete" for s in stimuli
    ):
        stimuli.append({"event": "complete"})

    sequences = generate_sequences(
        _ctx_factory(chart, treat_as_xml, used_advance),
        stimuli,
        max_depth=max_depth,
        limit=limit,
    )

    dest = out_dir / f"{chart.stem}.events.jsonl"
    # Emit only the top sequence for now (aligns with exec_compare consumption)
    top = sequences[0] if sequences else []
    # Minimize sequence greedily for more compact vectors
    try:
        top = _minimize_sequence(_ctx_factory(chart, treat_as_xml, used_advance), list(top))
    except Exception:
        pass
    # Optionally inject per-step time advances when delayed sends are detected
    # after initialization so timers are released before the next stimulus.
    try:
        def _inject_advances(seq: list[Any]) -> list[Any]:
            ctx = _ctx_factory(chart, treat_as_xml, used_advance)()
            out_seq: list[Any] = []
            epsilon = 1e-6
            for item in seq:
                # Append the external stimulus and simulate it
                out_seq.append(item)
                name = item.get("event") if isinstance(item, dict) else str(item)
                data = item.get("data") if isinstance(item, dict) and ("data" in item) else None
                trace = ctx.trace_step(Event(name=str(name), data=data))
                # If any delayed events are scheduled, advance time just past
                # the earliest due so they will be released before the next
                # external stimulus.
                try:
                    now = float(getattr(ctx, "_timer_now", 0.0))
                    deltas = [float(due) - now for (due, _evt) in getattr(ctx, "delayed_events", [])]
                    if deltas:
                        delta = max(0.0, min(deltas)) + epsilon
                        # Apply to runtime so subsequent simulation matches
                        ctx.advance_time(delta)
                        # Record control token for the CLI runner; reference
                        # engines ignore it since it lacks an 'event' field.
                        out_seq.append({"advance_time": float(delta)})
                except Exception:
                    # Ignore if timer inspection fails
                    pass
            return out_seq
        top = _inject_advances(list(top))
    except Exception:
        pass
    with dest.open("w", encoding="utf-8") as fh:
        for ev in top:
            if isinstance(ev, dict):
                # Control token: advance_time
                if "advance_time" in ev and (isinstance(ev["advance_time"], (int, float))):
                    fh.write(json.dumps({"advance_time": float(ev["advance_time"])}) + "\n")
                else:
                    name = ev.get("event") or ev.get("name")
                    data = ev.get("data") if "data" in ev else None
                    obj: dict[str, Any] = {"event": str(name)}
                    if data is not None:
                        obj["data"] = data
                    fh.write(json.dumps(obj) + "\n")
            else:
                fh.write(json.dumps({"event": str(ev)}) + "\n")
    # Emit a coverage summary sidecar for sweeps/reporting
    try:
        ctx2 = _ctx_factory(chart, treat_as_xml, used_advance)()
        cov = CoverageTracker()
        for ev in top:
            if isinstance(ev, dict):
                name = ev.get("event") or ev.get("name")
                data = ev.get("data") if "data" in ev else None
            else:
                name = str(ev)
                data = None
            trace = ctx2.trace_step(Event(name=str(name), data=data))
            cov.add_step(trace)
        cov_path = out_dir / f"{chart.stem}.coverage.json"
        summary = cov.summary()
        cov_path.write_text(json.dumps(summary, indent=2))
        # Emit vector meta with recommended advance time for consumers
        meta = {
            "advanceTime": used_advance,
            "alphabet": alphabet,
            "payloadHints": {k: len(v) for k, v in payload_hints.items()},
            "sequenceLength": len(top),
        }
        (out_dir / f"{chart.stem}.vector.json").write_text(json.dumps(meta, indent=2))
    except Exception:
        pass
    return dest


def main() -> None:
    """CLI entry point for vector generation.

    Usage: python py/vector_gen.py <chart> [--xml] --out <dir> [--max-depth N]
    """

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("chart", type=Path, help="Path to SCXML/SCJSON chart")
    ap.add_argument("--xml", action="store_true", help="Treat chart as SCXML")
    ap.add_argument("--out", type=Path, required=True, help="Output directory")
    ap.add_argument("--max-depth", type=int, default=1, help="Max events per vector")
    ap.add_argument("--advance-time", type=float, default=0.0, help="Advance time before generating (overrides auto-detect)")
    ap.add_argument("--no-auto-advance", action="store_true", help="Disable auto-detection of delayed sends during init")
    ap.add_argument("--variants-per-event", type=int, default=3, help="Max fused payload variants to consider per event")
    ap.add_argument("--limit", type=int, default=1, help="Maximum vectors to emit")
    args = ap.parse_args()

    path = generate_vectors(
        args.chart,
        treat_as_xml=args.xml,
        out_dir=args.out,
        max_depth=args.max_depth,
        advance_time=args.advance_time,
        limit=args.limit,
        auto_advance=not args.no_auto_advance,
        variants_per_event=args.variants_per_event,
    )
    print(str(path))


if __name__ == "__main__":
    main()
