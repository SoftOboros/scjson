/**
 * Agent Name: validate-scjson-cli
 *
 * Part of the scjson project.
 * Developed by Softoboros Technology Inc.
 * Licensed under the BSD 1-Clause License.
 */
package org.scjson;

import picocli.CommandLine.Command;
import picocli.CommandLine.Option;
import picocli.CommandLine.Parameters;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

/**
 * Validate SCJSON or SCXML files by round-tripping them in memory.
 */
@Command(name = "validate", description = "Validate conversions by round-tripping")
public class ValidateCommand implements java.util.concurrent.Callable<Integer> {

    /** File or directory to validate. */
    @Parameters(paramLabel = "PATH", description = "File or directory to validate")
    private File path;

    /** Recurse into subdirectories. */
    @Option(names = {"-r", "--recursive"}, description = "Recurse into directories")
    private boolean recursive;

    @Override
    public Integer call() throws Exception {
        boolean success;
        if (path.isDirectory()) {
            success = processDirectory(path.toPath());
        } else {
            success = validateFile(path.toPath());
        }
        return success ? 0 : 1;
    }

    private boolean processDirectory(Path dir) throws IOException {
        java.util.concurrent.atomic.AtomicBoolean ok = new java.util.concurrent.atomic.AtomicBoolean(true);
        Files.walk(dir, recursive ? Integer.MAX_VALUE : 1)
                .filter(Files::isRegularFile)
                .forEach(p -> {
                    if (!validateFile(p)) {
                        ok.set(false);
                    }
                });
        return ok.get();
    }

    private boolean validateFile(Path file) {
        try {
            String data = Files.readString(file);
            if (file.toString().endsWith(".scxml")) {
                String json = ScxmlToScjson.convertString(data);
                ScjsonToScxml.convertString(json);
            } else if (file.toString().endsWith(".scjson")) {
                String xml = ScjsonToScxml.convertString(data);
                ScxmlToScjson.convertString(xml);
            }
            return true;
        } catch (Exception e) {
            System.err.println("Validation failed for " + file + ": " + e.getMessage());
            return false;
        }
    }
}
