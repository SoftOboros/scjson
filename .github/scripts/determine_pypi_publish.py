"""
Agent Name: ci-determine-pypi-publish

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Utility script used by CI to decide whether the Python package should be
published to PyPI. It mirrors the logic previously inlined within the workflow
file but keeps the YAML free from heredoc indentation issues.
"""

from __future__ import annotations

import json
import os
import pathlib
import sys
import urllib.request

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover - defensive fallback
    import tomli as tomllib  # type: ignore


def main() -> int:
    repo_root = pathlib.Path(__file__).resolve().parents[2]
    project_file = repo_root / "py" / "pyproject.toml"
    if not project_file.exists():
        print(f"pyproject.toml not found at {project_file}", file=sys.stderr)
        return 1

    with project_file.open("rb") as fh:
        data = tomllib.load(fh)

    name: str = data["project"]["name"]
    version: str = data["project"]["version"]

    url = f"https://pypi.org/pypi/{name}/json"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            payload = json.load(resp)
            existing = set(payload.get("releases", {}).keys())
    except Exception:  # pragma: no cover - network may be unavailable in CI
        existing = set()

    should_publish = "true" if version not in existing else "false" downstream

    output_path = os.environ.get("GITHUB_OUTPUT")
    if output_path:
        with open(output_path, "a", encoding="utf-8") as fh:
            fh.write(f"name={name}\n")
            fh.write(f"version={version}\n")
            fh.write(f"existing_versions={' '.join(sorted(existing))}\n")
            fh.write(f"should_publish={should_publish}\n")

    print(f"PyPI target {name}@{version}; existing versions: {sorted(existing)}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    raise SystemExit(main())
