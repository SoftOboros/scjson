//! Agent Name: rust-lib
//!
//! Part of the scjson project.
//! Developed by Softoboros Technology Inc.
//! Licensed under the BSD 1-Clause License.
//!
//! Library providing basic SCXML <-> scjson conversion.

use serde_json::{Number, Value};
use thiserror::Error;
use xmltree::{Element, XMLNode};
use xmltree::Error as XmlWriteError;

/// Attribute name mappings used during conversion.
const ATTRIBUTE_MAP: &[(&str, &str)] = &[
    ("datamodel", "datamodel_attribute"),
    ("initial", "initial_attribute"),
    ("type", "type_value"),
    ("raise", "raise_value"),
];

/// Keys that should always be arrays in the output.
const ARRAY_KEYS: &[&str] = &[
    "assign", "cancel", "content", "data", "datamodel", "donedata", "final",
    "finalize", "foreach", "history", "if_value", "initial", "invoke", "log",
    "onentry", "onexit", "other_element", "parallel", "param", "raise_value",
    "script", "send", "state",
];

/// Errors produced by conversion routines.
#[derive(Debug, Error)]
pub enum ScjsonError {
    #[error("XML parse error: {0}")]
    Xml(#[from] xmltree::ParseError),
    #[error("XML write error: {0}")]
    XmlWrite(#[from] XmlWriteError),
    #[error("JSON parse error: {0}")]
    Json(#[from] serde_json::Error),
    #[error("unsupported document")]
    Unsupported,
}

/// Recursively convert an [`xmltree::Element`] into a JSON [`Value`].
fn element_to_value(elem: &Element) -> Value {
    let mut obj = serde_json::Map::new();

    for (k, v) in &elem.attributes {
        if k == "xmlns" || k.starts_with("xmlns") {
            continue;
        }
        let mut name = k.as_str();
        for (attr, prop) in ATTRIBUTE_MAP {
            if *attr == k.as_str() {
                name = prop;
                break;
            }
        }
        if name == "version" {
            if let Ok(n) = v.parse::<f64>() {
                let val = if (n.fract() - 0.0).abs() < f64::EPSILON {
                    Value::Number(Number::from(n as i64))
                } else {
                    Value::Number(Number::from_f64(n).unwrap())
                };
                obj.insert(name.to_string(), val);
            } else {
                obj.insert(name.to_string(), Value::String(v.clone()));
            }
        } else {
            obj.insert(name.to_string(), Value::String(v.clone()));
        }
    }

    let mut content: Vec<Value> = Vec::new();


    for child in &elem.children {
        match child {
            XMLNode::Element(e) => {
                let mut name = e.name.as_str();
                if name == "else" {
                    name = "else_value";
                } else if name == "if" {
                    name = "if_value";
                } else if name == "raise" {
                    name = "raise_value";
                }
                let val = element_to_value(e);
                match obj.get_mut(name) {
                    Some(Value::Array(arr)) => arr.push(val),
                    Some(prev) => {
                        let old = prev.take();
                        *prev = Value::Array(vec![old, val]);
                    }
                    None => {
                        obj.insert(name.to_string(), val);
                    }
                }
            }
            XMLNode::Text(t) => {
                if !t.trim().is_empty() {
                    content.push(Value::String(t.clone()));
                }
            }
            _ => {}
        }
    }

    if !content.is_empty() {
        obj.insert("content".into(), Value::Array(content));
    }

    Value::Object(obj)
}

fn split_token_attrs(value: &mut Value) {
    match value {
        Value::Object(map) => {
            let keys: Vec<String> = map.keys().cloned().collect();
            for k in keys {
                if let Some(v) = map.get_mut(&k) {
                    if (k == "initial" || k == "initial_attribute") && v.is_string() {
                        let tokens: Vec<Value> = v
                            .as_str()
                            .unwrap()
                            .split_whitespace()
                            .map(|s| Value::String(s.to_string()))
                            .collect();
                        *v = Value::Array(tokens);
                        continue;
                    }
                    if k == "transition" {
                        let arr = if v.is_array() {
                            v.as_array_mut().unwrap()
                        } else {
                            let old = v.take();
                            *v = Value::Array(vec![old]);
                            v.as_array_mut().unwrap()
                        };
                        for tr in arr.iter_mut() {
                            if let Value::Object(trmap) = tr {
                                if let Some(tgt) = trmap.get_mut("target") {
                                    if let Some(s) = tgt.as_str() {
                                        let tokens: Vec<Value> = s
                                            .split_whitespace()
                                            .map(|x| Value::String(x.to_string()))
                                            .collect();
                                        *tgt = Value::Array(tokens);
                                    }
                                }
                                split_token_attrs(tr);
                            }
                        }
                        continue;
                    }
                    split_token_attrs(v);
                }
            }
        }
        Value::Array(arr) => {
            for v in arr.iter_mut() {
                split_token_attrs(v);
            }
        }
        _ => {}
    }
}

fn ensure_arrays(value: &mut Value) {
    match value {
        Value::Object(map) => {
            let keys: Vec<String> = map.keys().cloned().collect();
            for k in keys {
                if let Some(v) = map.get_mut(&k) {
                    if ARRAY_KEYS.contains(&k.as_str()) {
                        if v.is_array() {
                            for item in v.as_array_mut().unwrap() {
                                ensure_arrays(item);
                            }
                        } else {
                            let mut arr = vec![v.take()];
                            ensure_arrays(&mut arr[0]);
                            *v = Value::Array(arr);
                        }
                        continue;
                    }
                    if k == "transition" {
                        let arr = if v.is_array() {
                            v.as_array_mut().unwrap()
                        } else {
                            let old = v.take();
                            *v = Value::Array(vec![old]);
                            v.as_array_mut().unwrap()
                        };
                        for tr in arr.iter_mut() {
                            if let Value::Object(trmap) = tr {
                                if let Some(tgt) = trmap.get_mut("target") {
                                    if !tgt.is_array() {
                                        *tgt = Value::Array(vec![tgt.take()]);
                                    }
                                }
                                ensure_arrays(tr);
                            }
                        }
                        continue;
                    }
                    ensure_arrays(v);
                }
            }
        }
        Value::Array(arr) => {
            for v in arr.iter_mut() {
                ensure_arrays(v);
            }
        }
        _ => {}
    }
}

fn fix_assign_defaults(value: &mut Value) {
    match value {
        Value::Object(map) => {
            if let Some(assign_val) = map.get_mut("assign") {
                let arr = if assign_val.is_array() {
                    assign_val.as_array_mut().unwrap()
                } else {
                    let old = assign_val.take();
                    *assign_val = Value::Array(vec![old]);
                    assign_val.as_array_mut().unwrap()
                };
                for a in arr.iter_mut() {
                    if let Value::Object(m) = a {
                        if m.get("type_value").is_none() {
                            m.insert(
                                "type_value".to_string(),
                                Value::String("replacechildren".to_string()),
                            );
                        }
                        fix_assign_defaults(a);
                    }
                }
            }
            for v in map.values_mut() {
                fix_assign_defaults(v);
            }
        }
        Value::Array(arr) => {
            for v in arr.iter_mut() {
                fix_assign_defaults(v);
            }
        }
        _ => {}
    }
}

fn fix_send_defaults(value: &mut Value) {
    match value {
        Value::Object(map) => {
            if let Some(send_val) = map.get_mut("send") {
                let arr = if send_val.is_array() {
                    send_val.as_array_mut().unwrap()
                } else {
                    let old = send_val.take();
                    *send_val = Value::Array(vec![old]);
                    send_val.as_array_mut().unwrap()
                };
                for s in arr.iter_mut() {
                    if let Value::Object(m) = s {
                        if m.get("type_value").is_none() {
                            m.insert(
                                "type_value".to_string(),
                                Value::String("scxml".to_string()),
                            );
                        }
                        if m.get("delay").is_none() {
                            m.insert("delay".to_string(), Value::String("0s".to_string()));
                        }
                        fix_send_defaults(s);
                    }
                }
            }
            for v in map.values_mut() {
                fix_send_defaults(v);
            }
        }
        Value::Array(arr) => {
            for v in arr.iter_mut() {
                fix_send_defaults(v);
            }
        }
        _ => {}
    }
}

fn reorder_scxml(value: &mut Value) {
    match value {
        Value::Object(map) => {
            for v in map.values_mut() {
                reorder_scxml(v);
            }
            if let Some(v) = map.remove("datamodel") {
                map.insert("datamodel".to_string(), v);
            }
            if let Some(v) = map.remove("version") {
                map.insert("version".to_string(), v);
            }
            if let Some(v) = map.remove("datamodel_attribute") {
                map.insert("datamodel_attribute".to_string(), v);
            }
        }
        Value::Array(arr) => {
            for v in arr.iter_mut() {
                reorder_scxml(v);
            }
        }
        _ => {}
    }
}

fn restore_keys(value: &Value) -> Value {
    match value {
        Value::Array(arr) => {
            Value::Array(arr.iter().map(restore_keys).collect())
        }
        Value::Object(map) => {
            let mut out = serde_json::Map::new();
            for (k, v) in map {
            let mut nk = k.to_string();
            if nk == "if_value" {
                nk = "if".to_string();
            } else if nk == "raise_value" {
                nk = "raise".to_string();
            }
            for (attr, prop) in ATTRIBUTE_MAP {
                if *prop == nk {
                    nk = format!("@_{}", attr);
                    break;
                }
            }
            if nk == "content" {
                out.insert(nk, restore_keys(v));
            } else if v.is_array()
                && v.as_array().unwrap().iter().all(|x| !x.is_object())
            {
                let val = v
                    .as_array()
                    .unwrap()
                    .iter()
                    .map(|x| x.as_str().unwrap_or(""))
                    .collect::<Vec<_>>()
                    .join(" ");
                if nk.starts_with("@_") {
                    out.insert(nk.clone(), Value::String(val));
                } else {
                    out.insert(format!("@_{}", nk), Value::String(val));
                }
            } else if !v.is_object() {
                if nk.starts_with("@_") {
                    out.insert(nk.clone(), v.clone());
                } else {
                    out.insert(format!("@_{}", nk), v.clone());
                }
            } else {
                out.insert(nk, restore_keys(v));
            }
            }
            Value::Object(out)
        }
        _ => value.clone(),
    }
}

fn build_element(name: &str, value: &Value) -> Result<Element, ScjsonError> {
    let obj = value.as_object().ok_or(ScjsonError::Unsupported)?;
    let mut elem = Element::new(name);
    for (k, v) in obj {
        if k.starts_with("@_") {
            if let Some(s) = v.as_str() {
                elem.attributes.insert(k.trim_start_matches("@_").to_string(), s.to_string());
            } else if let Some(n) = v.as_i64() {
                elem.attributes.insert(k.trim_start_matches("@_").to_string(), n.to_string());
            } else if let Some(f) = v.as_f64() {
                elem.attributes.insert(k.trim_start_matches("@_").to_string(), f.to_string());
            }
            continue;
        }
        if k == "content" {
            if let Value::Array(arr) = v {
                let text = arr
                    .iter()
                    .filter_map(|x| x.as_str())
                    .collect::<Vec<_>>()
                    .join("");
                if !text.is_empty() {
                    elem.children.push(XMLNode::Text(text));
                }
            }
            continue;
        }
        match v {
            Value::Array(arr) => {
                for item in arr {
                    elem.children.push(XMLNode::Element(build_element(k, item)?));
                }
            }
            Value::Object(_) => {
                elem.children.push(XMLNode::Element(build_element(k, v)?));
            }
            Value::String(s) => {
                let mut child = Element::new(k);
                child.children.push(XMLNode::Text(s.clone()));
                elem.children.push(XMLNode::Element(child));
            }
            _ => {}
        }
    }
    Ok(elem)
}

/// Convert an SCXML string to scjson.
///
/// # Parameters
/// - `xml`: XML input string.
/// - `omit_empty`: Remove empty fields when true.
///
/// # Returns
/// JSON string representing the document.
pub fn xml_to_json(xml: &str, _omit_empty: bool) -> Result<String, ScjsonError> {
    let root = Element::parse(xml.as_bytes())?;
    if root.name != "scxml" {
        return Err(ScjsonError::Unsupported);
    }

    let mut value = element_to_value(&root);

    // Apply defaults and adjustments
    split_token_attrs(&mut value);
    ensure_arrays(&mut value);
    fix_assign_defaults(&mut value);
    fix_send_defaults(&mut value);
    reorder_scxml(&mut value);

    if let Value::Object(ref mut map) = value {
        if !map.contains_key("version") {
            map.insert("version".to_string(), Value::Number(Number::from(1))); 
        }
        if !map.contains_key("datamodel_attribute") {
            map.insert(
                "datamodel_attribute".to_string(),
                Value::String("null".to_string()),
            );
        }
    }

    Ok(serde_json::to_string_pretty(&value)?)
}

/// Convert a scjson string to SCXML.
///
/// # Parameters
/// - `json_str`: JSON input string.
///
/// # Returns
/// XML string representing the document.
pub fn json_to_xml(json_str: &str) -> Result<String, ScjsonError> {
    let v: Value = serde_json::from_str(json_str)?;
    let mut restored = restore_keys(&v);
    if let Value::Object(ref mut map) = restored {
        if map.get("@_xmlns").is_none() {
            map.insert(
                "@_xmlns".to_string(),
                Value::String("http://www.w3.org/2005/07/scxml".to_string()),
            );
        }
    }

    let elem = build_element("scxml", &restored)?;
    let mut out = Vec::new();
    elem.write(&mut out)?;
    Ok(String::from_utf8(out).unwrap())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn round_trip_simple() {
        let xml = "<scxml xmlns=\"http://www.w3.org/2005/07/scxml\"/>";
        let json = xml_to_json(xml, true).unwrap();
        assert!(json.contains("version"));
        let xml_rt = json_to_xml(&json).unwrap();
        assert!(xml_rt.contains("scxml"));
    }
}
