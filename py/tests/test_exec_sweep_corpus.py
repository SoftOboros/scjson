"""
Agent Name: python-exec-sweep-corpus-tests

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

CI-friendly sweep test over a small corpus, defaulting to [SCION](https://www.npmjs.com/package/scion) if present or the Python engine otherwise.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


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
        # Reference omitted on purpose: uses SCION (https://www.npmjs.com/package/scion) if present or Python fallback
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
    assert result.returncode in (0, 1), f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
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
