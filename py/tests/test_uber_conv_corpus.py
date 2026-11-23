"""
Agent Name: python-uber-conv-corpus-tests

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Regression tests for the focused conversion corpus and uber-test harness
selection added by CONV-I.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from scjson_argv import format_command

import pytest
import uber_test


def _env(root: Path) -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(root / "py")
    return env


@pytest.mark.parametrize("fault", ["missing", "reordered", "invalid_xml", "converter_exit"])
def test_requested_corpus_comparison_rejects_bad_run(tmp_path, monkeypatch, fault):
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    source = '<scxml><state id="a"/><state id="b"/></scxml>'
    chart = corpus / "case.scxml"
    chart.write_text(source, encoding="utf-8")
    canonical = json.loads(uber_test.SCXMLDocumentHandler().xml_to_json(source))
    out = tmp_path / "out"
    # A previous successful run must never supply missing evidence.
    stale = out / "python" / "json" / "case.scjson"
    stale.parent.mkdir(parents=True)
    stale.write_text(json.dumps(canonical), encoding="utf-8")
    monkeypatch.setattr(uber_test, "_available", lambda *_: True)
    monkeypatch.setattr(uber_test.MismatchInvestigator, "_reference_summary", lambda *a, **kw: {})

    def convert(args, **kwargs):
        if fault == "converter_exit":
            raise subprocess.CalledProcessError(7, args, stderr="deliberate failure")
        dest = Path(args[args.index("-o") + 1])
        if "json" in args:
            if fault == "missing":
                return
            if fault == "reordered":
                canonical["state"].reverse()
            (dest / "case.scjson").write_text(json.dumps(canonical), encoding="utf-8")
        else:
            (dest / chart.name).write_text("<broken" if fault == "invalid_xml" else source, encoding="utf-8")

    monkeypatch.setattr(uber_test.subprocess, "run", convert)
    with pytest.raises(SystemExit, match="failed 1 converter comparison|converter exited 7"):
        uber_test.main(out, "python", corpus_root=corpus)


def test_requested_empty_corpus_fails(tmp_path):
    with pytest.raises(SystemExit, match="No admitted charts"):
        uber_test.main(tmp_path / "out", "python", corpus_root=tmp_path)


def test_reference_cannot_silently_shrink_the_corpus(tmp_path):
    (tmp_path / "valid.scxml").write_text("<scxml/>", encoding="utf-8")
    (tmp_path / "broken.scxml").write_text("<broken", encoding="utf-8")
    with pytest.raises(SystemExit, match="unexpectedly refused 1"):
        uber_test.main(tmp_path / "out", "python", corpus_root=tmp_path)


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
    reference = format_command([sys.executable, "-m", "scjson.cli", "engine-trace"])

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
