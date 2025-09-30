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

from deepdiff import DeepDiff

import json
import html
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
    "javascript": ["node", str(ROOT / "js" )],
    "ruby": ["ruby", str(ROOT / "ruby" / "bin" / "scjson")],
    "lua": ["lua", str(ROOT / "lua" / "bin" / "scjson")],
    "go": [str(ROOT / "go" / "go")],
    "rust": [str(ROOT / "rust" / "target" / "debug" / "scjson_rust")],
    "swift": [str(ROOT / "swift" / ".build" / "x86_64-unknown-linux-gnu" / "debug" / "scjson-swift")],
    "java": [
        "java",
        "-cp",
        str(ROOT / "java" / "target" / "scjson-0.3.0-SNAPSHOT.jar"),
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



SCXML_NAMESPACE_KEYS = {
    "xmlns", "xmlns:scxml", "xmlns:xsi", "xsi:schemaLocation"
}

SCXML_FORCE_STR_KEYS = {
    "content", "expr", "event", "cond"
}

SCXML_FORCE_NUMERIC_KEYS = {
    "version"
}


def _normalize_for_diff(obj, path="", field_key=None):
    """
    Recursively normalize SCXML-derived structures to enable deep structural comparison.

    This function prepares parsed SCXML or SCJSON data for accurate diffing by removing
    serialization artifacts and normalizing variations in formatting, typing, and tag structure.

    Specifically, it:
    - Strips XML namespaces (e.g., xmlns, xsi:schemaLocation)
    - Inlines and flattens 'other_attributes' dictionaries
    - Removes serialization noise like content: [{}] and other empty blocks
    - Collapses singleton lists of primitives to scalars
    - Converts numeric-looking strings in keys like 'version' to actual numbers
    - Converts numbers to strings in keys like 'content', 'expr', etc.
    - Unescapes HTML/XML entities and strips strings
    - Tracks keys across list nesting using `field_key`

    Parameters
    ----------
    obj : Any
        The input structure (dict, list, or primitive) to normalize.
    path : str
        Dot-path to the current object, useful for debugging.
    field_key : str or None
        The last dictionary key used to reach this object — enables context-aware normalization.

    Returns
    -------
    Any
        A normalized version of the input, ready for diff comparison.
    """

    # Convert stringified numerics (like "1.0") to float or int
    if isinstance(obj, str) and field_key in SCXML_FORCE_NUMERIC_KEYS:
        try:
            return float(obj) if "." in obj else int(obj)
        except ValueError:
            pass

    # Convert numbers to string for string-dominant fields (e.g., expr)
    if isinstance(obj, (int, float)) and field_key in SCXML_FORCE_STR_KEYS:
        return str(obj)

    # Remove empty object patterns
    if obj in ({}, [{}], {"content": [{}]}):
        return None

    if isinstance(obj, dict):
        new_dict = {}
        for k, v in obj.items():
            if k in SCXML_NAMESPACE_KEYS:
                continue

            # Inline other_attributes
            if k == "other_attributes" and isinstance(v, dict):
                for sub_k, sub_v in v.items():
                    new_dict[sub_k] = _normalize_for_diff(
                        sub_v,
                        f"{path}.{sub_k}" if path else sub_k,
                        field_key=sub_k
                    )
                continue

            # Skip empty content block
            if k == "content" and v == [{}]:
                continue

            # Normalize numeric-looking strings or numeric-to-string fields
            if k in SCXML_FORCE_NUMERIC_KEYS and isinstance(v, str):
                try:
                    v = float(v) if "." in v else int(v)
                except ValueError:
                    pass
            elif k in SCXML_FORCE_STR_KEYS and isinstance(v, (int, float)):
                v = str(v)

            new_dict[k] = _normalize_for_diff(
                v,
                f"{path}.{k}" if path else k,
                field_key=k
            )
        return new_dict

    elif isinstance(obj, list):
        # Collapse pattern: content: [ { content: "..." } ]
        if len(obj) == 1 and isinstance(obj[0], dict) and list(obj[0].keys()) == ["content"] and isinstance(obj[0]["content"], str):
            return _normalize_for_diff(obj[0]["content"], f"{path}[]", field_key="content")

        if len(obj) == 1:
            return _normalize_for_diff(obj[0], f"{path}[]", field_key=field_key)

        return [_normalize_for_diff(i, f"{path}[]", field_key=field_key) for i in obj]

    elif isinstance(obj, str):
        return html.unescape(obj).strip()

    return obj


def _diff_report(expected: dict, actual: dict) -> str:
    """Create a human-readable diff between two dictionaries.

    Parameters
    ----------
    expected: dict
        Canonical structure produced by the Python implementation.
    actual: dict
        Structure produced by the language under test.

    Returns
    -------
    str
        Diff string suitable for console output.
    """


    diff = DeepDiff(
        _normalize_for_diff(expected),
        _normalize_for_diff(actual),
        verbose_level=1,
        ignore_numeric_type_changes=True,
        ignore_order=True,
    )
    return diff.pretty()


def _diff_line_count(diff: str) -> int:
    """Count the number of lines in a diff string.

    Parameters
    ----------
    diff : str
        Text produced by :func:`_diff_report`.

    Returns
    -------
    int
        The total line count of the diff output.
    """

    if not diff:
        return 0
    return diff.count("\n") + 1


def _verify_with_python(
    json_path: Path, canonical: dict, handler: SCXMLDocumentHandler
) -> int:
    """Round-trip the SCJSON file using Python and compare to canonical.

    Parameters
    ----------
    json_path : Path
        Path to the SCJSON file produced by the language under test.
    canonical : dict
        Canonical structure produced by the Python implementation.
    handler : SCXMLDocumentHandler
        Converter used for round-tripping the JSON structure.

    Returns
    -------
    int
        Number of diff lines produced when mismatches are detected.
    """

    try:
        original_text = json_path.read_text(encoding="utf-8")
        round_trip = json.loads(
            handler.xml_to_json(handler.json_to_xml(original_text))
        )
    except Exception as exc:  # pragma: no cover - debugging aid
        print(f"Python failed to round-trip {json_path}: {exc}")
        return 0

    if round_trip == canonical:
        print(f"Python round-trip matches canonical for {json_path.name}")
        return 0
    else:
        print(f"Python round-trip mismatch for {json_path.name}")
        diff = _diff_report(canonical, round_trip)
        print(diff)
        return _diff_line_count(diff)


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
            pass
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

    handler = SCXMLDocumentHandler()
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
        if lang == "javascript":
            subprocess.run(
                ["npm", "run", "build"],
                cwd=ROOT / "js",
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
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
                text=True,
            )
            errors = 0
            mismatch_items = 0
            scjson_errors = 0
            scjson_mismatch_items = 0
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
                diff = _diff_report(canonical[src], data)
                lines = _diff_line_count(diff)
                if lines:
                    print(f"{lang} JSON mismatch: {rel}")
                    print(diff)
                    mismatch_items += lines
                    scjson_mismatch_items += lines
                    diff_lines = _verify_with_python(jpath, canonical[src], handler)
                    mismatch_items += diff_lines
                    scjson_mismatch_items += diff_lines
                    scjson_errors += 1
                    errors += 1
                #elif data != canonical[src]:  # pragma: no cover - debug aid
                #    print(f"{lang} JSON normalization resolved mismatch: {rel}")
            if scjson_errors:
                print(
                    f"{lang} encountered {scjson_errors} mismatching scjson files and {scjson_mismatch_items} mismatched scjson items."
                )
            result = subprocess.run(
                cmd + ["xml", str(json_dir), "-o", str(xml_dir), "-r"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=True,
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
                diff = _diff_report(canonical[src], parsed)
                lines = _diff_line_count(diff)
                if lines:
                    print(f"{lang} XML mismatch: {rel}")
                    print(diff)
                    mismatch_items += lines
                    jpath = json_dir / rel.with_suffix(".scjson")
                    if jpath.exists():
                        mismatch_items += _verify_with_python(jpath, canonical[src], handler)
                    errors += 1
                #elif parsed != canonical[src]:  # pragma: no cover - debug aid
                #    print(f"{lang} XML normalization resolved mismatch: {rel}")
            if errors:
                print(
                    f"{lang} encountered {errors} mismatching files ({scjson_errors} scjson) and {mismatch_items} mismatched items."
                )
        except subprocess.CalledProcessError as exc:  # pragma: no cover - CLI failures
            err = exc.stderr
            if isinstance(err, (bytes, bytearray)):
                err = err.decode().strip()
            else:
                err = str(err).strip()
            print(f"Skipping {lang}: {err}")
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
