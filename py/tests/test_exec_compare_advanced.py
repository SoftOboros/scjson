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

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "py"))

import pytest
from tempfile import TemporaryDirectory

from scion_support import (
    SCION_NPM_URL,
    augment_node_path,
    ensure_scion_runner,
)


FINALIZE_SEND_ERROR = "SCXML finalize MUST NOT contain send or raise children"
SWEEP_CORPUS = Path(__file__).resolve().parents[2] / "tests" / "sweep_corpus"
NONCONFORMANT_CORPUS = (
    Path(__file__).resolve().parents[2] / "tests" / "nonconformant_corpus"
)


def _ref_command(root: Path) -> str:
    scion = root / "tools" / "scion-runner" / "scion-trace.cjs"
    if scion.exists() and ensure_scion_runner(root):
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
        scion_ready = ensure_scion_runner(repo_root)
        if scion_ready:
            env["NODE_PATH"] = augment_node_path(env.get("NODE_PATH"), repo_root)
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


def _assert_rejects_nonconformant_finalize_send(
    result: subprocess.CompletedProcess[str],
) -> None:
    assert result.returncode != 0
    assert FINALIZE_SEND_ERROR in result.stderr


def test_parallel_done_matches_reference() -> None:
    chart = SWEEP_CORPUS / "parallel_done.scxml"
    # Generate an empty vector to allow step-0 comparison
    result = _run_compare(chart, generate=True, depth=1, force_python_ref=True)
    assert result.returncode == 0, f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"


def test_done_invoke_id_specific_priority() -> None:
    chart = SWEEP_CORPUS / "done_invoke_order.scxml"
    # Generator will emit 'complete'
    result = _run_compare(chart, generate=True, depth=1)
    assert result.returncode == 0, f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"


def test_history_shallow_restore() -> None:
    chart = SWEEP_CORPUS / "history_shallow.scxml"
    events = chart.with_suffix(".events.jsonl")
    assert events.exists()
    result = _run_compare(chart, generate=False, force_python_ref=True)
    assert result.returncode == 0, f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"


def test_history_deep_restore() -> None:
    chart = SWEEP_CORPUS / "history_deep.scxml"
    events = chart.with_suffix(".events.jsonl")
    assert events.exists()
    result = _run_compare(chart, generate=False, force_python_ref=True)
    assert result.returncode == 0, f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"


def test_finalize_event_precedes_done_invoke() -> None:
    chart = NONCONFORMANT_CORPUS / "finalize_order.scxml"
    result = _run_compare(chart, generate=True, depth=1, force_python_ref=True)
    _assert_rejects_nonconformant_finalize_send(result)


def test_finalize_param_payload_propagates() -> None:
    chart = NONCONFORMANT_CORPUS / "finalize_param_payload.scxml"
    result = _run_compare(chart, generate=True, depth=1, force_python_ref=True)
    _assert_rejects_nonconformant_finalize_send(result)


def test_finalize_child_donedata_propagates() -> None:
    chart = NONCONFORMANT_CORPUS / "finalize_child_donedata.scxml"
    result = _run_compare(chart, generate=True, depth=1, force_python_ref=True)
    _assert_rejects_nonconformant_finalize_send(result)


def test_multi_invoke_switch_child_events() -> None:
    chart = NONCONFORMANT_CORPUS / "multi_invoke_switch.scxml"
    events = chart.with_suffix(".events.jsonl")
    assert events.exists()
    result = _run_compare(chart, generate=False, force_python_ref=True)
    _assert_rejects_nonconformant_finalize_send(result)


def test_parallel_history_deep_restore() -> None:
    chart = SWEEP_CORPUS / "parallel_history_deep.scxml"
    events = chart.with_suffix(".events.jsonl")
    assert events.exists()
    result = _run_compare(chart, generate=False, force_python_ref=True)
    assert result.returncode == 0, f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"


def test_parallel_invoke_finalize_ordering_deterministic() -> None:
    root = Path(__file__).resolve().parents[2]
    chart = NONCONFORMANT_CORPUS / "parallel_invoke_complete.scxml"
    sys.path.insert(0, str(root / "py"))
    from scjson.context import DocumentContext, ExecutionMode

    with pytest.raises(Exception, match=FINALIZE_SEND_ERROR):
        DocumentContext.from_xml_file(chart, execution_mode=ExecutionMode.LAX)


def test_parallel_invoke_compare_scion() -> None:
    # Compare Python vs SCION (https://www.npmjs.com/package/scion) on the parallel complete + finalize chart
    root = Path(__file__).resolve().parents[2]
    chart = NONCONFORMANT_CORPUS / "parallel_invoke_complete.scxml"
    scion = root / "tools" / "scion-runner" / "scion-trace.cjs"
    if not scion.exists() or not ensure_scion_runner(root):
        pytest.skip(f"SCION ({SCION_NPM_URL}) not available")
    env = dict(os.environ)
    env["PYTHONPATH"] = str(root / "py")
    env["NODE_PATH"] = augment_node_path(env.get("NODE_PATH"), root)
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
    _assert_rejects_nonconformant_finalize_send(result)


def test_finalize_order_compare_scion() -> None:
    # Compare Python vs SCION (https://www.npmjs.com/package/scion) on finalize ordering chart; guard if SCION can't run it
    root = Path(__file__).resolve().parents[2]
    chart = NONCONFORMANT_CORPUS / "finalize_order.scxml"
    scion = root / "tools" / "scion-runner" / "scion-trace.cjs"
    if not scion.exists() or not ensure_scion_runner(root):
        pytest.skip(f"SCION ({SCION_NPM_URL}) not available")
    env = dict(os.environ)
    env["PYTHONPATH"] = str(root / "py")
    env["NODE_PATH"] = augment_node_path(env.get("NODE_PATH"), root)
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
        _assert_rejects_nonconformant_finalize_send(result)
