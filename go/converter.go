/*
Agent Name: go-converter

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.
*/

package main

import (
	"encoding/json"
	"errors"
	"os"
	"path/filepath"

	mxj "github.com/clbanning/mxj/v2"
)

// removeEmpty removes nil or empty values recursively.
//
// @param v any - value to clean.
// @returns any - cleaned value.
func removeEmpty(v interface{}) interface{} {
	switch val := v.(type) {
	case map[string]interface{}:
		cleaned := make(map[string]interface{})
		for k, sub := range val {
			r := removeEmpty(sub)
			switch rv := r.(type) {
			case nil:
				continue
			case map[string]interface{}:
				if len(rv) == 0 {
					continue
				}
			case []interface{}:
				if len(rv) == 0 {
					continue
				}
			}
			cleaned[k] = r
		}
		if len(cleaned) == 0 {
			return nil
		}
		return cleaned
	case []interface{}:
		var arr []interface{}
		for _, sub := range val {
			r := removeEmpty(sub)
			if r != nil {
				if arrMap, ok := r.(map[string]interface{}); ok && len(arrMap) == 0 {
					continue
				}
				if arrSlice, ok := r.([]interface{}); ok && len(arrSlice) == 0 {
					continue
				}
				arr = append(arr, r)
			}
		}
		if len(arr) == 0 {
			return nil
		}
		return arr
	case string:
		if val == "" {
			return nil
		}
		return val
	default:
		if val == nil {
			return nil
		}
		return val
	}
}

// xmlToJSON converts an SCXML XML string to scjson JSON string.
//
// @param xmlStr string - xml input.
// @param omitEmpty bool - if true, remove empty values.
// @returns string - json output or error.
func xmlToJSON(xmlStr string, omitEmpty bool) (string, error) {
	mv, err := mxj.NewMapXml([]byte(xmlStr))
	if err != nil {
		return "", err
	}
	m := mv.Old()
	if scxml, ok := m["scxml"].(map[string]interface{}); ok {
		m = scxml
	}
	if omitEmpty {
		m = removeEmpty(m).(map[string]interface{})
	}
	if _, ok := m["-xmlns"]; ok {
		delete(m, "-xmlns")
	}
	if _, ok := m["version"]; !ok {
		m["version"] = 1.0
	}
	if _, ok := m["datamodel_attribute"]; !ok {
		m["datamodel_attribute"] = "null"
	}
	if omitEmpty {
		m = removeEmpty(m).(map[string]interface{})
	}
	data, err := json.MarshalIndent(m, "", "  ")
	if err != nil {
		return "", err
	}
	return string(data), nil
}

// jsonToXML converts a scjson string to SCXML XML string.
//
// @param jsonStr string - json input.
// @returns string - xml output or error.
func jsonToXML(jsonStr string) (string, error) {
	var m map[string]interface{}
	if err := json.Unmarshal([]byte(jsonStr), &m); err != nil {
		return "", err
	}
	mv := mxj.Map{"scxml": m}
	bytes, err := mv.XmlIndent("", "  ")
	if err != nil {
		return "", err
	}
	return string(bytes), nil
}

// writeFile writes data to the destination path, ensuring directories exist.
//
// @param dest string - destination path.
// @param data string - data to write.
// @returns error - failure if any.
func writeFile(dest, data string) error {
	if dest == "" {
		return errors.New("destination path required")
	}
	if err := os.MkdirAll(filepath.Dir(dest), 0o755); err != nil {
		return err
	}
	return os.WriteFile(dest, []byte(data), 0o644)
}
