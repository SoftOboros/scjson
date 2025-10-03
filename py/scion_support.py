"""
Agent Name: python-scion-support

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Helpers that ensure the bundled SCION Node.js runner is available for
comparisons and expose utility functions for configuring the environment.
"""

from __future__ import annotations

from pathlib import Path
import os
import shutil
import subprocess
from typing import Dict, Optional

SCION_NPM_URL = "https://www.npmjs.com/package/scion"

_SCION_READY: Dict[Path, bool] = {}


def ensure_scion_runner(repo_root: Path) -> bool:
    """Ensure the SCION Node runner is installed and ready.

    @param repo_root: Repository root used to locate ``tools/scion-runner``.
    @returns True when dependencies are present or successfully installed.
    """

    resolved_root = repo_root.resolve()
    cached = _SCION_READY.get(resolved_root)
    if cached is not None:
        return cached

    runner_dir = resolved_root / "tools" / "scion-runner"
    runner = runner_dir / "scion-trace.cjs"
    if not runner.exists():
        _SCION_READY[resolved_root] = False
        return False

    if shutil.which("node") is None:
        _SCION_READY[resolved_root] = False
        return False

    node_modules = runner_dir / "node_modules"
    jsdom_path = node_modules / "jsdom"
    scxml_path = node_modules / "scxml"
    if jsdom_path.exists() and scxml_path.exists():
        _SCION_READY[resolved_root] = True
        return True

    npm_exe = shutil.which("npm")
    if npm_exe is None:
        _SCION_READY[resolved_root] = False
        return False

    lock_file = runner_dir / "package-lock.json"
    cmd = [npm_exe, "ci" if lock_file.exists() else "install"]
    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=str(runner_dir),
    )
    if proc.returncode != 0:
        _SCION_READY[resolved_root] = False
        return False

    ready = jsdom_path.exists() and scxml_path.exists()
    _SCION_READY[resolved_root] = ready
    return ready


def augment_node_path(existing: Optional[str], repo_root: Path) -> str:
    """Prepend the SCION ``node_modules`` directory to ``NODE_PATH``.

    @param existing: Existing ``NODE_PATH`` value (if any).
    @param repo_root: Repository root containing ``tools/scion-runner``.
    @returns Updated ``NODE_PATH`` string that includes SCION dependencies.
    """

    runner_modules = (repo_root / "tools" / "scion-runner" / "node_modules").resolve()
    parts = [str(runner_modules)]
    if existing:
        parts.append(existing)
    return os.pathsep.join(part for part in parts if part)

