"""
Agent Name: python-exec-compare

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Execute a chart in both the Python runtime and a reference engine, then
diff their JSONL traces.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Iterable, List, Tuple

from scjson.cli import engine_trace  # noqa: F401  # ensure CLI registered when installed locally


PYTHON_TRACE_CMD = [
    sys.executable,
    "-m",
    "scjson.cli",
    "engine-trace",
]

_SCION_SCRIPT = (
    Path(__file__).resolve().parent.parent / "tools" / "scion-runner" / "scion-trace.cjs"
)


def _default_events_path(chart: Path) -> Path | None:
    candidate = chart.with_suffix(".events.jsonl")
    if candidate.exists():
        return candidate
    candidate = chart.parent / (chart.stem + ".events.jsonl")
    return candidate if candidate.exists() else None


def _load_trace(path: Path) -> List[dict]:
    lines: List[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for raw in handle:
            raw = raw.strip()
            if not raw:
                continue
            lines.append(json.loads(raw))
    return lines


def _diff_steps(py_steps: List[dict], ref_steps: List[dict]) -> Tuple[bool, List[str], Tuple[int, int, int, int]]:
    mismatch = False
    notes: List[str] = []
    py_len = len(py_steps)
    ref_len = len(ref_steps)
    compared = min(py_len, ref_len)
    mismatching_keys = 0
    if py_len != ref_len:
        mismatch = True
        notes.append(
            f"Length mismatch: python trace has {py_len} steps, reference has {ref_len}."
        )
    for idx in range(compared):
        p_step = py_steps[idx]
        r_step = ref_steps[idx]
        if p_step == r_step:
            continue
        mismatch = True
        header = f"Step {idx}:"
        notes.append(header)
        all_keys = sorted(set(p_step.keys()) | set(r_step.keys()))
        for key in all_keys:
            p_val = p_step.get(key)
            r_val = r_step.get(key)
            if p_val != r_val:
                mismatching_keys += 1
                notes.append(f"  {key}: python={p_val!r} reference={r_val!r}")
        break
    return mismatch, notes, (py_len, ref_len, compared, mismatching_keys)


def _default_reference_cmd() -> List[str]:
    if _SCION_SCRIPT.exists():
        return ["node", str(_SCION_SCRIPT)]
    return []


def _resolve_reference_cmd(args: argparse.Namespace) -> List[str]:
    if args.reference:
        return shlex.split(args.reference)
    env_cmd = os.environ.get("SCJSON_REF_ENGINE_CMD")
    if env_cmd:
        return shlex.split(env_cmd)
    default = _default_reference_cmd()
    if default:
        return default
    raise SystemExit(
        "Reference command not provided. Use --reference, set SCJSON_REF_ENGINE_CMD, or install tools/scion-runner."
    )


def _build_trace_cmd(
    base: Iterable[str],
    chart: Path,
    events: Path | None,
    out: Path,
    treat_as_xml: bool,
) -> List[str]:
    cmd = list(base)
    cmd.extend(["-I", str(chart), "-o", str(out)])
    if events is not None:
        cmd.extend(["-e", str(events)])
    if treat_as_xml:
        cmd.append("--xml")
    return cmd


def _run(cmd: List[str], cwd: Path | None = None) -> None:
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit(
            "Command failed: {}\nstdout:\n{}\nstderr:\n{}".format(
                " ".join(cmd), result.stdout, result.stderr
            )
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("chart", type=Path, help="Path to SCXML or SCJSON chart")
    parser.add_argument(
        "--events",
        type=Path,
        help="JSONL event stream (defaults to <chart>.events.jsonl)",
    )
    parser.add_argument(
        "--reference",
        type=str,
        help="Reference engine command (defaults to SCJSON_REF_ENGINE_CMD)",
    )
    parser.add_argument(
        "--secondary",
        type=str,
        help="Optional secondary command to compare against the primary reference",
    )
    parser.add_argument(
        "--workdir",
        type=Path,
        help="Directory for trace artifacts (defaults to temporary directory)",
    )
    args = parser.parse_args()

    chart = args.chart.resolve()
    if not chart.exists():
        raise SystemExit(f"Chart not found: {chart}")

    events = args.events
    if events is None:
        auto = _default_events_path(chart)
        if auto is None:
            raise SystemExit("Event stream not provided and no default found.")
        events = auto
    events = events.resolve()
    if not events.exists():
        raise SystemExit(f"Event stream not found: {events}")

    treat_as_xml = chart.suffix.lower() == ".scxml"
    ref_cmd = _resolve_reference_cmd(args)

    temp_dir: TemporaryDirectory[str] | None = None
    workdir = args.workdir
    if workdir is None:
        temp_dir = TemporaryDirectory(prefix="scjson-exec-")
        workdir = Path(temp_dir.name)
    else:
        workdir.mkdir(parents=True, exist_ok=True)

    py_trace = workdir / "python.trace.jsonl"
    ref_trace = workdir / "reference.trace.jsonl"

    _run(_build_trace_cmd(PYTHON_TRACE_CMD, chart, events, py_trace, treat_as_xml))
    _run(_build_trace_cmd(ref_cmd, chart, events, ref_trace, treat_as_xml))

    py_steps = _load_trace(py_trace)
    ref_steps = _load_trace(ref_trace)
    mismatch, notes, stats = _diff_steps(py_steps, ref_steps)

    if mismatch:
        print("Mismatch detected (python vs reference):")
        for note in notes:
            print(note)
        py_len, ref_len, compared, mismatching_keys = stats
        print(
            f"Totals: python_steps={py_len} reference_steps={ref_len} compared={compared} mismatching_keys={mismatching_keys}"
        )
        if temp_dir:
            print(f"Artifacts retained in {workdir}")
        sys.exit(1)

    print("✔ Python vs reference traces match")

    if args.secondary:
        secondary_cmd = shlex.split(args.secondary)
    else:
        secondary_env = os.environ.get("SCJSON_SECONDARY_ENGINE_CMD")
        secondary_cmd = shlex.split(secondary_env) if secondary_env else []

    if secondary_cmd:
        secondary_trace = workdir / "secondary.trace.jsonl"
        _run(_build_trace_cmd(secondary_cmd, chart, events, secondary_trace, treat_as_xml))
        secondary_steps = _load_trace(secondary_trace)
        mismatch_sec, notes_sec, stats_sec = _diff_steps(ref_steps, secondary_steps)
        if mismatch_sec:
            print("Mismatch detected (reference vs secondary):")
            for note in notes_sec:
                print(note)
            py_len, ref_len, compared, mismatching_keys = stats_sec
            print(
                f"Totals: reference_steps={py_len} secondary_steps={ref_len} compared={compared} mismatching_keys={mismatching_keys}"
            )
            if temp_dir:
                print(f"Artifacts retained in {workdir}")
            sys.exit(2)
        print("✔ Reference vs secondary traces match")
    if temp_dir:
        temp_dir.cleanup()


if __name__ == "__main__":
    main()
