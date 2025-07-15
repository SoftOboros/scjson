/**
 * Agent Name: scxml-to-scjson
 *
 * Part of the scjson project.
 * Developed by Softoboros Technology Inc.
 * Licensed under the BSD 1-Clause License.
 */
package org.scjson;

import picocli.CommandLine.Command;
import picocli.CommandLine.Option;

/**
 * Command that converts SCXML documents to SCJSON format.
 */
@Command(name = "to-json", description = "Convert SCXML to SCJSON")
public class ScxmlToScjson implements Runnable {

    /** Path to input file. */
    @Option(names = {"-i", "--input"}, description = "Input SCXML file", required = true)
    private String inputPath;

    /** Path to output file. */
    @Option(names = {"-o", "--output"}, description = "Output SCJSON file")
    private String outputPath;

    @Override
    public void run() {
        // TODO: implement conversion logic
        System.out.println("Converting " + inputPath + " to SCJSON at " + outputPath);
    }
}
