/**
 * Agent Name: run-command-test
 *
 * Part of the scjson project.
 * Developed by Softoboros Technology Inc.
 * Licensed under the BSD 1-Clause License.
 */
package com.softobros;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import picocli.CommandLine;

import java.nio.file.Path;
import java.nio.file.Files;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Verify the run command produces an execution trace.
 */
public class RunCommandTest {

    private static final String SCXML = "<scxml xmlns=\"http://www.w3.org/2005/07/scxml\" version=\"1.0\" initial=\"start\">" +
            "<state id=\"start\"><transition event=\"go\" target=\"end\"/></state>" +
            "<final id=\"end\"/></scxml>";

    private static final String EVENTS = "[{\"name\": \"go\"}]";

    @Test
    void testRunProducesLog(@TempDir Path tmp) throws Exception {
        Path xml = tmp.resolve("machine.scxml");
        Files.writeString(xml, SCXML);
        Path evts = tmp.resolve("events.json");
        Files.writeString(evts, EVENTS);
        Path log = tmp.resolve("trace.json");

        int exit = new CommandLine(new RunCommand()).execute(
                xml.toString(), "-e", evts.toString(), "-o", log.toString());
        assertEquals(0, exit);
        assertTrue(Files.exists(log));
        String content = Files.readString(log);
        assertTrue(content.contains("enter"), "Trace should contain entries");
    }
}
