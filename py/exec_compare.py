"""
Agent Name: python-exec-compare

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Execute a chart in both the Python runtime and a reference engine, then
diff their JSONL traces. Supports leaf-only/state filtering, step-0
normalization, and optional field omission for focused comparisons.
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
from typing import Iterable, List, Tuple, Set, Dict, Any

try:
    from scjson.cli import engine_trace  # noqa: F401  # ensure CLI registered when installed locally
    from scjson.context import DocumentContext, ExecutionMode
    from scjson.events import Event as PyEvent
except Exception:  # pragma: no cover - fallback when package not importable
    DocumentContext = None  # type: ignore
    ExecutionMode = None  # type: ignore
    PyEvent = None  # type: ignore


PYTHON_TRACE_CMD = [sys.executable, "-m", "scjson.cli", "engine-trace"]

_SCION_SCRIPT = (
    Path(__file__).resolve().parent.parent / "tools" / "scion-runner" / "scion-trace.cjs"
)


def _default_events_path(chart: Path) -> Path | None:
    candidate = chart.with_suffix(".events.jsonl")
    if candidate.exists():
        return candidate
    candidate = chart.parent / (chart.stem + ".events.jsonl")
    return candidate if candidate.exists() else None


def _load_events_list(path: Path) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    if not path.exists():
        return items
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            items.append(json.loads(line))
        except Exception:
            continue
    return items


def _coverage_from_vector(chart: Path, events_path: Path, treat_as_xml: bool, advance_time: float) -> Dict[str, int] | None:
    if DocumentContext is None or PyEvent is None:
        return None
    try:
        ctx = (
            DocumentContext.from_xml_file(chart, execution_mode=ExecutionMode.LAX)
            if treat_as_xml
            else DocumentContext.from_json_file(chart, execution_mode=ExecutionMode.STRICT)
        )
        if advance_time and advance_time > 0:
            ctx.advance_time(advance_time)
        entered: Set[str] = set()
        fired = 0
        done = 0
        err = 0
        for item in _load_events_list(events_path):
            name = item.get("event") or item.get("name")
            data = item.get("data") if "data" in item else None
            if not name:
                continue
            trace = ctx.trace_step(PyEvent(name=str(name), data=data))
            fired += len(trace.get("firedTransitions", []) or [])
            for s in trace.get("enteredStates", []) or []:
                entered.add(str(s))
            evt = trace.get("event") or {}
            ename = evt.get("name") if isinstance(evt, dict) else None
            if isinstance(ename, str):
                if ename.startswith("done."):
                    done += 1
                if ename.startswith("error"):
                    err += 1
        return {"enteredStates": len(entered), "firedTransitions": fired, "doneEvents": done, "errorEvents": err}
    except Exception:
        return None


def _load_trace(path: Path) -> List[dict]:
    lines: List[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for raw in handle:
            raw = raw.strip()
            if not raw:
                continue
            lines.append(json.loads(raw))
    return lines


def _leaf_ids_from_chart(chart: Path, treat_as_xml: bool) -> Set[str]:
    """Compute leaf state IDs from an SCXML/SCJSON chart for normalization.

    A leaf state is a state with no child ``state`` or ``parallel`` elements.
    ``final`` elements are also considered leaves.
    """
    # First prefer computing leaves from the engine's activation tree
    if DocumentContext is not None:
        try:
            ctx = (
                DocumentContext.from_xml_file(chart, execution_mode=ExecutionMode.LAX)
                if treat_as_xml
                else DocumentContext.from_json_file(chart, execution_mode=ExecutionMode.LAX)
            )
            leaves: Set[str] = set()
            for act in ctx.activations.values():
                node = getattr(act, 'node', None)
                # finals are leaves; states with no state/parallel children are leaves
                has_state_children = bool(getattr(node, 'state', [])) or bool(
                    getattr(node, 'parallel', [])
                ) or bool(getattr(node, 'final', []))
                is_final = getattr(node.__class__, '__name__', '').lower().endswith('finaltype')
                if getattr(act, 'id', None) and (is_final or not has_state_children):
                    leaves.add(act.id)
            return leaves
        except Exception:
            pass
    # Fallback to naive JSON conversion
    try:
        if treat_as_xml:
            from scjson.SCXMLDocumentHandler import SCXMLDocumentHandler
            handler = SCXMLDocumentHandler(fail_on_unknown_properties=False)
            json_str = handler.xml_to_json(chart.read_text(encoding="utf-8"))
            data = json.loads(json_str)
        else:
            data = json.loads(chart.read_text(encoding="utf-8"))
    except Exception:
        return set()

    leaves: Set[str] = set()

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            tag_id = node.get("id")
            # Mark finals as leaves
            if "final" not in node and node.get("name") == "final":
                if tag_id:
                    leaves.add(tag_id)
            # Recurse into known containers
            children_states = node.get("state") or []
            children_parallel = node.get("parallel") or []
            children_final = node.get("final") or []
            # Identify leaf 'state' nodes
            if (
                node.get("name") == "state"
                or ("state" in node or "parallel" in node)
            ):
                if tag_id and not children_states and not children_parallel and not children_final:
                    leaves.add(tag_id)
            for item in children_states:
                walk(item)
            for item in children_parallel:
                walk(item)
            for item in children_final:
                walk(item)
            return
        if isinstance(node, list):
            for item in node:
                walk(item)

    walk(data)
    return leaves


def _normalize_steps_leaf_only(steps: List[dict], leaf_ids: Set[str]) -> List[dict]:
    if not leaf_ids:
        return steps
    norm: List[dict] = []
    for step in steps:
        s = dict(step)
        for key in ("configuration", "enteredStates", "exitedStates"):
            vals = s.get(key)
            if isinstance(vals, list):
                s[key] = [v for v in vals if v in leaf_ids]
        norm.append(s)
    return norm


def _strip_step0_noise(steps: List[dict]) -> List[dict]:
    """Normalize step 0 differences across engines.

    - Remove datamodelDelta at step 0 (engines include different init deltas)
    - Remove firedTransitions at step 0 (some engines record initial transitions)
    """
    if not steps:
        return steps
    out: List[dict] = []
    for s in steps:
        t = dict(s)
        if int(t.get("step", -1)) == 0:
            t["datamodelDelta"] = {}
            t["firedTransitions"] = []
        out.append(t)
    return out


def _strip_step0_states(steps: List[dict]) -> List[dict]:
    """Optionally clear step 0 entered/exited to reduce reference noise.

    Some engines surface initial transitions by reporting non-empty
    ``enteredStates``/``exitedStates`` at step 0. Others do not. When comparing
    traces, clearing these fields for step 0 helps focus diffs on
    post-initialization behavior. The final configuration remains available
    via ``configuration`` regardless.
    """
    if not steps:
        return steps
    out: List[dict] = []
    for s in steps:
        t = dict(s)
        if int(t.get("step", -1)) == 0:
            t["enteredStates"] = []
            t["exitedStates"] = []
        out.append(t)
    return out


def _normalize_transition_conditions(steps: List[dict]) -> List[dict]:
    """Clear transition conditions for comparison parity with SCION output."""

    normalized: List[dict] = []
    for step in steps:
        t = dict(step)
        transitions = t.get("firedTransitions")
        if isinstance(transitions, list):
            cleaned: List[dict] = []
            for item in transitions:
                if isinstance(item, dict):
                    entry = dict(item)
                    entry["cond"] = None
                    cleaned.append(entry)
                else:
                    cleaned.append(item)
            t["firedTransitions"] = cleaned
        normalized.append(t)
    return normalized


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
    extra_flags: Iterable[str] | None = None,
) -> List[str]:
    cmd = list(base)
    cmd.extend(["-I", str(chart), "-o", str(out)])
    if events is not None:
        cmd.extend(["-e", str(events)])
    if treat_as_xml:
        cmd.append("--xml")
    if extra_flags:
        cmd.extend(list(extra_flags))
    return cmd


def _omit_fields(
    steps: List[dict], *, omit_actions: bool, omit_delta: bool, omit_transitions: bool
) -> List[dict]:
    if not (omit_actions or omit_delta or omit_transitions):
        return steps
    out: List[dict] = []
    for s in steps:
        t = dict(s)
        if omit_actions and "actionLog" in t:
            t["actionLog"] = []
        if omit_delta and "datamodelDelta" in t:
            t["datamodelDelta"] = {}
        if omit_transitions and "firedTransitions" in t:
            t["firedTransitions"] = []
        out.append(t)
    return out


def _run(cmd: List[str], cwd: Path | None = None) -> None:
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit(
            "Command failed: {}\nstdout:\n{}\nstderr:\n{}".format(
                " ".join(cmd), result.stdout, result.stderr
            )
        )


def _write_python_trace_inline(
    chart: Path,
    events: Path | None,
    out: Path,
    treat_as_xml: bool,
    ordering: str = "tolerant",
) -> None:
    if DocumentContext is None or PyEvent is None:
        raise SystemExit(
            "Python inline trace fallback unavailable (scjson not importable)"
        )
    out.parent.mkdir(parents=True, exist_ok=True)
    execution_mode = ExecutionMode.LAX if treat_as_xml else ExecutionMode.STRICT
    ctx = (
        DocumentContext.from_xml_file(chart, execution_mode=execution_mode)
        if treat_as_xml
        else DocumentContext.from_json_file(chart, execution_mode=execution_mode)
    )
    try:
        ctx.ordering_mode = (ordering or "tolerant").lower()
    except Exception:
        pass
    with out.open("w", encoding="utf-8") as sink:
        # Step 0 snapshot
        config = sorted(ctx._filter_states(ctx.configuration), key=ctx._activation_order_key)
        init = {
            "step": 0,
            "event": None,
            "firedTransitions": [],
            "enteredStates": config,
            "exitedStates": [],
            "configuration": config,
            "actionLog": [],
            "datamodelDelta": dict(ctx.data_model),
        }
        sink.write(json.dumps(init) + "\n")
        # Events
        step_no = 1
        if events is not None and events.exists():
            for line in events.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                name = obj.get("event") or obj.get("name")
                if not name:
                    continue
                data = obj.get("data") if "data" in obj else None
                trace = ctx.trace_step(PyEvent(name=str(name), data=data))
                trace["step"] = step_no
                sink.write(json.dumps(trace) + "\n")
                step_no += 1


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
        "--generate-vectors",
        action="store_true",
        help="Generate minimal event vectors when no events file is provided",
    )
    parser.add_argument(
        "--python-cmd",
        type=str,
        help="Override python engine-trace command (default uses installed scjson)",
    )
    parser.add_argument(
        "--workdir",
        type=Path,
        help="Directory for trace artifacts (defaults to temporary directory)",
    )
    # Step-0 state normalization: allow explicit keep/strip and auto mode
    parser.add_argument(
        "--keep-step0-states",
        dest="keep_step0_states",
        action="store_true",
        default=None,
        help=(
            "Keep step-0 entered/exited state lists. By default, the tool auto-"
            "detects reference engine and strips when using SCION to reduce noise."
        ),
    )
    parser.add_argument(
        "--strip-step0-states",
        dest="keep_step0_states",
        action="store_false",
        help="Strip step-0 entered/exited state lists during normalization",
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
    parser.add_argument(
        "--omit-actions",
        action="store_true",
        help="Omit actionLog from normalized comparison",
    )
    parser.add_argument(
        "--omit-delta",
        action="store_true",
        help="Omit datamodelDelta from normalized comparison",
    )
    parser.add_argument(
        "--omit-transitions",
        action="store_true",
        help="Omit firedTransitions from normalized comparison",
    )
    parser.add_argument(
        "--advance-time",
        type=float,
        default=0.0,
        help="Advance mock time (python engine) before event processing",
    )
    parser.add_argument(
        "--gen-depth",
        type=int,
        default=2,
        help="Generation max depth when using --generate-vectors",
    )
    parser.add_argument(
        "--gen-limit",
        type=int,
        default=1,
        help="Generation max vectors to emit when using --generate-vectors",
    )
    parser.add_argument(
        "--gen-variants-per-event",
        type=int,
        default=3,
        help="Max fused payload variants to consider per event during vector generation",
    )
    parser.add_argument(
        "--ordering",
        type=str,
        choices=["tolerant", "strict", "scion"],
        default="tolerant",
        help="Ordering policy for child→parent emissions (finalize, etc.)",
    )
    parser.add_argument(
        "--norm",
        type=str,
        choices=["scion"],
        help=(
            "Apply a normalization profile. 'scion' sets leaf-only, omit-delta, "
            "omit-transitions, strip-step0-states, and ordering=scion."
        ),
    )
    args = parser.parse_args()

    chart = args.chart.resolve()
    if not chart.exists():
        raise SystemExit(f"Chart not found: {chart}")
    # Determine input type early (used by vector generation branch below)
    treat_as_xml = chart.suffix.lower() == ".scxml"

    events = args.events
    if events is None:
        auto = _default_events_path(chart)
        if auto is None and args.generate_vectors:
            # Generate into a temp vectors directory and use it
            vectors_dir = (args.workdir or Path(TemporaryDirectory(prefix="scjson-vectors-").name)) / "vectors"
            vectors_dir.mkdir(parents=True, exist_ok=True)
            # Invoke vector generator
            vg_cmd = [
                sys.executable,
                str((Path(__file__).resolve().parent / "vector_gen.py").resolve()),
                str(chart),
                "--out",
                str(vectors_dir),
            ]
            if treat_as_xml:
                vg_cmd.append("--xml")
            if args.advance_time and args.advance_time > 0:
                vg_cmd.extend(["--advance-time", str(args.advance_time)])
            if args.gen_depth:
                vg_cmd.extend(["--max-depth", str(args.gen_depth)])
            if args.gen_limit:
                vg_cmd.extend(["--limit", str(args.gen_limit)])
            if args.gen_variants_per_event:
                vg_cmd.extend(["--variants-per-event", str(args.gen_variants_per_event)])
            _run(vg_cmd)
            gen_path = vectors_dir / f"{chart.stem}.events.jsonl"
            if not gen_path.exists():
                raise SystemExit("Vector generator did not produce an events file.")
            events = gen_path
            # Adopt recommended advance time from vector metadata when none provided
            try:
                if (not args.advance_time) or args.advance_time <= 0:
                    meta_path = vectors_dir / f"{chart.stem}.vector.json"
                    if meta_path.exists():
                        meta = json.loads(meta_path.read_text(encoding="utf-8"))
                        adv = float(meta.get("advanceTime", 0.0) or 0.0)
                        if adv > 0:
                            args.advance_time = adv
            except Exception:
                pass
            # Print a brief coverage summary for the generated vector
            cov = _coverage_from_vector(chart, events, treat_as_xml, args.advance_time)
            if cov is not None:
                print(f"Generated vector coverage: entered={cov['enteredStates']} fired={cov['firedTransitions']} done={cov['doneEvents']} error={cov['errorEvents']}")
        elif auto is not None:
            events = auto
        else:
            raise SystemExit("Event stream not provided and no default found.")
    events = events.resolve()
    if not events.exists():
        raise SystemExit(f"Event stream not found: {events}")

    # treat_as_xml already computed above
    # Apply normalization profile defaults before resolving commands
    if args.norm == "scion":
        args.leaf_only = True
        args.omit_delta = True
        args.omit_transitions = True
        args.keep_step0_states = False
        args.ordering = "scion"

    ref_cmd = _resolve_reference_cmd(args)

    # If not explicitly specified, auto-set step-0 state normalization when using SCION as reference
    if args.keep_step0_states is None:
        try:
            ref_joined = " ".join(ref_cmd).lower()
            args.keep_step0_states = not ("scion" in ref_joined or "scion-runner" in ref_joined)
        except Exception:
            args.keep_step0_states = True

    temp_dir: TemporaryDirectory[str] | None = None
    workdir = args.workdir
    if workdir is None:
        temp_dir = TemporaryDirectory(prefix="scjson-exec-")
        workdir = Path(temp_dir.name)
    else:
        workdir.mkdir(parents=True, exist_ok=True)

    py_trace = workdir / "python.trace.jsonl"
    ref_trace = workdir / "reference.trace.jsonl"

    # Build python trace command (supports extra flags for size/determinism)
    py_cmd = (
        shlex.split(args.python_cmd) if args.python_cmd else list(PYTHON_TRACE_CMD)
    )
    py_flags: list[str] = []
    if args.leaf_only:
        py_flags.append("--leaf-only")
    if args.omit_actions:
        py_flags.append("--omit-actions")
    if args.omit_delta:
        py_flags.append("--omit-delta")
    if args.omit_transitions:
        py_flags.append("--omit-transitions")
    if args.advance_time and args.advance_time > 0:
        py_flags.extend(["--advance-time", str(args.advance_time)])
    if args.ordering:
        py_flags.extend(["--ordering", args.ordering])

    try:
        # Honor optional WORKDIR_OVERRIDE from environment
        if os.environ.get("WORKDIR_OVERRIDE"):
            workdir = Path(os.environ["WORKDIR_OVERRIDE"])  # type: ignore
            workdir.mkdir(parents=True, exist_ok=True)
            py_trace = workdir / "python.trace.jsonl"
        _run(_build_trace_cmd(py_cmd, chart, events, py_trace, treat_as_xml, py_flags))
    except SystemExit:
        # Fallback to inline generation when package CLI is unavailable
        _write_python_trace_inline(chart, events, py_trace, treat_as_xml, ordering=args.ordering)
    if os.environ.get("WORKDIR_OVERRIDE"):
        workdir = Path(os.environ["WORKDIR_OVERRIDE"])  # type: ignore
        workdir.mkdir(parents=True, exist_ok=True)
        ref_trace = workdir / "reference.trace.jsonl"
    _run(_build_trace_cmd(ref_cmd, chart, events, ref_trace, treat_as_xml))

    py_steps = _load_trace(py_trace)
    ref_steps = _load_trace(ref_trace)
    # Normalize states to leaf-only (optional)
    if args.leaf_only:
        leaf_ids = _leaf_ids_from_chart(chart, treat_as_xml)
        py_steps = _normalize_steps_leaf_only(py_steps, leaf_ids)
        ref_steps = _normalize_steps_leaf_only(ref_steps, leaf_ids)
    # Also normalize step 0 noisy fields (datamodelDelta and firedTransitions)
    py_steps = _strip_step0_noise(py_steps)
    ref_steps = _strip_step0_noise(ref_steps)
    # Optionally clear step-0 entered/exited state lists to reduce reference variance
    if not args.keep_step0_states:
        py_steps = _strip_step0_states(py_steps)
        ref_steps = _strip_step0_states(ref_steps)

    # Optionally omit fields from comparison for focus/size
    py_steps = _omit_fields(
        py_steps,
        omit_actions=args.omit_actions,
        omit_delta=args.omit_delta,
        omit_transitions=args.omit_transitions,
    )
    ref_steps = _omit_fields(
        ref_steps,
        omit_actions=args.omit_actions,
        omit_delta=args.omit_delta,
        omit_transitions=args.omit_transitions,
    )
    py_steps = _normalize_transition_conditions(py_steps)
    ref_steps = _normalize_transition_conditions(ref_steps)
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
        # Honor optional WORKDIR_OVERRIDE from environment (for CI harness retention)
        if os.environ.get("WORKDIR_OVERRIDE"):
            workdir = Path(os.environ["WORKDIR_OVERRIDE"])  # type: ignore
            workdir.mkdir(parents=True, exist_ok=True)
            secondary_trace = workdir / "secondary.trace.jsonl"
        _run(_build_trace_cmd(secondary_cmd, chart, events, secondary_trace, treat_as_xml))
        secondary_steps = _load_trace(secondary_trace)
        # Apply normalization to secondary to align with ref_steps
        if args.leaf_only:
            leaf_ids = _leaf_ids_from_chart(chart, treat_as_xml)
            secondary_steps = _normalize_steps_leaf_only(secondary_steps, leaf_ids)
        secondary_steps = _strip_step0_noise(secondary_steps)
        if not args.keep_step0_states:
            secondary_steps = _strip_step0_states(secondary_steps)
        secondary_steps = _omit_fields(
            secondary_steps,
            omit_actions=args.omit_actions,
            omit_delta=args.omit_delta,
            omit_transitions=args.omit_transitions,
        )
        secondary_steps = _normalize_transition_conditions(secondary_steps)
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
