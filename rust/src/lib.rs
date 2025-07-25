/*!
"""
Agent Name: rust-lib

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.
"""
*/

//! Library providing basic SCXML <-> scjson conversion.

use serde_json::{Map, Number, Value};
use thiserror::Error;
use xmltree::Error as XmlWriteError;
use xmltree::{Element, XMLNode};

/// Attribute name mappings used during conversion.
// const ATTRIBUTE_MAP: &[(&str, &str)] = &[
//     ("datamodel", "datamodel_attribute"),
//     ("initial", "initial_attribute"),
//     ("type", "type_value"),
//     ("raise", "raise_value"),
// ];
// NOTE: reserved for future use when attribute renaming is implemented.

/// Keys that should always be arrays in the output.
// const ARRAY_KEYS: &[&str] = &[
//     "assign",
//     "cancel",
//     "content",
//     "data",
//     "datamodel",
//     "donedata",
//     "final",
//     "finalize",
//     "foreach",
//     "history",
//     "if_value",
//     "initial",
//     "invoke",
//     "log",
//     "onentry",
//     "onexit",
//     "other_element",
//     "parallel",
//     "param",
//     "raise_value",
//     "script",
//     "send",
//     "state",
// ];
// NOTE: may be reintroduced when enforcing array types during parsing.

/// Attributes whose whitespace should be collapsed.
const COLLAPSE_ATTRS: &[&str] = &[
    "expr",
    "cond",
    "event",
    "target",
    "delay",
    "location",
    "name",
    "src",
    "id",
];

/// Known SCXML element names used for conversion.
const SCXML_ELEMS: &[&str] = &[
    "scxml",
    "state",
    "parallel",
    "final",
    "history",
    "transition",
    "invoke",
    "finalize",
    "datamodel",
    "data",
    "onentry",
    "onexit",
    "log",
    "send",
    "cancel",
    "raise",
    "assign",
    "script",
    "foreach",
    "param",
    "if",
    "elseif",
    "else",
    "content",
    "donedata",
    "initial",
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

fn append_child(map: &mut Map<String, Value>, key: &str, val: Value) {
    match map.get_mut(key) {
        Some(Value::Array(arr)) => arr.push(val),
        Some(other) => {
            let old = other.take();
            *other = Value::Array(vec![old, val]);
        }
        None => {
            map.insert(key.to_string(), Value::Array(vec![val]));
        }
    }
}

fn any_element_to_value(elem: &Element) -> Value {
    let mut map = Map::new();
    map.insert("qname".into(), Value::String(elem.name.clone()));
    let text = elem.get_text().map(|c| c.into_owned()).unwrap_or_default();
    map.insert("text".into(), Value::String(text));
    if !elem.attributes.is_empty() {
        let mut attrs = Map::new();
        for (k, v) in &elem.attributes {
            attrs.insert(k.clone(), Value::String(v.clone()));
        }
        map.insert("attributes".into(), Value::Object(attrs));
    }
    if !elem.children.is_empty() {
        let mut children = Vec::new();
        for c in &elem.children {
            if let XMLNode::Element(e) = c {
                children.push(any_element_to_value(e));
            }
        }
        if !children.is_empty() {
            map.insert("children".into(), Value::Array(children));
        }
    }
    Value::Object(map)
}

fn element_to_map(elem: &Element) -> Map<String, Value> {
    let mut map = Map::new();
    for (k, v) in &elem.attributes {
        match (elem.name.as_str(), k.as_str()) {
            ("transition", "target") => {
                let vals: Vec<Value> = v
                    .split_whitespace()
                    .map(|s| Value::String(s.to_string()))
                    .collect();
                map.insert("target".into(), Value::Array(vals));
            }
            (_, "initial") => {
                let vals: Vec<Value> = v
                    .split_whitespace()
                    .map(|s| Value::String(s.to_string()))
                    .collect();
                if elem.name == "scxml" {
                    map.insert("initial".into(), Value::Array(vals));
                } else {
                    map.insert("initial_attribute".into(), Value::Array(vals));
                }
            }
            (_, "version") => {
                if let Ok(n) = v.parse::<f64>() {
                    if let Some(num) = Number::from_f64(n) {
                        map.insert("version".into(), Value::Number(num));
                    }
                } else {
                    map.insert("version".into(), Value::String(v.clone()));
                }
            }
            (_, "datamodel") => {
                map.insert("datamodel_attribute".into(), Value::String(v.clone()));
            }
            (_, "type") => {
                map.insert("type_value".into(), Value::String(v.clone()));
            }
            (_, "raise") => {
                map.insert("raise_value".into(), Value::String(v.clone()));
            }
            ("send", "delay") => {
                map.insert("delay".into(), Value::String(v.clone()));
            }
            ("send", "event") => {
                map.insert("event".into(), Value::String(v.clone()));
            }
            (_, "xmlns") => {}
            _ => {
                map.insert(k.clone(), Value::String(v.clone()));
            }
        }
    }

    if elem.name == "assign" && !map.contains_key("type_value") {
        map.insert(
            "type_value".to_string(),
            Value::String("replacechildren".into()),
        );
    }
    if elem.name == "send" {
        map.entry("type_value".to_string())
            .or_insert_with(|| Value::String("scxml".into()));
        map.entry("delay".to_string())
            .or_insert_with(|| Value::String("0s".into()));
    }

    let mut text_items = Vec::new();
    for child in &elem.children {
        match child {
            XMLNode::Element(e) => {
                if SCXML_ELEMS.contains(&e.name.as_str()) {
                    let key = match e.name.as_str() {
                        "if" => "if_value",
                        "else" => "else_value",
                        name => name,
                    };
                    let child_map = element_to_map(e);
                    let target_key = if e.name == "scxml" && elem.name != "scxml" {
                        "content"
                    } else if elem.name == "content" && e.name == "scxml" {
                        "content"
                    } else {
                        key
                    };
                    append_child(&mut map, target_key, Value::Object(child_map));
                } else {
                    let val = any_element_to_value(e);
                    append_child(&mut map, "content", val);
                }
            }
            XMLNode::Text(t) => {
                if !t.trim().is_empty() {
                    text_items.push(Value::String(t.to_string()));
                }
            }
            _ => {}
        }
    }
    if !text_items.is_empty() {
        for item in text_items {
            append_child(&mut map, "content", item);
        }
    }

    if elem.name == "scxml" {
        if !map.contains_key("version") {
            map.insert(
                "version".into(),
                Value::Number(Number::from_f64(1.0).unwrap()),
            );
        }
        map.entry("datamodel_attribute".to_string())
            .or_insert_with(|| Value::String("null".into()));
    }
    map
}

fn join_tokens(v: &Value) -> Option<String> {
    match v {
        Value::Array(arr) => {
            if arr.iter().all(|x| x.is_string()) {
                let parts: Vec<String> = arr
                    .iter()
                    .filter_map(|x| x.as_str().map(|s| s.to_string()))
                    .collect();
                Some(parts.join(" "))
            } else {
                None
            }
        }
        Value::String(s) => Some(s.clone()),
        _ => None,
    }
}

fn map_to_element(name: &str, map: &Map<String, Value>) -> Element {
    if name == "scxml" && map.len() == 1 {
        if let Some(Value::Array(arr)) = map.get("content") {
            if arr.len() == 1 {
                if let Some(Value::Object(obj)) = arr.get(0) {
                    return map_to_element("scxml", obj);
                }
            }
        }
    }
    let mut elem_name = name.to_string();
    if let Some(Value::String(q)) = map.get("qname") {
        elem_name = q.clone();
    }
    let mut elem = Element::new(&elem_name);
    if name == "scxml" {
        elem.attributes
            .insert("xmlns".into(), "http://www.w3.org/2005/07/scxml".into());
    }
    if let Some(Value::String(text)) = map.get("text") {
        if !text.is_empty() {
            elem.children.push(XMLNode::Text(text.clone()));
        }
    }
    if let Some(Value::Object(attrs)) = map.get("attributes") {
        for (k, v) in attrs {
            if let Some(s) = v.as_str() {
                elem.attributes.insert(k.clone(), s.to_string());
            }
        }
    }
    for (k, v) in map {
        if ["qname", "text", "attributes"].contains(&k.as_str()) {
            continue;
        }
        if k == "content" {
            if let Value::Array(arr) = v {
                if name == "invoke" {
                    for item in arr {
                        match item {
                            Value::String(s) => {
                                let mut c = Element::new("content");
                                c.children.push(XMLNode::Text(s.clone()));
                                elem.children.push(XMLNode::Element(c));
                            }
                            Value::Object(obj) => {
                                let child_name = if obj.contains_key("state")
                                    || obj.contains_key("final")
                                    || obj.contains_key("version")
                                    || obj.contains_key("datamodel_attribute")
                                {
                                    "scxml"
                                } else {
                                    "content"
                                };
                                let child = map_to_element(child_name, obj);
                                elem.children.push(XMLNode::Element(child));
                            }
                            _ => {}
                        }
                    }
                } else if name == "script" {
                    for item in arr {
                        if let Value::String(s) = item {
                            elem.children.push(XMLNode::Text(s.clone()));
                        }
                    }
                } else {
                    for item in arr {
                        match item {
                            Value::String(s) => elem.children.push(XMLNode::Text(s.clone())),
                            Value::Object(obj) => {
                                let child_name = if obj.contains_key("state")
                                    || obj.contains_key("final")
                                    || obj.contains_key("version")
                                    || obj.contains_key("datamodel_attribute")
                                {
                                    "scxml"
                                } else {
                                    "content"
                                };
                                let child = map_to_element(child_name, obj);
                                elem.children.push(XMLNode::Element(child));
                            }
                            _ => {}
                        }
                    }
                }
            }
            continue;
        }
        if k.ends_with("_attribute") {
            let attr = k.trim_end_matches("_attribute");
            if let Some(val) = join_tokens(v) {
                elem.attributes.insert(attr.into(), val);
            }
            continue;
        }
        if k == "datamodel_attribute" {
            if let Some(val) = join_tokens(v) {
                elem.attributes.insert("datamodel".into(), val);
            }
            continue;
        }
        if k == "type_value" {
            if let Some(val) = join_tokens(v) {
                elem.attributes.insert("type".into(), val);
            }
            continue;
        }
        if k == "raise_value" {
            if let Some(val) = join_tokens(v) {
                elem.attributes.insert("raise".into(), val);
            }
            continue;
        }
        if name == "transition" && k == "target" {
            if let Some(val) = join_tokens(v) {
                elem.attributes.insert("target".into(), val);
            }
            continue;
        }
        if k == "delay" || k == "event" || k == "initial" {
            if let Some(val) = join_tokens(v) {
                elem.attributes.insert(k.clone(), val);
                continue;
            }
        }
        if let Some(val) = join_tokens(v) {
            elem.attributes.insert(k.clone(), val);
            continue;
        }
        match v {
            Value::Array(arr) => {
                let child_name = match k.as_str() {
                    "if_value" => "if",
                    "else_value" => "else",
                    other => other,
                };
                for item in arr {
                    if let Value::Object(obj) = item {
                        let child = map_to_element(child_name, obj);
                        elem.children.push(XMLNode::Element(child));
                    } else if let Value::String(text) = item {
                        elem.children
                            .push(XMLNode::Element(map_to_element(child_name, &Map::new())));
                        elem.children.push(XMLNode::Text(text.clone()));
                    }
                }
            }
            Value::String(s) => {
                if k == "version" {
                    elem.attributes.insert("version".into(), s.clone());
                } else {
                    elem.children
                        .push(XMLNode::Element(map_to_element(k, &Map::new())));
                    elem.children.push(XMLNode::Text(s.clone()));
                }
            }
            Value::Number(n) => {
                if k == "version" {
                    elem.attributes.insert("version".into(), n.to_string());
                }
            }
            _ => {}
        }
    }
    elem
}

/// Collapse newlines and tabs in attribute values recursively.
///
/// # Parameters
/// - `value`: Mutable JSON value to normalise.
fn collapse_whitespace(value: &mut Value) {
    match value {
        Value::Array(arr) => {
            for v in arr {
                collapse_whitespace(v);
            }
        }
        Value::Object(map) => {
            let keys: Vec<String> = map.keys().cloned().collect();
            for k in keys {
                if let Some(v) = map.get_mut(&k) {
                    if (k.ends_with("_attribute") || COLLAPSE_ATTRS.contains(&k.as_str()))
                        && v.is_string()
                    {
                        if let Some(s) = v.as_str() {
                            let collapsed = s.replace(['\n', '\r', '\t'], " ");
                            *v = Value::String(collapsed);
                        }
                    } else {
                        collapse_whitespace(v);
                    }
                }
            }
        }
        _ => {}
    }
}

fn remove_empty(value: &mut Value) -> bool {
    match value {
        Value::Object(map) => {
            let keys: Vec<String> = map.keys().cloned().collect();
            for k in keys {
                if let Some(v) = map.get_mut(&k) {
                    if remove_empty(v) {
                        map.remove(&k);
                    }
                }
            }
            map.is_empty()
        }
        Value::Array(arr) => {
            arr.retain(|v| {
                let mut v = v.clone();
                !remove_empty(&mut v)
            });
            arr.is_empty()
        }
        Value::Null => true,
        Value::String(s) => s.is_empty(),
        _ => false,
    }
}

/// Convert an SCXML string to scjson.
///
/// # Parameters
/// - `xml`: XML input string.
/// - `omit_empty`: Remove empty fields when `true`.
///
/// # Returns
/// JSON string representing the document.
pub fn xml_to_json(xml: &str, omit_empty: bool) -> Result<String, ScjsonError> {
    let root = Element::parse(xml.as_bytes())?;
    if root.name != "scxml" {
        return Err(ScjsonError::Unsupported);
    }
    // let mut map = element_to_map(&root); // retained for potential future mutations
    let map = element_to_map(&root);
    let mut value = Value::Object(map);
    collapse_whitespace(&mut value);
    if omit_empty {
        remove_empty(&mut value);
    }
    Ok(serde_json::to_string_pretty(&value)?)
}

/// Convert a scjson string to SCXML using options.
///
/// # Parameters
/// - `json_str`: JSON input string.
/// - `omit_empty`: Remove empty fields when `true`.
///
/// # Returns
/// XML string representing the document.
pub fn json_to_xml_opts(json_str: &str, omit_empty: bool) -> Result<String, ScjsonError> {
    let mut v: Value = serde_json::from_str(json_str)?;
    if omit_empty {
        remove_empty(&mut v);
    }
    let obj = v.as_object().ok_or(ScjsonError::Unsupported)?;
    let elem = map_to_element("scxml", obj);
    let mut out = Vec::new();
    elem.write(&mut out)?;
    Ok(String::from_utf8(out).unwrap())
}

/// Convert a scjson string to SCXML.
///
/// # Parameters
/// - `json_str`: JSON input string.
///
/// # Returns
/// XML string representing the document.
pub fn json_to_xml(json_str: &str) -> Result<String, ScjsonError> {
    json_to_xml_opts(json_str, true)
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
