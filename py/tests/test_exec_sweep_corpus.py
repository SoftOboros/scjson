"""
Agent Name: python-exec-sweep-corpus-tests

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Generate and check corpus coverage with SCION when its dependencies are available.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from scjson_argv import format_command
from scion_support import ensure_scion_runner


def test_exec_sweep_small_corpus(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    corpus = root / "tests" / "sweep_corpus"
    assert corpus.exists()

    workdir = tmp_path / "artifacts"
    env = dict(os.environ)
    env["PYTHONPATH"] = str(root / "py")
    cmd = [
        sys.executable,
        str(root / "py" / "exec_sweep.py"),
        str(corpus),
        "--glob",
        "**/*.scxml",
        "--generate-vectors",
        "--workdir",
        str(workdir),
    ]
    if not ensure_scion_runner(root):
        cmd.extend(["--reference", format_command([sys.executable, "-m", "scjson.cli", "engine-trace"])])
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
    assert result.returncode == 0, f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    # Coverage summary should be written when vectors are generated
    summary = workdir / "coverage-summary.json"
    assert summary.exists(), "coverage-summary.json missing"
    data = json.loads(summary.read_text(encoding="utf-8"))
    assert "totals" in data and "charts" in data
    # All corpus charts should appear
    for name in (
        "one.scxml",
        "invoke_deferred.scxml",
        "delayed_init.scxml",
        "toggle_simple.scxml",
        "branch_flag.scxml",
        "membership.scxml",
        "range.scxml",
    ):
        matches = [k for k in data["charts"].keys() if k.endswith(name)]
        assert matches, f"missing chart entry for {name}"
        if name in {"membership.scxml", "range.scxml", "branch_flag.scxml"}:
            assert data["charts"][matches[0]]["firedTransitions"] > 0, name


@pytest.mark.parametrize("chart,payloads,expected", [
    ("branch_flag", [None], ["s2"]),
    ("branch_flag", [{"flag": False}], ["s2"]),
    ("branch_flag", [{"flag": True}], ["s1"]),
    ("membership", [None, {"kind": "C"}, {"kind": "A"}], ["s0", "s0", "ok"]),
    ("membership", [{"kind": "B"}], ["ok"]),
    ("range", [{"n": n} for n in (-1, 0, 5, 6, 3)], ["s0", "s0", "s0", "s0", "ok"]),
])
def test_shared_guards_in_python_and_scion(chart, payloads, expected, tmp_path):
    """Check each engine against the intended state after every event."""
    root = Path(__file__).resolve().parents[2]
    source = root / "tests" / "sweep_corpus" / f"{chart}.scxml"
    events = tmp_path / "events.jsonl"
    events.write_text("".join(json.dumps({"event": "go", "data": p}) + "\n" for p in payloads))
    args = ["--xml", "-I", str(source), "-e", str(events)]
    python = [sys.executable, "-m", "scjson.cli", "engine-trace"]
    ref = ["node", str(root / "tools" / "scion-runner" / "scion-trace.cjs")]
    for command in (python, ref):
        if command == ref and not ensure_scion_runner(root):
            pytest.skip("SCION dependencies unavailable")
        result = subprocess.run(command + args, cwd=root / "py", capture_output=True, text=True, check=True)
        states = [json.loads(line)["configuration"] for line in result.stdout.splitlines()]
        assert states == [["s0"]] + [[state] for state in expected], command
