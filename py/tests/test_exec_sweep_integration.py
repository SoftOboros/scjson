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
    reference = f"{sys.executable} -m scjson.cli engine-trace"
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
