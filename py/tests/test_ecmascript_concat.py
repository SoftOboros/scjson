"""
Agent Name: ecmascript-foreach-concat-regressions

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Check Array.prototype.concat in the execution engine and original foreach charts.
"""

from pathlib import Path

import pytest

from scjson.SCXMLDocumentHandler import SCXMLDocumentHandler
from scjson.context import DocumentContext


NS = "http://www.w3.org/2005/07/scxml"


@pytest.mark.parametrize("route", ["xml", "scjson"])
@pytest.mark.parametrize("dialect,case,final,array,count", [
    ("ecma", 460, "pass", [1, 2, 3, 4, 4, 4], 3),
    ("ecma", 525, "pass", [1, 2, 3, 4, 4, 4], 3),
    ("python", 460, "pass", [1, 2, 3, 4, 4, 4], 3),
    ("python", 525, "fail", [1, 2, 3], 0),
])
def test_original_concat_or_python_type_error(route, dialect, case, final, array, count, tmp_path):
    """Verify mutations, loop visit count, raised errors, and the authored terminal state."""
    tier = "Optional" if case == 460 else "Mandatory"
    path = Path(__file__).resolve().parents[2] / "tutorial" / "Tests" / dialect / "W3C" / tier / "Auto" / f"test{case}.scxml"
    if not path.is_file():
        pytest.skip("Alex Z tutorial submodule unavailable")
    if route == "scjson":
        wire = tmp_path / "chart.scjson"
        wire.write_text(SCXMLDocumentHandler().xml_to_json(path.read_text("utf-8")), encoding="utf-8")
        ctx = DocumentContext.from_json_file(wire)
    else:
        ctx = DocumentContext.from_xml_file(path)
    assert ctx.configuration - {"__scxml_root__"} == {final}
    assert ctx.data_model["Var1"] == array
    assert ctx.data_model["Var2"] == count
    errors = [event.name for event in iter(ctx.events.pop, None) if event.name == "error.execution"]
    assert errors == (["error.execution"] if final == "fail" else [])


def test_concat_returns_new_shallow_arrays_in_initializers_assignments_and_scripts():
    """Nested arrays stay nested, scalars append once, and no input is modified."""
    xml = f'''<scxml xmlns="{NS}" version="1.0" datamodel="ecmascript" initial="s">
      <datamodel>
        <data id="source" expr="[[1]].concat(2)"/><data id="copy"/>
        <data id="shadow" expr="'x.concat(no)'"/><data id="_scjson_arrays" expr="7"/>
        <data id="flat"/><data id="result"/><data id="untouched"/>
      </datamodel>
      <state id="s"><onentry>
        <assign location="copy" expr="source.concat()"/>
        <assign location="flat" expr="source.concat([3,[4]], 5, null, 'ok').concat([6])"/>
        <script>result = [].concat(source, [7])</script>
        <assign location="untouched" expr="_scjson_arrays + 1"/>
      </onentry></state></scxml>'''
    ctx = DocumentContext.from_xml_string(xml)
    data = ctx.data_model
    assert data["copy"] == data["source"] == [[1], 2]
    assert data["copy"] is not data["source"] and data["copy"][0] is data["source"][0]
    assert data["flat"] == [[1], 2, 3, [4], 5, None, "ok", 6]
    assert data["result"] == [[1], 2, 7]
    assert data["untouched"] == 8 and data["shadow"] == "x.concat(no)"
