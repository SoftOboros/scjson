"""
Agent Name: uber-test

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.
"""

"""Cross-language conversion test runner."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

from py.scjson.SCXMLDocumentHandler import SCXMLDocumentHandler

ROOT = Path(__file__).resolve().parent
TUTORIAL = ROOT / "tutorial"

LANG_CMDS: dict[str, list[str]] = {
    "python": [sys.executable, "-m", "scjson.cli"],
    "javascript": ["node", str(ROOT / "js" / "bin" / "scjson.js")],
    "ruby": ["ruby", str(ROOT / "ruby" / "bin" / "scjson")],
    "lua": ["lua5.4", str(ROOT / "lua" / "bin" / "scjson")],
    "go": [str(ROOT / "go" / "go")],
    "rust": [str(ROOT / "rust" / "target" / "debug" / "scjson_rust")],
    "swift": [str(ROOT / "swift" / ".build" / "x86_64-unknown-linux-gnu" / "debug" / "scjson-swift")],
    "java": [
        "java",
        "-cp",
        str(ROOT / "java" / "target" / "scjson-0.1.0-SNAPSHOT.jar"),
        "com.softobros.ScjsonCli",
    ],
    "csharp": [
        "dotnet",
        str(ROOT / "csharp" / "ScjsonCli" / "bin" / "Debug" / "net8.0" / "ScjsonCli.dll"),
    ],
}


def _available(cmd: list[str]) -> bool:
    exe = cmd[0]
    if not (Path(exe).exists() or shutil.which(exe)):
        return False
    try:
        subprocess.run(cmd + ["--help"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except Exception:
        return False


def _canonical_json(files: list[Path], handler: SCXMLDocumentHandler) -> dict[Path, dict]:
    result = {}
    for f in files:
        data = f.read_text(encoding="utf-8")
        result[f] = json.loads(handler.xml_to_json(data))
    return result


def main(out_dir: str | Path = "uber_out") -> None:
    handler = SCXMLDocumentHandler()
    scxml_files = sorted(TUTORIAL.rglob("*.scxml"))
    canonical = _canonical_json(scxml_files, handler)
    out_root = Path(out_dir)
    for lang, cmd in LANG_CMDS.items():
        if not _available(cmd):
            print(f"Skipping {lang}: executable not available")
            continue
        json_dir = out_root / lang / "json"
        xml_dir = out_root / lang / "xml"
        json_dir.mkdir(parents=True, exist_ok=True)
        xml_dir.mkdir(parents=True, exist_ok=True)
        subprocess.run(cmd + ["json", str(TUTORIAL), "-o", str(json_dir), "-r"], check=True)
        for src in scxml_files:
            rel = src.relative_to(TUTORIAL)
            jpath = json_dir / rel.with_suffix(".scjson")
            data = json.loads(jpath.read_text())
            assert data == canonical[src], f"{lang} JSON mismatch: {rel}"
        subprocess.run(cmd + ["xml", str(json_dir), "-o", str(xml_dir), "-r"], check=True)
        for src in scxml_files:
            rel = src.relative_to(TUTORIAL)
            xpath = xml_dir / rel
            data = handler.xml_to_json(xpath.read_text())
            assert json.loads(data) == canonical[src], f"{lang} XML mismatch: {rel}"
        print(f"{lang} ok")


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("uber_out")
    main(target)
