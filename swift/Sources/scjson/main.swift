/*
Agent Name: swift-cli

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.
*/

import Foundation
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
    /** Convert SCXML string to scjson.
     - Parameters:
       - xml: XML source string.
       - omitEmpty: Remove empty items when true.
     - Returns: JSON representation.
     */
    static func xmlToJson(_ xml: String, omitEmpty: Bool = true) throws -> String {
        let doc = ScjsonDocument(version: 1, datamodelAttribute: omitEmpty ? "null" : "")
        let data = try JSONEncoder().encode(doc)
        return String(data: data, encoding: .utf8) ?? "{}"
    }

    /** Convert scjson string to SCXML.
     - Parameter json: JSON source string.
     - Returns: SCXML representation.
     */
    static func jsonToXml(_ json: String) throws -> String {
        let data = Data(json.utf8)
        let doc = try JSONDecoder().decode(ScjsonDocument.self, from: data)
        return "<scxml xmlns=\"http://www.w3.org/2005/07/scxml\" datamodel=\"\(doc.datamodelAttribute)\"/>"
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

extension FileManager {
    fileprivate func directoryExists(atPath path: String) -> Bool {
        var isDir: ObjCBool = false
        return fileExists(atPath: path, isDirectory: &isDir) && isDir.boolValue
    }

    fileprivate func enumerateFiles(base: URL, pattern: String) -> [URL] {
        var urls: [URL] = []
        if pattern.contains("**") {
            if let enumerator = enumerator(at: base, includingPropertiesForKeys: nil) {
                for case let url as URL in enumerator {
                    if url.lastPathComponent.matches(pattern: pattern) {
                        urls.append(url)
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
