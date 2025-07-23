/**
 * Agent Name: scxml-runner
 *
 * Part of the scjson project.
 * Developed by Softoboros Technology Inc.
 * Licensed under the BSD 1-Clause License.
 */
package com.softobros;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.commons.scxml2.SCXMLExecutor;
import org.apache.commons.scxml2.env.SimpleDispatcher;
import org.apache.commons.scxml2.env.SimpleErrorReporter;
import org.apache.commons.scxml2.env.SimpleSCXMLListener;
import org.apache.commons.scxml2.env.jexl.JexlEvaluator;
import org.apache.commons.scxml2.env.jexl.JexlUtils;
import org.apache.commons.scxml2.io.SCXMLReader;
import org.apache.commons.scxml2.model.EnterableState;
import org.apache.commons.scxml2.model.SCXML;
import org.apache.commons.scxml2.model.TransitionTarget;
import org.apache.commons.scxml2.TriggerEvent;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.util.ArrayList;
import java.util.List;

/**
 * Standalone runner using Apache Commons SCXML.
 */
public final class ScxmlRunner {

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
        ObjectMapper mapper = new ObjectMapper();
        try (FileInputStream in = new FileInputStream(file)) {
            return mapper.readValue(in, new TypeReference<List<Event>>() {});
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
        ObjectMapper mapper = new ObjectMapper();
        try (FileOutputStream out = new FileOutputStream(file)) {
            mapper.writerWithDefaultPrettyPrinter().writeValue(out, trace);
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
        SCXML scxml;
        try (FileInputStream in = new FileInputStream(scxmlFile)) {
            scxml = SCXMLReader.read(in);
        }

        ExecutionTrace trace = new ExecutionTrace();
        SCXMLExecutor exec = new SCXMLExecutor(new JexlEvaluator(), new SimpleDispatcher(), new SimpleErrorReporter());
        exec.setStateMachine(scxml);
        exec.setRootContext(JexlUtils.newContext(null));
        exec.addListener(scxml, new SimpleSCXMLListener() {
            @Override
            public void onEntry(EnterableState state) {
                TraceEntry e = new TraceEntry();
                e.type = "enter";
                e.id = state.getId();
                trace.entries.add(e);
            }

            @Override
            public void onExit(EnterableState state) {
                TraceEntry e = new TraceEntry();
                e.type = "exit";
                e.id = state.getId();
                trace.entries.add(e);
            }

            @Override
            public void onTransition(TransitionTarget from, TransitionTarget to, org.apache.commons.scxml2.model.Transition transition, String event) {
                TraceEntry e = new TraceEntry();
                e.type = "transition";
                e.id = from.getId() + "->" + to.getId();
                trace.entries.add(e);
            }
        });
        exec.go();

        for (Event evt : inputs) {
            exec.triggerEvent(new TriggerEvent(evt.name, TriggerEvent.SIGNAL_EVENT, evt.data));
        }
        return trace;
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
            System.err.println("Usage: java ScxmlRunner <machine.scxml> <events.json> <trace.json>");
            System.exit(1);
        }
        File scxmlFile = new File(args[0]);
        File eventsFile = new File(args[1]);
        File traceFile = new File(args[2]);

        List<Event> events = loadEvents(eventsFile);
        ExecutionTrace trace = run(scxmlFile, events);
        writeTrace(trace, traceFile);
    }
}
