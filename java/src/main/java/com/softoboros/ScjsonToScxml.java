/**
 * Agent Name: scjson-to-scxml
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
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

/**
 * Command that converts SCJSON documents to SCXML format.
 */
@Command(name = "to-xml", description = "Convert SCJSON to SCXML")
public class ScjsonToScxml implements java.util.concurrent.Callable<Integer> {

    /** Input file or directory. */
    @Parameters(paramLabel = "PATH", description = "SCJSON file or directory")
    private File path;

    /** Optional output file or directory. */
    @Option(names = {"-o", "--output"}, description = "Output file or directory")
    private File outputPath;

    /** Recursively process directories. */
    @Option(names = {"-r", "--recursive"}, description = "Recurse into directories")
    private boolean recursive;

    /** Verify conversions without writing output. */
    @Option(names = {"-v", "--verify"}, description = "Verify conversion only")
    private boolean verify;

    @Override
    public Integer call() throws Exception {
        if (path.isDirectory()) {
            File out = outputPath != null ? outputPath : path;
            processDirectory(path.toPath(), out.toPath());
        } else {
            File out = determineOutputFile(path.toPath(), outputPath);
            convertFile(path.toPath(), out.toPath());
        }
        return 0;
    }

    private void processDirectory(Path srcDir, Path destDir) throws IOException {
        if (!verify && !Files.exists(destDir)) {
            Files.createDirectories(destDir);
        }
        Files.walk(srcDir, recursive ? Integer.MAX_VALUE : 1)
                .filter(p -> p.toString().endsWith(".scjson"))
                .forEach(p -> {
                    Path rel = srcDir.relativize(p);
                    Path dest = destDir.resolve(rel).resolveSibling(rel.getFileName().toString().replaceFirst("\\.scjson$", ".scxml"));
                    try {
                        if (!verify && !Files.exists(dest.getParent())) {
                            Files.createDirectories(dest.getParent());
                        }
                        convertFile(p, dest);
                    } catch (IOException e) {
                        throw new RuntimeException(e);
                    }
                });
    }

    private File determineOutputFile(Path input, File outOpt) {
        if (outOpt != null && outOpt.isFile()) {
            return outOpt;
        }
        Path base = outOpt != null ? outOpt.toPath() : input.getParent();
        String name = input.getFileName().toString().replaceFirst("\\.scjson$", ".scxml");
        return base.resolve(name).toFile();
    }

    private void convertFile(Path input, Path output) throws IOException {
        String json = Files.readString(input);
        String xml = convertString(json);
        if (!verify) {
            Files.writeString(output, xml);
        }
    }

    /**
     * Convert SCJSON content back to SCXML.
     *
     * @param json JSON string
     * @return XML string matching the reference Python implementation
     */
    public static String convertString(String json) {
        return ScjsonConverter.jsonToXml(json);
    }
}
