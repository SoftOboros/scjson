/*
Agent Name: cs-cli

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.
*/

using System;
using System.Collections.Generic;
using System.IO;

namespace ScjsonCli;

/// <summary>
/// Command line interface mirroring the Python utility.
/// </summary>
public static class Program
{
    /// <summary>
    /// Entry point for the scjson CLI.
    /// </summary>
    /// <param name="args">Arguments array.</param>
    /// <returns>Exit code.</returns>
    public static int Main(string[] args)
    {
        if (args.Length == 0 || args[0] is "-h" or "--help")
        {
            PrintUsage();
            return 0;
        }

        var command = args[0].ToLowerInvariant();
        var options = ParseOptions(args);
        string path = options.Path ?? string.Empty;
        try
        {
            switch (command)
            {
                case "xml":
                    return RunXml(path, options.Output, options.Recursive, options.Verify, options.KeepEmpty);
                case "json":
                    return RunJson(path, options.Output, options.Recursive, options.Verify, options.KeepEmpty);
                case "validate":
                    return RunValidate(path, options.Recursive);
                default:
                    PrintUsage();
                    return 1;
            }
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"Failed to convert {path}: {ex.Message}");
            return 1;
        }
    }

    /// <summary>
    /// Display command usage information.
    /// </summary>
    private static void PrintUsage()
    {
        Console.WriteLine("scjson [xml|json|validate] <path> [options]");
        Console.WriteLine("  --help, -h          Show this message");
        Console.WriteLine("  -o, --output PATH   Output file or directory");
        Console.WriteLine("  -r, --recursive     Process directories recursively");
        Console.WriteLine("  -v, --verify        Verify conversions without writing files");
        Console.WriteLine("      --keep-empty    Preserve empty elements during conversion");
    }

    /// <summary>
    /// Convert SCXML files to scjson.
    /// </summary>
    /// <param name="path">Input file or directory path.</param>
    /// <param name="output">Output location or null for default.</param>
    /// <param name="recursive">Process directories recursively.</param>
    /// <param name="verify">Only verify without writing output.</param>
    /// <param name="keepEmpty">Retain empty elements.</param>
    /// <returns>Exit code.</returns>
    private static int RunJson(string path, string? output, bool recursive, bool verify, bool keepEmpty)
    {
        bool success = true;
        void ConvertFile(string src, string? dest)
        {
            try
            {
                var xmlStr = File.ReadAllText(src);
                var jsonStr = Converter.XmlToJson(xmlStr, !keepEmpty);
                if (verify)
                {
                    Converter.JsonToXml(jsonStr);
                    Console.WriteLine($"Verified {src}");
                    return;
                }
                if (dest != null)
                {
                    var dir = Path.GetDirectoryName(dest);
                    if (!string.IsNullOrEmpty(dir))
                    {
                        Directory.CreateDirectory(dir);
                    }
                    File.WriteAllText(dest, jsonStr);
                    Console.WriteLine($"Wrote {dest}");
                }
            }
            catch (Exception e)
            {
                Console.Error.WriteLine($"Failed to convert {src}: {e.Message}");
                success = false;
            }
        }

        if (Directory.Exists(path))
        {
            string outDir = output ?? path;
            var files = Directory.GetFiles(path, "*.scxml", recursive ? SearchOption.AllDirectories : SearchOption.TopDirectoryOnly);
            foreach (var src in files)
            {
                var rel = Path.GetRelativePath(path, src);
                string? dest = verify ? null : Path.Combine(outDir, Path.ChangeExtension(rel, ".scjson"));
                ConvertFile(src, dest);
            }
        }
        else if (File.Exists(path))
        {
            string? dest = null;
            if (!verify)
            {
                if (output != null && (Directory.Exists(output) || Path.GetExtension(output) == string.Empty))
                {
                    Directory.CreateDirectory(output);
                    dest = Path.Combine(output, Path.GetFileNameWithoutExtension(path) + ".scjson");
                }
                else
                {
                    dest = output ?? Path.ChangeExtension(path, ".scjson");
                }
            }
            ConvertFile(path, dest);
        }
        else
        {
            Console.Error.WriteLine("path not found");
            return 1;
        }

        return success ? 0 : 1;
    }

    /// <summary>
    /// Convert scjson files to SCXML.
    /// </summary>
    /// <param name="path">Input file or directory path.</param>
    /// <param name="output">Output location or null for default.</param>
    /// <param name="recursive">Process directories recursively.</param>
    /// <param name="verify">Only verify without writing output.</param>
    /// <param name="keepEmpty">Retain empty elements.</param>
    /// <returns>Exit code.</returns>
    private static int RunXml(string path, string? output, bool recursive, bool verify, bool keepEmpty)
    {
        bool success = true;
        void ConvertFile(string src, string? dest)
        {
            try
            {
                var jsonStr = File.ReadAllText(src);
                var xmlStr = Converter.JsonToXml(jsonStr);
                if (verify)
                {
                    Converter.XmlToJson(xmlStr, !keepEmpty);
                    Console.WriteLine($"Verified {src}");
                    return;
                }
                if (dest != null)
                {
                    var dir = Path.GetDirectoryName(dest);
                    if (!string.IsNullOrEmpty(dir))
                    {
                        Directory.CreateDirectory(dir);
                    }
                    File.WriteAllText(dest, xmlStr);
                    Console.WriteLine($"Wrote {dest}");
                }
            }
            catch (Exception e)
            {
                Console.Error.WriteLine($"Failed to convert {src}: {e.Message}");
                success = false;
            }
        }

        if (Directory.Exists(path))
        {
            string outDir = output ?? path;
            var files = Directory.GetFiles(path, "*.scjson", recursive ? SearchOption.AllDirectories : SearchOption.TopDirectoryOnly);
            foreach (var src in files)
            {
                var rel = Path.GetRelativePath(path, src);
                string? dest = verify ? null : Path.Combine(outDir, Path.ChangeExtension(rel, ".scxml"));
                ConvertFile(src, dest);
            }
        }
        else if (File.Exists(path))
        {
            string? dest = null;
            if (!verify)
            {
                if (output != null && (Directory.Exists(output) || Path.GetExtension(output) == string.Empty))
                {
                    Directory.CreateDirectory(output);
                    dest = Path.Combine(output, Path.GetFileNameWithoutExtension(path) + ".scxml");
                }
                else
                {
                    dest = output ?? Path.ChangeExtension(path, ".scxml");
                }
            }
            ConvertFile(path, dest);
        }
        else
        {
            Console.Error.WriteLine("path not found");
            return 1;
        }

        return success ? 0 : 1;
    }

    /// <summary>
    /// Validate scjson or SCXML files by round-tripping.
    /// </summary>
    /// <param name="path">Input file or directory path.</param>
    /// <param name="recursive">Process directories recursively.</param>
    /// <returns>Exit code.</returns>
    private static int RunValidate(string path, bool recursive)
    {
        bool success = true;

        void ValidateFile(string p)
        {
            try
            {
                var data = File.ReadAllText(p);
                if (p.EndsWith(".scxml"))
                {
                    var jsonStr = Converter.XmlToJson(data);
                    Converter.JsonToXml(jsonStr);
                }
                else if (p.EndsWith(".scjson"))
                {
                    var xmlStr = Converter.JsonToXml(data);
                    Converter.XmlToJson(xmlStr);
                }
            }
            catch (Exception e)
            {
                Console.Error.WriteLine($"Validation failed for {p}: {e.Message}");
                success = false;
            }
        }

        if (Directory.Exists(path))
        {
            var pattern = recursive ? "*" : "*"; // same
            var files = Directory.GetFiles(path, pattern, recursive ? SearchOption.AllDirectories : SearchOption.TopDirectoryOnly);
            foreach (var f in files)
            {
                if (f.EndsWith(".scxml") || f.EndsWith(".scjson"))
                {
                    ValidateFile(f);
                }
            }
        }
        else if (File.Exists(path))
        {
            ValidateFile(path);
        }
        else
        {
            Console.Error.WriteLine("path not found");
            return 1;
        }

        return success ? 0 : 1;
    }

    /// <summary>
    /// Parsed command line options.
    /// </summary>
    /// <param name="Path">Input path.</param>
    /// <param name="Output">Output location.</param>
    /// <param name="Recursive">Process directories recursively.</param>
    /// <param name="Verify">Only verify without writing output.</param>
    /// <param name="KeepEmpty">Retain empty elements.</param>
    private record Options(string? Path, string? Output, bool Recursive, bool Verify, bool KeepEmpty);

    /// <summary>
    /// Parse command line options.
    /// </summary>
    /// <param name="args">Command line arguments.</param>
    /// <returns>Parsed options.</returns>
    private static Options ParseOptions(string[] args)
    {
        string? output = null;
        bool recursive = false;
        bool verify = false;
        bool keepEmpty = false;
        string? path = null;

        for (int i = 1; i < args.Length; i++)
        {
            var arg = args[i];
            switch (arg)
            {
                case "-o":
                case "--output":
                    if (i + 1 < args.Length)
                    {
                        output = args[++i];
                    }
                    break;
                case "-r":
                case "--recursive":
                    recursive = true;
                    break;
                case "-v":
                case "--verify":
                    verify = true;
                    break;
                case "--keep-empty":
                    keepEmpty = true;
                    break;
                default:
                    if (path == null)
                    {
                        path = arg;
                    }
                    break;
            }
        }

        return new Options(path, output, recursive, verify, keepEmpty);
    }
}
