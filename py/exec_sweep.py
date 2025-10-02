"""
Agent Name: python-exec-sweep

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Sweep a corpus of charts and compare Python engine traces to a reference.

This utility discovers SCXML/SCJSON files under a root directory, locates
matching JSONL event streams, and invokes ``py/exec_compare.py`` for each
chart. It summarizes mismatches and optionally retains artifacts.
"""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Tuple
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parent.parent


def _default_events_path(chart: Path) -> Path | None:
    candidate = chart.with_suffix(".events.jsonl")
    if candidate.exists():
        return candidate
    candidate = chart.parent / (chart.stem + ".events.jsonl")
    return candidate if candidate.exists() else None


def _iter_charts(root: Path, pattern: str) -> Iterable[Path]:
    for p in sorted(root.rglob(pattern)):
        if p.suffix.lower() in {".scxml", ".scjson"} and p.is_file():
            yield p


def _run(cmd: List[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "root",
        type=Path,
        nargs="?",
        default=ROOT / "tutorial",
        help="Root directory to search for charts (default: tutorial)",
    )
    parser.add_argument(
        "--glob",
        default="**/*.scxml",
        help="Glob pattern under root to locate charts",
    )
    parser.add_argument(
        "--reference",
        type=str,
        help="Reference engine command (defaults to SCJSON_REF_ENGINE_CMD)",
    )
    parser.add_argument(
        "--workdir",
        type=Path,
        help="Directory to store per-chart artifacts (default: temp)",
    )
    parser.add_argument(
        "--keep-step0-states",
        action="store_true",
        default=True,
        help="Do not strip step-0 entered/exited state lists during normalization",
    )
    parser.add_argument(
        "--leaf-only",
        dest="leaf_only",
        action="store_true",
        default=True,
        help="Normalize configuration/entered/exited to leaf states",
    )
    parser.add_argument(
        "--full-states",
        dest="leaf_only",
        action="store_false",
        help="Compare full state sets instead of leaf-only",
    )
    parser.add_argument("--omit-actions", action="store_true")
    parser.add_argument("--omit-delta", action="store_true")
    parser.add_argument("--omit-transitions", action="store_true")
    parser.add_argument("--advance-time", type=float, default=0.0)
    parser.add_argument(
        "--skip",
        action="append",
        default=[],
        help="Glob or substring to skip charts (repeatable)",
    )
    parser.add_argument(
        "--skipfile",
        type=Path,
        help="Optional file with one glob/substring per line to skip",
    )
    opts = parser.parse_args()

    # Load skip patterns from file, if provided
    if opts.skipfile and opts.skipfile.exists():
        for line in opts.skipfile.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            opts.skip.append(line)

    charts: List[Path] = []
    for c in _iter_charts(opts.root, opts.glob):
        name = str(c)
        if any((s in name) or Path(name).match(s) for s in opts.skip):
            continue
        charts.append(c)
    if not charts:
        print("No charts found.")
        sys.exit(0)

    mismatches: List[Tuple[Path, str]] = []
    total = 0

    base_cmd = [sys.executable, str((ROOT / "py" / "exec_compare.py").resolve())]
    if opts.reference:
        base_cmd.extend(["--reference", opts.reference])
    if opts.workdir:
        artifacts_root = Path(opts.workdir)
        artifacts_root.mkdir(parents=True, exist_ok=True)
    else:
        artifacts_root = None

    # Common normalization flags
    common_flags: List[str] = []
    if opts.leaf_only:
        common_flags.append("--leaf-only")
    else:
        common_flags.append("--full-states")
    if opts.keep_step0_states:
        common_flags.append("--keep-step0-states")
    if opts.omit_actions:
        common_flags.append("--omit-actions")
    if opts.omit_delta:
        common_flags.append("--omit-delta")
    if opts.omit_transitions:
        common_flags.append("--omit-transitions")
    if opts.advance_time and opts.advance_time > 0:
        common_flags.extend(["--advance-time", str(opts.advance_time)])

    # Temporary directory for auto-generated empty event streams
    temp_dir: TemporaryDirectory[str] | None = None
    try:
        for chart in charts:
            events = _default_events_path(chart)
            # Create an empty event stream when none is available so we can
            # still compare at least step-0 semantics.
            if events is None:
                if temp_dir is None:
                    temp_dir = TemporaryDirectory(prefix="scjson-sweep-")
                tmp = Path(temp_dir.name) / (chart.stem + ".events.jsonl")
                tmp.parent.mkdir(parents=True, exist_ok=True)
                tmp.write_text("")
                events = tmp
            total += 1
            cmd = list(base_cmd)
            if artifacts_root:
                rel = chart.relative_to(opts.root)
                workdir = artifacts_root / rel.parent / rel.stem
                cmd.extend(["--workdir", str(workdir)])
            cmd.extend(common_flags)
            cmd.append(str(chart))
            if events:
                cmd.extend(["--events", str(events)])
            result = _run(cmd)
            if result.returncode != 0:
                mismatches.append((chart, result.stdout + "\n" + result.stderr))
                # Keep going; summarize later
    finally:
        if temp_dir is not None:
            temp_dir.cleanup()

    if mismatches:
        print(f"Mismatches: {len(mismatches)} of {total}")
        for path, out in mismatches[:10]:
            print(f"- {path}:")
            print(out.strip())
        sys.exit(1)

    print(f"✔ All charts matched reference ({total} compared)")
    sys.exit(0)


if __name__ == "__main__":
    main()
