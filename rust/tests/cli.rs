//! Agent Name: rust-cli-tests
//!
//! Part of the scjson project.
//! Developed by Softoboros Technology Inc.
//! Licensed under the BSD 1-Clause License.

use predicates::prelude::*;
use std::fs;
use tempfile::TempDir;

fn create_scxml() -> String {
    "<scxml xmlns=\"http://www.w3.org/2005/07/scxml\"/>".to_string()
}

fn create_scjson() -> String {
    let obj = serde_json::json!({
        "version": 1,
        "datamodel_attribute": "null"
    });
    serde_json::to_string_pretty(&obj).unwrap()
}

#[test]
fn keep_empty_json_conversion() {
    let dir = TempDir::new().unwrap();
    let xml_path = dir.path().join("sample.scxml");
    fs::write(&xml_path, create_scxml()).unwrap();

    let mut cmd = assert_cmd::Command::cargo_bin("scjson_rust").unwrap();
    cmd.args(["json", xml_path.to_str().unwrap(), "--keep-empty"]);
    cmd.assert().success();

    let out_path = xml_path.with_extension("scjson");
    let data: serde_json::Value =
        serde_json::from_str(&fs::read_to_string(out_path).unwrap()).unwrap();
    assert!(data.get("datamodel_attribute").is_some());
}

#[test]
fn shows_help() {
    let mut cmd = assert_cmd::Command::cargo_bin("scjson_rust").unwrap();
    cmd.arg("--help");
    cmd.assert()
        .success()
        .stdout(predicate::str::contains("scjson"));
}

#[test]
fn single_json_conversion() {
    let dir = TempDir::new().unwrap();
    let xml_path = dir.path().join("sample.scxml");
    fs::write(&xml_path, create_scxml()).unwrap();

    let mut cmd = assert_cmd::Command::cargo_bin("scjson_rust").unwrap();
    cmd.args(["json", xml_path.to_str().unwrap()]);
    cmd.assert().success();

    let out_path = xml_path.with_extension("scjson");
    assert!(out_path.exists());
    let data: serde_json::Value =
        serde_json::from_str(&fs::read_to_string(out_path).unwrap()).unwrap();
    assert_eq!(data["version"], 1);
}

#[test]
fn directory_json_conversion() {
    let dir = TempDir::new().unwrap();
    let src_dir = dir.path().join("src");
    fs::create_dir(&src_dir).unwrap();
    for n in ["a", "b"] {
        fs::write(src_dir.join(format!("{}.scxml", n)), create_scxml()).unwrap();
    }

    let mut cmd = assert_cmd::Command::cargo_bin("scjson_rust").unwrap();
    cmd.args(["json", src_dir.to_str().unwrap()]);
    cmd.assert().success();

    for n in ["a", "b"] {
        assert!(src_dir.join(format!("{}.scjson", n)).exists());
    }
}

#[test]
fn single_xml_conversion() {
    let dir = TempDir::new().unwrap();
    let json_path = dir.path().join("sample.scjson");
    fs::write(&json_path, create_scjson()).unwrap();

    let mut cmd = assert_cmd::Command::cargo_bin("scjson_rust").unwrap();
    cmd.args(["xml", json_path.to_str().unwrap()]);
    cmd.assert().success();

    let out_path = json_path.with_extension("scxml");
    assert!(out_path.exists());
    let data = fs::read_to_string(out_path).unwrap();
    assert!(data.contains("scxml"));
}

#[test]
fn keep_empty_xml_conversion() {
    let dir = TempDir::new().unwrap();
    let json_path = dir.path().join("sample.scjson");
    fs::write(&json_path, create_scjson()).unwrap();

    let mut cmd = assert_cmd::Command::cargo_bin("scjson_rust").unwrap();
    cmd.args(["xml", json_path.to_str().unwrap(), "--keep-empty"]);
    cmd.assert().success();

    let out_path = json_path.with_extension("scxml");
    let data = fs::read_to_string(out_path).unwrap();
    assert!(data.contains("datamodel=\"null\""));
}

#[test]
fn directory_xml_conversion() {
    let dir = TempDir::new().unwrap();
    let src_dir = dir.path().join("jsons");
    fs::create_dir(&src_dir).unwrap();
    for n in ["x", "y"] {
        fs::write(src_dir.join(format!("{}.scjson", n)), create_scjson()).unwrap();
    }

    let mut cmd = assert_cmd::Command::cargo_bin("scjson_rust").unwrap();
    cmd.args(["xml", src_dir.to_str().unwrap()]);
    cmd.assert().success();

    for n in ["x", "y"] {
        assert!(src_dir.join(format!("{}.scxml", n)).exists());
    }
}

fn build_dataset(base: &std::path::Path) {
    let d1 = base.join("level1");
    let d2 = d1.join("level2");
    fs::create_dir_all(&d2).unwrap();
    for n in ["a", "b"] {
        fs::write(d1.join(format!("{}.scxml", n)), create_scxml()).unwrap();
        fs::write(d2.join(format!("{}.scxml", n)), create_scxml()).unwrap();
    }
}

#[test]
fn recursive_conversion() {
    let dataset = TempDir::new().unwrap();
    build_dataset(dataset.path());
    let scjson_dir = dataset.path().join("outjson");
    let scxml_dir = dataset.path().join("outxml");

    let mut cmd = assert_cmd::Command::cargo_bin("scjson_rust").unwrap();
    cmd.args([
        "json",
        dataset.path().to_str().unwrap(),
        "-o",
        scjson_dir.to_str().unwrap(),
        "-r",
    ]);
    cmd.assert().success();
    let mut cmd = assert_cmd::Command::cargo_bin("scjson_rust").unwrap();
    cmd.args([
        "xml",
        scjson_dir.to_str().unwrap(),
        "-o",
        scxml_dir.to_str().unwrap(),
        "-r",
    ]);
    cmd.assert().success();

    let json_files: Vec<_> = glob::glob(&format!("{}/**/*.scjson", scjson_dir.display()))
        .unwrap()
        .filter_map(Result::ok)
        .collect();
    let xml_files: Vec<_> = glob::glob(&format!("{}/**/*.scxml", scxml_dir.display()))
        .unwrap()
        .filter_map(Result::ok)
        .collect();
    assert!(!json_files.is_empty());
    assert!(!xml_files.is_empty());
    assert!(xml_files.len() <= json_files.len());
}

#[test]
fn recursive_validation() {
    let dataset = TempDir::new().unwrap();
    build_dataset(dataset.path());
    let scjson_dir = dataset.path().join("outjson");
    let scxml_dir = dataset.path().join("outxml");

    let mut cmd = assert_cmd::Command::cargo_bin("scjson_rust").unwrap();
    cmd.args([
        "json",
        dataset.path().to_str().unwrap(),
        "-o",
        scjson_dir.to_str().unwrap(),
        "-r",
    ])
    .assert()
    .success();
    let mut cmd = assert_cmd::Command::cargo_bin("scjson_rust").unwrap();
    cmd.args([
        "xml",
        scjson_dir.to_str().unwrap(),
        "-o",
        scxml_dir.to_str().unwrap(),
        "-r",
    ])
    .assert()
    .success();

    fs::write(scjson_dir.join("corrupt.scjson"), "bad").unwrap();

    let mut cmd = assert_cmd::Command::cargo_bin("scjson_rust").unwrap();
    cmd.args(["validate", dataset.path().to_str().unwrap(), "-r"]);
    cmd.assert()
        .failure()
        .stderr(predicate::str::contains("Validation failed"));
}

#[test]
fn recursive_verify() {
    let dataset = TempDir::new().unwrap();
    build_dataset(dataset.path());
    let scjson_dir = dataset.path().join("outjson");
    let scxml_dir = dataset.path().join("outxml");

    let mut cmd = assert_cmd::Command::cargo_bin("scjson_rust").unwrap();
    cmd.args([
        "json",
        dataset.path().to_str().unwrap(),
        "-o",
        scjson_dir.to_str().unwrap(),
        "-r",
    ])
    .assert()
    .success();
    let mut cmd = assert_cmd::Command::cargo_bin("scjson_rust").unwrap();
    cmd.args([
        "xml",
        scjson_dir.to_str().unwrap(),
        "-o",
        scxml_dir.to_str().unwrap(),
        "-r",
    ])
    .assert()
    .success();

    let mut cmd = assert_cmd::Command::cargo_bin("scjson_rust").unwrap();
    cmd.args(["json", scxml_dir.to_str().unwrap(), "-r", "-v"])
        .assert()
        .success();
    let mut cmd = assert_cmd::Command::cargo_bin("scjson_rust").unwrap();
    cmd.args(["xml", scjson_dir.to_str().unwrap(), "-r", "-v"])
        .assert()
        .success();
}
