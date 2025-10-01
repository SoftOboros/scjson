/**
 * Agent Name: scxml-runner
 *
 * Part of the scjson project.
 * Developed by Softoboros Technology Inc.
 * Licensed under the BSD 1-Clause License.
 */
package com.softobros;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.Duration;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Runner that proxies execution to the SCION Node.js CLI.
 */
public final class ScxmlRunner {

    private static final ObjectMapper MAPPER = new ObjectMapper();
    private static final Duration PROCESS_TIMEOUT = Duration.ofMinutes(5);

    private ScxmlRunner() {
    }

    /** Data object representing a single input event. */
    public static class Event {
        /** Event name. */
        public String name;
        /** Optional payload data. */
        public Object data;
    }

    /** Simple trace entry for state machine execution. */
    public static class TraceEntry {
        /** Type of entry: enter/exit/transition. */
        public String type;
        /** State or transition identifier. */
        public String id;
        /** Step index in the trace. */
        public int step;
        /** Triggering event name, if any. */
        public String event;
    }

    /** Collection of trace entries. */
    public static class ExecutionTrace {
        /** Ordered list of entries. */
        public List<TraceEntry> entries = new ArrayList<>();
    }

    /**
     * Load input events from JSON.
     *
     * @param file path to JSON file containing an array of events
     * @return list of Event objects
     * @throws Exception on parse errors
     */
    public static List<Event> loadEvents(File file) throws Exception {
        try (FileInputStream in = new FileInputStream(file)) {
            return MAPPER.readValue(in, new TypeReference<List<Event>>() {
            });
        }
    }

    /**
     * Write the execution trace to a JSON file.
     *
     * @param trace trace data to write
     * @param file output JSON file
     * @throws Exception on serialization errors
     */
    public static void writeTrace(ExecutionTrace trace, File file) throws Exception {
        try (FileOutputStream out = new FileOutputStream(file)) {
            MAPPER.writerWithDefaultPrettyPrinter().writeValue(out, trace);
        }
    }

    /**
     * Run the state machine for a sequence of events.
     *
     * @param scxmlFile SCXML document
     * @param inputs event list
     * @return collected execution trace
     * @throws Exception if execution fails
     */
    public static ExecutionTrace run(File scxmlFile, List<Event> inputs) throws Exception {
        Path script = locateScionScript();
        if (!Files.exists(script)) {
            throw new IllegalStateException("SCION runner script not found: " + script);
        }

        Path traceFile = Files.createTempFile("scjson-trace", ".jsonl");
        Path eventsFile = inputs.isEmpty() ? null : Files.createTempFile("scjson-events", ".jsonl");
        try {
            if (eventsFile != null) {
                writeEventsFile(eventsFile, inputs);
            }
            List<String> command = new ArrayList<>();
            command.add("node");
            command.add(script.toString());
            command.add("-I");
            command.add(scxmlFile.getAbsolutePath());
            command.add("-o");
            command.add(traceFile.toString());
            if (eventsFile != null) {
                command.add("-e");
                command.add(eventsFile.toString());
            }

            ProcessBuilder builder = new ProcessBuilder(command);
            builder.redirectError(ProcessBuilder.Redirect.INHERIT);
            Process process = builder.start();
            boolean finished = process.waitFor(PROCESS_TIMEOUT.toMillis(), java.util.concurrent.TimeUnit.MILLISECONDS);
            if (!finished) {
                process.destroyForcibly();
                throw new IOException("SCION runner timed out");
            }
            if (process.exitValue() != 0) {
                throw new IOException("SCION runner exited with code " + process.exitValue());
            }
            return parseTrace(traceFile);
        } finally {
            Files.deleteIfExists(traceFile);
            if (eventsFile != null) {
                Files.deleteIfExists(eventsFile);
            }
        }
    }

    private static Path locateScionScript() {
        Path cwd = Paths.get("").toAbsolutePath();
        Path script = cwd.resolve("tools").resolve("scion-runner").resolve("scion-trace.cjs");
        if (Files.exists(script)) {
            return script;
        }
        Path parent = cwd.getParent();
        if (parent != null) {
            Path candidate = parent.resolve("tools").resolve("scion-runner").resolve("scion-trace.cjs");
            if (Files.exists(candidate)) {
                return candidate;
            }
        }
        // Attempt relative to jar location when running from packaged artifact.
        try {
            Path jarLocation = Paths.get(ScjsonCli.class.getProtectionDomain()
                    .getCodeSource()
                    .getLocation()
                    .toURI());
            Path root = jarLocation.getParent();
            if (root != null) {
                Path candidate = root.resolve("../tools/scion-runner/scion-trace.cjs").normalize();
                if (Files.exists(candidate)) {
                    return candidate;
                }
            }
        } catch (Exception ignored) {
            // Fallback handled below.
        }
        return script;
    }

    private static void writeEventsFile(Path path, List<Event> events) throws IOException {
        try (BufferedWriter writer = Files.newBufferedWriter(path, StandardCharsets.UTF_8)) {
            for (Event event : events) {
                Map<String, Object> line = new LinkedHashMap<>();
                String name = event.name != null ? event.name : "";
                line.put("event", name);
                if (event.data != null) {
                    line.put("data", event.data);
                }
                writer.write(MAPPER.writeValueAsString(line));
                writer.write('\n');
            }
        }
    }

    private static ExecutionTrace parseTrace(Path traceFile) throws IOException {
        ExecutionTrace trace = new ExecutionTrace();
        List<String> lines = Files.readAllLines(traceFile, StandardCharsets.UTF_8);
        int stepIndex = 0;
        for (String line : lines) {
            if (line == null || line.isBlank()) {
                continue;
            }
            JsonNode node = MAPPER.readTree(line);
            stepIndex = node.has("step") ? node.get("step").asInt(stepIndex) : stepIndex + 1;
            String eventName = null;
            if (node.has("event") && node.get("event").has("name")) {
                eventName = node.get("event").get("name").asText(null);
            }
            appendEntries(trace, node.path("enteredStates"), "enter", stepIndex, eventName);
            appendEntries(trace, node.path("exitedStates"), "exit", stepIndex, eventName);
            if (node.has("firedTransitions") && node.get("firedTransitions").isArray()) {
                for (JsonNode tr : node.get("firedTransitions")) {
                    String source = tr.path("source").asText("?");
                    List<String> targets = new ArrayList<>();
                    if (tr.has("targets") && tr.get("targets").isArray()) {
                        for (JsonNode tgt : tr.get("targets")) {
                            targets.add(tgt.asText());
                        }
                    }
                    String id = source + "->" + String.join(",", targets);
                    TraceEntry entry = new TraceEntry();
                    entry.type = "transition";
                    entry.id = id;
                    entry.step = stepIndex;
                    entry.event = eventName;
                    trace.entries.add(entry);
                }
            }
        }
        return trace;
    }

    private static void appendEntries(ExecutionTrace trace, JsonNode node, String type, int step, String eventName) {
        if (!node.isArray()) {
            return;
        }
        for (JsonNode item : node) {
            String id = item.asText();
            if (id == null || id.isEmpty()) {
                continue;
            }
            TraceEntry entry = new TraceEntry();
            entry.type = type;
            entry.id = id;
            entry.step = step;
            entry.event = eventName;
            trace.entries.add(entry);
        }
    }

    /**
     * Entry point for command line usage.
     *
     * @param args command line arguments
     *             0 - path to SCXML file
     *             1 - path to events JSON
     *             2 - output trace JSON
     * @throws Exception on failures
     */
    public static void main(String[] args) throws Exception {
        if (args.length != 3) {
            System.err.println("Usage: java com.softobros.ScxmlRunner <machine.scxml> <events.json> <trace.json>");
            System.exit(1);
        }
        File scxmlFile = new File(args[0]);
        File eventsFile = new File(args[1]);
        File traceFile = new File(args[2]);

        List<Event> events = new ArrayList<>();
        if (eventsFile.exists()) {
            events = loadEvents(eventsFile);
        }
        ExecutionTrace trace = run(scxmlFile, events);
        writeTrace(trace, traceFile);
    }
}
