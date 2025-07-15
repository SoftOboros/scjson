/**
 * Agent Name: scjson-to-scxml
 *
 * Part of the scjson project.
 * Developed by Softoboros Technology Inc.
 * Licensed under the BSD 1-Clause License.
 */
package org.scjson;

import picocli.CommandLine.Command;
import picocli.CommandLine.Option;

/**
 * Command that converts SCJSON documents to SCXML format.
 */
@Command(name = "to-xml", description = "Convert SCJSON to SCXML")
public class ScjsonToScxml implements Runnable {

    /** Path to input file. */
    @Option(names = {"-i", "--input"}, description = "Input SCJSON file", required = true)
    private String inputPath;

    /** Path to output file. */
    @Option(names = {"-o", "--output"}, description = "Output SCXML file")
    private String outputPath;

    @Override
    public void run() {
        // TODO: implement conversion logic
        System.out.println("Converting " + inputPath + " to SCXML at " + outputPath);
    }
}
