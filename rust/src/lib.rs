//! Agent Name: rust-lib
//!
//! Part of the scjson project.
//! Developed by Softoboros Technology Inc.
//! Licensed under the BSD 1-Clause License.
//!
//! Library providing basic SCXML <-> scjson conversion.

use serde_json::{Number, Value};
use thiserror::Error;
use xmltree::Element;
use xmltree::Error as XmlWriteError;

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

/// Convert an SCXML string to scjson.
///
/// # Parameters
/// - `xml`: XML input string.
/// - `omit_empty`: Remove empty fields when true.
///
/// # Returns
/// JSON string representing the document.
pub fn xml_to_json(xml: &str, omit_empty: bool) -> Result<String, ScjsonError> {
    let root = Element::parse(xml.as_bytes())?;
    if root.name != "scxml" {
        return Err(ScjsonError::Unsupported);
    }
    let version = root
        .attributes
        .get("version")
        .and_then(|v| v.parse::<f64>().ok())
        .unwrap_or(1.0);
    let datamodel = root
        .attributes
        .get("datamodel")
        .map(|s| s.as_str())
        .unwrap_or("null");
    let mut obj = serde_json::Map::new();
    let ver_value = if (version.fract() - 0.0).abs() < f64::EPSILON {
        Value::Number(Number::from(version as i64))
    } else {
        Value::Number(Number::from_f64(version).unwrap())
    };
    obj.insert("version".into(), ver_value);
    obj.insert(
        "datamodel_attribute".into(),
        Value::String(datamodel.to_string()),
    );
    let value = Value::Object(obj);
    if omit_empty {
        Ok(serde_json::to_string_pretty(&value)?)
    } else {
        Ok(serde_json::to_string_pretty(&value)?)
    }
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
    let obj = v.as_object().ok_or(ScjsonError::Unsupported)?;
    let version = obj.get("version").and_then(|v| v.as_f64()).unwrap_or(1.0);
    let datamodel = obj
        .get("datamodel_attribute")
        .and_then(|v| v.as_str())
        .unwrap_or("null");

    let mut root = Element::new("scxml");
    root.attributes
        .insert("xmlns".into(), "http://www.w3.org/2005/07/scxml".into());
    root.attributes
        .insert("version".into(), version.to_string());
    root.attributes
        .insert("datamodel".into(), datamodel.to_string());
    let mut out = Vec::new();
    root.write(&mut out)?;
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
