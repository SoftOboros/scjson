/*
Agent Name: go-cli-tests

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.
*/

package main

import (
	"encoding/json"
	"os"
	"os/exec"
	"path/filepath"
	"testing"
)

func createScxml() string {
	return `<scxml xmlns="http://www.w3.org/2005/07/scxml"/>`
}

func createScjson() string {
	obj := map[string]interface{}{
		"version":             1.0,
		"datamodel_attribute": "null",
	}
	b, _ := json.MarshalIndent(obj, "", "  ")
	return string(b)
}

func TestSingleJsonConversion(t *testing.T) {
	dir := t.TempDir()
	xmlPath := filepath.Join(dir, "sample.scxml")
	os.WriteFile(xmlPath, []byte(createScxml()), 0o644)

	cmd := exec.Command("go", "run", ".", "json", xmlPath)
	cmd.Dir = "./"
	out, err := cmd.CombinedOutput()
	if err != nil {
		t.Fatalf("command failed: %v, out=%s", err, string(out))
	}

	outPath := filepath.Join(dir, "sample.scjson")
	data, err := os.ReadFile(outPath)
	if err != nil {
		t.Fatalf("output not found: %v", err)
	}
	var m map[string]interface{}
	json.Unmarshal(data, &m)
	if m["version"] != 1.0 {
		t.Errorf("expected version 1.0")
	}
}

func TestDirectoryJsonConversion(t *testing.T) {
	dir := t.TempDir()
	srcDir := filepath.Join(dir, "src")
	os.Mkdir(srcDir, 0o755)
	for _, n := range []string{"a", "b"} {
		os.WriteFile(filepath.Join(srcDir, n+".scxml"), []byte(createScxml()), 0o644)
	}

	cmd := exec.Command("go", "run", ".", "json", srcDir)
	cmd.Dir = "./"
	out, err := cmd.CombinedOutput()
	if err != nil {
		t.Fatalf("command failed: %v, %s", err, string(out))
	}
	for _, n := range []string{"a", "b"} {
		if _, err := os.Stat(filepath.Join(srcDir, n+".scjson")); err != nil {
			t.Errorf("missing %s.scjson", n)
		}
	}
}

func TestSingleXmlConversion(t *testing.T) {
	dir := t.TempDir()
	jsonPath := filepath.Join(dir, "sample.scjson")
	os.WriteFile(jsonPath, []byte(createScjson()), 0o644)

	cmd := exec.Command("go", "run", ".", "xml", jsonPath)
	cmd.Dir = "./"
	out, err := cmd.CombinedOutput()
	if err != nil {
		t.Fatalf("command failed: %v, %s", err, string(out))
	}
	outPath := filepath.Join(dir, "sample.scxml")
	data, err := os.ReadFile(outPath)
	if err != nil {
		t.Fatalf("output not found: %v", err)
	}
	if string(data) == "" {
		t.Errorf("no data")
	}
}

func TestDirectoryXmlConversion(t *testing.T) {
	dir := t.TempDir()
	srcDir := filepath.Join(dir, "jsons")
	os.Mkdir(srcDir, 0o755)
	for _, n := range []string{"x", "y"} {
		os.WriteFile(filepath.Join(srcDir, n+".scjson"), []byte(createScjson()), 0o644)
	}

	cmd := exec.Command("go", "run", ".", "xml", srcDir)
	cmd.Dir = "./"
	out, err := cmd.CombinedOutput()
	if err != nil {
		t.Fatalf("command failed: %v, %s", err, string(out))
	}
	for _, n := range []string{"x", "y"} {
		if _, err := os.Stat(filepath.Join(srcDir, n+".scxml")); err != nil {
			t.Errorf("missing %s.scxml", n)
		}
	}
}
