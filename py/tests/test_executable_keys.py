"""Exercise reserved action keys through canonical intake and editor projections.

Agent Name: executable-key-intake

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.
"""

import json
from pathlib import Path

from click.testing import CliRunner
from jsonschema import Draft202012Validator
import pytest

from scjson import pydantic, pydantic_strict
from scjson.SCXMLDocumentHandler import SCXMLDocumentHandler
from scjson.cli import main
from scjson.context import DocumentContext
from scjson.exec_ir import RaiseNode, lower_document
from scjson.executable_keys import InvalidExecutableKey, validate_executable_keys


ROOT = Path(__file__).resolve().parents[2]
CODEC = SCXMLDocumentHandler()
XML = ('<scxml xmlns="http://www.w3.org/2005/07/scxml" version="1.0" initial="s">'
       '<state id="s"><onentry><raise event="go"/></onentry>'
       '<transition event="go" target="done"/></state><final id="done"/></scxml>')
SCHEMA = Draft202012Validator(json.loads((ROOT / "scjson.schema.json").read_bytes()))


@pytest.mark.parametrize("tag", ["raise", "if", "else"])
@pytest.mark.parametrize("spelling", ["xml", "camel", "both", "xml_and_canonical"])
def test_malformed_keys_refused_on_every_canonical_path(tag, spelling, tmp_path):
    """An empty payload or duplicate spelling cannot hide the authored key."""
    raw = json.loads(CODEC.xml_to_json(XML))
    block = raw["state"][0]["onentry"][0]
    block.clear()
    pointer = "/state/0/onentry/0"
    if tag == "else":
        block["if_value"] = [{"cond": "False"}]
        block = block["if_value"][0]
        pointer += "/if_value/0"
    key, camel = tag + "_value", tag + "Value"
    value = {} if tag == "else" else []
    aliases = {"xml": [tag], "camel": [camel], "both": [key, camel], "xml_and_canonical": [tag, key]}
    block.update({alias: value for alias in aliases[spelling]})
    assert not SCHEMA.is_valid(raw)
    path = tmp_path / "bad.scjson"
    path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(InvalidExecutableKey, match=pointer):
        validate_executable_keys(raw)
    for action in (pydantic.Scxml.model_validate, pydantic_strict.Scxml.model_validate,
                   lambda data: CODEC.json_to_xml(json.dumps(data)),
                   lambda data: DocumentContext.from_json_file(path)):
        with pytest.raises(ValueError, match=key):
            action(raw)
    if spelling == "camel":
        validate_executable_keys(raw, allow_camel=True)
    else:
        with pytest.raises(InvalidExecutableKey, match=pointer):
            validate_executable_keys(raw, allow_camel=True)


def test_canonical_raise_round_trips_executes_and_lowers(tmp_path):
    """XML, saved JSON, generated IR and the XML reverse route retain the event."""
    data = json.loads(CODEC.xml_to_json(XML))
    validate_executable_keys(data)
    SCHEMA.validate(data)
    p = tmp_path / "raise.scjson"
    p.write_text(json.dumps(data), encoding="utf-8")
    for ctx in (DocumentContext.from_json_file(p), DocumentContext.from_xml_string(XML),
                DocumentContext.from_xml_string(CODEC.json_to_xml(p.read_text()))):
        assert ctx.trace_step()["configuration"] == ["done"]
    ir, _ = lower_document(pydantic.Scxml.model_validate(data))
    action, = ir.children[0].onentry
    assert isinstance(action, RaiseNode) and action.event == "go"


@pytest.mark.parametrize("existing", [False, True])
def test_reverse_cli_reports_refusal_and_preserves_destination(tmp_path, existing):
    """A refused single-file conversion never creates or replaces its destination."""
    raw = json.loads(CODEC.xml_to_json(XML))
    entry = raw["state"][0]["onentry"][0]
    entry["raise"] = entry.pop("raise_value")
    path, dest = tmp_path / "raw.scjson", tmp_path / "review.scxml"
    path.write_text(json.dumps(raw))
    if existing:
        dest.write_bytes(b"previous review")
    result = CliRunner().invoke(main, ["xml", str(path), "-o", str(dest)])
    assert result.exit_code == 1 and "/state/0/onentry/0/raise" in result.output
    assert dest.is_file() == existing
    if existing:
        assert dest.read_bytes() == b"previous review"


def test_drafts_wildcards_and_data_payloads_are_opaque_but_embedded_charts_are_checked():
    """Optional draft fields can be absent and payloads own their property names."""
    metadata = {"raise": "label", "ifValue": {"if": "example"}, "raise_value": "hint"}
    foreign = {"qname": "{urn:d}if", "attributes": {"raise": "example"}}
    draft = {"state": [{"onentry": [{"other_attributes": metadata, "other_element": [foreign]}],
                        "invoke": [{"content": [{"content": [foreign, "text"]}]}]}],
             "datamodel": [{"data": [{"content": [{"onentry": [metadata]}]}]}]}
    validate_executable_keys(draft, allow_camel=True)
    nested = {"state": [{"onentry": [{"ifValue": [{"cond": "True", "raise": []}]}]}]}
    draft["state"][0]["invoke"][0]["content"][0]["content"].append(nested)
    with pytest.raises(InvalidExecutableKey, match=r"/content/2/state/0/onentry/0/ifValue/0/raise"):
        validate_executable_keys(draft, allow_camel=True)


@pytest.mark.parametrize("owner", ["onentry", "onexit", "transition", "finalize", "foreach", "if_value"])
def test_empty_xml_key_is_refused_at_each_executable_owner(owner):
    """The same key guard covers every action owner even without execution_order."""
    block = {"raise": []}
    if owner == "finalize":
        state = {"invoke": [{"finalize": [block]}]}
    elif owner in {"foreach", "if_value"}:
        state = {"onentry": [{owner: [block]}]}
    else:
        state = {owner: [block]}
    raw = {"state": [state]}
    for call in (validate_executable_keys, pydantic.Scxml.model_validate,
                 pydantic_strict.Scxml.model_validate, lambda data: CODEC.json_to_xml(json.dumps(data))):
        with pytest.raises(ValueError, match="raise_value"):
            call(raw)
