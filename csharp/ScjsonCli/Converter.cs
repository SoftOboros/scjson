/*
Agent Name: cs-converter

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.
*/

using System.Collections.Generic;
using System.Xml;
using System.Xml.Linq;
using Newtonsoft.Json;

namespace ScjsonCli;

/// <summary>
/// Utility class for SCXML &lt;-&gt; scjson conversions.
/// </summary>
public static class Converter
{
    /// <summary>
    /// Convert an SCXML XML string to scjson.
    /// </summary>
    /// <param name="xmlStr">SCXML input string.</param>
    /// <param name="omitEmpty">Remove empty fields.</param>
    /// <returns>Canonical scjson string.</returns>
    public static string XmlToJson(string xmlStr, bool omitEmpty = true)
    {
        var doc = new XmlDocument();
        doc.LoadXml(xmlStr);
        var root = doc.DocumentElement;
        var obj = new Dictionary<string, object?>();
        double version = 1.0;
        if (root?.Attributes?["version"] != null)
        {
            double.TryParse(root.Attributes["version"].Value, out version);
        }
        obj["version"] = version;
        string datamodel = root?.Attributes?["datamodel"]?.Value ?? "null";
        obj["datamodel_attribute"] = datamodel;
        return JsonConvert.SerializeObject(obj, Newtonsoft.Json.Formatting.Indented);
    }

    /// <summary>
    /// Convert a scjson string to SCXML.
    /// </summary>
    /// <param name="jsonStr">JSON input string.</param>
    /// <returns>SCXML XML string.</returns>
    public static string JsonToXml(string jsonStr)
    {
        var obj = JsonConvert.DeserializeObject<Dictionary<string, object?>>(jsonStr) ?? new();
        string version = obj.TryGetValue("version", out var v) ? v?.ToString() ?? "1.0" : "1.0";
        string datamodel = obj.TryGetValue("datamodel_attribute", out var d) ? d?.ToString() ?? "null" : "null";
        XNamespace ns = "http://www.w3.org/2005/07/scxml";
        var elem = new XElement(ns + "scxml",
            new XAttribute("version", version),
            new XAttribute("datamodel", datamodel));
        var doc = new XDocument(new XDeclaration("1.0", "utf-8", null), elem);
        return doc.ToString(SaveOptions.DisableFormatting);
    }
}
