/**
 * Agent Name: scjson-cli-test
 *
 * Part of the scjson project.
 * Developed by Softoboros Technology Inc.
 * Licensed under the BSD 1-Clause License.
 */
package org.scjson;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import picocli.CommandLine;

import org.scjson.ValidateCommand;

import java.nio.file.Path;

import java.nio.file.Files;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Basic CLI integration tests mirroring the Python suite.
 */
public class ScjsonCliTest {

    private static final String SCXML = "<scxml xmlns=\"http://www.w3.org/2005/07/scxml\"/>";
    private static final String JSON = "{\n  \"version\": 1.0\n}";

    @Test
    void testSingleJsonConversion(@TempDir Path tmp) throws Exception {
        Path xml = tmp.resolve("sample.scxml");
        Files.writeString(xml, SCXML);
        int exit = new CommandLine(new ScxmlToScjson()).execute(xml.toString());
        assertEquals(0, exit);
        Path out = xml.resolveSibling("sample.scjson");
        assertTrue(Files.exists(out));
        String content = Files.readString(out);
        assertTrue(content.contains("\"version\""));
    }

    @Test
    void testDirectoryJsonConversion(@TempDir Path tmp) throws Exception {
        Path dir = tmp.resolve("dir");
        Files.createDirectories(dir);
        Files.writeString(dir.resolve("a.scxml"), SCXML);
        Files.writeString(dir.resolve("b.scxml"), SCXML);
        int exit = new CommandLine(new ScxmlToScjson()).execute(dir.toString());
        assertEquals(0, exit);
        assertTrue(Files.exists(dir.resolve("a.scjson")));
        assertTrue(Files.exists(dir.resolve("b.scjson")));
    }

    @Test
    void testSingleXmlConversion(@TempDir Path tmp) throws Exception {
        Path json = tmp.resolve("sample.scjson");
        Files.writeString(json, JSON);
        int exit = new CommandLine(new ScjsonToScxml()).execute(json.toString());
        assertEquals(0, exit);
        Path out = json.resolveSibling("sample.scxml");
        assertTrue(Files.exists(out));
        String content = Files.readString(out);
        assertTrue(content.contains("scxml"));
    }

    @Test
    void testDirectoryXmlConversion(@TempDir Path tmp) throws Exception {
        Path dir = tmp.resolve("jsons");
        Files.createDirectories(dir);
        Files.writeString(dir.resolve("x.scjson"), JSON);
        Files.writeString(dir.resolve("y.scjson"), JSON);
        int exit = new CommandLine(new ScjsonToScxml()).execute(dir.toString());
        assertEquals(0, exit);
        assertTrue(Files.exists(dir.resolve("x.scxml")));
        assertTrue(Files.exists(dir.resolve("y.scxml")));
    }

    @Test
    void testRecursiveConversion(@TempDir Path tmp) throws Exception {
        Path tutorial = Path.of("..", "tutorial").normalize();
        Path jsonDir = tmp.resolve("tests").resolve("scjson");
        Path xmlDir = tmp.resolve("tests").resolve("scxml");

        int exit1 = new CommandLine(new ScxmlToScjson())
                .execute(tutorial.toString(), "-o", jsonDir.toString(), "-r");
        assertEquals(0, exit1);
        int exit2 = new CommandLine(new ScjsonToScxml())
                .execute(jsonDir.toString(), "-o", xmlDir.toString(), "-r");
        assertEquals(0, exit2);

        assertTrue(Files.walk(jsonDir).anyMatch(p -> p.toString().endsWith(".scjson")));
        assertTrue(Files.walk(xmlDir).anyMatch(p -> p.toString().endsWith(".scxml")));
    }

    @Test
    void testRecursiveValidation(@TempDir Path tmp) throws Exception {
        Path tutorial = Path.of("..", "tutorial").normalize();
        Path jsonDir = tmp.resolve("tests").resolve("scjson");
        Path xmlDir = tmp.resolve("tests").resolve("scxml");

        new CommandLine(new ScxmlToScjson())
                .execute(tutorial.toString(), "-o", jsonDir.toString(), "-r");
        new CommandLine(new ScjsonToScxml())
                .execute(jsonDir.toString(), "-o", xmlDir.toString(), "-r");

        int exit = new CommandLine(new ValidateCommand())
                .execute(tmp.resolve("tests").toString(), "-r");
        assertEquals(0, exit);
    }

    @Test
    void testRecursiveVerify(@TempDir Path tmp) throws Exception {
        Path tutorial = Path.of("..", "tutorial").normalize();
        Path jsonDir = tmp.resolve("tests").resolve("scjson");
        Path xmlDir = tmp.resolve("tests").resolve("scxml");

        int e1 = new CommandLine(new ScxmlToScjson())
                .execute(tutorial.toString(), "-o", jsonDir.toString(), "-r");
        assertEquals(0, e1);
        int e2 = new CommandLine(new ScjsonToScxml())
                .execute(jsonDir.toString(), "-o", xmlDir.toString(), "-r");
        assertEquals(0, e2);

        int v1 = new CommandLine(new ScxmlToScjson())
                .execute(xmlDir.toString(), "-r", "-v");
        assertEquals(0, v1);
        int v2 = new CommandLine(new ScjsonToScxml())
                .execute(jsonDir.toString(), "-r", "-v");
        assertEquals(0, v2);
    }
}
