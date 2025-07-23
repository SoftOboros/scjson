/**
 * Agent Name: run-command
 *
 * Part of the scjson project.
 * Developed by Softoboros Technology Inc.
 * Licensed under the BSD 1-Clause License.
 */
package com.softobros;

import picocli.CommandLine.Command;
import picocli.CommandLine.Option;
import picocli.CommandLine.Parameters;

import java.io.File;
import java.util.ArrayList;
import java.util.List;

/**
 * Execute an SCXML document and optionally write an execution trace.
 */
@Command(name = "run", description = "Execute an SCXML document")
public class RunCommand implements java.util.concurrent.Callable<Integer> {

    /** SCXML document to execute. */
    @Parameters(paramLabel = "SCXML", description = "SCXML file to execute")
    private File scxmlFile;

    /** Optional JSON file containing input events. */
    @Option(names = {"-e", "--events"}, description = "JSON file of events")
    private File eventsFile;

    /** Optional output file for the execution trace. */
    @Option(names = {"-o", "--output"}, description = "Output trace file")
    private File outputFile;

    @Override
    public Integer call() throws Exception {
        List<ScxmlRunner.Event> events = new ArrayList<>();
        if (eventsFile != null) {
            events = ScxmlRunner.loadEvents(eventsFile);
        }
        ScxmlRunner.ExecutionTrace trace = ScxmlRunner.run(scxmlFile, events);
        if (outputFile != null) {
            ScxmlRunner.writeTrace(trace, outputFile);
        } else {
            com.fasterxml.jackson.databind.ObjectMapper mapper = new com.fasterxml.jackson.databind.ObjectMapper();
            mapper.writerWithDefaultPrettyPrinter().writeValue(System.out, trace);
        }
        return 0;
    }
}
