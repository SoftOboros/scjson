"""
Agent Name: python-vector-gen

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Simple event vector generator (Phase 1 stub).

This tool analyzes a chart to extract an event alphabet from transition
definitions, then emits minimal JSONL event sequences (vectors) intended to
increase behavioral coverage when driving the engine. Coverage accounting and
search are intentionally lightweight in this initial phase.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, List, Set

from scjson.context import DocumentContext, ExecutionMode
from scjson.events import Event
from vector_lib.analyzer import extract_event_alphabet, extract_invoke_hints
from vector_lib.search import generate_sequences


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


def generate_vectors(
    chart: Path,
    *,
    treat_as_xml: bool,
    out_dir: Path,
    max_depth: int = 1,
    advance_time: float = 0.0,
    limit: int = 1,
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
    if advance_time and advance_time > 0:
        ctx.advance_time(advance_time)

    alphabet = extract_event_alphabet(ctx)
    hints = extract_invoke_hints(ctx)
    # Phase 1: ignore hints; generate sequences from alphabet only.
    sequences = generate_sequences(
        _ctx_factory(chart, treat_as_xml, advance_time),
        alphabet,
        max_depth=max_depth,
        limit=limit,
    )

    dest = out_dir / f"{chart.stem}.events.jsonl"
    # Emit only the top sequence for now (aligns with exec_compare consumption)
    top = sequences[0] if sequences else []
    with dest.open("w", encoding="utf-8") as fh:
        for ev in top:
            fh.write(f"{{\"event\": \"{ev}\"}}\n")
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
    ap.add_argument("--advance-time", type=float, default=0.0, help="Advance time before generating")
    ap.add_argument("--limit", type=int, default=1, help="Maximum vectors to emit")
    args = ap.parse_args()

    path = generate_vectors(
        args.chart,
        treat_as_xml=args.xml,
        out_dir=args.out,
        max_depth=args.max_depth,
        advance_time=args.advance_time,
        limit=args.limit,
    )
    print(str(path))


if __name__ == "__main__":
    main()
