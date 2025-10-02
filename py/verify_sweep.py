"""
Agent Name: python-verify-sweep

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Sweep a corpus with the Python engine verifier and summarize outcomes.

Runs `python -m scjson.cli engine-verify` on each chart and reports counts of
pass/fail/other. Useful for quickly triaging coverage without requiring an
events stream.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Iterable, Tuple

ROOT = Path(__file__).resolve().parent.parent


def _iter_charts(root: Path, pattern: str) -> Iterable[Path]:
    for p in sorted(root.rglob(pattern)):
        if p.suffix.lower() == ".scxml":
            yield p


def _verify(chart: Path, advance_time: float) -> Tuple[str, str]:
    cmd = [
        sys.executable,
        "-m",
        "scjson.cli",
        "engine-verify",
        "-I",
        str(chart),
        "--xml",
    ]
    if advance_time and advance_time > 0:
        cmd.extend(["--advance-time", str(advance_time)])
    proc = subprocess.run(cmd, capture_output=True, text=True)
    out = (proc.stdout or "") + (proc.stderr or "")
    # Output contains lines like "outcome: pass"
    outcome = "other"
    for line in out.splitlines():
        line = line.strip().lower()
        if line.startswith("outcome:"):
            outcome = line.split(":", 1)[1].strip()
            break
    return outcome, out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "root",
        type=Path,
        nargs="?",
        default=ROOT / "tutorial" / "Tests" / "python" / "W3C" / "Mandatory" / "Auto",
        help="Root folder to scan (default: W3C Mandatory/Auto)",
    )
    parser.add_argument(
        "--glob",
        default="**/*.scxml",
        help="Glob pattern under root to locate charts",
    )
    parser.add_argument(
        "--advance-time",
        type=float,
        default=3.0,
        help="Advance time by N seconds for each chart (for delayed sends)",
    )
    args = parser.parse_args()

    total = 0
    counts = {"pass": 0, "fail": 0, "other": 0}
    failures: list[tuple[Path, str]] = []

    for chart in _iter_charts(args.root, args.glob):
        total += 1
        outcome, raw = _verify(chart, args.advance_time)
        counts[outcome] = counts.get(outcome, 0) + 1
        if outcome != "pass":
            failures.append((chart, raw))

    print(
        f"Verify summary: total={total} pass={counts['pass']} fail={counts['fail']} other={counts['other']}"
    )
    if failures:
        print("Sample failures (first 10):")
        for path, text in failures[:10]:
            print(f"- {path}")
            print(text.strip())
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()

