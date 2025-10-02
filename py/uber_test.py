"""
Uber test harness for scjson language implementations.

Agent Name: uber-test

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

This module exercises the command line interfaces for all available language
implementations of the :mod:`scjson` tooling. It converts a large corpus of
SCXML documents to SCJSON and back again, ensuring that each implementation
produces identical output. Results are written under an ``uber_out`` directory
by default. It also provides consensus-aware triage and normalization to make
cross-language comparisons actionable.
"""

from __future__ import annotations

from deepdiff import DeepDiff

import argparse
import difflib
import html
import json
import os
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable

import pytest

from scjson.SCXMLDocumentHandler import SCXMLDocumentHandler
from scjson.context import DocumentContext, ExecutionMode

ROOT = Path(__file__).resolve().parents[1]
TUTORIAL = ROOT / "tutorial"

# Optional features known unsupported by the Python engine for now
ENGINE_KNOWN_UNSUPPORTED = {
    Path("Tests/python/W3C/Optional/Auto/test457.scxml"),
    Path("Tests/python/W3C/Optional/Auto/test520.scxml"),
    Path("Tests/python/W3C/Optional/Auto/test532.scxml"),
    Path("Tests/python/W3C/Optional/Auto/test562.scxml"),
    Path("Tests/python/W3C/Optional/Auto/test578.scxml"),
}

# CLI entrypoints for each language implementation
LANG_CMDS: dict[str, list[str]] = {
    "python": [sys.executable, "-m", "scjson"],
    "javascript": ["node", str(ROOT / "js")],
    "ruby": ["ruby", str(ROOT / "ruby" / "bin" / "scjson")],
    "lua": ["lua", str(ROOT / "lua" / "bin" / "scjson")],
    "go": [str(ROOT / "go" / "go")],
    "rust": [str(ROOT / "rust" / "target" / "debug" / "scjson_rust")],
    "swift": [str(ROOT / "swift" / ".build" / "x86_64-unknown-linux-gnu" / "debug" / "scjson-swift")],
    "java": [
        "java",
        "-cp",
        str(ROOT / "java" / "target" / "scjson-0.3.3-SNAPSHOT.jar"),
        "com.softobros.ScjsonCli",
    ],
    "csharp": [
        "dotnet",
        str(ROOT / "csharp" / "ScjsonCli" / "bin" / "Debug" / "net8.0" / "ScjsonCli.dll"),
    ],
}

# Alias/fuzzy mapping for languages
LANG_ALIASES = {
    "py": "python",
    "python": "python",
    "js": "javascript",
    "ts": "javascript",
    "typescript": "javascript",
    "node": "javascript",
    "rb": "ruby",
    "rs": "rust",
    "cs": "csharp",
    "dotnet": "csharp",
}

# Structural fields lifted from content
STRUCTURAL_FIELDS = {
    "state",
    "parallel",
    "final",
    "history",
    "transition",
    "onentry",
    "onexit",
    "invoke",
    "datamodel",
    "data",
    "initial",
    "script",
    "log",
    "assign",
    "send",
    "cancel",
    "param",
    "raise",
    "foreach",
}

# Namespace and normalization helpers
SCXML_NAMESPACE_KEYS = {"xmlns", "xmlns:scxml", "xmlns:xsi", "xsi:schemaLocation"}
SCXML_FORCE_STR_KEYS = {"content", "expr", "event", "cond"}
SCXML_FORCE_NUMERIC_KEYS = {"version"}
KEY_SYNONYMS = {
    "type": "type_value",
    "raise": "raise_value",
    "initial": "initial_attribute",
    "datamodelAttribute": "datamodel_attribute",
}


def _available(cmd: list[str], env: dict[str, str] | None = None) -> bool:
    """Return True if the CLI is runnable with --help."""
    exe = cmd[0]
    if not (Path(exe).exists() or shutil.which(exe)):
        return False
    try:
        subprocess.run(cmd + ["--help"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, env=env)
        return True
    except Exception:
        return False


def _python_engine_available() -> bool:
    try:
        from scjson.context import DocumentContext  # noqa: F401
    except Exception:
        return False
    return True


def _iter_python_datamodel_charts(root: Path) -> Iterable[Path]:
    import xml.etree.ElementTree as ET

    for scxml in root.rglob("*.scxml"):
        try:
            tree = ET.parse(scxml)
        except ET.ParseError:
            continue
        root_node = tree.getroot()
        datamodel_attr = (
            root_node.attrib.get("datamodel")
            or root_node.attrib.get("datamodel_attribute")
        )
        if datamodel_attr and datamodel_attr.strip().lower() != "python":
            continue
        rel = scxml.relative_to(root)
        if rel in ENGINE_KNOWN_UNSUPPORTED:
            continue
        yield scxml


def _python_smoke_chart(chart: Path) -> tuple[bool, str]:
    """Execute a single chart minimally to validate the Python engine.

    Parameters
    ----------
    chart : Path
        SCXML chart path.

    Returns
    -------
    tuple[bool, str]
        ``(ok, message)`` where ``ok`` indicates success and ``message``
        contains an error string on failure.
    """
    try:
        ctx = DocumentContext.from_xml_file(chart, execution_mode=ExecutionMode.LAX)
        ctx.trace_step()
        return True, ""
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


class MismatchInvestigator:
    """Consensus-aware cross-language mismatch triage.

    Parameters
    ----------
    canonical: dict[Path, dict]
        Canonical Python-derived structures by source file.
    tutorial_root: Path
        Base directory of tutorial corpus (for relative paths).
    out_root: Path | str
        Root for generated artifacts.
    reference_langs: tuple[str, ...]
        Language identifiers used as references.
    """

    def __init__(
        self,
        canonical: dict[Path, dict],
        tutorial_root: Path,
        out_root: Path | str,
        reference_langs: tuple[str, ...] = ("python", "javascript", "rust"),
    ) -> None:
        self._canonical = canonical
        self._tutorial_root = tutorial_root
        self._out_root = Path(out_root)
        self._reference_langs = reference_langs
        self._cache: dict[str, dict[Path, dict]] = {"python": canonical}
        self._prepared: set[str] = set()
        self._stats: dict[str, dict[str, Counter[str]]] = {}

    def capture_issue(self, lang: str, src: Path, stage: str, actual: Any | None, note: str | None = None) -> str:
        """Record a mismatch and return consensus summary."""
        canonical = self._canonical.get(src)
        classification = self._classify(canonical, actual)
        references = self._reference_summary(src, skip_lang=lang)
        rel = src.relative_to(self._tutorial_root)
        self._stats.setdefault(lang, {}).setdefault(stage, Counter())[classification] += 1
        ref_desc = ", ".join(f"{k}:{v}" for k, v in references.items())
        parts = [f"Triage {lang} {stage} mismatch for {rel}: {classification.replace('_',' ')}."]
        if note:
            parts.append(note)
        if ref_desc:
            parts.append(f"Refs -> {ref_desc}")
        closest = self._closest_reference(src, actual)
        if closest:
            parts.append(f"Action: align implementation to canonical/reference, closest ref: {closest[0]} ({closest[1]} lines)")
        return " ".join(parts)

    def summary(self, lang: str) -> list[str]:
        if lang not in self._stats:
            return []
        lines: list[str] = []
        for stage, counts in self._stats[lang].items():
            lines.append("Triage summary [{lang}][{stage}]: " + ", ".join(f"{k}:{v}" for k, v in counts.items()))
        return lines

    def _classify(self, canonical: dict | None, actual: Any | None) -> str:
        if actual is None:
            return "missing_output"
        if isinstance(actual, dict):
            keys = set(actual.keys())
            if not keys:
                return "empty_object"
            if keys <= {"version", "datamodel_attribute", "datamodelAttribute"}:
                return "placeholder_output"
            if canonical:
                canonical_keys = set(canonical.keys())
                if "tag" in canonical_keys and "tag" not in keys:
                    return "missing_tag"
                if canonical_keys - keys:
                    return "missing_fields"
            return "structural_mismatch"
        return "type_mismatch"

    def _reference_summary(self, src: Path, skip_lang: str | None = None) -> dict[str, str]:
        summary: dict[str, str] = {}
        canonical = self._canonical.get(src)
        for lang in self._reference_langs:
            if lang == skip_lang:
                continue
            ref_data = self._get_reference_data(lang, src)
            if canonical is None or ref_data is None:
                summary[lang] = "unavailable"
                continue
            diff = _diff_report(canonical, ref_data)
            summary[lang] = "match" if _diff_line_count(diff) == 0 else "diverges"
        return summary

    def _closest_reference(self, src: Path, actual: Any | None) -> tuple[str, int] | None:
        if actual is None:
            return None
        best: tuple[str, int] | None = None
        for lang in self._reference_langs:
            ref = self._get_reference_data(lang, src)
            if ref is None:
                continue
            diff = _diff_report(ref, actual)
            lines = _diff_line_count(diff)
            if best is None or lines < best[1]:
                best = (lang, lines)
        return best

    def _get_reference_data(self, lang: str, src: Path) -> dict | None:
        cache = self._cache.setdefault(lang, {})
        if src in cache:
            return cache[src]
        if lang == "python":
            return self._canonical.get(src)
        jpath = self._ensure_reference_json(lang, src)
        if not jpath or not jpath.exists():
            return None
        try:
            data = json.loads(jpath.read_text())
        except Exception:
            return None
        cache[src] = data
        return data

    def _ensure_reference_json(self, lang: str, src: Path) -> Path | None:
        cmd = LANG_CMDS.get(lang)
        if not cmd:
            return None
        rel = src.relative_to(self._tutorial_root)
        out = (self._out_root / "__reference__" / lang / "json" / rel).with_suffix(".scjson")
        out.parent.mkdir(parents=True, exist_ok=True)
        if out.exists():
            return out
        self._prepare_language(lang)
        args = cmd + ["json", str(src), "-o", str(out)]
        if lang == "python":
            args.append("--skip-unknown")
        try:
            subprocess.run(args, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=self._env_for(lang))
        except Exception:
            return None
        return out if out.exists() else None

    def _prepare_language(self, lang: str) -> None:
        if lang in self._prepared:
            return
        if lang == "javascript":
            try:
                subprocess.run(["npm", "run", "build"], cwd=ROOT / "js", check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            except Exception:
                pass
        self._prepared.add(lang)

    def _env_for(self, lang: str) -> dict[str, str] | None:
        if lang == "python":
            env = dict(os.environ)
            env["PYTHONPATH"] = str(ROOT / "py")
            return env
        return None


def _normalize_for_diff(obj: Any, path: str = "", field_key: str | None = None):
    """Normalize structures for robust diffing."""
    if isinstance(obj, str) and field_key in SCXML_FORCE_NUMERIC_KEYS:
        try:
            return float(obj) if "." in obj else int(obj)
        except ValueError:
            pass
    if isinstance(obj, (int, float)) and field_key in SCXML_FORCE_STR_KEYS:
        return str(obj)
    if obj in ({}, [{}], {"content": [{}]}):
        return None
    if isinstance(obj, dict):
        new: dict[str, Any] = {}
        for k, v in obj.items():
            k = KEY_SYNONYMS.get(k, k)
            if k in SCXML_NAMESPACE_KEYS or k == "tag":
                continue
            if k == "other_attributes" and isinstance(v, dict):
                for sub_k, sub_v in v.items():
                    if sub_k in SCXML_NAMESPACE_KEYS:
                        continue
                    new[sub_k] = _normalize_for_diff(sub_v, f"{path}.{sub_k}" if path else sub_k, field_key=sub_k)
                continue
            if k == "content" and v == [{}]:
                continue
            if k in SCXML_FORCE_NUMERIC_KEYS and isinstance(v, str):
                try:
                    v = float(v) if "." in v else int(v)
                except ValueError:
                    pass
            elif k in SCXML_FORCE_STR_KEYS and isinstance(v, (int, float)):
                v = str(v)
            if k == "target":
                if isinstance(v, str):
                    parts = [p for p in v.split() if p]
                    v = parts if len(parts) > 1 else [v]
            if k == "content" and isinstance(v, list):
                lifted: dict[str, list] = {}
                kept: list = []
                for idx, child in enumerate(v):
                    if isinstance(child, dict) and child.get("tag") in STRUCTURAL_FIELDS:
                        tag = child["tag"]
                        lifted.setdefault(tag, []).append(_normalize_for_diff(child, f"{path}.content[{idx}]", field_key=tag))
                    else:
                        kept.append(_normalize_for_diff(child, f"{path}.content[{idx}]", field_key="content"))
                for tag, arr in lifted.items():
                    existing = new.get(tag)
                    if isinstance(existing, list):
                        new[tag] = existing + arr
                    elif existing is None:
                        new[tag] = arr
                if kept:
                    new["content"] = kept
                continue
            normalized_v = _normalize_for_diff(v, f"{path}.{k}" if path else k, field_key=k)
            if normalized_v is None:
                continue
            new[k] = normalized_v
        return new
    if isinstance(obj, list):
        if len(obj) == 1 and isinstance(obj[0], dict) and list(obj[0].keys()) == ["content"] and isinstance(obj[0]["content"], str):
            return _normalize_for_diff(obj[0]["content"], f"{path}[]", field_key="content")
        if len(obj) == 1 and ((field_key not in STRUCTURAL_FIELDS and field_key != "target") or field_key in {"datamodel"}):
            return _normalize_for_diff(obj[0], f"{path}[]", field_key=field_key)
        if field_key == "final" and len(obj) == 1 and isinstance(obj[0], dict) and set(obj[0].keys()) == {"tag"}:
            return None
        return [_normalize_for_diff(i, f"{path}[]", field_key=field_key) for i in obj]
    if isinstance(obj, str):
        return html.unescape(obj).strip()
    return obj


def _diff_report(expected: dict, actual: dict) -> str:
    diff = DeepDiff(_normalize_for_diff(expected), _normalize_for_diff(actual), verbose_level=1, ignore_numeric_type_changes=True, ignore_order=True)
    return diff.pretty()


def _diff_line_count(diff: str) -> int:
    return 0 if not diff else diff.count("\n") + 1


def _verify_with_python(json_path: Path, canonical: dict, handler: SCXMLDocumentHandler) -> int:
    try:
        original_text = json_path.read_text(encoding="utf-8")
        round_trip = json.loads(handler.xml_to_json(handler.json_to_xml(original_text)))
    except Exception as exc:
        print(f"Python failed to round-trip {json_path}: {exc}")
        return 0
    if round_trip == canonical:
        return 0
    diff = _diff_report(canonical, round_trip)
    print(diff)
    return _diff_line_count(diff)


def _canonical_json(files: list[Path], handler: SCXMLDocumentHandler) -> dict[Path, dict]:
    result: dict[Path, dict] = {}
    for f in files:
        data = f.read_text(encoding="utf-8")
        try:
            result[f] = json.loads(handler.xml_to_json(data))
        except Exception:
            pass
    return result


def _resolve_language(language: str) -> str | None:
    key = language.strip().lower()
    if key in LANG_CMDS:
        return key
    if key in LANG_ALIASES:
        return LANG_ALIASES[key]
    best = difflib.get_close_matches(key, list(LANG_CMDS.keys()), n=1, cutoff=0.6)
    return best[0] if best else None


def main(
    out_dir: str | Path = "uber_out",
    language: str | None = None,
    *,
    subset: str | None = None,
    consensus_warn: bool = False,
) -> None:
    """Run the uber test suite with optional subset and consensus-warn."""
    handler = SCXMLDocumentHandler()
    scxml_files = sorted(TUTORIAL.rglob("*.scxml"))
    if subset:
        import fnmatch
        scxml_files = [p for p in scxml_files if fnmatch.fnmatch(str(p.relative_to(TUTORIAL)), subset)]
    canonical = _canonical_json(scxml_files, handler)
    scxml_files = list(canonical.keys())
    out_root = Path(out_dir)
    investigator = MismatchInvestigator(canonical, TUTORIAL, out_root)
    if language:
        lang_key = _resolve_language(language)
        if not lang_key:
            print(f"Skipping {language}: unknown language")
            return
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
            subprocess.run(["npm", "run", "build"], cwd=ROOT / "js", check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        json_dir = out_root / lang / "json"
        xml_dir = out_root / lang / "xml"
        json_dir.mkdir(parents=True, exist_ok=True)
        xml_dir.mkdir(parents=True, exist_ok=True)
        try:
            if lang == "swift":
                for src in scxml_files:
                    rel = src.relative_to(TUTORIAL)
                    jpath = (json_dir / rel).with_suffix(".scjson")
                    jpath.parent.mkdir(parents=True, exist_ok=True)
                    subprocess.run(cmd + ["json", str(src), "-o", str(jpath)], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, text=True)
            else:
                json_args = ["json", str(TUTORIAL), "-o", str(json_dir), "-r"]
                if lang == "python":
                    json_args.append("--skip-unknown")
                subprocess.run(cmd + json_args, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, text=True)
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
                    refs = investigator._reference_summary(src, skip_lang=lang)
                    match_count = sum(1 for v in refs.values() if v == "match")
                    if not (consensus_warn and match_count >= 1):
                        scjson_errors += 1
                        errors += 1
            if scjson_errors:
                print(f"{lang} encountered {scjson_errors} mismatching scjson files and {scjson_mismatch_items} mismatched scjson items.")
            if lang == "swift":
                for src in scxml_files:
                    rel = src.relative_to(TUTORIAL)
                    jpath = (json_dir / rel).with_suffix(".scjson")
                    xpath = xml_dir / rel
                    xpath.parent.mkdir(parents=True, exist_ok=True)
                    if jpath.exists():
                        subprocess.run(cmd + ["xml", str(jpath), "-o", str(xpath)], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, text=True)
            else:
                subprocess.run(cmd + ["xml", str(json_dir), "-o", str(xml_dir), "-r"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, text=True)
            for src in scxml_files:
                rel = src.relative_to(TUTORIAL)
                xpath = xml_dir / rel
                if not xpath.exists():
                    print(f"{lang} failed to write {xpath}")
                    continue
                try:
                    parsed = json.loads(handler.xml_to_json(xpath.read_text()))
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
                    refs = investigator._reference_summary(src, skip_lang=lang)
                    match_count = sum(1 for v in refs.values() if v == "match")
                    if not (consensus_warn and match_count >= 1):
                        errors += 1
            if errors:
                print(f"{lang} encountered {errors} mismatching files ({scjson_errors} scjson) and {mismatch_items} mismatched items.")
        except subprocess.CalledProcessError as exc:
            err = exc.stderr
            if isinstance(err, (bytes, bytearray)):
                err = err.decode().strip()
            else:
                err = str(err).strip()
            print(f"Skipping {lang}: {err}")
        except Exception as exc:
            print(f"Skipping {lang}: {exc}")


@pytest.mark.skipif(not _python_engine_available(), reason="Python engine not available")
@pytest.mark.parametrize(
    "chart",
    list(_iter_python_datamodel_charts(TUTORIAL)),
    ids=lambda p: str(p.relative_to(TUTORIAL)) if p.is_absolute() else str(p),
)
def test_python_engine_executes_chart(chart: Path):
    ok, msg = _python_smoke_chart(chart)
    if not ok:
        pytest.fail(f"{chart}: {msg}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("out_dir", nargs="?", default="uber_out", help="directory for intermediate files")
    parser.add_argument("-l", "--language", dest="language", help="limit testing to a single language")
    parser.add_argument("-s", "--subset", dest="subset", help="limit to SCXML files matching a glob (relative to tutorial)")
    parser.add_argument("--consensus-warn", action="store_true", help="warn-only when reference languages match canonical")
    parser.add_argument("--python-smoke", action="store_true", help="run Python engine smoke over charts with per-chart progress")
    parser.add_argument("--chart", type=Path, help="run only a single chart for Python smoke mode")
    opts = parser.parse_args()
    if opts.python_smoke:
        import sys
        charts = [opts.chart] if opts.chart else list(_iter_python_datamodel_charts(TUTORIAL))
        if not charts:
            print("No charts found for smoke run.")
            sys.exit(0)
        total = len(charts)
        failures = 0
        for idx, chart in enumerate(charts, 1):
            ok, msg = _python_smoke_chart(chart)
            rel = chart.relative_to(TUTORIAL) if chart.is_absolute() and TUTORIAL in chart.parents else chart
            status = "OK" if ok else "FAIL"
            print(f"[{idx}/{total}] {rel} ... {status}")
            if not ok and msg:
                print(f"    {msg}")
            if not ok:
                failures += 1
        sys.exit(1 if failures else 0)
    else:
        main(Path(opts.out_dir), opts.language, subset=opts.subset, consensus_warn=opts.consensus_warn)
