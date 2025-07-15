/*
Agent Name: swift-cli-tests

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.
*/

import XCTest
import class Foundation.FileManager
@testable import scjson

final class scjsonTests: XCTestCase {
    func createScxml() -> String {
        return "<scxml xmlns=\"http://www.w3.org/2005/07/scxml\"/>"
    }

    func createScjson() -> String {
        return "{\n  \"version\": 1,\n  \"datamodel_attribute\": \"null\"\n}"
    }

    func testSingleJsonConversion() throws {
        let dir = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        let xmlPath = dir.appendingPathComponent("sample.scxml")
        try createScxml().write(to: xmlPath, atomically: true, encoding: .utf8)

        try SCJSON.Json.main([xmlPath.path])

        let outPath = dir.appendingPathComponent("sample.scjson")
        XCTAssertTrue(FileManager.default.fileExists(atPath: outPath.path))
        let data = try String(contentsOf: outPath)
        XCTAssertTrue(data.contains("\"version\""))
    }

    func testSingleXmlConversion() throws {
        let dir = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        let jsonPath = dir.appendingPathComponent("sample.scjson")
        try createScjson().write(to: jsonPath, atomically: true, encoding: .utf8)

        try SCJSON.Xml.main([jsonPath.path])

        let outPath = dir.appendingPathComponent("sample.scxml")
        XCTAssertTrue(FileManager.default.fileExists(atPath: outPath.path))
        let data = try String(contentsOf: outPath)
        XCTAssertTrue(data.contains("scxml"))
    }
}
