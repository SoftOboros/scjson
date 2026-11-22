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

pub mod scjson_props;

const SCXML_NS: &str = "http://www.w3.org/2005/07/scxml";

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
    "expr", "cond", "event", "target", "delay", "location", "name", "src", "id",
];

/// SCXML attribute names that are represented as first-class SCJSON fields.
const KNOWN_SCXML_ATTRS: &[&str] = &[
    "array",
    "attr",
    "autoforward",
    "binding",
    "cond",
    "datamodel",
    "delay",
    "delayexpr",
    "event",
    "eventexpr",
    "exmode",
    "expr",
    "id",
    "idlocation",
    "index",
    "initial",
    "item",
    "label",
    "location",
    "name",
    "namelist",
    "profile",
    "sendid",
    "sendidexpr",
    "src",
    "srcexpr",
    "target",
    "targetexpr",
    "type",
    "typeexpr",
    "version",
];

/// Elements whose body text is source-like and whose comments are not promoted.
const SOURCE_BODY_TAGS: &[&str] = &["script", "data"];

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
    #[error("invalid region_order: {0}")]
    RegionOrder(&'static str),
    #[error("invalid state_order: {0}")]
    StateOrder(&'static str),
    #[error("invalid executable key on {0}: {1}")]
    ExecutableKey(String, String),
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

fn repair_comment_text(raw: &str) -> String {
    let text = raw.replace("\r\n", "\n").replace('\r', "\n");
    if !text.contains('\n') {
        return text.trim().to_string();
    }
    let mut lines: Vec<String> = text.lines().map(|line| line.to_string()).collect();
    while lines.first().map(|line| line.trim().is_empty()).unwrap_or(false) {
        lines.remove(0);
    }
    while lines.last().map(|line| line.trim().is_empty()).unwrap_or(false) {
        lines.pop();
    }
    let margin = lines
        .iter()
        .filter(|line| !line.trim().is_empty())
        .map(|line| line.chars().take_while(|ch| ch.is_whitespace()).count())
        .min()
        .unwrap_or(0);
    let continuation_margin = if margin == 0
        && lines.len() > 1
        && lines
            .last()
            .map(|line| line.ends_with(char::is_whitespace))
            .unwrap_or(false)
        && lines
            .iter()
            .skip(1)
            .filter(|line| !line.trim().is_empty())
            .all(|line| line.chars().next().map(|ch| ch.is_whitespace()).unwrap_or(false))
    {
        lines
            .iter()
            .skip(1)
            .filter(|line| !line.trim().is_empty())
            .map(|line| line.chars().take_while(|ch| ch.is_whitespace()).count())
            .filter(|count| *count > 0)
            .min()
            .unwrap_or(0)
    } else {
        0
    };
    lines
        .into_iter()
        .enumerate()
        .map(|(idx, line)| {
            if line.trim().is_empty() {
                String::new()
            } else if margin > 0 {
                line.chars().skip(margin).collect::<String>()
            } else if continuation_margin > 0 && idx > 0 {
                let leading = line.chars().take_while(|ch| ch.is_whitespace()).count();
                if leading >= continuation_margin {
                    line.chars().skip(continuation_margin).collect::<String>()
                } else {
                    line
                }
            } else {
                line
            }
        })
        .collect::<Vec<_>>()
        .join("\n")
        .trim()
        .to_string()
}

fn emit_safe_comment_text(text: &str) -> String {
    let mut safe = text.replace("--", "- -");
    if safe.ends_with('-') {
        safe.push(' ');
    }
    if safe.contains('\n') {
        safe = format!("\n{}\n", safe);
    }
    safe
}

fn append_help_text(map: &mut Map<String, Value>, comments: Vec<String>, prepend: bool) {
    let repaired: Vec<Value> = comments
        .into_iter()
        .filter(|item| !item.is_empty())
        .map(Value::String)
        .collect();
    if repaired.is_empty() {
        return;
    }
    match map.get_mut("help_text") {
        Some(Value::Array(arr)) => {
            if prepend {
                let mut next = repaired;
                next.append(arr);
                *arr = next;
            } else {
                arr.extend(repaired);
            }
        }
        Some(other) => {
            let old = other.take();
            let mut arr = Vec::new();
            if prepend {
                arr.extend(repaired);
                arr.push(old);
            } else {
                arr.push(old);
                arr.extend(repaired);
            }
            *other = Value::Array(arr);
        }
        None => {
            map.insert("help_text".to_string(), Value::Array(repaired));
        }
    }
}

fn any_element_to_value(elem: &Element) -> Value {
    let mut map = Map::new();
    let qname = match elem.namespace.as_deref() {
        Some(ns) => format!("{{{ns}}}{}", elem.name),
        None => elem.name.clone(),
    };
    map.insert("qname".into(), Value::String(qname));
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

fn parse_extension_attr_value(value: &str) -> Value {
    let trimmed = value.trim();
    if (trimmed.starts_with('{') || trimmed.starts_with('['))
        && (trimmed.ends_with('}') || trimmed.ends_with(']'))
    {
        if let Ok(parsed) = serde_json::from_str::<Value>(trimmed) {
            return parsed;
        }
    }
    Value::String(value.to_string())
}

fn append_other_attribute(map: &mut Map<String, Value>, key: &str, value: &str) {
    let attrs = map
        .entry("other_attributes".to_string())
        .or_insert_with(|| Value::Object(Map::new()));
    if let Value::Object(obj) = attrs {
        obj.insert(key.to_string(), parse_extension_attr_value(value));
    }
}

fn other_attribute_to_xml_value(value: &Value) -> Option<String> {
    match value {
        Value::Null => None,
        Value::String(s) => Some(s.clone()),
        Value::Bool(b) => Some(if *b { "true" } else { "false" }.to_string()),
        Value::Number(n) => Some(n.to_string()),
        Value::Array(_) | Value::Object(_) => serde_json::to_string(value).ok(),
    }
}

fn element_to_map(elem: &Element, suppress_help_text: bool) -> Map<String, Value> {
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
            (_, attr) if !KNOWN_SCXML_ATTRS.contains(&attr) => {
                append_other_attribute(&mut map, k, v);
            }
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
    if elem.name == "invoke" {
        map.entry("type_value".to_string())
            .or_insert_with(|| Value::String("scxml".into()));
        map.entry("autoforward".to_string())
            .or_insert_with(|| Value::String("false".into()));
    }

    let mut text_items = Vec::new();
    let structural = child_order(&elem.name);
    let mut child_kinds = Vec::new();
    let mut pending_comments: Vec<String> = Vec::new();
    let mut saw_non_ws_text_since_comment = false;
    let current_can_own_help = SCXML_ELEMS.contains(&elem.name.as_str()) && !suppress_help_text;
    let child_suppresses_help =
        suppress_help_text
            || SOURCE_BODY_TAGS.contains(&elem.name.as_str())
            || elem.name == "content";
    for child in &elem.children {
        match child {
            XMLNode::Comment(text) => {
                if current_can_own_help {
                    pending_comments.push(repair_comment_text(text));
                    saw_non_ws_text_since_comment = false;
                }
            }
            XMLNode::Element(e) => {
                if e.namespace == elem.namespace && SCXML_ELEMS.contains(&e.name.as_str()) {
                    if elem.namespace.as_deref() == Some(SCXML_NS)
                        && structural.is_some_and(|order| order.kinds.contains(&e.name.as_str()))
                    {
                        child_kinds.push(e.name.as_str());
                    }
                    let key = match e.name.as_str() {
                        "if" => "if_value",
                        "else" => "else_value",
                        "raise" => "raise_value",
                        name => name,
                    };
                    let mut child_map = element_to_map(e, child_suppresses_help);
                    let target_key = if e.name == "scxml" && elem.name != "scxml" {
                        "content"
                    } else if elem.name == "content" && e.name == "scxml" {
                        "content"
                    } else {
                        key
                    };
                    if !pending_comments.is_empty()
                        && elem.name == "content"
                        && e.name == "scxml"
                    {
                        // Comments inside inline <content> payloads are not
                        // promoted onto the nested state machine.
                    } else if !pending_comments.is_empty() && !saw_non_ws_text_since_comment {
                        append_help_text(&mut child_map, pending_comments, true);
                    } else if !pending_comments.is_empty() && current_can_own_help {
                        append_help_text(&mut map, pending_comments, false);
                    }
                    pending_comments = Vec::new();
                    saw_non_ws_text_since_comment = false;
                    if (elem.name == "initial" || elem.name == "history") && e.name == "transition" {
                        map.insert(target_key.to_string(), Value::Object(child_map));
                    } else {
                        append_child(&mut map, target_key, Value::Object(child_map));
                    }
                } else {
                    let val = any_element_to_value(e);
                    let field = if structural.is_some() { "other_element" } else { "content" };
                    append_child(&mut map, field, val);
                }
            }
            XMLNode::Text(t) => {
                if !t.trim().is_empty() {
                    if !pending_comments.is_empty() && current_can_own_help {
                        append_help_text(&mut map, pending_comments, false);
                        pending_comments = Vec::new();
                    }
                    saw_non_ws_text_since_comment = true;
                    text_items.push(Value::String(t.to_string()));
                }
            }
            _ => {}
        }
    }
    if !pending_comments.is_empty() && current_can_own_help {
        append_help_text(&mut map, pending_comments, false);
    }
    if !text_items.is_empty() {
        for item in text_items {
            append_child(&mut map, "content", item);
        }
    }

    if let Some(order) = structural {
        if child_kinds.windows(2).any(|pair| pair[0] != pair[1]) {
            map.insert(order.field.into(), Value::from(child_kinds));
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
    } else if elem.name == "donedata" {
        if let Some(Value::Array(arr)) = map.get_mut("content") {
            if arr.len() == 1 {
                if let Some(item) = arr.pop() {
                    map.insert("content".into(), item);
                }
            }
        }
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

#[derive(Clone, Copy)]
struct ChildOrder {
    field: &'static str,
    kinds: &'static [&'static str],
    error: fn(&'static str) -> ScjsonError,
}

fn child_order(owner: &str) -> Option<ChildOrder> {
    match owner {
        "scxml" | "state" => Some(ChildOrder {
            field: "state_order",
            kinds: &["state", "parallel", "final"],
            error: ScjsonError::StateOrder,
        }),
        "parallel" => Some(ChildOrder {
            field: "region_order",
            kinds: &["state", "parallel"],
            error: ScjsonError::RegionOrder,
        }),
        _ => None,
    }
}

type StateChild<'a> = (&'static str, &'a Map<String, Value>);

/// Consume each kind's payloads in array order, independent of JSON key order.
fn ordered_state_children<'a>(
    order: ChildOrder,
    map: &'a Map<String, Value>,
) -> Result<Option<Vec<StateChild<'a>>>, ScjsonError> {
    let mut groups = Vec::new();
    for &kind in order.kinds {
        match map.get(kind) {
            Some(Value::Array(items)) => groups.push((kind, items.iter())),
            None => {}
            Some(_) if !map.contains_key(order.field) => return Ok(None),
            Some(_) => return Err((order.error)("expected a child array")),
        }
    }
    let Some(markers) = map.get(order.field) else {
        if groups.iter().filter(|(_, items)| items.len() > 0).count() < 2 {
            return Ok(None);
        }
        let children = groups.into_iter().flat_map(|(kind, items)| {
            items.map(move |v| v.as_object().map(|obj| (kind, obj)))
        });
        return Ok(children.collect());
    };
    let kinds = markers.as_array().ok_or((order.error)("expected an array"))?;
    let mut children = Vec::with_capacity(kinds.len());
    for marker in kinds {
        let (kind, items) = groups
            .iter_mut()
            .find(|(kind, _)| Some(*kind) == marker.as_str())
            .ok_or((order.error)("unknown or absent child kind"))?;
        let value = items.next().ok_or((order.error)("excess child occurrence"))?;
        let payload = value.as_object().ok_or((order.error)("expected a child object"))?;
        children.push((*kind, payload));
    }
    if groups.iter().any(|(_, items)| items.len() > 0) {
        return Err((order.error)("one or more children omitted"));
    }
    Ok(Some(children))
}

fn map_to_element(name: &str, map: &Map<String, Value>) -> Result<Element, ScjsonError> {
    if name == "scxml" && map.len() == 1 {
        if let Some(Value::Array(arr)) = map.get("content") {
            if arr.len() == 1 {
                if let Some(Value::Object(obj)) = arr.get(0) {
                    return map_to_element("scxml", obj);
                }
            }
        }
    }
    let qname = map.get("qname").and_then(Value::as_str);
    let mut elem = if let Some(qname) = qname {
        let (namespace, local) = qname
            .strip_prefix('{')
            .and_then(|q| q.split_once('}'))
            .unwrap_or(("", qname));
        let mut element = Element::new(local);
        element
            .attributes
            .insert("xmlns".into(), namespace.to_owned());
        element
    } else {
        let mut element = Element::new(name);
        if name == "scxml" {
            element.attributes.insert("xmlns".into(), SCXML_NS.into());
        } else if !SCXML_ELEMS.contains(&name) && !name.contains(':') {
            element.attributes.insert("xmlns".into(), String::new());
        }
        element
    };
    let structural = child_order(name);
    if map.contains_key("region_order") && name != "parallel" {
        return Err(ScjsonError::RegionOrder("only a parallel may specify region_order"));
    }
    if map.contains_key("state_order") && !matches!(name, "scxml" | "state") {
        return Err(ScjsonError::StateOrder("only scxml and state may specify state_order"));
    }
    let mut sequence = match structural {
        Some(order) => ordered_state_children(order, map)?.map(Vec::into_iter),
        None => None,
    };
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
        if matches!(k.as_str(), "region_order" | "state_order") {
            continue;
        }
        if structural.is_some_and(|order| order.kinds.contains(&k.as_str())) {
            if let (Some(ordered), Some(slots)) = (&mut sequence, v.as_array()) {
                // Fill only child-state slots so unrelated siblings keep their positions.
                for (kind, payload) in ordered.take(slots.len()) {
                    append_element_with_help_text(&mut elem, kind, payload)?;
                }
                continue;
            }
        }
        if ["qname", "text", "attributes", "help_text"].contains(&k.as_str()) {
            continue;
        }
        if k == "other_attributes" {
            if let Value::Object(attrs) = v {
                for (attr, attr_value) in attrs {
                    if let Some(serialized) = other_attribute_to_xml_value(attr_value) {
                        elem.attributes.insert(attr.clone(), serialized);
                    }
                }
            }
            continue;
        }
        if k == "content" {
            match v {
                Value::Array(arr) => {
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
                                    append_element_with_help_text(&mut elem, child_name, obj)?;
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
                                    append_element_with_help_text(&mut elem, child_name, obj)?;
                                }
                                _ => {}
                            }
                        }
                    }
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
                    append_element_with_help_text(&mut elem, child_name, obj)?;
                }
                Value::String(s) => {
                    if name == "script" {
                        elem.children.push(XMLNode::Text(s.clone()));
                    } else {
                        let mut c = Element::new("content");
                        c.children.push(XMLNode::Text(s.clone()));
                        elem.children.push(XMLNode::Element(c));
                    }
                }
                _ => {}
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
                continue;
            }
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
                    "raise_value" => "raise",
                    other => other,
                };
                for item in arr {
                    if let Value::Object(obj) = item {
                        append_element_with_help_text(&mut elem, child_name, obj)?;
                    } else if let Value::String(text) = item {
                        elem.children
                            .push(XMLNode::Element(map_to_element(child_name, &Map::new())?));
                        elem.children.push(XMLNode::Text(text.clone()));
                    }
                }
            }
            Value::Object(obj) => {
                let child_name = match k.as_str() {
                    "if_value" => "if",
                    "else_value" => "else",
                    "raise_value" => "raise",
                    other => other,
                };
                append_element_with_help_text(&mut elem, child_name, obj)?;
            }
            Value::String(s) => {
                if k == "version" {
                    elem.attributes.insert("version".into(), s.clone());
                } else {
                    elem.children
                        .push(XMLNode::Element(map_to_element(k, &Map::new())?));
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
    Ok(elem)
}

fn help_text_comments(map: &Map<String, Value>) -> Vec<XMLNode> {
    let mut nodes = Vec::new();
    if let Some(Value::Array(entries)) = map.get("help_text") {
        for entry in entries {
            if let Some(text) = entry.as_str() {
                nodes.push(XMLNode::Comment(emit_safe_comment_text(text)));
            }
        }
    }
    nodes
}

fn append_element_with_help_text(
    parent: &mut Element,
    child_name: &str,
    obj: &Map<String, Value>,
) -> Result<(), ScjsonError> {
    for comment in help_text_comments(obj) {
        parent.children.push(comment);
    }
    parent
        .children
        .push(XMLNode::Element(map_to_element(child_name, obj)?));
    Ok(())
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
                // Keep explicit metadata (including invalid null) and every referenced
                // region occurrence intact until the owning element validates it.
                if matches!(k.as_str(), "region_order" | "state_order") {
                    continue;
                }
                if matches!(k.as_str(), "state" | "parallel" | "final")
                    && (map.contains_key("region_order") || map.contains_key("state_order")
                        || map[&k].as_array().is_some_and(|a| a.iter().any(Value::is_object)))
                {
                    continue;
                }
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
    let nodes = Element::parse_all(xml.as_bytes())?;
    let mut root: Option<Element> = None;
    let mut root_comments: Vec<String> = Vec::new();
    for node in nodes {
        match node {
            XMLNode::Element(elem) => root = Some(elem),
            XMLNode::Comment(text) => root_comments.push(repair_comment_text(&text)),
            _ => {}
        }
    }
    let root = root.ok_or(ScjsonError::Unsupported)?;
    if root.name != "scxml" {
        return Err(ScjsonError::Unsupported);
    }
    // let mut map = element_to_map(&root); // retained for potential future mutations
    let mut map = element_to_map(&root, false);
    append_help_text(&mut map, root_comments, false);
    let mut value = Value::Object(map);
    collapse_whitespace(&mut value);
    if omit_empty {
        remove_empty(&mut value);
    }
    Ok(serde_json::to_string_pretty(&value)?)
}

/// Check reserved fields on modeled executable owners before empty fields are pruned.
fn validate_executable_keys(value: &Value, tag: &str) -> Result<(), ScjsonError> {
    if let Value::Array(items) = value {
        for item in items {
            validate_executable_keys(item, tag)?;
        }
        return Ok(());
    }
    let Some(obj) = value.as_object() else { return Ok(()) };
    if matches!(tag, "onentry" | "onexit" | "finalize" | "if" | "foreach" | "transition") {
        for (raw, camel, canonical) in [
            ("raise", "raiseValue", "raise_value"),
            ("if", "ifValue", "if_value"),
            ("else", "elseValue", "else_value"),
        ] {
            let names: Vec<_> = [raw, camel, canonical].into_iter().filter(|k| obj.contains_key(*k)).collect();
            let Some(&present) = names.first() else { continue };
            let reason = if names.len() > 1 {
                format!("conflicting spellings {}", names.join(", "))
            } else if raw == "else" && tag != "if" {
                "else is only valid inside an if_value block".to_string()
            } else if present != canonical {
                format!("use {canonical} for {present}")
            } else {
                continue;
            };
            return Err(ScjsonError::ExecutableKey(tag.into(), reason));
        }
    }
    for (key, child) in obj {
        let child_tag = match key.as_str() {
            "state" | "parallel" | "final" | "initial" | "history" | "transition"
            | "onentry" | "onexit" | "invoke" | "finalize" | "foreach" | "send"
            | "donedata" => key,
            "if_value" => "if",
            "content" if matches!(tag, "send" | "invoke" | "donedata") => "content",
            "content" if tag == "content" => {
                for item in child.as_array().into_iter().flatten() {
                    if item.is_object() && item.get("qname").is_none() {
                        validate_executable_keys(item, "scxml")?;
                    }
                }
                continue;
            }
            _ => continue,
        };
        validate_executable_keys(child, child_tag)?;
    }
    Ok(())
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
    validate_executable_keys(&v, "scxml")?;
    if omit_empty {
        remove_empty(&mut v);
    }
    let obj = v.as_object().ok_or(ScjsonError::Unsupported)?;
    let elem = map_to_element("scxml", obj)?;
    let mut out = Vec::new();
    elem.write(&mut out)?;
    let mut xml = String::from_utf8(out).unwrap();
    let root_comments = help_text_comments(obj)
        .into_iter()
        .filter_map(|node| match node {
            XMLNode::Comment(text) => Some(format!("<!--{}-->", text)),
            _ => None,
        })
        .collect::<Vec<_>>();
    if !root_comments.is_empty() {
        let prefix = root_comments.join("");
        if let Some(idx) = xml.find("?>") {
            let insert_at = idx + 2;
            xml.insert_str(insert_at, &prefix);
        } else {
            xml = format!("{}{}", prefix, xml);
        }
    }
    Ok(xml)
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
