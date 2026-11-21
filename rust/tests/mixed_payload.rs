//! Verify mixed payload values and ordered-action metadata on the Rust wire.
use scjson::scjson_props::{IfProps, OnentryProps, ScxmlProps};
use serde_json::{json, Value};

#[test]
fn mixed_payloads_round_trip() {
    let wire: Value =
        serde_json::from_str(include_str!("fixtures/ordered-mixed-payload.scjson")).unwrap();
    let decoded: ScxmlProps = serde_json::from_value(wire.clone()).unwrap();
    let encoded = serde_json::to_value(decoded).unwrap();
    let entry = "/state/0/onentry/0";
    for field in ["send/0/content/0/content", "execution_order"] {
        let path = format!("{entry}/{field}");
        assert!(wire.pointer(&path).is_some());
        assert_eq!(encoded.pointer(&path), wire.pointer(&path));
    }
}

#[test]
fn absence_and_explicit_order_round_trip() {
    for wire in [
        json!({}),
        json!({"execution_order":[]}),
        json!({"execution_order": ["assign", "raise"]}),
    ] {
        let value: OnentryProps = serde_json::from_value(wire.clone()).unwrap();
        let encoded = serde_json::to_value(value).unwrap();
        assert_eq!(encoded.get("execution_order"), wire.get("execution_order"));
    }
    for markers in [json!({"cond": "a"}), json!([{"cond":"a"},{"cond":"b"}])] {
        let value: IfProps = serde_json::from_value(json!({"elseif": markers})).unwrap();
        assert_eq!(serde_json::to_value(value).unwrap()["elseif"], markers);
    }
}
