"""
Agent Name: python-exec-sweep-tests

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Integration test for exec_sweep vector generation and coverage summary emission.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from scjson_argv import format_command


def test_exec_sweep_generates_coverage_summary(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    charts_dir = tmp_path / "charts"
    charts_dir.mkdir(parents=True, exist_ok=True)
    chart = charts_dir / "one.scxml"
    chart.write_text(
        (
            """
            <scxml initial="s0" xmlns="http://www.w3.org/2005/07/scxml">
              <state id="s0"/>
            </scxml>
            """
        ).strip(),
        encoding="utf-8",
    )

    workdir = tmp_path / "artifacts"
    reference = format_command([sys.executable, "-m", "scjson.cli", "engine-trace"])
    env = dict(os.environ)
    env["PYTHONPATH"] = str(root / "py")
    cmd = [
        sys.executable,
        str(root / "py" / "exec_sweep.py"),
        str(charts_dir),
        "--glob",
        "**/*.scxml",
        "--generate-vectors",
        "--workdir",
        str(workdir),
        "--reference",
        reference,
        "--gen-depth",
        "1",
        "--gen-limit",
        "1",
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
    assert result.returncode == 0, f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"

    summary = workdir / "coverage-summary.json"
    assert summary.exists()
    data = json.loads(summary.read_text(encoding="utf-8"))
    assert "totals" in data and "charts" in data
    # Expect the chart path to be present in the charts map (stringified path)
    assert any(str(chart) in k or k == str(chart) for k in data["charts"].keys())


def test_sweep_checks_fresh_reference_output(tmp_path: Path) -> None:
    """Keep an external reference authoritative across retries in the same workdir."""
    chart = tmp_path / "one.scxml"
    chart.write_text('<scxml xmlns="http://www.w3.org/2005/07/scxml" initial="s"><state id="s"/></scxml>')
    golden = tmp_path / "golden.jsonl"
    step = {
        "step": 0, "event": None, "configuration": ["s"], "enteredStates": ["s"],
        "exitedStates": [], "firedTransitions": [], "actionLog": [], "datamodelDelta": {},
    }
    golden.write_text(json.dumps(step))
    reference = tmp_path / "reference.py"
    reference.write_text(
        "import shutil, sys\n"
        "shutil.copyfile(sys.argv[1], sys.argv[sys.argv.index('-o') + 1])\n"
    )
    module_dir = Path(__file__).resolve().parents[1]
    env = dict(os.environ, SCJSON_REF_ENGINE_CMD=format_command([sys.executable, str(reference), str(golden)]))
    cmd = [sys.executable, str(module_dir / "exec_sweep.py"), str(tmp_path), "--workdir", str(tmp_path / "results")]

    def run():
        return subprocess.run(cmd, cwd=tmp_path, env=env, capture_output=True, text=True)

    matched = run()
    assert matched.returncode == 0, matched.stdout + matched.stderr
    assert "1 compared" in matched.stdout

    step["configuration"] = []
    golden.write_text(json.dumps(step))
    wrong = run()
    assert wrong.returncode == 1 and "configuration:" in wrong.stdout
    golden.write_text("")
    empty = run()
    assert empty.returncode == 1 and "empty trace" in empty.stdout
    reference.write_text("pass\n")
    missing = run()
    assert missing.returncode == 1 and "did not write" in missing.stdout
