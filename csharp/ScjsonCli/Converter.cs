/*
Agent Name: cs-converter

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.
*/

using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Xml.Linq;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace ScjsonCli;

/// <summary>
/// Utility class for SCXML &lt;-&gt; scjson conversions.
/// </summary>
public static class Converter
{
    private static readonly XNamespace ScxmlNamespace = "http://www.w3.org/2005/07/scxml";

    private static readonly HashSet<string> ScxmlElements = new(StringComparer.Ordinal)
    {
        "scxml",
        "state",
        "parallel",
        "final",
        "history",
        "transition",
        "invoke",
        "finalize",
        "datamodel",
        "data",
        "onentry",
        "onexit",
        "log",
        "send",
        "cancel",
        "raise",
        "assign",
        "script",
        "foreach",
        "param",
        "if",
        "elseif",
        "else",
        "content",
        "donedata",
        "initial",
    };

    private static readonly HashSet<string> CollapseAttributes = new(StringComparer.Ordinal)
    {
        "expr",
        "cond",
        "event",
        "target",
        "delay",
        "location",
        "name",
        "src",
        "id",
    };

    private static readonly HashSet<string> AlwaysKeep = new(StringComparer.Ordinal)
    {
        "else_value",
        "else",
        "final",
        "onentry",
    };

    private static readonly HashSet<string> PreserveEmptyStringKeys = new(StringComparer.Ordinal)
    {
        "expr",
        "cond",
        "event",
        "target",
        "id",
        "name",
        "label",
        "text",
    };

    /// <summary>
    /// Convert an SCXML XML string to scjson.
    /// </summary>
    /// <param name="xmlStr">SCXML input string.</param>
    /// <param name="omitEmpty">Remove empty fields when true.</param>
    /// <returns>Canonical scjson string.</returns>
    public static string XmlToJson(string xmlStr, bool omitEmpty = true)
    {
        if (string.IsNullOrWhiteSpace(xmlStr))
        {
            throw new ArgumentException("XML input cannot be empty", nameof(xmlStr));
        }

        var document = XDocument.Parse(xmlStr, LoadOptions.PreserveWhitespace);
        var root = document.Root ?? throw new InvalidOperationException("Document missing root element.");

        if (root.Name.LocalName == "scxml" && root.Attribute("xmlns") == null)
        {
            root.SetAttributeValue("xmlns", ScxmlNamespace.NamespaceName);
        }

        var map = ElementToMap(root);
        CollapseWhitespace(map);
        if (omitEmpty)
        {
            _ = RemoveEmpty(map);
        }

        return JsonConvert.SerializeObject(map, Formatting.Indented);
    }

    /// <summary>
    /// Convert a scjson string to SCXML.
    /// </summary>
    /// <param name="jsonStr">JSON payload representing an SCXML document.</param>
    /// <param name="omitEmpty">Remove empty fields before generating XML.</param>
    /// <returns>Canonical SCXML string.</returns>
    public static string JsonToXml(string jsonStr, bool omitEmpty = true)
    {
        if (string.IsNullOrWhiteSpace(jsonStr))
        {
            throw new ArgumentException("JSON input cannot be empty", nameof(jsonStr));
        }

        var token = JsonConvert.DeserializeObject(jsonStr) ?? throw new InvalidOperationException("Unable to parse JSON input.");
        var normalized = Normalize(token) as Dictionary<string, object?> ?? new Dictionary<string, object?>();

        if (omitEmpty)
        {
            _ = RemoveEmpty(normalized);
        }

        var element = MapToElement("scxml", normalized);
        var document = new XDocument(new XDeclaration("1.0", "utf-8", null), element);
        return document.ToString(SaveOptions.DisableFormatting);
    }

    /// <summary>
        /// Recursively normalise JSON tokens into plain CLR collections.
    /// </summary>
    /// <param name="value">Token to normalise.</param>
    /// <returns>Plain CLR representation.</returns>
    private static object? Normalize(object? value)
    {
        switch (value)
        {
            case JObject obj:
                return obj.Properties().ToDictionary(p => p.Name, p => Normalize(p.Value), StringComparer.Ordinal);
            case JArray arr:
                return arr.Select(Normalize).ToList();
            case JValue val:
                return val.Value;
            default:
                return value;
        }
    }

    /// <summary>
    /// Build a dictionary representation of an SCXML element.
    /// </summary>
    /// <param name="element">Element to convert.</param>
    /// <returns>Dictionary representation.</returns>
    private static Dictionary<string, object?> ElementToMap(XElement element)
    {
        var map = new Dictionary<string, object?>(StringComparer.Ordinal);

        foreach (var attribute in element.Attributes())
        {
            if (attribute.IsNamespaceDeclaration)
            {
                continue;
            }
            var name = attribute.Name.LocalName;
            if (name == "xmlns" || name.StartsWith("xmlns", StringComparison.Ordinal))
            {
                continue;
            }

            var value = attribute.Value;
            switch (element.Name.LocalName, name)
            {
                case ("transition", "target"):
                    map["target"] = SplitTokens(value);
                    break;
                case (_, "initial") when element.Name.LocalName == "scxml":
                    map["initial"] = SplitTokens(value);
                    break;
                case (_, "initial"):
                    map["initial_attribute"] = SplitTokens(value);
                    break;
                case (_, "version"):
                    if (double.TryParse(value, NumberStyles.Float, CultureInfo.InvariantCulture, out var number))
                    {
                        map["version"] = number;
                    }
                    else
                    {
                        map["version"] = value;
                    }
                    break;
                case (_, "datamodel"):
                    map["datamodel_attribute"] = value;
                    break;
                case (_, "type"):
                    map["type_value"] = value;
                    break;
                case (_, "raise"):
                    map["raise_value"] = value;
                    break;
                case ("send", "delay"):
                    map["delay"] = value;
                    break;
                case ("send", "event"):
                    map["event"] = value;
                    break;
                default:
                    map[name] = value;
                    break;
            }
        }

        var textItems = new List<string>();
        foreach (var node in element.Nodes())
        {
            if (node is XElement child)
            {
                var childName = child.Name.LocalName;
                if (ScxmlElements.Contains(childName))
                {
                    var converted = ElementToMap(child);
                    var targetKey = childName switch
                    {
                        "if" => "if_value",
                        "else" => "else_value",
                        "raise" => "raise_value",
                        _ => childName,
                    };

                    if (childName == "scxml" && element.Name.LocalName != "scxml")
                    {
                        targetKey = "content";
                    }

                    if ((element.Name.LocalName == "initial" || element.Name.LocalName == "history") && childName == "transition")
                    {
                        map[targetKey] = converted;
                    }
                    else
                    {
                        AppendChild(map, targetKey, converted);
                    }
                }
                else
                {
                    AppendChild(map, "content", AnyElementToValue(child));
                }
            }
            else if (node is XText text && !string.IsNullOrWhiteSpace(text.Value))
            {
                textItems.Add(text.Value);
            }
        }

        foreach (var text in textItems)
        {
            AppendChild(map, "content", text);
        }

        if (element.Name.LocalName == "assign" && !map.ContainsKey("type_value"))
        {
            map["type_value"] = "replacechildren";
        }

        if (element.Name.LocalName == "send")
        {
            if (!map.ContainsKey("type_value"))
            {
                map["type_value"] = "scxml";
            }
            if (!map.ContainsKey("delay"))
            {
                map["delay"] = "0s";
            }
        }

        if (element.Name.LocalName == "invoke")
        {
            if (!map.ContainsKey("type_value"))
            {
                map["type_value"] = "scxml";
            }
            if (!map.ContainsKey("autoforward"))
            {
                map["autoforward"] = "false";
            }
        }

        if (element.Name.LocalName == "scxml")
        {
            if (!map.ContainsKey("version"))
            {
                map["version"] = 1.0;
            }
            if (!map.ContainsKey("datamodel_attribute"))
            {
                map["datamodel_attribute"] = "null";
            }
        }

        if (element.Name.LocalName == "donedata" && map.TryGetValue("content", out var content) && content is List<object?> list && list.Count == 1)
        {
            map["content"] = list[0];
        }

        return map;
    }

    /// <summary>
    /// Convert arbitrary XML element into a lightweight scjson representation.
    /// </summary>
    /// <param name="element">Element to capture.</param>
    /// <returns>Dictionary describing the element.</returns>
    private static Dictionary<string, object?> AnyElementToValue(XElement element)
    {
        var map = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["qname"] = element.Name.ToString(),
            ["text"] = element.Value ?? string.Empty,
        };

        var attributes = new Dictionary<string, object?>(StringComparer.Ordinal);
        foreach (var attribute in element.Attributes())
        {
            if (attribute.IsNamespaceDeclaration)
            {
                continue;
            }
            attributes[attribute.Name.ToString()] = attribute.Value;
        }

        if (attributes.Count > 0)
        {
            map["attributes"] = attributes;
        }

        var children = element.Elements().Select(AnyElementToValue).Cast<object?>().ToList();
        if (children.Count > 0)
        {
            map["children"] = children;
        }

        return map;
    }

    /// <summary>
    /// Append a value to a map entry, ensuring the storage is always an array.
    /// </summary>
    /// <param name="map">Target dictionary.</param>
    /// <param name="key">Dictionary key.</param>
    /// <param name="value">Value to append.</param>
    private static void AppendChild(Dictionary<string, object?> map, string key, object? value)
    {
        if (!map.TryGetValue(key, out var existing) || existing is null)
        {
            map[key] = new List<object?> { value };
            return;
        }

        if (existing is List<object?> list)
        {
            list.Add(value);
        }
        else
        {
            map[key] = new List<object?> { existing, value };
        }
    }

    /// <summary>
    /// Split a whitespace-separated attribute list into individual tokens.
    /// </summary>
    /// <param name="value">Source string.</param>
    /// <returns>List of individual identifiers.</returns>
    private static List<object?> SplitTokens(string value)
    {
        return value
            .Split((char[]?)null, StringSplitOptions.RemoveEmptyEntries)
            .Select(token => (object?)token)
            .ToList();
    }

    /// <summary>
    /// Collapse whitespace for attribute-style values recursively.
    /// </summary>
    /// <param name="value">Candidate object.</param>
    private static void CollapseWhitespace(object? value)
    {
        switch (value)
        {
            case Dictionary<string, object?> map:
                foreach (var key in map.Keys.ToList())
                {
                    if (map[key] is string str && (key.EndsWith("_attribute", StringComparison.Ordinal) || CollapseAttributes.Contains(key)))
                    {
                        map[key] = str.Replace('\n', ' ').Replace('\r', ' ').Replace('\t', ' ');
                    }
                    else
                    {
                        CollapseWhitespace(map[key]);
                    }
                }
                break;
            case List<object?> list:
                foreach (var item in list)
                {
                    CollapseWhitespace(item);
                }
                break;
        }
    }

    /// <summary>
    /// Remove empty objects, arrays, and strings recursively.
    /// </summary>
    /// <param name="value">Candidate object.</param>
    /// <returns>True when the object should be removed from its parent.</returns>
    private static bool RemoveEmpty(object? value, string? parentKey = null)
    {
        switch (value)
        {
            case Dictionary<string, object?> map:
                foreach (var childKey in map.Keys.ToList())
                {
                    if (RemoveEmpty(map[childKey], childKey))
                    {
                        map.Remove(childKey);
                    }
                }

                return map.Count == 0 && (parentKey == null || !AlwaysKeep.Contains(parentKey));

            case List<object?> list:
                for (int i = list.Count - 1; i >= 0; i--)
                {
                    if (RemoveEmpty(list[i], parentKey))
                    {
                        list.RemoveAt(i);
                    }
                }

                return list.Count == 0 && (parentKey == null || !AlwaysKeep.Contains(parentKey));

            case null:
                return parentKey == null || !AlwaysKeep.Contains(parentKey);

            case string str:
                if (str.Length == 0)
                {
                    if (parentKey != null)
                    {
                        if (parentKey.EndsWith("_attribute", StringComparison.Ordinal) || parentKey.EndsWith("_value", StringComparison.Ordinal) || PreserveEmptyStringKeys.Contains(parentKey))
                        {
                            return false;
                        }
                    }
                    return parentKey == null || !AlwaysKeep.Contains(parentKey);
                }

                return false;

            default:
                return false;
        }
    }

    /// <summary>
    /// Convert a dictionary representation into an XElement.
    /// </summary>
    /// <param name="name">Element name hint.</param>
    /// <param name="map">Dictionary to convert.</param>
    /// <returns>Generated XElement.</returns>
    private static XElement MapToElement(string name, Dictionary<string, object?> map)
    {
        var elementName = ResolveElementName(name, map);
        var element = new XElement(elementName);

        if (map.TryGetValue("text", out var textValue) && textValue is string text && !string.IsNullOrEmpty(text))
        {
            element.Add(new XText(text));
        }

        if (map.TryGetValue("attributes", out var attrObj) && attrObj is Dictionary<string, object?> attributes)
        {
            foreach (var pair in attributes)
            {
                var resolved = ResolveElementName(pair.Key, new Dictionary<string, object?>());
                var attrValue = JoinTokens(pair.Value);
                if (!string.IsNullOrEmpty(attrValue))
                {
                    element.SetAttributeValue(resolved, attrValue);
                }
            }
        }

        foreach (var (key, value) in map)
        {
            if (key is "qname" or "text" or "attributes")
            {
                continue;
            }

            if (key == "content")
            {
                WriteContent(element, value);
                continue;
            }

            string? attributeName = null;
            if (key.EndsWith("_attribute", StringComparison.Ordinal))
            {
                attributeName = key[..^"_attribute".Length];
            }
            else if (key == "type_value")
            {
                attributeName = "type";
            }
            else if (key == "datamodel_attribute")
            {
                attributeName = "datamodel";
            }
            else if (element.Name.LocalName == "transition" && key == "target")
            {
                if (value is List<object?> targetList && targetList.All(IsPrimitiveValue))
                {
                    attributeName = "target";
                }
                else if (IsPrimitiveValue(value))
                {
                    attributeName = "target";
                }
            }
            else if (key is "delay" or "event")
            {
                attributeName = key;
            }
            else if (key == "initial")
            {
                if (value is List<object?> valueList && valueList.All(IsPrimitiveValue))
                {
                    attributeName = "initial";
                }
                else if (IsPrimitiveValue(value))
                {
                    attributeName = "initial";
                }
            }

            if (attributeName != null)
            {
                var attrValue = JoinTokens(value);
                if (attrValue == null)
                {
                    continue;
                }
                if (attrValue.Length == 0 && !ShouldPreserveEmptyAttribute(attributeName))
                {
                    continue;
                }
                element.SetAttributeValue(attributeName, attrValue);
                continue;
            }

            switch (value)
            {
                case Dictionary<string, object?> childMap:
                {
                    var childName = ResolveChildName(key);
                    element.Add(MapToElement(childName, childMap));
                    break;
                }
                case List<object?> list:
                {
                    if (list.All(IsPrimitiveValue))
                    {
                        var attrValue = JoinTokens(list);
                        if (attrValue != null)
                        {
                            if (attrValue.Length == 0 && !ShouldPreserveEmptyAttribute(key))
                            {
                                break;
                            }
                            element.SetAttributeValue(key, attrValue);
                        }
                        break;
                    }
                    var childName = ResolveChildName(key);
                    foreach (var item in list)
                    {
                        if (item is Dictionary<string, object?> child)
                        {
                            element.Add(MapToElement(childName, child));
                        }
                        else if (item is string textItem && !string.IsNullOrWhiteSpace(textItem))
                        {
                            var childElement = new XElement(childName);
                            childElement.Add(new XText(textItem));
                            element.Add(childElement);
                        }
                    }

                    break;
                }
                case string str when key == "version":
                    element.SetAttributeValue(key, str);
                    break;
                case IFormattable formattable when key == "version":
                    element.SetAttributeValue("version", FormatVersion(formattable));
                    break;
                case string or IFormattable or bool:
                {
                    var attrValue = JoinTokens(value);
                    if (attrValue != null)
                    {
                        if (attrValue.Length == 0 && !ShouldPreserveEmptyAttribute(key))
                        {
                            break;
                        }
                        element.SetAttributeValue(key, attrValue);
                    }
                    break;
                }
            }
        }

        return element;
    }

    /// <summary>
    /// Resolve the element name, honouring any explicit qname overrides.
    /// </summary>
    /// <param name="fallback">Fallback tag name.</param>
    /// <param name="map">Element map.</param>
    /// <returns>Resolved XName.</returns>
    private static XName ResolveElementName(string fallback, Dictionary<string, object?> map)
    {
        if (map.TryGetValue("qname", out var qnameObj) && qnameObj is string qname && !string.IsNullOrEmpty(qname))
        {
            return CreateXName(qname);
        }

        if (ScxmlElements.Contains(fallback))
        {
            return ScxmlNamespace + fallback;
        }

        return CreateXName(fallback);
    }

    /// <summary>
    /// Create an <see cref="XName"/> from a qualified name, handling prefixes.
    /// </summary>
    /// <param name="candidate">Name candidate.</param>
    /// <returns>Resolved <see cref="XName"/>.</returns>
    private static XName CreateXName(string candidate)
    {
        if (candidate.StartsWith("{", StringComparison.Ordinal))
        {
            var end = candidate.IndexOf('}');
            if (end > 0)
            {
                var ns = candidate.Substring(1, end - 1);
                var local = candidate[(end + 1)..];
                return XName.Get(local, ns);
            }
        }

        var colon = candidate.IndexOf(':');
        if (colon > 0)
        {
            var prefix = candidate[..colon];
            var local = candidate[(colon + 1)..];
            XNamespace ns = prefix switch
            {
                "xml" => XNamespace.Xml,
                "xmlns" => XNamespace.Xmlns,
                _ => XNamespace.None,
            };
            return ns == XNamespace.None ? XName.Get(local) : ns + local;
        }

        return XName.Get(candidate);
    }

    /// <summary>
    /// Resolve scjson field names back to XML tag names.
    /// </summary>
    /// <param name="name">Field name.</param>
    /// <returns>XML tag name.</returns>
    private static string ResolveChildName(string name)
    {
        return name switch
        {
            "if_value" => "if",
            "else_value" => "else",
            "raise_value" => "raise",
            _ => name,
        };
    }

    /// <summary>
    /// Render a content payload to XML.
    /// </summary>
    /// <param name="parent">Parent element.</param>
    /// <param name="value">Content payload.</param>
    private static void WriteContent(XElement parent, object? value)
    {
        switch (value)
        {
            case List<object?> list:
                foreach (var item in list)
                {
                    WriteContent(parent, item);
                }

                break;

            case Dictionary<string, object?> obj:
            {
                var childName = obj.ContainsKey("state") || obj.ContainsKey("final") || obj.ContainsKey("version") || obj.ContainsKey("datamodel_attribute")
                    ? "scxml"
                    : "content";
                parent.Add(MapToElement(childName, obj));
                break;
            }

            case string str:
                if (parent.Name.LocalName == "invoke")
                {
                    var contentElement = new XElement("content") { Value = str };
                    parent.Add(contentElement);
                }
                else if (parent.Name.LocalName == "script")
                {
                    parent.Add(new XText(str));
                }
                else
                {
                    parent.Add(new XText(str));
                }

                break;
        }
    }

    /// <summary>
    /// Join token arrays back into a single space-separated string.
    /// </summary>
    /// <param name="value">Candidate value.</param>
    /// <returns>Space separated string or null when unsupported.</returns>
    private static string? JoinTokens(object? value)
    {
        switch (value)
        {
            case null:
                return null;
            case string str:
                return str;
            case double d:
                return d.ToString(CultureInfo.InvariantCulture);
            case float f:
                return f.ToString(CultureInfo.InvariantCulture);
            case long l:
                return l.ToString(CultureInfo.InvariantCulture);
            case int i:
                return i.ToString(CultureInfo.InvariantCulture);
            case bool b:
                return b ? "true" : "false";
            case decimal m:
                return m.ToString(CultureInfo.InvariantCulture);
            case List<object?> list when list.All(IsPrimitiveValue):
            {
                var tokens = list
                    .Select(item => item switch
                    {
                        null => null,
                        string s => s,
                        IFormattable formattable => formattable.ToString(null, CultureInfo.InvariantCulture),
                        bool b => b ? "true" : "false",
                        _ => null,
                    })
                    .Where(s => !string.IsNullOrEmpty(s))
                    .ToList();
                return tokens.Count > 0 ? string.Join(" ", tokens) : null;
            }
            default:
                return value?.ToString();
        }
    }

    /// <summary>
    /// Determine whether a value is representable as an XML attribute.
    /// </summary>
    /// <param name="value">Candidate value.</param>
    /// <returns>True when value is a primitive token.</returns>
    private static bool IsPrimitiveValue(object? value)
    {
        return value is null or string or IFormattable or bool;
    }

    /// <summary>
    /// Format version numbers with a fixed decimal point when applicable.
    /// </summary>
    /// <param name="formattable">Numeric value to format.</param>
    /// <returns>Formatted version string.</returns>
    private static string FormatVersion(IFormattable formattable)
    {
        switch (formattable)
        {
            case double d:
                return d % 1 == 0 ? d.ToString("0.0###############", CultureInfo.InvariantCulture) : d.ToString(CultureInfo.InvariantCulture);
            case float f:
                return f % 1 == 0 ? f.ToString("0.0########", CultureInfo.InvariantCulture) : f.ToString(CultureInfo.InvariantCulture);
            case decimal m:
                return m % 1 == 0 ? m.ToString("0.0############################", CultureInfo.InvariantCulture) : m.ToString(CultureInfo.InvariantCulture);
            case long l:
                return l.ToString("0.0", CultureInfo.InvariantCulture);
            case int i:
                return i.ToString("0.0", CultureInfo.InvariantCulture);
            default:
                return formattable.ToString(null, CultureInfo.InvariantCulture);
        }
    }

    /// <summary>
    /// Determine whether an empty attribute should be preserved in XML.
    /// </summary>
    /// <param name="name">Attribute name.</param>
    /// <returns>True when empty string values must be emitted.</returns>
    private static bool ShouldPreserveEmptyAttribute(string name)
    {
        return name.EndsWith("_attribute", StringComparison.Ordinal)
            || name.EndsWith("_value", StringComparison.Ordinal)
            || PreserveEmptyStringKeys.Contains(name);
    }
}
