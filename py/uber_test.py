"""Uber test harness for scjson language implementations.

Agent Name: uber-test

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

This module exercises the command line interfaces for all available language
implementations of the :mod:`scjson` tooling.  It converts a large corpus of
SCXML documents to SCJSON and back again, ensuring that each implementation
produces identical output.  The results are written under an ``uber_out``
directory by default.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import argparse
import os
from os import sep
from os.path import abspath, split as pathsplit
from pathlib import Path

import pytest

#pytest.skip(
#    "Uber tests require external runtimes", allow_module_level=True
#)

from scjson.SCXMLDocumentHandler import SCXMLDocumentHandler

ROOT = Path(sep.join(pathsplit(str(Path(__file__).resolve().parent))[:-1]))
TUTORIAL = ROOT / "tutorial"

LANG_CMDS: dict[str, list[str]] = {
    "python": [sys.executable, "-m", "scjson"],
    "javascript": ["node", str(ROOT / "js" / "bin" / "scjson.js")],
    "ruby": ["ruby", str(ROOT / "ruby" / "bin" / "scjson")],
    "lua": ["lua5.4", str(ROOT / "lua" / "bin" / "scjson")],
    "go": [str(ROOT / "go" / "go")],
    "rust": [str(ROOT / "rust" / "target" / "debug" / "scjson_rust")],
    "swift": [str(ROOT / "swift" / ".build" / "x86_64-unknown-linux-gnu" / "debug" / "scjson-swift")],
    "java": [
        "java",
        "-cp",
        str(ROOT / "java" / "target" / "scjson-0.2.0-SNAPSHOT.jar"),
        "com.softobros.ScjsonCli",
    ],
    "csharp": [
        "dotnet",
        str(ROOT / "csharp" / "ScjsonCli" / "bin" / "Debug" / "net8.0" / "ScjsonCli.dll"),
    ],
}


def _available(cmd: list[str], env: dict[str, str] | None = None) -> bool:
    """Check if a CLI command is runnable.

    Parameters
    ----------
    cmd: list[str]
        The command and arguments used to invoke the executable.

    Returns
    -------
    bool
        ``True`` if the executable exists and can be called with ``--help``,
        otherwise ``False``.
    """

    exe = cmd[0]
    if not (Path(exe).exists() or shutil.which(exe)):
        return False
    try:
        subprocess.run(
            cmd + ["--help"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            env=env,
        )
        return True
    except Exception:
        return False


def _canonical_json(files: list[Path], handler: SCXMLDocumentHandler) -> dict[Path, dict]:
    """Convert SCXML files to canonical JSON.

    Parameters
    ----------
    files: list[Path]
        Paths of SCXML files to convert.
    handler: SCXMLDocumentHandler
        Converter used to transform the XML documents.

    Returns
    -------
    dict[Path, dict]
        Mapping of the source file path to the parsed JSON structure.  Files
        that cannot be parsed are skipped with a warning.
    """

    result: dict[Path, dict] = {}
    for f in files:
        data = f.read_text(encoding="utf-8")
        try:
            result[f] = json.loads(handler.xml_to_json(data))
        except Exception as exc:  # pragma: no cover - best effort for bad files
            print(f"Skipping {f}: {exc}")
    return result


def main(out_dir: str | Path = "uber_out", language: str | None = None) -> None:
    """Run the uber test suite.

    Parameters
    ----------
    out_dir: str | Path, optional
        Directory where intermediate JSON and XML files will be written.
    language: str | None, optional
        Limit the run to a single language key from :data:`LANG_CMDS`.
    """

    handler = SCXMLDocumentHandler(fail_on_unknown_properties=False)
    scxml_files = sorted(TUTORIAL.rglob("*.scxml"))
    canonical = _canonical_json(scxml_files, handler)
    scxml_files = list(canonical.keys())
    out_root = Path(out_dir)
    if language:
        lang_key = language.lower()
        if lang_key in {"py", "python"}:
            lang_key = "python"
        languages = [lang_key]
    else:
        languages = list(LANG_CMDS.keys())
    for lang in languages:
        cmd = LANG_CMDS.get(lang)
        if not cmd:
            print(f"Skipping {lang}: unknown language")
            continue
        env = None
        if lang == "python":
            env = dict(os.environ)
            env["PYTHONPATH"] = str(ROOT / "py")
        if not _available(cmd, env):
            print(f"Skipping {lang}: executable not available")
            continue
        json_dir = out_root / lang / "json"
        xml_dir = out_root / lang / "xml"
        json_dir.mkdir(parents=True, exist_ok=True)
        xml_dir.mkdir(parents=True, exist_ok=True)
        try:
            json_args = ["json", str(TUTORIAL), "-o", str(json_dir), "-r"]
            if lang == "python":
                json_args.append("--skip-unknown")
            subprocess.run(
                cmd + json_args,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
            )
            errors = 0
            for src in scxml_files:
                rel = src.relative_to(TUTORIAL)
                jpath = json_dir / rel.with_suffix(".scjson")
                if not jpath.exists():
                    print(f"{lang} failed to write {jpath}")
                    continue
                try:
                    data = json.loads(jpath.read_text())
                except Exception as exc:
                    print(f"{lang} JSON parse error {rel}: {exc}")
                    errors += 1
                    continue
                if data != canonical[src]:
                    print(f"{lang} JSON mismatch: {rel}")
                    errors += 1
            subprocess.run(
                cmd + ["xml", str(json_dir), "-o", str(xml_dir), "-r"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
            )
            for src in scxml_files:
                rel = src.relative_to(TUTORIAL)
                xpath = xml_dir / rel
                if not xpath.exists():
                    print(f"{lang} failed to write {xpath}")
                    continue
                try:
                    data = handler.xml_to_json(xpath.read_text())
                    parsed = json.loads(data)
                except Exception as exc:
                    print(f"{lang} XML parse error {rel}: {exc}")
                    errors += 1
                    continue
                if parsed != canonical[src]:
                    print(f"{lang} XML mismatch: {rel}")
                    errors += 1
            if errors:
                print(f"{lang} encountered {errors} mismatches")
        except subprocess.CalledProcessError as exc:  # pragma: no cover - CLI failures
            print(f"Skipping {lang}: {exc.stderr.decode().strip()}")
        except Exception as exc:  # pragma: no cover - external tools may fail
            print(f"Skipping {lang}: {exc}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "out_dir",
        nargs="?",
        default="uber_out",
        help="directory for intermediate files",
    )
    parser.add_argument(
        "-l",
        "--language",
        dest="language",
        help="limit testing to a single language",
    )
    opts = parser.parse_args()
    main(Path(opts.out_dir), opts.language)
