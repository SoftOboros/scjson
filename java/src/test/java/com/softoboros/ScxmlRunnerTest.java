/**
 * Agent Name: scxml-runner-test
 *
 * Part of the scjson project.
 * Developed by Softoboros Technology Inc.
 * Licensed under the BSD 1-Clause License.
 */
package com.softobros;

import org.junit.jupiter.api.Test;

import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * Execute a tutorial state machine using {@link ScxmlRunner} and verify the
 * collected execution trace.
 */
public class ScxmlRunnerTest {

    /**
     * Create a runner event with the given name.
     *
     * @param name event identifier
     * @return configured event instance
     */
    private static ScxmlRunner.Event event(String name) {
        ScxmlRunner.Event e = new ScxmlRunner.Event();
        e.name = name;
        return e;
    }

    /**
     * Run the W3C test150 state machine and ensure all states are visited.
     *
     * @throws Exception on failure
     */
    @Test
    void testExecutionTrace() throws Exception {
        List<ScxmlRunner.Event> events = new ArrayList<>();
        events.add(event("foo"));
        events.add(event("bar"));

        Path scxml = Path.of("..", "tutorial", "Tests", "ecma", "W3C",
                "Mandatory", "Auto", "test150.scxml").normalize();
        ScxmlRunner.ExecutionTrace trace = ScxmlRunner.run(scxml.toFile(), events);

        List<String> entered = trace.entries.stream()
                .filter(t -> "enter".equals(t.type))
                .map(t -> t.id)
                .toList();
        assertTrue(entered.containsAll(List.of("s0", "s1", "s2", "pass")),
                "Did not traverse all expected states");
        assertTrue(!entered.contains("fail"),
                "Machine entered unexpected fail state");
    }
}
