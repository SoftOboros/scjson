"""Exercise command arguments, deep paths, and local Unicode XInclude bases.

Agent Name: python-portable-qualification

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.
"""
import json
import os
import subprocess
import sys

from click.testing import CliRunner
from scjson.cli import main
from scjson_argv import format_command, split_command


def test_reference_command_preserves_argument_boundaries(tmp_path):
    """Run a script whose path and arguments require native command quoting."""
    script = tmp_path / "reference engine.py"
    script.write_text("import json, sys\nprint(json.dumps(sys.argv[1:]))\n", encoding="utf-8")
    values = ["an argument with spaces", "", 'literal "quote"', "C:\\nested path\\tail\\"]
    command = format_command([sys.executable, str(script), *values])
    argv = split_command(command)
    result = subprocess.run(argv, capture_output=True, text=True, check=True)
    assert json.loads(result.stdout) == values


def test_recursive_cli_preserves_long_paths_and_unicode(tmp_path):
    """Read the generated file beyond Windows' legacy 260-character limit."""
    source = tmp_path / "source with spaces"
    source.mkdir()
    (source / "root.scxml").write_text(
        '<scxml xmlns="http://www.w3.org/2005/07/scxml" version="1.0" initial="start">'
        '<state id="start"/></scxml>', encoding="utf-8-sig"
    )
    target = tmp_path.joinpath(*["nested-012345678901234567890123456789"] * 7, "output")
    result = CliRunner().invoke(main, ["json", str(source), "-o", str(target), "-r"])
    assert result.exit_code == 0, (result.output, result.exception)
    output = target / "root.scjson"
    # Read the actual destination independently on Windows hosts with MAX_PATH enabled.
    native = "\\\\?\\" + str(output) if os.name == "nt" else str(output)
    with open(native, encoding="utf-8") as handle:
        assert json.load(handle)["state"][0]["id"] == "start"


def test_xinclude_file_and_directory_uris_preserve_relative_children(tmp_path):
    """Resolve a local document supplied as a path, file URI, or directory URI."""
    from scjson.SCXMLDocumentHandler import SCXMLDocumentHandler

    folder = tmp_path / "UTF-8 café"
    folder.mkdir()
    (folder / "child.scxml").write_text('<state xmlns="http://www.w3.org/2005/07/scxml" id="included"/>', encoding="utf-8")
    parent = folder / "root.scxml"
    xml = ('<scxml xmlns="http://www.w3.org/2005/07/scxml" xmlns:xi="http://www.w3.org/2001/XInclude">'
           '<xi:include href="child.scxml"/></scxml>')
    parent.write_text(xml, encoding="utf-8")
    handler = SCXMLDocumentHandler(xinclude="resolve")
    for base in (str(parent), parent.as_uri(), folder.as_uri() + "/"):
        assert json.loads(handler.xml_to_json(xml, xinclude_base_url=base))["state"][0]["id"] == "included"
    result = CliRunner().invoke(main, ["json", str(parent), "--xinclude", "resolve"])
    assert result.exit_code == 0, (result.output, result.exception)
    assert json.loads(parent.with_suffix(".scjson").read_text(encoding="utf-8"))["state"][0]["id"] == "included"
