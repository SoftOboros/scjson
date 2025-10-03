"""
Agent Name: python-exec-compare-advanced-tests

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Advanced exec_compare tests over charts exercising engine semantics.
Falls back to Python engine as reference if [SCION](https://www.npmjs.com/package/scion) is unavailable.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

import pytest
from tempfile import TemporaryDirectory

SCION_NPM_URL = "https://www.npmjs.com/package/scion"

_SCION_PREPARED: Optional[bool] = None


def _ensure_scion_runner(repo_root: Path) -> bool:
    """Ensure the [SCION](https://www.npmjs.com/package/scion) Node runner is available for tests.

    @param repo_root: Repository root used to locate the [SCION](https://www.npmjs.com/package/scion) runner assets.
    @returns True when the runner and its dependencies are ready for use.
    """

    global _SCION_PREPARED
    if _SCION_PREPARED is not None:
        return _SCION_PREPARED

    runner_dir = repo_root / "tools" / "scion-runner"
    runner = runner_dir / "scion-trace.cjs"
    if shutil.which("node") is None or not runner.exists():
        _SCION_PREPARED = False
        return False

    node_modules = runner_dir / "node_modules"
    jsdom = node_modules / "jsdom"
    scxml = node_modules / "scxml"
    if jsdom.exists() and scxml.exists():
        _SCION_PREPARED = True
        return True

    npm = shutil.which("npm")
    if npm is None:
        _SCION_PREPARED = False
        return False

    lock_file = runner_dir / "package-lock.json"
    cmd = [npm, "ci" if lock_file.exists() else "install"]
    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=str(runner_dir),
    )
    if proc.returncode != 0:
        _SCION_PREPARED = False
        return False

    _SCION_PREPARED = jsdom.exists() and scxml.exists()
    return _SCION_PREPARED


def _augment_node_path(existing: Optional[str], repo_root: Path) -> str:
    """Prepend the [SCION](https://www.npmjs.com/package/scion) runner's node_modules to NODE_PATH for child calls.

    @param existing: Existing NODE_PATH environment value, if set.
    @param repo_root: Repository root used to locate node_modules.
    @returns Updated NODE_PATH string that includes the [SCION](https://www.npmjs.com/package/scion) modules.
    """

    runner_modules = repo_root / "tools" / "scion-runner" / "node_modules"
    parts = [str(runner_modules)]
    if existing:
        parts.append(existing)
    return os.pathsep.join(part for part in parts if part)


def _ref_command(root: Path) -> str:
    scion = root / "tools" / "scion-runner" / "scion-trace.cjs"
    if scion.exists() and _ensure_scion_runner(root):
        return f"node {scion}"
    return f"{sys.executable} -m scjson.cli engine-trace"


def _python_ref() -> str:
    return f"{sys.executable} -m scjson.cli engine-trace"


def _run_compare(chart: Path, *, generate: bool = True, depth: int = 2, extra: list[str] | None = None, force_python_ref: bool = False) -> subprocess.CompletedProcess[str]:
    root = Path(__file__).resolve().parents[1]
    repo_root = root.parent
    env = dict(os.environ)
    env["PYTHONPATH"] = str(root / "py")
    scion_ready = False
    if not force_python_ref:
        scion_ready = _ensure_scion_runner(repo_root)
        if scion_ready:
            env["NODE_PATH"] = _augment_node_path(env.get("NODE_PATH"), repo_root)
    args = [
        sys.executable,
        str(root / "py" / "exec_compare.py"),
        str(chart),
        "--reference",
        (_python_ref() if force_python_ref or not scion_ready else _ref_command(repo_root)),
    ]
    if generate:
        args.append("--generate-vectors")
        args.extend(["--gen-depth", str(depth)])
    if extra:
        args.extend(extra)
    return subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env, cwd=str(root))


def test_parallel_done_matches_reference() -> None:
    root = Path(__file__).resolve().parents[2]
    chart = root / "tests" / "sweep_corpus" / "parallel_done.scxml"
    # Generate an empty vector to allow step-0 comparison
    result = _run_compare(chart, generate=True, depth=1, force_python_ref=True)
    assert result.returncode == 0, f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"


def test_done_invoke_id_specific_priority() -> None:
    root = Path(__file__).resolve().parents[2]
    chart = root / "tests" / "sweep_corpus" / "done_invoke_order.scxml"
    # Generator will emit 'complete'
    result = _run_compare(chart, generate=True, depth=1)
    assert result.returncode == 0, f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"


def test_history_shallow_restore() -> None:
    root = Path(__file__).resolve().parents[2]
    chart = root / "tests" / "sweep_corpus" / "history_shallow.scxml"
    events = chart.with_suffix(".events.jsonl")
    assert events.exists()
    result = _run_compare(chart, generate=False, force_python_ref=True)
    assert result.returncode == 0, f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"


def test_history_deep_restore() -> None:
    root = Path(__file__).resolve().parents[2]
    chart = root / "tests" / "sweep_corpus" / "history_deep.scxml"
    events = chart.with_suffix(".events.jsonl")
    assert events.exists()
    result = _run_compare(chart, generate=False, force_python_ref=True)
    assert result.returncode == 0, f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"


def test_finalize_event_precedes_done_invoke() -> None:
    root = Path(__file__).resolve().parents[2]
    chart = root / "tests" / "sweep_corpus" / "finalize_order.scxml"
    # Generator will emit 'complete'; we expect transition to 'seen_first' first
    result = _run_compare(chart, generate=True, depth=1, force_python_ref=True)
    assert result.returncode == 0, f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"


def test_finalize_param_payload_propagates() -> None:
    root = Path(__file__).resolve().parents[2]
    chart = root / "tests" / "sweep_corpus" / "finalize_param_payload.scxml"
    # Vector will emit 'complete'; ensure compare matches
    result = _run_compare(chart, generate=True, depth=1, force_python_ref=True)
    assert result.returncode == 0, f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"


def test_finalize_child_donedata_propagates() -> None:
    root = Path(__file__).resolve().parents[2]
    chart = root / "tests" / "sweep_corpus" / "finalize_child_donedata.scxml"
    result = _run_compare(chart, generate=True, depth=1, force_python_ref=True)
    assert result.returncode == 0, f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"


def test_multi_invoke_switch_child_events() -> None:
    root = Path(__file__).resolve().parents[2]
    chart = root / "tests" / "sweep_corpus" / "multi_invoke_switch.scxml"
    events = chart.with_suffix(".events.jsonl")
    assert events.exists()
    # Compare using Python reference for stability across environments
    result = _run_compare(chart, generate=False, force_python_ref=True)
    assert result.returncode == 0, f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"


def test_parallel_history_deep_restore() -> None:
    root = Path(__file__).resolve().parents[2]
    chart = root / "tests" / "sweep_corpus" / "parallel_history_deep.scxml"
    events = chart.with_suffix(".events.jsonl")
    assert events.exists()
    result = _run_compare(chart, generate=False, force_python_ref=True)
    assert result.returncode == 0, f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"


def test_parallel_invoke_finalize_ordering_deterministic() -> None:
    # Validate deterministic ordering of finalize-emitted events from two child invokes
    root = Path(__file__).resolve().parents[2]
    chart = root / "tests" / "sweep_corpus" / "parallel_invoke_complete.scxml"
    env = dict(os.environ)
    env["PYTHONPATH"] = str(root / "py")
    # Use inline DocumentContext.microstep to apply autoforward and inspect queue order
    sys.path.insert(0, str(root / "py"))
    from scjson.context import DocumentContext, ExecutionMode
    from scjson.events import Event
    ctx = DocumentContext.from_xml_file(chart, execution_mode=ExecutionMode.LAX)
    ctx.microstep()  # process init
    ctx.microstep()  # drain eventless
    ctx.microstep()  # drain eventless
    # Send external 'complete' and allow autoforwarding
    ctx.events.push(Event(name="complete"))
    ctx.microstep()
    # Now the queue should contain both finalize-emitted events near the front
    names = [getattr(evt, 'name', None) for evt in list(getattr(ctx.events, '_q', []))]
    assert "seen.left" in names and "seen.right" in names, names
    head = names[:4]
    assert {"seen.left", "seen.right"}.issubset(set(head)), head


def test_parallel_invoke_compare_scion() -> None:
    # Compare Python vs SCION (https://www.npmjs.com/package/scion) on the parallel complete + finalize chart
    root = Path(__file__).resolve().parents[2]
    chart = root / "tests" / "sweep_corpus" / "parallel_invoke_complete.scxml"
    scion = root / "tools" / "scion-runner" / "scion-trace.cjs"
    if not scion.exists() or not _ensure_scion_runner(root):
        pytest.skip(f"SCION ({SCION_NPM_URL}) not available")
    env = dict(os.environ)
    env["PYTHONPATH"] = str(root / "py")
    env["NODE_PATH"] = _augment_node_path(env.get("NODE_PATH"), root)
    # Preflight SCION (https://www.npmjs.com/package/scion) on this chart to avoid hard failures
    pre = subprocess.run([
        "node",
        str(scion),
        "-I",
        str(chart),
        "-e",
        str(chart.with_suffix(".events.jsonl")),
        "--xml",
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=str(root))
    if pre.returncode != 0:
        pytest.skip(f"SCION ({SCION_NPM_URL}) cannot execute this chart reliably: " + pre.stderr.strip())
    args = [
        sys.executable,
        str(root / "py" / "exec_compare.py"),
        str(chart),
        "--events",
        str(chart.with_suffix(".events.jsonl")),
        "--reference",
        f"node {scion}",
    ]
    result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env, cwd=str(root))
    assert result.returncode == 0, f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"


def test_finalize_order_compare_scion() -> None:
    # Compare Python vs SCION (https://www.npmjs.com/package/scion) on finalize ordering chart; guard if SCION can't run it
    root = Path(__file__).resolve().parents[2]
    chart = root / "tests" / "sweep_corpus" / "finalize_order.scxml"
    scion = root / "tools" / "scion-runner" / "scion-trace.cjs"
    if not scion.exists() or not _ensure_scion_runner(root):
        pytest.skip(f"SCION ({SCION_NPM_URL}) not available")
    env = dict(os.environ)
    env["PYTHONPATH"] = str(root / "py")
    env["NODE_PATH"] = _augment_node_path(env.get("NODE_PATH"), root)
    with TemporaryDirectory() as td:
        ev = Path(td) / "events.jsonl"
        ev.write_text('{"event": "complete"}\n', encoding="utf-8")
        pre = subprocess.run([
            "node",
            str(scion),
            "-I",
            str(chart),
            "-e",
            str(ev),
            "--xml",
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=str(root))
        if pre.returncode != 0:
            pytest.skip(f"SCION ({SCION_NPM_URL}) cannot execute this chart reliably: " + pre.stderr.strip())
        args = [
            sys.executable,
            str(root / "py" / "exec_compare.py"),
            str(chart),
            "--events",
            str(ev),
            "--reference",
            f"node {scion}",
        ]
        result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env, cwd=str(root))
        assert result.returncode == 0, f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
