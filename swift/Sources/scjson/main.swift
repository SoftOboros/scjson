/*
Agent Name: swift-cli

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.
*/

import Foundation
import FoundationXML
import ArgumentParser
import SCJSONKit

/**
 Conversion utilities and CLI for SCXML <-> scjson.
 */
struct SCJSON: ParsableCommand {
    static var configuration = CommandConfiguration(
        abstract: "SCXML <-> scjson converter and validator",
        subcommands: [Json.self, Xml.self, Validate.self]
    )

    /**
     Convert an SCXML file or directory to scjson.
     - Parameters:
       - path: Input path to file or directory.
       - output: Optional output destination.
       - recursive: Recurse into subdirectories.
       - verify: Verify conversion without writing.
       - keepEmpty: Keep null or empty items when producing JSON.
     */
    struct Json: ParsableCommand {
        static var configuration = CommandConfiguration(abstract: "Convert SCXML to scjson")

        @Argument var path: String
        @Option(name: .shortAndLong) var output: String?
        @Flag(name: .shortAndLong) var recursive = false
        @Flag(name: .shortAndLong) var verify = false
        @Flag var keepEmpty = false

        func run() throws {
            let src = URL(fileURLWithPath: path)
            let outURL = output.map { URL(fileURLWithPath: $0) } ?? src
            if FileManager.default.directoryExists(atPath: src.path) {
                let pattern = recursive ? "**/*.scxml" : "*.scxml"
                for file in FileManager.default.enumerateFiles(base: src, pattern: pattern) {
                    let rel = file.path.replacingOccurrences(of: src.path, with: "")
                    let dest = outURL.appendingPathComponent(rel).deletingPathExtension().appendingPathExtension("scjson")
                    try convertScxmlFile(src: file, dest: verify ? nil : dest, keepEmpty: keepEmpty, verify: verify)
                }
            } else {
                let dest: URL
                if let output = output {
                    let base = URL(fileURLWithPath: output)
                    dest = (base.hasDirectoryPath ? base.appendingPathComponent(src.lastPathComponent) : base).deletingPathExtension().appendingPathExtension("scjson")
                } else {
                    dest = src.deletingPathExtension().appendingPathExtension("scjson")
                }
                try convertScxmlFile(src: src, dest: verify ? nil : dest, keepEmpty: keepEmpty, verify: verify)
            }
        }
    }

    /**
     Convert a scjson file or directory to SCXML.
     - Parameters:
       - path: Input path to file or directory.
       - output: Optional output destination.
       - recursive: Recurse into subdirectories.
       - verify: Verify conversion without writing.
       - keepEmpty: Keep null or empty items when producing JSON.
     */
    struct Xml: ParsableCommand {
        static var configuration = CommandConfiguration(abstract: "Convert scjson to SCXML")

        @Argument var path: String
        @Option(name: .shortAndLong) var output: String?
        @Flag(name: .shortAndLong) var recursive = false
        @Flag(name: .shortAndLong) var verify = false
        @Flag var keepEmpty = false

        func run() throws {
            let src = URL(fileURLWithPath: path)
            let outURL = output.map { URL(fileURLWithPath: $0) } ?? src
            if FileManager.default.directoryExists(atPath: src.path) {
                let pattern = recursive ? "**/*.scjson" : "*.scjson"
                for file in FileManager.default.enumerateFiles(base: src, pattern: pattern) {
                    let rel = file.path.replacingOccurrences(of: src.path, with: "")
                    let dest = outURL.appendingPathComponent(rel).deletingPathExtension().appendingPathExtension("scxml")
                    try convertScjsonFile(src: file, dest: verify ? nil : dest, verify: verify)
                }
            } else {
                let dest: URL
                if let output = output {
                    let base = URL(fileURLWithPath: output)
                    dest = (base.hasDirectoryPath ? base.appendingPathComponent(src.lastPathComponent) : base).deletingPathExtension().appendingPathExtension("scxml")
                } else {
                    dest = src.deletingPathExtension().appendingPathExtension("scxml")
                }
                try convertScjsonFile(src: src, dest: verify ? nil : dest, verify: verify)
            }
        }
    }

    /**
     Validate scjson or SCXML files by round-tripping them in memory.
     - Parameters:
       - path: Input file or directory.
       - recursive: Recurse into subdirectories.
     */
    struct Validate: ParsableCommand {
        static var configuration = CommandConfiguration(abstract: "Validate files by round-tripping")

        @Argument var path: String
        @Flag(name: .shortAndLong) var recursive = false

        func run() throws {
            let src = URL(fileURLWithPath: path)
            var success = true
            if FileManager.default.directoryExists(atPath: src.path) {
                let pattern = recursive ? "**/*" : "*"
                for file in FileManager.default.enumerateFiles(base: src, pattern: pattern) {
                    if file.pathExtension == "scxml" || file.pathExtension == "scjson" {
                        if !validateFile(file) { success = false }
                    }
                }
            } else {
                if src.pathExtension == "scxml" || src.pathExtension == "scjson" {
                    success = validateFile(src)
                } else {
                    throw ValidationError("Unsupported file type")
                }
            }
            if !success { throw ExitCode.failure }
        }

        private func validateFile(_ url: URL) -> Bool {
            do {
                let data = try String(contentsOf: url)
                if url.pathExtension == "scxml" {
                    let json = try xmlToJson(data, omitEmpty: true)
                    _ = try jsonToXml(json)
                } else {
                    let xml = try jsonToXml(data)
                    _ = try xmlToJson(xml, omitEmpty: true)
                }
                return true
            } catch {
                FileHandle.standardError.write(Data("Validation failed for \(url.path): \(error.localizedDescription)\n".utf8))
                return false
            }
        }
    }
}

extension SCJSON {
    /** Convert SCXML string to scjson. */
    static func xmlToJson(_ xml: String, omitEmpty: Bool = true) throws -> String {
        guard let data = xml.data(using: .utf8) else {
            throw NSError(domain: "scjson", code: 1, userInfo: [NSLocalizedDescriptionKey: "Invalid UTF-8"])
        }
        let builder = XMLTreeBuilder()
        let parser = XMLParser(data: data)
        parser.delegate = builder
        if !parser.parse() {
            throw parser.parserError ?? NSError(domain: "scjson", code: 2, userInfo: [NSLocalizedDescriptionKey: "Parse failed"])
        }
        guard let root = builder.root else {
            throw NSError(domain: "scjson", code: 3, userInfo: [NSLocalizedDescriptionKey: "Empty document"])
        }
        let jsonObj = try convertElement(root)
        let jsonData = try JSONSerialization.data(withJSONObject: jsonObj, options: [.prettyPrinted])
        return String(data: jsonData, encoding: .utf8) ?? "{}"
    }

    /** Convert scjson string to SCXML. */
    static func jsonToXml(_ json: String) throws -> String {
        guard let data = json.data(using: .utf8),
              let obj = try JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            throw NSError(domain: "scjson", code: 4, userInfo: [NSLocalizedDescriptionKey: "Invalid JSON"])
        }
        var root = obj
        if root["tag"] as? String == nil { root["tag"] = "scxml" }
        if root["xmlns"] == nil { root["xmlns"] = "http://www.w3.org/2005/07/scxml" }
        return xmlFromJSONObject(root)
    }

    private static func convertScxmlFile(src: URL, dest: URL?, keepEmpty: Bool, verify: Bool) throws {
        let xmlStr = try String(contentsOf: src)
        let jsonStr = try xmlToJson(xmlStr, omitEmpty: !keepEmpty)
        if verify {
            _ = try jsonToXml(jsonStr)
        } else if let dest = dest {
            try FileManager.default.createDirectory(at: dest.deletingLastPathComponent(), withIntermediateDirectories: true)
            try jsonStr.write(to: dest, atomically: true, encoding: .utf8)
        }
    }

    private static func convertScjsonFile(src: URL, dest: URL?, verify: Bool) throws {
        let jsonStr = try String(contentsOf: src)
        let xmlStr = try jsonToXml(jsonStr)
        if verify {
            _ = try xmlToJson(xmlStr)
        } else if let dest = dest {
            try FileManager.default.createDirectory(at: dest.deletingLastPathComponent(), withIntermediateDirectories: true)
            try xmlStr.write(to: dest, atomically: true, encoding: .utf8)
        }
    }
}

// MARK: - XML tree builder

private let STRUCTURAL_FIELDS_ARR: [String] = [
    "state", "parallel", "final", "history", "transition", "onentry", "onexit",
    "invoke", "datamodel", "data", "initial", "script", "log", "assign", "send",
    "cancel", "param", "raise", "foreach"
]
@inline(__always)
private func isStructural(_ tag: String) -> Bool { STRUCTURAL_FIELDS_ARR.contains(tag) }

private let SCXML_KNOWN_TAGS: Set<String> = [
    "scxml", "state", "parallel", "final", "history", "transition", "onentry",
    "onexit", "invoke", "datamodel", "data", "initial", "script", "log", "assign",
    "send", "cancel", "param", "raise", "foreach", "if", "elseif", "else",
    "donedata", "finalize", "content"
]


private class XMLTreeBuilder: NSObject, XMLParserDelegate {
    class Node {
        var tag: String
        var attributes: [String: String]
        var children: [Node] = []
        var text: String = ""
        init(tag: String, attributes: [String: String]) {
            self.tag = tag; self.attributes = attributes
        }
    }
    var stack: [Node] = []
    var root: Node?

    func parser(_ parser: XMLParser, didStartElement elementName: String, namespaceURI: String?, qualifiedName qName: String?, attributes attributeDict: [String : String] = [:]) {
        var attrs = attributeDict
        for k in attributeDict.keys where k.hasPrefix("xmlns:") { attrs.removeValue(forKey: k) }
        let node = Node(tag: (qName ?? elementName), attributes: attrs)
        stack.append(node)
    }

    func parser(_ parser: XMLParser, foundCharacters string: String) {
        guard let cur = stack.last else { return }
        cur.text += string
    }

    func parser(_ parser: XMLParser, didEndElement elementName: String, namespaceURI: String?, qualifiedName qName: String?) {
        guard let node = stack.popLast() else { return }
        if let parent = stack.last {
            parent.children.append(node)
        } else {
            self.root = node
        }
    }
}

// MARK: - Converters

private func convertAnyElement(_ node: XMLTreeBuilder.Node) -> [String: Any] {
    var obj: [String: Any] = ["qname": node.tag]
    let text = node.text.trimmingCharacters(in: .whitespacesAndNewlines)
    obj["text"] = text
    let attrs = node.attributes.filter { !$0.key.hasPrefix("xmlns") }
    if !attrs.isEmpty { obj["attributes"] = attrs }
    if !node.children.isEmpty {
        obj["children"] = node.children.map { convertAnyElement($0) }
    }
    return obj
}

private func convertElement(_ node: XMLTreeBuilder.Node) throws -> [String: Any] {
    let tag = localTag(node.tag)
    if !SCXML_KNOWN_TAGS.contains(tag) {
        return convertAnyElement(node)
    }
    var obj: [String: Any] = [:]
    obj["tag"] = tag
    // Attributes
    for (k, v) in node.attributes {
        let key = remapAttributeKey(k)
        if key == "datamodel_attribute" {
            obj[key] = v
        } else if key == "version", let d = Double(v) {
            obj[key] = d
        } else if key == "initial_attribute" {
            let parts = v.split { $0 == " " || $0 == "\t" || $0 == "\n" }.map(String.init)
            obj[key] = parts
        } else if key == "target" {
            let parts = v.split{ $0 == " " || $0 == "\t" || $0 == "\n" }.map(String.init)
            obj[key] = parts
        } else {
            obj[key] = v
        }
    }
    // Text content for any element
    let text = node.text.trimmingCharacters(in: .whitespacesAndNewlines)

    // Children: lift structural fields and special shapes
    var content: [Any] = []
    if !text.isEmpty { content.append(text) }
    var lifted: [String: [[String: Any]]] = [:]
    for child in node.children {
        let converted = try convertElement(child)
        if let childTag = converted["tag"] as? String {
            // if/elseif/else/donedata/finalize; assign nested scxml
            if tag == "if" && childTag == "elseif" {
                var arr = (obj["elseif"] as? [[String: Any]]) ?? []
                arr.append(converted); obj["elseif"] = arr; continue
            }
            if childTag == "content" {
                if tag == "send" {
                    var arr = (obj["content"] as? [Any]) ?? []
                    arr.append(converted)
                    obj["content"] = arr
                    continue
                }
                if tag == "donedata" {
                    obj["content"] = converted
                    continue
                }
                if tag == "data" {
                    if let nested = converted["content"] as? [Any] {
                        obj["content"] = nested
                    } else if let nestedDict = converted["content"] as? [String: Any] {
                        obj["content"] = [nestedDict]
                    } else {
                        obj["content"] = converted
                    }
                    continue
                }
            }
            if childTag == "donedata" {
                var arr = (obj["donedata"] as? [[String: Any]]) ?? []
                arr.append(converted)
                obj["donedata"] = arr
                continue
            }
            if childTag == "finalize" { obj["finalize"] = converted; continue }
            if tag == "assign" && childTag == "scxml" {
                var minimal = converted
                if minimal["datamodel_attribute"] == nil { minimal["datamodel_attribute"] = "null" }
                var arr = (obj["content"] as? [Any]) ?? []
                arr.append(minimal); obj["content"] = arr; continue
            }
            if childTag == "if" {
                var arr = lifted["if_value"] ?? []; arr.append(converted); lifted["if_value"] = arr; continue
            }
            if childTag == "else" {
                if converted.keys.count <= 1 { obj["else_value"] = NSNull() } else { obj["else_value"] = converted }
                continue
            }
            if isStructural(childTag) {
                var arr = lifted[childTag] ?? []; arr.append(converted); lifted[childTag] = arr; continue
            }
        }
        content.append(converted)
    }
    // Defaults
    if tag == "assign" && obj["type_value"] == nil { obj["type_value"] = "replacechildren" }
    if tag == "invoke" {
        if obj["autoforward"] == nil { obj["autoforward"] = "false" }
        if obj["type_value"] == nil { obj["type_value"] = "scxml" }
    }
    if tag == "send" {
        if obj["type_value"] == nil { obj["type_value"] = "scxml" }
        if obj["delay"] == nil { obj["delay"] = "0s" }
    }
    // Merge lifted and content
    for (k, v) in lifted { obj[k] = v }
    if !content.isEmpty {
        if var existing = obj["content"] as? [Any] {
            existing.append(contentsOf: content)
            obj["content"] = existing
        } else if let existingDict = obj["content"] as? [String: Any] {
            var combined: [Any] = [existingDict]
            combined.append(contentsOf: content)
            obj["content"] = combined
        } else {
            obj["content"] = content
        }
    }
    // Canonical single-transition dict under initial/history
    if tag == "initial", let arr = obj["transition"] as? [[String: Any]], arr.count == 1 { obj["transition"] = arr[0] }
    if tag == "history", let arr = obj["transition"] as? [[String: Any]], arr.count == 1 { obj["transition"] = arr[0] }
    // Root/nested scxml defaults
    if tag == "scxml" {
        if obj["version"] == nil { obj["version"] = 1.0 }
        if let dm = obj["datamodel"] as? String { obj["datamodel_attribute"] = dm; obj.removeValue(forKey: "datamodel") }
        if obj["datamodel_attribute"] == nil { obj["datamodel_attribute"] = "null" }
    }
    for key in ["onentry", "onexit"] {
        if var sections = obj[key] as? [[String: Any]] {
            sections.removeAll { entry in
                var copy = entry
                copy.removeValue(forKey: "tag")
                return copy.isEmpty
            }
            if sections.isEmpty {
                obj.removeValue(forKey: key)
            } else {
                obj[key] = sections
            }
        }
    }
    return obj
}

private func xmlFromJSONObject(_ obj: [String: Any]) -> String {
    let tag = (obj["tag"] as? String) ?? "scxml"
    var attrs: [(String, String)] = []
    // Attributes
    for (kAny, vAny) in obj {
        let k = kAny
        if k == "tag" || k == "content" || isStructural(k) { continue }
        let outKey: String
        switch k {
        case "datamodel_attribute": outKey = "datamodel"
        case "initial_attribute": outKey = "initial"
        case "type_value": outKey = "type"
        default: outKey = k
        }
        if outKey == "target" || outKey == "initial" {
            if let arr = vAny as? [Any] {
                let items = arr.compactMap { $0 as? String }
                if !items.isEmpty { attrs.append((outKey, items.joined(separator: " "))) }
            } else if let s = vAny as? String {
                attrs.append((outKey, s))
            }
        } else if let s = vAny as? String {
            attrs.append((outKey, s))
        } else if let n = vAny as? NSNumber {
            attrs.append((outKey, n.stringValue))
        }
    }
    var children: [String] = []
    // Structural arrays
    for key in STRUCTURAL_FIELDS_ARR {
        if let arr = obj[key] as? [Any] {
            for item in arr {
                if let child = item as? [String: Any] {
                    if child["qname"] != nil {
                        children.append(xmlFromAnyElement(child))
                    } else {
                        children.append(xmlFromJSONObject(child))
                    }
                }
            }
        } else if let childObj = obj[key] as? [String: Any] {
            if childObj["qname"] != nil {
                children.append(xmlFromAnyElement(childObj))
            } else {
                children.append(xmlFromJSONObject(childObj))
            }
        }
    }
    // donedata (singular)
    if let ddArray = obj["donedata"] as? [Any] {
        for item in ddArray {
            if let child = item as? [String: Any] {
                if child["qname"] != nil {
                    children.append(xmlFromAnyElement(child))
                } else {
                    children.append(xmlFromJSONObject(child))
                }
            }
        }
    } else if let dd = obj["donedata"] as? [String: Any] {
        if dd["qname"] != nil {
            children.append(xmlFromAnyElement(dd))
        } else {
            children.append(xmlFromJSONObject(dd))
        }
    }
    // Content (object or array)
    if let contentObj = obj["content"] as? [String: Any] {
        if contentObj["qname"] != nil {
            children.append(xmlFromAnyElement(contentObj))
        } else {
            children.append(xmlFromJSONObject(contentObj))
        }
    } else if let content = obj["content"] as? [Any] {
        for item in content {
            if let child = item as? [String: Any] {
                if child["qname"] != nil {
                    children.append(xmlFromAnyElement(child))
                } else {
                    children.append(xmlFromJSONObject(child))
                }
            } else if let s = item as? String {
                children.append(escapeXML(s))
            }
        }
    }
    // if/elseif/else
    if let ifArr = obj["if_value"] as? [Any] {
        for item in ifArr {
            if let child = item as? [String: Any] {
                if child["qname"] != nil {
                    children.append(xmlFromAnyElement(child))
                } else {
                    children.append(xmlFromJSONObject(child))
                }
            }
        }
    } else if let ifObj = obj["if_value"] as? [String: Any] {
        if ifObj["qname"] != nil {
            children.append(xmlFromAnyElement(ifObj))
        } else {
            children.append(xmlFromJSONObject(ifObj))
        }
    }
    if let elseifArr = obj["elseif"] as? [Any] {
        for item in elseifArr {
            if let child = item as? [String: Any] {
                if child["qname"] != nil {
                    children.append(xmlFromAnyElement(child))
                } else {
                    children.append(xmlFromJSONObject(child))
                }
            }
        }
    }
    if obj.keys.contains("else_value") {
        if let elseObj = obj["else_value"] as? [String: Any] {
            if elseObj["qname"] != nil {
                children.append(xmlFromAnyElement(elseObj))
            } else {
                children.append(xmlFromJSONObject(elseObj))
            }
        } else {
            children.append("<else/>")
        }
    }
    // finalize
    if let fin = obj["finalize"] as? [String: Any] {
        children.append(xmlFromJSONObject(fin))
    }
    // Emit element
    var xml = "<\(tag)"
    for (k, v) in attrs { xml += " \(k)=\"\(escapeXML(v))\"" }
    if children.isEmpty {
        xml += "/>"
    } else {
        xml += ">" + children.joined() + "</\(tag)>"
    }
    return xml
}

private func xmlFromAnyElement(_ obj: [String: Any]) -> String {
    guard let qname = obj["qname"] as? String else { return "" }
    var attrs: [(String, String)] = []
    if let attrDict = obj["attributes"] as? [String: Any] {
        for (k, v) in attrDict {
            if let s = v as? String {
                attrs.append((k, s))
            } else if let n = v as? NSNumber {
                attrs.append((k, n.stringValue))
            }
        }
    } else if let attrDict = obj["attributes"] as? [String: String] {
        for (k, v) in attrDict { attrs.append((k, v)) }
    }
    var body: [String] = []
    if let text = obj["text"] as? String, !text.isEmpty {
        body.append(escapeXML(text))
    }
    if let children = obj["children"] as? [Any] {
        for child in children {
            if let childDict = child as? [String: Any] {
                body.append(xmlFromAnyElement(childDict))
            } else if let s = child as? String {
                body.append(escapeXML(s))
            }
        }
    }
    var xml = "<\(qname)"
    let hasNamespaceAttr = attrs.contains { $0.0 == "xmlns" || $0.0.hasPrefix("xmlns:") }
    if !hasNamespaceAttr && !qname.contains(":") && !qname.contains("{") {
        attrs.append(("xmlns", ""))
    }
    for (k, v) in attrs {
        xml += " \(k)=\"\(escapeXML(v))\""
    }
    if body.isEmpty {
        xml += "/>"
    } else {
        xml += ">" + body.joined() + "</\(qname)>"
    }
    if let tail = obj["tail"] as? String, !tail.isEmpty {
        xml += escapeXML(tail)
    }
    return xml
}

// MARK: - Helpers

private func localTag(_ qname: String) -> String {
    if let idx = qname.lastIndex(of: ":") { return String(qname[qname.index(after: idx)...]) }
    return qname
}

private func remapAttributeKey(_ key: String) -> String {
    switch key {
    case "datamodel": return "datamodel_attribute"
    case "initial": return "initial_attribute"
    case "type": return "type_value"
    default: return key
    }
}

private func escapeXML(_ s: String) -> String {
    var r = s
    r = r.replacingOccurrences(of: "&", with: "&amp;")
    r = r.replacingOccurrences(of: "\"", with: "&quot;")
    r = r.replacingOccurrences(of: "'", with: "&apos;")
    r = r.replacingOccurrences(of: "<", with: "&lt;")
    r = r.replacingOccurrences(of: ">", with: "&gt;")
    return r
}

extension FileManager {
    fileprivate func directoryExists(atPath path: String) -> Bool {
        var isDir: ObjCBool = false
        return fileExists(atPath: path, isDirectory: &isDir) && isDir.boolValue
    }

    fileprivate func enumerateFiles(base: URL, pattern: String) -> [URL] {
        var urls: [URL] = []
        if pattern.contains("**") {
            let ext = (pattern as NSString).pathExtension
            if let enumerator = enumerator(at: base, includingPropertiesForKeys: nil) {
                for case let url as URL in enumerator {
                    if !ext.isEmpty {
                        if url.pathExtension == ext { urls.append(url) }
                    } else {
                        var rel = url.path.replacingOccurrences(of: base.path, with: "")
                        if rel.hasPrefix("/") { rel.removeFirst() }
                        if rel.matches(pattern: pattern) { urls.append(url) }
                    }
                }
            }
        } else {
            if let items = try? contentsOfDirectory(at: base, includingPropertiesForKeys: nil) {
                urls = items.filter { $0.lastPathComponent.matches(pattern: pattern) }
            }
        }
        return urls
    }
}

extension String {
    fileprivate func matches(pattern: String) -> Bool {
        let regexPattern = "^" + pattern.replacingOccurrences(of: ".", with: "\\.").replacingOccurrences(of: "*", with: ".*") + "$"
        return range(of: regexPattern, options: [.regularExpression]) != nil
    }
}

SCJSON.main()
