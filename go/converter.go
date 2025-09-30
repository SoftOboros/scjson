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
	"math"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"

	"github.com/beevik/etree"
)

// arrayKeys lists map keys that must always remain arrays in canonical scjson output.
var arrayKeys = map[string]bool{
	"assign":        true,
	"cancel":        true,
	"content":       true,
	"data":          true,
	"datamodel":     true,
	"donedata":      true,
	"final":         true,
	"finalize":      true,
	"foreach":       true,
	"history":       true,
	"if_value":      true,
	"initial":       true,
	"invoke":        true,
	"log":           true,
	"onentry":       true,
	"onexit":        true,
	"other_element": true,
	"parallel":      true,
	"param":         true,
	"raise_value":   true,
	"script":        true,
	"send":          true,
	"state":         true,
}

var collapseAttrKeys = map[string]bool{
	"expr":     true,
	"cond":     true,
	"event":    true,
	"target":   true,
	"delay":    true,
	"location": true,
	"name":     true,
	"src":      true,
	"id":       true,
}

var renameChildKeys = map[string]string{
	"if":    "if_value",
	"else":  "else_value",
	"raise": "raise_value",
}

var reverseRenameChildKeys = map[string]string{
	"if_value":    "if",
	"else_value":  "else",
	"raise_value": "raise",
}

var scxmlElements = map[string]bool{
	"scxml":      true,
	"state":      true,
	"parallel":   true,
	"final":      true,
	"history":    true,
	"transition": true,
	"invoke":     true,
	"finalize":   true,
	"datamodel":  true,
	"data":       true,
	"onentry":    true,
	"onexit":     true,
	"log":        true,
	"send":       true,
	"cancel":     true,
	"raise":      true,
	"assign":     true,
	"script":     true,
	"foreach":    true,
	"param":      true,
	"if":         true,
	"elseif":     true,
	"else":       true,
	"content":    true,
	"donedata":   true,
	"initial":    true,
}

var keepEmptyKeys = map[string]bool{
	"else":       true,
	"else_value": true,
	"final":      true,
	"onentry":    true,
	"donedata":   true,
	"log":        true,
	"param":      true,
}

var keepEmptyStrings = map[string]bool{
	"cond": true,
	"expr": true,
	"text": true,
}

var whitespaceReplacer = strings.NewReplacer("\n", " ", "\r", " ", "\t", " ")

// appendChild ensures that nested structural children are stored as arrays.
//
// @param target map[string]interface{} - parent structure.
// @param key string - target key for the child.
// @param value interface{} - child value.
func appendChild(target map[string]interface{}, key string, value interface{}) {
	if value == nil {
		return
	}
	if existing, ok := target[key]; ok {
		if arr, ok := existing.([]interface{}); ok {
			target[key] = append(arr, value)
			return
		}
		target[key] = []interface{}{existing, value}
		return
	}
	target[key] = []interface{}{value}
}

// tokenise splits whitespace separated identifiers into a generic slice.
//
// @param raw string - input string with potential whitespace separation.
// @returns []interface{} - slice of string tokens.
func tokenise(raw string) []interface{} {
	fields := strings.Fields(raw)
	out := make([]interface{}, 0, len(fields))
	for _, f := range fields {
		out = append(out, f)
	}
	if len(out) == 0 {
		return []interface{}{}
	}
	return out
}

// anyElementToValue converts an unknown XML element into the generic "any element" representation.
//
// @param elem *etree.Element - element to serialise.
// @returns map[string]interface{} - scjson any-element payload.
func anyElementToValue(elem *etree.Element) map[string]interface{} {
	node := map[string]interface{}{
		"qname": elem.Tag,
	}
	// accumulate text nodes preserving whitespace
	if text := strings.TrimSpace(elem.Text()); text != "" {
		node["text"] = text
	} else {
		node["text"] = ""
	}
	if len(elem.Attr) > 0 {
		attrs := make(map[string]interface{}, len(elem.Attr))
		for _, attr := range elem.Attr {
			name := attr.Key
			if attr.Space != "" {
				name = attr.Space + ":" + attr.Key
			}
			attrs[name] = attr.Value
		}
		node["attributes"] = attrs
	}
	var children []interface{}
	for _, child := range elem.ChildElements() {
		children = append(children, anyElementToValue(child))
	}
	if len(children) > 0 {
		node["children"] = children
	}
	return node
}

// isScxmlLike determines whether a map resembles an SCXML structure.
//
// @param obj map[string]interface{} - candidate map.
// @returns bool - true when the object should be treated as nested SCXML.
func isScxmlLike(obj map[string]interface{}) bool {
	if obj == nil {
		return false
	}
	if _, ok := obj["state"]; ok {
		return true
	}
	if _, ok := obj["parallel"]; ok {
		return true
	}
	if _, ok := obj["final"]; ok {
		return true
	}
	if _, ok := obj["version"]; ok {
		return true
	}
	if _, ok := obj["datamodel_attribute"]; ok {
		return true
	}
	return false
}

// ensureScxmlDefaults injects canonical defaults required by the schema.
//
// @param tag string - element tag name.
// @param node map[string]interface{} - element map to mutate.
func ensureScxmlDefaults(tag string, node map[string]interface{}, includeOptional bool) {
	if tag != "scxml" {
		return
	}
	if _, ok := node["version"]; !ok {
		node["version"] = 1.0
	}
	if _, ok := node["datamodel_attribute"]; !ok {
		node["datamodel_attribute"] = "null"
	}
	if includeOptional {
		if _, ok := node["name"]; !ok {
			node["name"] = nil
		}
		if _, ok := node["binding"]; !ok {
			node["binding"] = nil
		}
		if _, ok := node["exmode"]; !ok {
			node["exmode"] = nil
		}
	}
}

// elementToMap converts an etree Element into the canonical scjson representation.
//
// @param elem *etree.Element - input XML element.
// @returns map[string]interface{} - scjson object.
func elementToMap(elem *etree.Element, includeOptional bool) map[string]interface{} {
	node := make(map[string]interface{})

	for _, attr := range elem.Attr {
		name := attr.Key
		if attr.Space != "" {
			name = attr.Space + ":" + attr.Key
		}
		switch {
		case name == "xmlns":
			continue
		case elem.Tag == "transition" && name == "target":
			node["target"] = tokenise(attr.Value)
		case name == "initial":
			if elem.Tag == "scxml" {
				node["initial"] = tokenise(attr.Value)
			} else {
				node["initial_attribute"] = tokenise(attr.Value)
			}
		case name == "version":
			if parsed, err := strconv.ParseFloat(attr.Value, 64); err == nil {
				node["version"] = parsed
			} else {
				node["version"] = attr.Value
			}
		case name == "datamodel":
			node["datamodel_attribute"] = attr.Value
		case name == "type":
			node["type_value"] = attr.Value
		case name == "raise":
			node["raise_value"] = attr.Value
		default:
			if strings.HasPrefix(name, "xmlns") {
				continue
			}
			node[name] = attr.Value
		}
	}

	switch elem.Tag {
	case "assign":
		if _, ok := node["type_value"]; !ok {
			node["type_value"] = "replacechildren"
		}
	case "send":
		if _, ok := node["type_value"]; !ok {
			node["type_value"] = "scxml"
		}
		if _, ok := node["delay"]; !ok {
			node["delay"] = "0s"
		}
	case "invoke":
		if _, ok := node["type_value"]; !ok {
			node["type_value"] = "scxml"
		}
		if _, ok := node["autoforward"]; !ok {
			node["autoforward"] = "false"
		}
	}

	for _, childToken := range elem.Child {
		switch child := childToken.(type) {
		case *etree.Element:
			if !scxmlElements[child.Tag] {
				appendChild(node, "content", anyElementToValue(child))
				continue
			}
			key := child.Tag
			if renamed, ok := renameChildKeys[key]; ok {
				key = renamed
			}
			childMap := elementToMap(child, includeOptional)
			ensureScxmlDefaults(child.Tag, childMap, includeOptional)

			targetKey := key
			if child.Tag == "scxml" && elem.Tag != "scxml" {
				targetKey = "content"
			}
			if elem.Tag == "content" && child.Tag == "scxml" {
				targetKey = "content"
			}
			if targetKey == "else_value" || targetKey == "elseif" {
				node[targetKey] = childMap
				continue
			}
			if (elem.Tag == "initial" || elem.Tag == "history") && child.Tag == "transition" {
				node[targetKey] = childMap
			} else {
				appendChild(node, targetKey, childMap)
			}
		case *etree.CharData:
			text := child.Data
			if strings.TrimSpace(text) == "" {
				continue
			}
			appendChild(node, "content", text)
		}
	}

	if elem.Tag == "donedata" {
		if content, ok := node["content"].([]interface{}); ok && len(content) == 1 {
			node["content"] = content[0]
		}
	}

	ensureScxmlDefaults(elem.Tag, node, includeOptional)

	return node
}

// collapseWhitespace normalises significant attribute whitespace recursively.
//
// @param value interface{} - value to process.
// @returns interface{} - normalised value.
func collapseWhitespace(value interface{}) interface{} {
	switch val := value.(type) {
	case []interface{}:
		for i := range val {
			val[i] = collapseWhitespace(val[i])
		}
		return val
	case map[string]interface{}:
		for k, v := range val {
			if strings.HasSuffix(k, "_attribute") || collapseAttrKeys[k] {
				if s, ok := v.(string); ok {
					if strings.HasPrefix(s, "\n") {
						val[k] = "\n" + whitespaceReplacer.Replace(s[1:])
					} else {
						val[k] = whitespaceReplacer.Replace(s)
					}
					continue
				}
			}
			val[k] = collapseWhitespace(v)
		}
		return val
	default:
		return value
	}
}

// removeEmptyWithKey strips empty values while preserving schema-required placeholders.
//
// @param key string - current map key context.
// @param value interface{} - value to inspect.
// @returns interface{} - cleaned value or nil if removed.
func removeEmptyWithKey(key string, value interface{}) interface{} {
	switch val := value.(type) {
	case map[string]interface{}:
		cleaned := make(map[string]interface{})
		for k, v := range val {
			cleanedVal := removeEmptyWithKey(k, v)
			if cleanedVal == nil {
				if keepEmptyKeys[k] {
					if arrayKeys[k] {
						cleaned[k] = []interface{}{}
					} else {
						cleaned[k] = map[string]interface{}{}
					}
				}
				continue
			}
			switch typed := cleanedVal.(type) {
			case map[string]interface{}:
				if len(typed) == 0 && !keepEmptyKeys[k] {
					continue
				}
			case []interface{}:
				if len(typed) == 0 && !keepEmptyKeys[k] {
					continue
				}
			}
			cleaned[k] = cleanedVal
		}
		if len(cleaned) == 0 {
			if keepEmptyKeys[key] {
				return map[string]interface{}{}
			}
			return nil
		}
		return cleaned
	case []interface{}:
		arr := make([]interface{}, 0, len(val))
		for _, item := range val {
			cleanedItem := removeEmptyWithKey(key, item)
			if cleanedItem == nil {
				continue
			}
			switch typed := cleanedItem.(type) {
			case map[string]interface{}:
				if len(typed) == 0 && !keepEmptyKeys[key] {
					continue
				}
			case []interface{}:
				if len(typed) == 0 && !keepEmptyKeys[key] {
					continue
				}
			}
			arr = append(arr, cleanedItem)
		}
		if len(arr) == 0 {
			if keepEmptyKeys[key] {
				return []interface{}{}
			}
			return nil
		}
		return arr
	case string:
		if val == "" && !keepEmptyStrings[key] {
			return nil
		}
		return val
	case nil:
		return nil
	default:
		return value
	}
}

// removeEmpty removes empty values from arbitrary structures.
//
// @param value interface{} - value to clean.
// @returns interface{} - cleaned value or nil.
func removeEmpty(value interface{}) interface{} {
	return removeEmptyWithKey("", value)
}

// joinTokens flattens array or primitive values into string tokens suitable for XML attributes.
//
// @param value interface{} - candidate value.
// @returns (string, bool) - joined string and success flag.
func joinTokens(value interface{}) (string, bool) {
	switch val := value.(type) {
	case []interface{}:
		parts := make([]string, 0, len(val))
		for _, item := range val {
			switch t := item.(type) {
			case string:
				if t == "" {
					continue
				}
				parts = append(parts, t)
			case float64:
				parts = append(parts, strconv.FormatFloat(t, 'f', -1, 64))
			case bool:
				parts = append(parts, strconv.FormatBool(t))
			default:
				return "", false
			}
		}
		return strings.Join(parts, " "), true
	case string:
		return val, true
	case float64:
		return strconv.FormatFloat(val, 'f', -1, 64), true
	case bool:
		return strconv.FormatBool(val), true
	default:
		return "", false
	}
}

// initialAsAttribute determines whether an "initial" field should be rendered as an attribute.
//
// @param value interface{} - value assigned to "initial".
// @returns bool - true when the value represents attribute content.
func initialAsAttribute(value interface{}) bool {
	switch val := value.(type) {
	case []interface{}:
		for _, item := range val {
			switch item.(type) {
			case string, float64, bool:
				continue
			default:
				return false
			}
		}
		return true
	case string, float64, bool:
		return true
	default:
		return false
	}
}

// formatVersion ensures the version attribute retains a single decimal place for integers.
//
// @param value float64 - target version number.
// @returns string - formatted version string.
func formatVersion(value float64) string {
	if math.Mod(value, 1) == 0 {
		return strconv.FormatFloat(value, 'f', 1, 64)
	}
	return strconv.FormatFloat(value, 'f', -1, 64)
}

// mapToElement converts a scjson map into an etree Element.
//
// @param name string - desired element name.
// @param obj map[string]interface{} - scjson node.
// @returns *etree.Element - constructed XML element.
func mapToElement(name string, obj map[string]interface{}) *etree.Element {
	if name == "scxml" && len(obj) == 1 {
		if content, ok := obj["content"].([]interface{}); ok && len(content) == 1 {
			if childObj, ok := content[0].(map[string]interface{}); ok {
				return mapToElement("scxml", childObj)
			}
		}
	}

	elemName := name
	if qname, ok := obj["qname"].(string); ok && qname != "" {
		elemName = qname
	}

	elem := etree.NewElement(elemName)
	if elemName == "scxml" {
		elem.CreateAttr("xmlns", "http://www.w3.org/2005/07/scxml")
	} else if !strings.Contains(elemName, ":") && !strings.Contains(elemName, "{") && !scxmlElements[elemName] {
		elem.CreateAttr("xmlns", "")
	}

	if text, ok := obj["text"].(string); ok && text != "" {
		elem.SetText(text)
	}
	if attrs, ok := obj["attributes"].(map[string]interface{}); ok {
		keys := make([]string, 0, len(attrs))
		for k := range attrs {
			keys = append(keys, k)
		}
		sort.Strings(keys)
		for _, k := range keys {
			if v, ok := attrs[k].(string); ok {
				elem.CreateAttr(k, v)
			}
		}
	}

	keys := make([]string, 0, len(obj))
	for k := range obj {
		if k == "qname" || k == "text" || k == "attributes" {
			continue
		}
		keys = append(keys, k)
	}
	sort.Strings(keys)

	for _, k := range keys {
		v := obj[k]
		if v == nil {
			continue
		}
		switch {
		case k == "content":
			switch val := v.(type) {
			case []interface{}:
				for _, item := range val {
					appendContentChild(elem, name, item)
				}
			case map[string]interface{}:
				appendContentChild(elem, name, val)
			case string:
				appendContentChild(elem, name, val)
			}
		case strings.HasSuffix(k, "_attribute"):
			attrName := strings.TrimSuffix(k, "_attribute")
			if token, ok := joinTokens(v); ok && token != "" {
				elem.CreateAttr(attrName, token)
			}
		case k == "datamodel_attribute":
			if token, ok := joinTokens(v); ok && token != "" {
				elem.CreateAttr("datamodel", token)
			}
		case k == "type_value":
			if token, ok := joinTokens(v); ok && token != "" {
				elem.CreateAttr("type", token)
			}
		case name == "transition" && k == "target":
			if token, ok := joinTokens(v); ok && token != "" {
				elem.CreateAttr("target", token)
			}
		case k == "delay" || k == "event":
			if token, ok := joinTokens(v); ok && token != "" {
				elem.CreateAttr(k, token)
			}
			continue
		default:
			if k == "initial" && initialAsAttribute(v) {
				if token, ok := joinTokens(v); ok && token != "" {
					elem.CreateAttr(k, token)
				}
				continue
			}
			if token, ok := joinTokens(v); ok && (token != "" || keepEmptyStrings[k]) && k != "version" {
				elem.CreateAttr(k, token)
				continue
			}
			switch val := v.(type) {
			case []interface{}:
				childName := k
				if renamed, ok := reverseRenameChildKeys[k]; ok {
					childName = renamed
				}
				for _, item := range val {
					if item == nil {
						continue
					}
					if childMap, ok := item.(map[string]interface{}); ok {
						elem.AddChild(mapToElement(childName, childMap))
					} else if text, ok := item.(string); ok {
						child := etree.NewElement(childName)
						child.SetText(text)
						elem.AddChild(child)
					}
				}
			case map[string]interface{}:
				childName := k
				if renamed, ok := reverseRenameChildKeys[k]; ok {
					childName = renamed
				}
				elem.AddChild(mapToElement(childName, val))
			case string:
				if k == "version" {
					elem.CreateAttr("version", val)
				} else {
					child := etree.NewElement(k)
					child.SetText(val)
					elem.AddChild(child)
				}
			case float64:
				if k == "version" {
					elem.CreateAttr("version", formatVersion(val))
				}
			case bool:
				elem.CreateAttr(k, strconv.FormatBool(val))
			}
		}
	}

	return elem
}

// appendContentChild normalises content blocks when reconstructing XML.
//
// @param parent *etree.Element - parent XML element.
// @param parentName string - name of the parent.
// @param item interface{} - content payload.
func appendContentChild(parent *etree.Element, parentName string, item interface{}) {
	switch val := item.(type) {
	case string:
		switch parentName {
		case "invoke":
			child := etree.NewElement("content")
			child.SetText(val)
			parent.AddChild(child)
		case "script":
			parent.AddChild(etree.NewText(val))
		case "content":
			parent.AddChild(etree.NewText(val))
		default:
			parent.AddChild(etree.NewText(val))
		}
	case map[string]interface{}:
		childName := "content"
		if isScxmlLike(val) {
			childName = "scxml"
		}
		parent.AddChild(mapToElement(childName, val))
	}
}

// stripRootTransitions removes top-level transition arrays to match canonical behaviour.
//
// @param node map[string]interface{} - root scjson map.
func stripRootTransitions(node map[string]interface{}) {
	delete(node, "transition")
}

// xmlToJSON converts an SCXML XML string to a canonical scjson JSON string.
//
// @param xmlStr string - XML input.
// @param omitEmpty bool - whether to remove empty structures.
// @returns string - formatted JSON output or error.
func xmlToJSON(xmlStr string, omitEmpty bool) (string, error) {
	doc := etree.NewDocument()
	if err := doc.ReadFromString(xmlStr); err != nil {
		return "", err
	}
	root := doc.Root()
	if root == nil {
		return "", errors.New("missing root element")
	}
	if root.Tag != "scxml" {
		return "", errors.New("unsupported root element")
	}

	includeOptional := !omitEmpty
	data := elementToMap(root, includeOptional)
	stripRootTransitions(data)
	collapseWhitespace(data)
	result := interface{}(data)
	if omitEmpty {
		if cleaned := removeEmpty(result); cleaned != nil {
			result = cleaned
		} else {
			result = map[string]interface{}{}
		}
	}
	ensureScxmlDefaults("scxml", result.(map[string]interface{}), includeOptional)

	jsonBytes, err := json.MarshalIndent(result, "", "  ")
	if err != nil {
		return "", err
	}
	jsonStrOut := string(jsonBytes)
	jsonStrOut = strings.ReplaceAll(jsonStrOut, "\"version\": 1,\n", "\"version\": 1.0,\n")
	jsonStrOut = strings.ReplaceAll(jsonStrOut, "\"version\": 1\n", "\"version\": 1.0\n")
	return jsonStrOut, nil
}

// jsonToXML converts a scjson string to SCXML XML string.
//
// @param jsonStr string - JSON input.
// @returns string - XML output or error.
func jsonToXML(jsonStr string) (string, error) {
	var data map[string]interface{}
	if err := json.Unmarshal([]byte(jsonStr), &data); err != nil {
		return "", err
	}
	if data == nil {
		return "", errors.New("invalid JSON payload")
	}
	collapseWhitespace(data)
	if cleaned := removeEmpty(data); cleaned != nil {
		if root, ok := cleaned.(map[string]interface{}); ok {
			data = root
		}
	}
	elem := mapToElement("scxml", data)
	doc := etree.NewDocument()
	doc.SetRoot(elem)
	doc.Indent(2)
	xmlOut, err := doc.WriteToString()
	if err != nil {
		return "", err
	}
	return xmlOut, nil
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
