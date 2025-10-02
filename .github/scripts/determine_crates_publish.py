"""
Agent Name: ci-determine-crates-publish

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

CI helper that checks crates.io for the current Rust package version and emits
GitHub Actions outputs describing whether a publish attempt should be made.
"""

from __future__ import annotations

import json
import os
import pathlib
import sys
import urllib.request

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore


def main() -> int:
    repo_root = pathlib.Path(__file__).resolve().parents[2]
    cargo_toml = repo_root / "rust" / "Cargo.toml"
    if not cargo_toml.exists():
        print(f"Cargo.toml not found at {cargo_toml}", file=sys.stderr)
        return 1

    with cargo_toml.open("rb") as fh:
        data = tomllib.load(fh)

    name: str = data["package"]["name"]
    version: str = data["package"]["version"]

    url = f"https://crates.io/api/v1/crates/{name}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            payload = json.load(resp)
            existing = [v.get("num") for v in payload.get("versions", []) if v.get("num")]
    except Exception:  # pragma: no cover
        existing = []

    should_publish = "true" if version not in existing else "false"

    output_path = os.environ.get("GITHUB_OUTPUT")
    if output_path:
        with open(output_path, "a", encoding="utf-8") as fh:
            fh.write(f"name={name}\n")
            fh.write(f"version={version}\n")
            fh.write(f"should_publish={should_publish}\n")

    print(f"Crates target {name}@{version}; existing versions: {existing}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
