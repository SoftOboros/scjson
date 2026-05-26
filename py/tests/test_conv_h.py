"""
Agent Name: conv-h-reachability-tests

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

CONV-H tests for root-reachable chart inclusion and communication surfaces.
These tests cover representation and validation only; runtime event delivery
and child-session execution remain owned by the execution concepts.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

import scjson.pydantic as pydantic_models
import scjson.pydantic_strict as strict_pydantic_models
from scjson.SCXMLDocumentHandler import SCXMLDocumentHandler


REPO_ROOT = Path(__file__).resolve().parents[2]
ROOT_SCHEMA = REPO_ROOT / "scjson.schema.json"


def _walk_refs(schema: dict[str, Any], node: Any, seen: set[str]) -> None:
    """Collect reachable ``$defs`` names from a JSON Schema node."""
    if isinstance(node, dict):
        ref = node.get("$ref")
        if isinstance(ref, str) and ref.startswith("#/$defs/"):
            name = ref.rsplit("/", 1)[-1]
            if name not in seen:
                seen.add(name)
                _walk_refs(schema, schema["$defs"][name], seen)
        for key, value in node.items():
            if key == "$defs":
                continue
            _walk_refs(schema, value, seen)
    elif isinstance(node, list):
        for item in node:
            _walk_refs(schema, item, seen)


def test_root_schema_reaches_inclusion_and_communication_surface():
    """Walking from root ``Scxml`` reaches all CONV-H structural families."""
    schema = json.loads(ROOT_SCHEMA.read_text())
    seen = {"Scxml"}
    _walk_refs(schema, schema["$defs"]["Scxml"], seen)
    assert {
        "Scxml",
        "State",
        "Send",
        "Invoke",
        "Content",
        "Param",
        "Donedata",
        "Finalize",
        "Data",
        "Script",
    }.issubset(seen)
    root_props = schema["$defs"]["Scxml"]["properties"]
    assert not {
        "send",
        "invoke",
        "onentry",
        "onexit",
        "transition",
        "finalize",
    }.intersection(root_props)


def test_schema_rejects_non_empty_send_and_raise_under_finalize():
    """The canonical schema records the CONV-H finalize restriction."""
    schema = json.loads(ROOT_SCHEMA.read_text())
    finalize = schema["$defs"]["Finalize"]
    assert finalize["allOf"] == [
        {
            "not": {
                "required": ["send"],
                "properties": {"send": {"type": "array", "minItems": 1}},
            }
        },
        {
            "not": {
                "required": ["raise_value"],
                "properties": {
                    "raise_value": {"type": "array", "minItems": 1}
                },
            }
        },
    ]


@pytest.mark.parametrize("module", [pydantic_models, strict_pydantic_models])
def test_pydantic_finalize_rejects_send_and_raise(module):
    """Pydantic validation mirrors SCXML's finalize restriction."""
    module.Scxml.model_validate(
        {
            "state": [
                {
                    "id": "s",
                    "invoke": [
                        {
                            "finalize": [
                                {"assign": [{"location": "x", "expr": "1"}]}
                            ]
                        }
                    ],
                }
            ]
        }
    )

    with pytest.raises(ValidationError):
        module.Scxml.model_validate(
            {
                "state": [
                    {
                        "id": "s",
                        "invoke": [{"finalize": [{"send": [{"event": "bad"}]}]}],
                    }
                ]
            }
        )

    with pytest.raises(ValidationError):
        module.Scxml.model_validate(
            {
                "state": [
                    {
                        "id": "s",
                        "invoke": [
                            {"finalize": [{"raise_value": [{"event": "bad"}]}]}
                        ],
                    }
                ]
            }
        )


def test_xml_to_json_preserves_standard_inclusion_and_resource_surfaces():
    """SCXML conversion preserves CONV-H fields from the root document graph."""
    xml = """
    <scxml xmlns="http://www.w3.org/2005/07/scxml"
           datamodel="python" initial="s">
      <datamodel>
        <data id="external" src="external.json"/>
      </datamodel>
      <script src="logic.py"/>
      <state id="s">
        <invoke id="childBySrc" type="scxml" src="child.scxml">
          <param name="seed" expr="1"/>
        </invoke>
        <invoke type="scxml">
          <content>
            <scxml datamodel="python" initial="inner">
              <state id="inner"/>
            </scxml>
          </content>
          <finalize>
            <assign location="done" expr="true"/>
          </finalize>
        </invoke>
        <onentry>
          <send event="hello" target="#_parent">
            <param name="payload" expr="42"/>
            <content expr="payload_expr"/>
          </send>
        </onentry>
        <transition target="f"/>
      </state>
      <final id="f">
        <donedata>
          <content expr="result"/>
          <param name="status" expr="'ok'"/>
        </donedata>
      </final>
    </scxml>
    """
    handler = SCXMLDocumentHandler()
    data = json.loads(handler.xml_to_json(xml))

    assert data["datamodel"][0]["data"][0]["src"] == "external.json"
    assert data["script"][0]["src"] == "logic.py"

    state = data["state"][0]
    by_src = state["invoke"][0]
    assert by_src["id"] == "childBySrc"
    assert by_src["src"] == "child.scxml"
    assert by_src["param"][0]["name"] == "seed"

    inline = state["invoke"][1]
    nested = inline["content"][0]["content"][0]
    assert nested["state"][0]["id"] == "inner"
    assert inline["finalize"][0]["assign"][0]["location"] == "done"

    send = state["onentry"][0]["send"][0]
    assert send["event"] == "hello"
    assert send["target"] == "#_parent"
    assert send["param"][0]["name"] == "payload"
    assert send["content"][0]["expr"] == "payload_expr"

    donedata = data["final"][0]["donedata"][0]
    assert donedata["content"]["expr"] == "result"
    assert donedata["param"][0]["name"] == "status"

    round_tripped = json.loads(handler.xml_to_json(handler.json_to_xml(json.dumps(data))))
    assert round_tripped["state"][0]["invoke"][0]["src"] == "child.scxml"
    assert (
        round_tripped["state"][0]["invoke"][1]["content"][0]["content"][0][
            "state"
        ][0]["id"]
        == "inner"
    )
    assert round_tripped["state"][0]["onentry"][0]["send"][0]["target"] == "#_parent"
    assert round_tripped["final"][0]["donedata"][0]["param"][0]["name"] == "status"


def test_xinclude_preserve_mode_keeps_include_directive_as_extension():
    """Unresolved XInclude mode preserves the include directive explicitly."""
    xml = """
    <scxml xmlns="http://www.w3.org/2005/07/scxml"
           xmlns:xi="http://www.w3.org/2001/XInclude"
           initial="s">
      <xi:include href="child.scxml"/>
      <state id="s"/>
    </scxml>
    """
    handler = SCXMLDocumentHandler()
    data = json.loads(handler.xml_to_json(xml))

    include = data["other_element"][0]
    assert include["qname"] == "{http://www.w3.org/2001/XInclude}include"
    assert include["attributes"]["href"] == "child.scxml"
    assert data["state"][0]["id"] == "s"


def test_xinclude_resolve_mode_converts_assembled_tree(tmp_path):
    """Resolved XInclude mode converts the assembled SCXML tree."""
    child = tmp_path / "child.scxml"
    child.write_text(
        '<state xmlns="http://www.w3.org/2005/07/scxml" id="included"/>',
        encoding="utf-8",
    )
    root = tmp_path / "root.scxml"
    xml = """
    <scxml xmlns="http://www.w3.org/2005/07/scxml"
           xmlns:xi="http://www.w3.org/2001/XInclude"
           initial="included">
      <xi:include href="child.scxml"/>
    </scxml>
    """
    root.write_text(xml, encoding="utf-8")

    handler = SCXMLDocumentHandler(xinclude="resolve")
    data = json.loads(
        handler.xml_to_json(xml, xinclude_base_url=str(root))
    )

    assert "other_element" not in data
    assert data["state"][0]["id"] == "included"
    assert data["initial"] == ["included"]


@pytest.mark.parametrize(
    ("path", "snippets"),
    [
        (
            REPO_ROOT / "js/src/scjsonProps.ts",
            [
                "export interface SendProps",
                "export const defaultSend",
                "export type SendArray",
                "export interface InvokeProps",
                "export const defaultInvoke",
                "export type InvokeArray",
                "export interface ContentProps",
                "export const defaultContent",
                "export type ContentArray",
                "export interface ParamProps",
                "export const defaultParam",
                "export type ParamArray",
                "export interface DonedataProps",
                "export const defaultDonedata",
                "export type DonedataArray",
                "export interface FinalizeProps",
                "export const defaultFinalize",
                "export type FinalizeArray",
            ],
        ),
        (
            REPO_ROOT / "rust/src/scjson_props.rs",
            [
                "pub struct SendProps",
                "impl Default for SendProps",
                "pub content: Vec<ContentProps>",
                "pub param: Vec<ParamProps>",
                "pub struct InvokeProps",
                "impl Default for InvokeProps",
                "pub finalize: Vec<FinalizeProps>",
                "pub struct ContentProps",
                "impl Default for ContentProps",
                "pub content: Option<Vec<ScxmlProps>>",
                "pub struct ParamProps",
                "impl Default for ParamProps",
                "pub struct DonedataProps",
                "impl Default for DonedataProps",
                "pub content: Option<ContentProps>",
                "pub struct FinalizeProps",
                "impl Default for FinalizeProps",
                "pub send: Vec<SendProps>",
            ],
        ),
        (
            REPO_ROOT / "swift/Sources/SCJSONKit/ScjsonTypes.swift",
            [
                "public struct SendProps",
                "public static func makeDefault() -> SendProps",
                "public typealias SendArray",
                "public struct InvokeProps",
                "public static func makeDefault() -> InvokeProps",
                "public typealias InvokeArray",
                "public struct ContentProps",
                "public static func makeDefault() -> ContentProps",
                "public typealias ContentArray",
                "public struct ParamProps",
                "public static func makeDefault() -> ParamProps",
                "public typealias ParamArray",
                "public struct DonedataProps",
                "public static func makeDefault() -> DonedataProps",
                "public typealias DonedataArray",
                "public struct FinalizeProps",
                "public static func makeDefault() -> FinalizeProps",
                "public typealias FinalizeArray",
            ],
        ),
    ],
)
def test_maintained_language_bindings_expose_conv_h_surface(path, snippets):
    """Maintained generated bindings expose CONV-H families and defaults."""
    text = path.read_text(encoding="utf-8")
    missing = [snippet for snippet in snippets if snippet not in text]
    assert missing == []
