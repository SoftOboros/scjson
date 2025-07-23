/**
 * Agent Name: scjson-cli
 *
 * Part of the scjson project.
 * Developed by Softoboros Technology Inc.
 * Licensed under the BSD 1-Clause License.
 */
package com.softobros;

import picocli.CommandLine;
import picocli.CommandLine.Command;

import com.softobros.ValidateCommand;

/**
 * Entry point for the scjson command line interface.
 */
@Command(name = "scjson", mixinStandardHelpOptions = true, version = "0.1",
         description = "SCXML <-> SCJSON conversion tool")
public class ScjsonCli implements Runnable {
    /**
     * Display help if no subcommand is provided.
     */
    @Override
    public void run() {
        System.out.println("Use a subcommand like 'convert' or 'validate'.");
    }

    /**
     * Main method used when running from the command line.
     *
     * @param args program arguments
     */
    public static void main(String[] args) {
        int exitCode = new CommandLine(new ScjsonCli())
                .addSubcommand("to-json", new ScxmlToScjson())
                .addSubcommand("to-xml", new ScjsonToScxml())
                .addSubcommand("validate", new ValidateCommand())
                .addSubcommand("run", new RunCommand())
                .execute(args);
        System.exit(exitCode);
    }
}
