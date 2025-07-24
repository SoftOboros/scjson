"""
Agent Name: python-cli-tests

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.
"""

from pathlib import Path
import json
import sys
from click.testing import CliRunner
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scjson.pydantic import Scxml
from scjson.context import DocumentContext

from scjson.cli import main
from scjson.SCXMLDocumentHandler import SCXMLDocumentHandler


def _create_scxml(path: Path) -> str:
    return '<scxml xmlns="http://www.w3.org/2005/07/scxml"/>'


def test_single_json_conversion(tmp_path):
    xml_path = tmp_path / "sample.scxml"
    xml_path.write_text(_create_scxml(xml_path))
    runner = CliRunner()
    result = runner.invoke(main, ["json", str(xml_path)])
    assert result.exit_code == 0
    out_path = xml_path.with_suffix(".scjson")
    assert out_path.exists()
    data = json.loads(out_path.read_text())
    assert data["version"] == 1.0


def test_directory_json_conversion(tmp_path):
    src_dir = tmp_path / "dir"
    src_dir.mkdir()
    for name in ["a", "b"]:
        (src_dir / f"{name}.scxml").write_text(_create_scxml(Path(name)))
    runner = CliRunner()
    result = runner.invoke(main, ["json", str(src_dir)])
    assert result.exit_code == 0
    for name in ["a", "b"]:
        assert (src_dir / f"{name}.scjson").exists()


def _create_scjson(handler: SCXMLDocumentHandler) -> str:
    xml = _create_scxml(Path())
    return handler.xml_to_json(xml)


def test_single_xml_conversion(tmp_path):
    handler = SCXMLDocumentHandler()
    json_path = tmp_path / "sample.scjson"
    json_path.write_text(_create_scjson(handler))
    runner = CliRunner()
    result = runner.invoke(main, ["xml", str(json_path)])
    assert result.exit_code == 0
    out_path = json_path.with_suffix(".scxml")
    assert out_path.exists()
    data = out_path.read_text()
    assert "scxml" in data


def test_directory_xml_conversion(tmp_path):
    handler = SCXMLDocumentHandler()
    src_dir = tmp_path / "jsons"
    src_dir.mkdir()
    for name in ["x", "y"]:
        (src_dir / f"{name}.scjson").write_text(_create_scjson(handler))
    runner = CliRunner()
    result = runner.invoke(main, ["xml", str(src_dir)])
    assert result.exit_code == 0
    for name in ["x", "y"]:
        assert (src_dir / f"{name}.scxml").exists()


def test_recursive_conversion(tmp_path):
    runner = CliRunner()
    tutorial_dir = Path(__file__).resolve().parents[2] / "tutorial"
    scjson_dir = tmp_path / "tests" / "scjson"
    scxml_dir = tmp_path / "tests" / "scxml"

    result = runner.invoke(main, ["json", str(tutorial_dir), "-o", str(scjson_dir), "-r"])
    assert result.exit_code == 0
    result = runner.invoke(main, ["xml", str(scjson_dir), "-o", str(scxml_dir), "-r"])
    assert result.exit_code == 0

    json_files = list(scjson_dir.rglob("*.scjson"))
    xml_files = list(scxml_dir.rglob("*.scxml"))
    assert json_files
    assert xml_files
    assert len(xml_files) <= len(json_files)

    handler = SCXMLDocumentHandler()
    for f in xml_files[:5]:
        xml_str = f.read_text()
        json_str = handler.xml_to_json(xml_str)
        xml_rt = handler.json_to_xml(json_str)
        assert "scxml" in xml_rt


def test_recursive_validation(tmp_path):
    """Validate all converted files recursively."""
    runner = CliRunner()
    tutorial_dir = Path(__file__).resolve().parents[2] / "tutorial"
    scjson_dir = tmp_path / "tests" / "scjson"
    scxml_dir = tmp_path / "tests" / "scxml"

    assert (
        runner.invoke(main, ["json", str(tutorial_dir), "-o", str(scjson_dir), "-r"]).exit_code
        == 0
    )
    assert (
        runner.invoke(main, ["xml", str(scjson_dir), "-o", str(scxml_dir), "-r"]).exit_code
        == 0
    )

    result = runner.invoke(main, ["validate", str(tmp_path / "tests"), "-r"])
    assert result.exit_code == 0


def test_recursive_verify(tmp_path):
    """Verify converted files recursively using -v option."""
    runner = CliRunner()
    tutorial_dir = Path(__file__).resolve().parents[2] / "tutorial"
    scjson_dir = tmp_path / "tests" / "scjson"
    scxml_dir = tmp_path / "tests" / "scxml"

    assert (
        runner.invoke(main, ["json", str(tutorial_dir), "-o", str(scjson_dir), "-r"]).exit_code
        == 0
    )
    assert (
        runner.invoke(main, ["xml", str(scjson_dir), "-o", str(scxml_dir), "-r"]).exit_code
        == 0
    )

    result = runner.invoke(main, ["json", str(scxml_dir), "-r", "-v"])
    assert result.exit_code == 0
    result = runner.invoke(main, ["xml", str(scjson_dir), "-r", "-v"])
    assert result.exit_code == 0

    handler = SCXMLDocumentHandler()
    originals = sorted(tutorial_dir.rglob("*.scxml"))
    for orig in originals[:3]:
        rel = orig.relative_to(tutorial_dir)
        converted = scxml_dir / rel
        if converted.exists():
            o_json = json.loads(handler.xml_to_json(orig.read_text()))
            c_json = json.loads(handler.xml_to_json(converted.read_text()))
            assert o_json == c_json


def test_run_command_scjson(tmp_path):
    """Run the engine with a SCJSON input file."""
    handler = SCXMLDocumentHandler()
    json_path = tmp_path / "machine.scjson"
    json_path.write_text(_create_scjson(handler))
    runner = CliRunner()
    result = runner.invoke(main, ["run", "-I", str(json_path), "-o", str(tmp_path)])
    assert result.exit_code == 0
    log_path = tmp_path / "events.log"
    assert log_path.exists()
    assert "[microstep] consumed event: start" in log_path.read_text()


def test_run_command_scxml(tmp_path):
    """Run the engine with an SCXML input file."""
    xml_path = tmp_path / "machine.scxml"
    xml_path.write_text(_create_scxml(xml_path))
    runner = CliRunner()
    result = runner.invoke(main, ["run", "-I", str(xml_path), "--xml", "-o", str(tmp_path)])
    assert result.exit_code == 0
    log_path = tmp_path / "events.log"
    assert log_path.exists()
    assert "[microstep] consumed event: start" in log_path.read_text()



def test_run_command_stream(tmp_path):
    """Run engine reading multiple events from stdin."""
    handler = SCXMLDocumentHandler()
    json_path = tmp_path / "machine.scjson"
    json_path.write_text(_create_scjson(handler))
    runner = CliRunner()
    input_data = '{"event":"x"}{"event":"y"}{'
    result = runner.invoke(main, ["run", "-I", str(json_path)], input=input_data)
    assert result.exit_code == 0
    assert "[microstep] consumed event: start" in result.output
    assert "[microstep] consumed event: x" in result.output
    assert "[microstep] consumed event: y" in result.output


def test_document_context_datamodel_default():
    """Ensure datamodel_attribute defaults to python."""
    doc = Scxml(state=[{"id": "a"}], version=1.0)
    ctx = DocumentContext.from_doc(doc)
    assert doc.datamodel_attribute == "python"
    assert ctx.data_model == {}


def test_document_context_invalid_datamodel():
    """Creating a context with non-python datamodel should fail."""
    doc = Scxml(state=[{"id": "a"}], datamodel_attribute="ecmascript", version=1.0)
    with pytest.raises(ValueError):
        DocumentContext.from_doc(doc)
