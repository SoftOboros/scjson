/*
Agent Name: cs-cli-tests

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.
*/

using System;
using System.IO;
using Newtonsoft.Json.Linq;
using Xunit;

namespace ScjsonCli.Tests;

/// <summary>
/// Test suite for the C# scjson CLI.
/// </summary>
public class CliTests
{
    private static string CreateScxml() => "<scxml xmlns=\"http://www.w3.org/2005/07/scxml\"/>";

    private static string CreateScjson()
    {
        var obj = new JObject
        {
            ["version"] = 1.0,
            ["datamodel_attribute"] = "null"
        };
        return obj.ToString(Newtonsoft.Json.Formatting.Indented);
    }

    [Fact]
    public void SingleJsonConversion()
    {
        var dir = Directory.CreateTempSubdirectory();
        var xmlPath = Path.Combine(dir.FullName, "sample.scxml");
        File.WriteAllText(xmlPath, CreateScxml());

        var code = Program.Main(new[] { "json", xmlPath });
        Assert.Equal(0, code);

        var outPath = Path.ChangeExtension(xmlPath, ".scjson");
        Assert.True(File.Exists(outPath));
        var data = JObject.Parse(File.ReadAllText(outPath));
        Assert.Equal(1.0, data["version"]!.Value<double>());
    }

    [Fact]
    public void DirectoryJsonConversion()
    {
        var dir = Directory.CreateTempSubdirectory();
        var srcDir = Path.Combine(dir.FullName, "src");
        Directory.CreateDirectory(srcDir);
        foreach (var n in new[] { "a", "b" })
        {
            File.WriteAllText(Path.Combine(srcDir, n + ".scxml"), CreateScxml());
        }

        var code = Program.Main(new[] { "json", srcDir });
        Assert.Equal(0, code);
        foreach (var n in new[] { "a", "b" })
        {
            Assert.True(File.Exists(Path.Combine(srcDir, n + ".scjson")));
        }
    }

    [Fact]
    public void SingleXmlConversion()
    {
        var dir = Directory.CreateTempSubdirectory();
        var jsonPath = Path.Combine(dir.FullName, "sample.scjson");
        File.WriteAllText(jsonPath, CreateScjson());

        var code = Program.Main(new[] { "xml", jsonPath });
        Assert.Equal(0, code);

        var outPath = Path.ChangeExtension(jsonPath, ".scxml");
        Assert.True(File.Exists(outPath));
        var data = File.ReadAllText(outPath);
        Assert.Contains("scxml", data);
    }

    [Fact]
    public void DirectoryXmlConversion()
    {
        var dir = Directory.CreateTempSubdirectory();
        var srcDir = Path.Combine(dir.FullName, "jsons");
        Directory.CreateDirectory(srcDir);
        foreach (var n in new[] { "x", "y" })
        {
            File.WriteAllText(Path.Combine(srcDir, n + ".scjson"), CreateScjson());
        }

        var code = Program.Main(new[] { "xml", srcDir });
        Assert.Equal(0, code);
        foreach (var n in new[] { "x", "y" })
        {
            Assert.True(File.Exists(Path.Combine(srcDir, n + ".scxml")));
        }
    }

    private static void BuildDataset(string baseDir)
    {
        var d1 = Path.Combine(baseDir, "level1");
        var d2 = Path.Combine(d1, "level2");
        Directory.CreateDirectory(d2);
        foreach (var n in new[] { "a", "b" })
        {
            File.WriteAllText(Path.Combine(d1, n + ".scxml"), CreateScxml());
            File.WriteAllText(Path.Combine(d2, n + ".scxml"), CreateScxml());
        }
    }

    [Fact]
    public void RecursiveConversion()
    {
        var dataset = Directory.CreateTempSubdirectory();
        BuildDataset(dataset.FullName);
        var scjsonDir = Path.Combine(dataset.FullName, "outjson");
        var scxmlDir = Path.Combine(dataset.FullName, "outxml");

        Assert.Equal(0, Program.Main(new[] { "json", dataset.FullName, "-o", scjsonDir, "-r" }));
        Assert.Equal(0, Program.Main(new[] { "xml", scjsonDir, "-o", scxmlDir, "-r" }));

        var jsonFiles = Directory.GetFiles(scjsonDir, "*.scjson", SearchOption.AllDirectories);
        var xmlFiles = Directory.GetFiles(scxmlDir, "*.scxml", SearchOption.AllDirectories);
        Assert.NotEmpty(jsonFiles);
        Assert.NotEmpty(xmlFiles);
        Assert.True(xmlFiles.Length <= jsonFiles.Length);
    }

    [Fact]
    public void RecursiveValidation()
    {
        var dataset = Directory.CreateTempSubdirectory();
        BuildDataset(dataset.FullName);
        var scjsonDir = Path.Combine(dataset.FullName, "outjson");
        var scxmlDir = Path.Combine(dataset.FullName, "outxml");

        Assert.Equal(0, Program.Main(new[] { "json", dataset.FullName, "-o", scjsonDir, "-r" }));
        Assert.Equal(0, Program.Main(new[] { "xml", scjsonDir, "-o", scxmlDir, "-r" }));

        File.WriteAllText(Path.Combine(scjsonDir, "corrupt.scjson"), "bad");
        var code = Program.Main(new[] { "validate", dataset.FullName, "-r" });
        Assert.NotEqual(0, code);
    }

    [Fact]
    public void RecursiveVerify()
    {
        var dataset = Directory.CreateTempSubdirectory();
        BuildDataset(dataset.FullName);
        var scjsonDir = Path.Combine(dataset.FullName, "outjson");
        var scxmlDir = Path.Combine(dataset.FullName, "outxml");

        Assert.Equal(0, Program.Main(new[] { "json", dataset.FullName, "-o", scjsonDir, "-r" }));
        Assert.Equal(0, Program.Main(new[] { "xml", scjsonDir, "-o", scxmlDir, "-r" }));

        Assert.Equal(0, Program.Main(new[] { "json", scxmlDir, "-r", "-v" }));
        Assert.Equal(0, Program.Main(new[] { "xml", scjsonDir, "-r", "-v" }));
    }
}
