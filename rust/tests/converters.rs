//! Agent Name: rust-converters-tests
//!
//! Part of the scjson project.
//! Developed by Softoboros Technology Inc.
//! Licensed under the BSD 1-Clause License.

use scjson::{xml_to_json, json_to_xml};
use serde_json::Value;

fn round_trip(xml: &str) -> Value {
    let json = xml_to_json(xml, true).unwrap();
    let xml_rt = json_to_xml(&json).unwrap();
    let json_rt = xml_to_json(&xml_rt, true).unwrap();
    serde_json::from_str(&json_rt).unwrap()
}

#[test]
fn script_becomes_object() {
    let xml = "<scxml xmlns=\"http://www.w3.org/2005/07/scxml\"><script>foo</script></scxml>";
    let obj: Value = serde_json::from_str(&xml_to_json(xml, true).unwrap()).unwrap();
    assert!(obj.get("script").is_some());
    assert_eq!(obj["script"][0]["content"][0], "foo");
    let rt = round_trip(xml);
    assert_eq!(rt, obj);
}

#[test]
fn transition_targets_split() {
    let xml = "<scxml xmlns=\"http://www.w3.org/2005/07/scxml\"><state id=\"s1\"><transition target=\"a b\"/></state></scxml>";
    let obj: Value = serde_json::from_str(&xml_to_json(xml, true).unwrap()).unwrap();
    let trans = &obj["state"][0]["transition"][0];
    assert_eq!(trans["target"], serde_json::json!(["a", "b"]));
    let rt = round_trip(xml);
    assert_eq!(rt, obj);
}

#[test]
fn invoke_nested_scxml() {
    let xml = "<scxml xmlns=\"http://www.w3.org/2005/07/scxml\"><state id=\"s\"><invoke><content><scxml><state id=\"i\"/></scxml></content></invoke></state></scxml>";
    let obj: Value = serde_json::from_str(&xml_to_json(xml, true).unwrap()).unwrap();
    assert!(obj["state"][0]["invoke"][0]["content"][0]["content"][0].get("state").is_some());
    let rt = round_trip(xml);
    assert_eq!(rt, obj);
}

#[test]
fn assign_send_defaults() {
    let xml = "<scxml xmlns=\"http://www.w3.org/2005/07/scxml\"><state id=\"s\"><onentry><assign location=\"foo\" expr=\"1\"/><send event=\"e\"/></onentry></state></scxml>";
    let obj: Value = serde_json::from_str(&xml_to_json(xml, true).unwrap()).unwrap();
    let entry = &obj["state"][0]["onentry"][0];
    assert_eq!(entry["assign"][0]["type_value"], "replacechildren");
    assert_eq!(entry["send"][0]["type_value"], "scxml");
    assert_eq!(entry["send"][0]["delay"], "0s");
    let rt = round_trip(xml);
    assert_eq!(rt, obj);
}

#[test]
fn empty_else_and_final() {
    let xml_else = "<scxml xmlns=\"http://www.w3.org/2005/07/scxml\"><state id=\"s\"><onentry><if cond=\"true\"><else/></if></onentry></state></scxml>";
    let obj_else: Value = serde_json::from_str(&xml_to_json(xml_else, true).unwrap()).unwrap();
    assert!(obj_else["state"][0]["onentry"][0]["if_value"][0].get("else_value").is_some());

    let xml_final = "<scxml xmlns=\"http://www.w3.org/2005/07/scxml\"><state id=\"s\"><onentry><assign location=\"x\"><scxml><final/></scxml></assign></onentry></state></scxml>";
    let obj_final: Value = serde_json::from_str(&xml_to_json(xml_final, true).unwrap()).unwrap();
    assert_eq!(obj_final["state"][0]["onentry"][0]["assign"][0]["content"][0]["final"], serde_json::json!([{}]));

    let rt_else = round_trip(xml_else);
    assert_eq!(rt_else, obj_else);
    let rt_final = round_trip(xml_final);
    assert_eq!(rt_final, obj_final);
}

