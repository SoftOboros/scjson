"""
Agent Name: python-uber-conv-corpus-tests

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Regression tests for the focused conversion corpus and uber-test harness
selection added by CONV-I.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


def _env(root: Path) -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(root / "py")
    return env


def test_uber_test_runs_focused_conversion_corpus(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    corpus = root / "tests" / "conv_corpus"
    out_dir = tmp_path / "uber"

    result = subprocess.run(
        [
            sys.executable,
            str(root / "py" / "uber_test.py"),
            str(out_dir),
            "--language",
            "python",
            "--corpus",
            str(corpus),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=_env(root),
        cwd=str(root),
    )

    assert result.returncode == 0, f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    combined = f"{result.stdout}\n{result.stderr}".lower()
    assert "mismatch" not in combined
    assert (out_dir / "python" / "json" / "inclusion_surface.scjson").exists()
    assert (out_dir / "python" / "xml" / "help_text_comments.scxml").exists()


def test_uber_test_python_exec_compare_mode_accepts_reference(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    corpus = root / "tests" / "exec"
    reference = f"{sys.executable} -m scjson.cli engine-trace"

    result = subprocess.run(
        [
            sys.executable,
            str(root / "py" / "uber_test.py"),
            str(tmp_path / "exec-uber"),
            "--corpus",
            str(corpus),
            "--subset",
            "toggle.scxml",
            "--python-exec-compare",
            "--exec-reference",
            reference,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=_env(root),
        cwd=str(root),
    )

    assert result.returncode == 0, f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    assert "exec_compare toggle.scxml ... OK" in result.stdout


@pytest.mark.skipif(shutil.which("ruby") is None, reason="Ruby CLI unavailable")
def test_uber_test_ruby_matches_focused_conversion_corpus(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    corpus = root / "tests" / "conv_corpus"

    result = subprocess.run(
        [
            sys.executable,
            str(root / "py" / "uber_test.py"),
            str(tmp_path / "ruby-uber"),
            "--language",
            "ruby",
            "--corpus",
            str(corpus),
            "--consensus-warn",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=_env(root),
        cwd=str(root),
    )

    assert result.returncode == 0, f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    combined = f"{result.stdout}\n{result.stderr}".lower()
    assert "mismatch" not in combined
