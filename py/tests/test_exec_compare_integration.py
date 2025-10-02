"""
Agent Name: python-exec-compare-tests

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Integration tests for exec_compare vector generation and coverage print.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _write_chart(tmp: Path, name: str, xml: str) -> Path:
    p = tmp / name
    p.write_text(xml.strip(), encoding="utf-8")
    return p


def test_exec_compare_generates_vectors_and_prints_coverage(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    chart = _write_chart(
        tmp_path,
        "a.scxml",
        """
        <scxml initial=\"s0\" xmlns=\"http://www.w3.org/2005/07/scxml\">
          <state id=\"s0\"/>
        </scxml>
        """,
    )
    workdir = tmp_path / "artifacts"
    env = dict(os.environ)
    env["PYTHONPATH"] = str(root)
    reference = f"{sys.executable} -m scjson.cli engine-trace"
    cmd = [
        sys.executable,
        str(root / "exec_compare.py"),
        str(chart),
        "--generate-vectors",
        "--workdir",
        str(workdir),
        "--reference",
        reference,
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env, cwd=str(root))
    assert result.returncode == 0, f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    assert "Generated vector coverage:" in result.stdout


def test_exec_compare_uses_existing_events_no_generation(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    chart = _write_chart(
        tmp_path,
        "b.scxml",
        """
        <scxml initial=\"s0\" xmlns=\"http://www.w3.org/2005/07/scxml\">
          <state id=\"s0\"/>
        </scxml>
        """,
    )
    # Provide an empty events stream explicitly
    events = tmp_path / "b.events.jsonl"
    events.write_text("", encoding="utf-8")
    env = dict(os.environ)
    env["PYTHONPATH"] = str(root)
    reference = f"{sys.executable} -m scjson.cli engine-trace"
    cmd = [
        sys.executable,
        str(root / "exec_compare.py"),
        str(chart),
        "--events",
        str(events),
        "--reference",
        reference,
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env, cwd=str(root))
    assert result.returncode == 0, f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    # No coverage message expected because we didn't generate vectors here
    assert "Generated vector coverage:" not in result.stdout

