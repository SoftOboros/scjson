//! Agent Name: rust-converters-tests
//!
//! Part of the scjson project.
//! Developed by Softoboros Technology Inc.
//! Licensed under the BSD 1-Clause License.

use scjson::{xml_to_json, json_to_xml};
use serde_json::Value;
use xmltree::{Element, XMLNode};

const SCXML_NS: &str = "http://www.w3.org/2005/07/scxml";

#[test]
fn mixed_executable_order_retains_branch_markers_and_extensions() {
    let xml = r#"<scxml xmlns="http://www.w3.org/2005/07/scxml" xmlns:x="urn:example">
        <state><onentry><if cond="a"><log label="a"/><elseif cond="b"/><x:note/>
        <else/><log label="b"/></if></onentry></state></scxml>"#;
    let wire: Value = serde_json::from_str(&xml_to_json(xml, true).unwrap()).unwrap();
    let branch = &wire["state"][0]["onentry"][0]["if_value"][0];
    assert_eq!(branch["execution_order"], serde_json::json!(["log","elseif","{urn:example}note","else","log"]));
    assert_eq!(branch["elseif"], serde_json::json!({"cond": "b"}));
    assert_eq!(round_trip(xml), wire);
}

#[test]
fn invalid_execution_order_and_misplaced_markers_are_refused() {
    use serde_json::json;
    for order in [Value::Null, json!([]), json!(["unknown"]), json!(["log","log"])] {
        let wire = json!({"state":[{"onentry":[{"log":[{}],"execution_order":order}]}]});
        assert!(json_to_xml(&wire.to_string()).is_err());
    }
    for body in ["<else/>", "<if cond='a'><else/><elseif cond='b'/></if>"] {
        let xml = format!("<scxml><state><onentry>{body}</onentry></state></scxml>");
        assert!(xml_to_json(&xml, true).is_err());
    }
}

#[test]
fn document_and_compound_state_keep_their_own_child_order() {
    let xml = r#"<scxml xmlns="http://www.w3.org/2005/07/scxml" initial="owner">
        <final/><state id="owner"><initial><transition target="p"/></initial>
        <parallel id="p"><state id="leaf"/></parallel><final/><state id="s"/></state></scxml>"#;
    let mut wire: Value = serde_json::from_str(&xml_to_json(xml, true).unwrap()).unwrap();
    assert_eq!(wire["state_order"], serde_json::json!(["final", "state"]));
    assert_eq!(wire["state"][0]["state_order"], serde_json::json!(["parallel", "final", "state"]));
    let output = json_to_xml(&wire.to_string()).unwrap();
    assert!(!output.contains("state_order"));
    let reread: Value = serde_json::from_str(&xml_to_json(&output, true).unwrap()).unwrap();
    assert_eq!(wire, reread);
    wire.as_object_mut().unwrap().remove("state_order");
    wire["state"][0].as_object_mut().unwrap().remove("state_order");
    let restored = json_to_xml(&wire.to_string()).unwrap();
    let legacy: Value = serde_json::from_str(&xml_to_json(&restored, true).unwrap()).unwrap();
    assert_eq!(legacy["state_order"], serde_json::json!(["state", "final"]));
    assert_eq!(legacy["state"][0]["state_order"], serde_json::json!(["state", "parallel", "final"]));
}

#[test]
fn rejects_invalid_state_order_before_pruning() {
    let doc = serde_json::json!({"state":[{}], "final":[{}]});
    for marker in [Value::Null, serde_json::json!([]), serde_json::json!(["state"]),
                   serde_json::json!(["final","final"]), serde_json::json!(["other","state"])] {
        let mut bad = doc.clone();
        bad["state_order"] = marker;
        for omit in [true, false] {
            let error = scjson::json_to_xml_opts(&bad.to_string(), omit).unwrap_err();
            assert!(error.to_string().contains("state_order"));
        }
    }
    for bad in [r#"{"parallel":[{"state_order":[]}]}"#, r#"{"final":[{"state_order":[]}]}"#] {
        assert!(json_to_xml(bad).unwrap_err().to_string().contains("state_order"));
    }
}

fn region_ids(node: &Element) -> Vec<&str> {
    node.children
        .iter()
        .filter_map(XMLNode::as_element)
        .filter(|e| {
            e.namespace.as_deref() == Some(SCXML_NS)
                && matches!(e.name.as_str(), "state" | "parallel")
        })
        .map(|e| e.attributes["id"].as_str())
        .collect()
}

#[test]
fn mixed_regions_round_trip_with_comments_foreign_names_and_nested_charts() {
    let chart = r#"<scxml xmlns="http://www.w3.org/2005/07/scxml" xmlns:f="urn:foreign">
      <parallel id="outer"><state id="a"/><f:parallel id="foreign"/>
        <!-- attached to inner --><parallel id="inner"><parallel id="ip"/><state id="is"/></parallel>
        <history id="h"/><state id="b"><invoke><content><scxml>
          <parallel id="child"><state id="cs"/><parallel id="cp"/></parallel>
        </scxml></content></invoke></state>
      </parallel></scxml>"#;
    let wire = xml_to_json(chart, true).unwrap();
    let value: Value = serde_json::from_str(&wire).unwrap();
    let outer = &value["parallel"][0];
    assert_eq!(
        outer["region_order"],
        serde_json::json!(["state", "parallel", "state"])
    );
    assert_eq!(
        outer["parallel"][0]["region_order"],
        serde_json::json!(["parallel", "state"])
    );
    assert_eq!(outer["parallel"][0]["help_text"][0], "attached to inner");
    assert_eq!(outer["other_element"][0]["qname"], "{urn:foreign}parallel");
    assert_eq!(
        outer["state"][1]["invoke"][0]["content"][0]["content"][0]["parallel"][0]["region_order"],
        serde_json::json!(["state", "parallel"])
    );
    let output = json_to_xml(&wire).unwrap();
    assert!(!output.contains("region_order"));
    let root = Element::parse(output.as_bytes()).unwrap();
    let p = root.get_child(("parallel", SCXML_NS)).unwrap();
    assert_eq!(region_ids(p), ["a", "inner", "b"]);
    assert_eq!(
        region_ids(p.get_child(("parallel", SCXML_NS)).unwrap()),
        ["ip", "is"]
    );
    assert!(p.get_child(("parallel", "urn:foreign")).is_some());
    let again: Value = serde_json::from_str(&xml_to_json(&output, true).unwrap()).unwrap();
    assert_eq!(again, value);
}

#[test]
fn legacy_and_explicit_region_occurrences() {
    for (model, expected) in [
        (
            r#"{"parallel":[{"parallel":[{"id":"p"}],"state":[{"id":"a"},{"id":"b"}]}]}"#,
            ["a", "b", "p"],
        ),
        (
            r#"{"parallel":[{"state":[{"id":"a"},{"id":"b"}],"parallel":[{"id":"p"}]}]}"#,
            ["a", "b", "p"],
        ),
        (
            r#"{"parallel":[{"region_order":["parallel","state","state"],"state":[{"id":"a"},{"id":"b"}],"parallel":[{"id":"p"}]}]}"#,
            ["p", "a", "b"],
        ),
    ] {
        let xml = json_to_xml(model).unwrap();
        let root = Element::parse(xml.as_bytes()).unwrap();
        assert_eq!(region_ids(root.get_child("parallel").unwrap()), expected);
    }
    let empty = r#"{"parallel":[{"id":"p","region_order":[]}]}"#;
    assert!(!json_to_xml(empty).unwrap().contains("region_order"));
    let omitted = xml_to_json(r#"<scxml xmlns="http://www.w3.org/2005/07/scxml"><parallel><state id="s"/></parallel></scxml>"#, true).unwrap();
    assert!(!omitted.contains("region_order"));
}

#[test]
fn invalid_region_metadata_is_rejected_before_it_can_be_omitted() {
    let base =
        serde_json::json!({"parallel":[{"id":"p","parallel":[{"id":"q"}],"state":[{"id":"a"}]}]});
    for order in [
        Value::Null,
        serde_json::json!("state"),
        serde_json::json!([]),
        serde_json::json!(["parallel"]),
        serde_json::json!(["state", "state", "parallel"]),
        serde_json::json!(["state", "foreign"]),
        serde_json::json!([1, "parallel"]),
    ] {
        let mut doc = base.clone();
        doc["parallel"][0]["region_order"] = order;
        for omit in [false, true] {
            let err = scjson::json_to_xml_opts(&doc.to_string(), omit).unwrap_err();
            assert!(err.to_string().contains("region_order"));
        }
    }
    for raw in [
        r#"{"region_order":null}"#,
        r#"{"state":[{"region_order":[]}]}"#,
    ] {
        assert!(json_to_xml(raw)
            .unwrap_err()
            .to_string()
            .contains("region_order"));
    }
    let opaque =
        r#"{"parallel":[{"id":"p","other_attributes":{"settings":{"region_order":[99]}}}]}"#;
    assert!(json_to_xml(opaque).unwrap().contains("settings="));
}

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

#[test]
fn other_attributes_preserve_json_metadata() {
    let scjson = serde_json::json!({
        "version": 1.0,
        "datamodel_attribute": "null",
        "state": [{
            "id": "s",
            "other_attributes": {
                "position": "1,2",
                "help_text_box": {"visible": true, "x": 1},
                "priority": 3
            }
        }]
    });
    let xml = json_to_xml(&scjson.to_string()).unwrap();

    assert!(xml.contains("position=\"1,2\""));
    assert!(xml.contains("priority=\"3\""));
    assert!(xml.contains("help_text_box=\""));
    assert!(!xml.contains("<other_attributes"));

    let back: Value = serde_json::from_str(&xml_to_json(&xml, true).unwrap()).unwrap();
    let attrs = &back["state"][0]["other_attributes"];
    assert_eq!(attrs["position"], "1,2");
    assert_eq!(attrs["priority"], "3");
    assert_eq!(attrs["help_text_box"]["visible"], true);
    assert_eq!(attrs["help_text_box"]["x"], 1);
}

#[test]
fn comments_promote_to_help_text_and_emit_back() {
    let xml = r#"
<!-- root help -->
<scxml xmlns="http://www.w3.org/2005/07/scxml" initial="s">
  <!-- state help -->
  <state id="s">
    <!-- transition help -->
    <transition target="done"/>
  </state>
  <final id="done"/>
</scxml>
"#;
    let obj: Value = serde_json::from_str(&xml_to_json(xml, true).unwrap()).unwrap();
    assert_eq!(obj["help_text"], serde_json::json!(["root help"]));
    assert_eq!(obj["state"][0]["help_text"], serde_json::json!(["state help"]));
    assert_eq!(
        obj["state"][0]["transition"][0]["help_text"],
        serde_json::json!(["transition help"])
    );

    let emitted = json_to_xml(&obj.to_string()).unwrap();
    assert!(emitted.contains("<!--root help-->"));
    assert!(emitted.contains("state help"));
    assert!(emitted.contains("transition help"));
    let rt: Value = serde_json::from_str(&xml_to_json(&emitted, true).unwrap()).unwrap();
    assert_eq!(rt["help_text"], serde_json::json!(["root help"]));
    assert_eq!(rt["state"][0]["help_text"], serde_json::json!(["state help"]));
    assert_eq!(
        rt["state"][0]["transition"][0]["help_text"],
        serde_json::json!(["transition help"])
    );
}
#[test]
fn executable_keys_cannot_be_dropped_or_shadowed() {
    use serde_json::json;
    let chart = |entry| json!({"state":[{"id":"s","onentry":[entry]}]}).to_string();
    let good = chart(json!({"raise_value":[{"event":"go"}]}));
    assert!(scjson::json_to_xml(&good).unwrap().contains("<raise event=\"go\""));
    for block in [
        json!({"raise":[]}), json!({"raiseValue":[]}),
        json!({"raise":[], "raise_value":[]}),
        json!({"if_value":[{"cond":"True", "else":{}}]}),
        json!({"if":[]}), json!({"ifValue":[]}),
    ] {
        assert!(scjson::json_to_xml(&chart(block)).is_err());
    }
}
