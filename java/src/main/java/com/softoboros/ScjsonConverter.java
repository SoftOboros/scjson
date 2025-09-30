/**
 * Agent Name: scjson-converter
 *
 * Part of the scjson project.
 * Developed by Softoboros Technology Inc.
 * Licensed under the BSD 1-Clause License.
 */
package com.softobros;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.StringReader;
import java.io.StringWriter;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import javax.xml.XMLConstants;
import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.transform.OutputKeys;
import javax.xml.transform.Transformer;
import javax.xml.transform.TransformerFactory;
import javax.xml.transform.dom.DOMSource;
import javax.xml.transform.stream.StreamResult;
import org.w3c.dom.Attr;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.NamedNodeMap;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;
import org.xml.sax.InputSource;

/**
 * Utility class that performs SCXML <-> SCJSON conversions.
 */
public final class ScjsonConverter {

    private static final ObjectMapper MAPPER = new ObjectMapper();

    private static final Set<String> COLLAPSE_ATTRS = Set.of(
            "expr",
            "cond",
            "event",
            "target",
            "delay",
            "location",
            "name",
            "src",
            "id"
    );

    private static final Set<String> ALWAYS_KEEP = Set.of(
            "else_value",
            "onentry",
            "final",
            "initial"
    );

    private static final Set<String> SCXML_ELEMENTS = new LinkedHashSet<>(List.of(
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
            "initial"
    ));

    private ScjsonConverter() {
    }

    /**
     * Convert an SCXML string to canonical SCJSON.
     *
     * @param xml source XML string
     * @return formatted SCJSON string
     */
    public static String xmlToJson(String xml) {
        try {
            DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
            configureFactory(dbf);
            DocumentBuilder builder = dbf.newDocumentBuilder();
            String sanitized = stripBom(xml);
            Document doc = builder.parse(new InputSource(new StringReader(sanitized)));
            Element root = doc.getDocumentElement();
            if (root == null || !"scxml".equals(localName(root))) {
                throw new ScjsonConversionException("Expected <scxml> root element");
            }
            Map<String, Object> map = elementToMap(root);
            collapseWhitespace(map);
            pruneEmpty(map);
            return MAPPER.writerWithDefaultPrettyPrinter().writeValueAsString(map);
        } catch (ScjsonConversionException ex) {
            throw ex;
        } catch (Exception ex) {
            throw new ScjsonConversionException("Failed to convert XML to JSON", ex);
        }
    }

    /**
     * Convert an SCJSON string to SCXML.
     *
     * @param json canonical SCJSON string
     * @return XML document string
     */
    public static String jsonToXml(String json) {
        try {
            Map<String, Object> data = MAPPER.readValue(
                    json,
                    new TypeReference<LinkedHashMap<String, Object>>() {
                    }
            );
            pruneEmpty(data);
            DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
            configureFactory(dbf);
            DocumentBuilder builder = dbf.newDocumentBuilder();
            Document doc = builder.newDocument();
            Element root = mapToElement(doc, "scxml", data);
            doc.appendChild(root);
            return writeDocument(doc);
        } catch (ScjsonConversionException ex) {
            throw ex;
        } catch (Exception ex) {
            throw new ScjsonConversionException("Failed to convert JSON to XML", ex);
        }
    }

    private static String stripBom(String value) {
        if (value == null || value.isEmpty()) {
            return value;
        }
        return value.charAt(0) == '\ufeff' ? value.substring(1) : value;
    }

    private static void configureFactory(DocumentBuilderFactory factory) {
        factory.setNamespaceAware(true);
        try {
            factory.setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true);
        } catch (Exception ignored) {
            // Feature not supported on all runtimes.
        }
        try {
            factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
        } catch (Exception ignored) {
            // Optional hardening feature.
        }
    }

    private static String localName(Node node) {
        String name = node.getLocalName();
        return name != null ? name : node.getNodeName();
    }

    private static Map<String, Object> elementToMap(Element element) {
        LinkedHashMap<String, Object> result = new LinkedHashMap<>();
        String name = localName(element);

        NamedNodeMap attrs = element.getAttributes();
        for (int i = 0; i < attrs.getLength(); i++) {
            Node node = attrs.item(i);
            if (!(node instanceof Attr attr)) {
                continue;
            }
            String ns = attr.getNamespaceURI();
            if (Objects.equals(ns, XMLConstants.XMLNS_ATTRIBUTE_NS_URI)) {
                continue;
            }
            String attrName = attr.getName();
            String attrLocal = attr.getLocalName() != null ? attr.getLocalName() : attrName;
            String value = attr.getValue();
            switch (attrLocal) {
                case "target":
                    if ("transition".equals(name)) {
                        result.put("target", splitTokens(value));
                        break;
                    }
                    result.put(attrName, value);
                    break;
                case "initial":
                    List<String> tokens = splitTokens(value);
                    if ("scxml".equals(name)) {
                        result.put("initial", tokens);
                    } else {
                        result.put("initial_attribute", tokens);
                    }
                    break;
                case "version":
                    try {
                        double parsed = Double.parseDouble(value);
                        result.put("version", parsed);
                    } catch (NumberFormatException ex) {
                        result.put("version", value);
                    }
                    break;
                case "datamodel":
                    result.put("datamodel_attribute", value);
                    break;
                case "type":
                    result.put("type_value", value);
                    break;
                case "raise":
                    result.put("raise_value", value);
                    break;
                default:
                    result.put(attrName, value);
                    break;
            }
        }

        if ("assign".equals(name) && !result.containsKey("type_value")) {
            result.put("type_value", "replacechildren");
        }
        if ("send".equals(name)) {
            result.putIfAbsent("type_value", "scxml");
            result.putIfAbsent("delay", "0s");
        }
        if ("invoke".equals(name)) {
            result.putIfAbsent("type_value", "scxml");
            result.putIfAbsent("autoforward", "false");
        }

        List<String> textItems = new ArrayList<>();
        NodeList children = element.getChildNodes();
        for (int i = 0; i < children.getLength(); i++) {
            Node child = children.item(i);
            if (child instanceof Element childElement) {
                String childName = localName(childElement);
                if (SCXML_ELEMENTS.contains(childName)) {
                    Map<String, Object> converted = elementToMap(childElement);
                    String mappedName = switch (childName) {
                        case "if" -> "if_value";
                        case "else" -> "else_value";
                        case "raise" -> "raise_value";
                        default -> childName;
                    };
                    String targetKey;
                    if ("scxml".equals(childName) && !"scxml".equals(name)) {
                        targetKey = "content";
                    } else if ("content".equals(name) && "scxml".equals(childName)) {
                        targetKey = "content";
                    } else {
                        targetKey = mappedName;
                    }
                    if (("initial".equals(name) || "history".equals(name)) && "transition".equals(childName)) {
                        result.put(targetKey, converted);
                    } else if ("else_value".equals(targetKey)) {
                        result.put(targetKey, converted.isEmpty() ? new LinkedHashMap<>() : converted);
                    } else if ("elseif".equals(childName)) {
                        result.put(targetKey, converted);
                    } else {
                        appendChild(result, targetKey, converted);
                    }
                } else {
                    appendChild(result, "content", anyElementToValue(childElement));
                }
            } else if (child.getNodeType() == Node.TEXT_NODE || child.getNodeType() == Node.CDATA_SECTION_NODE) {
                String text = child.getTextContent();
                if (text != null && !text.trim().isEmpty()) {
                    textItems.add(text);
                }
            }
        }
        for (String text : textItems) {
            appendChild(result, "content", text);
        }

        if ("scxml".equals(name)) {
            result.putIfAbsent("version", 1.0d);
            result.putIfAbsent("datamodel_attribute", "null");
        } else if ("donedata".equals(name)) {
            Object content = result.get("content");
            if (content instanceof List<?> list && list.size() == 1) {
                result.put("content", list.get(0));
            }
        }
        return result;
    }

    private static Map<String, Object> anyElementToValue(Element element) {
        LinkedHashMap<String, Object> map = new LinkedHashMap<>();
        map.put("qname", element.getTagName());
        String text = element.getTextContent();
        map.put("text", text == null ? "" : text);
        NamedNodeMap attrs = element.getAttributes();
        if (attrs != null && attrs.getLength() > 0) {
            LinkedHashMap<String, Object> attrMap = new LinkedHashMap<>();
            for (int i = 0; i < attrs.getLength(); i++) {
                Node node = attrs.item(i);
                if (node instanceof Attr attr) {
                    String name = attr.getName();
                    if ("xmlns".equals(name) || name.startsWith("xmlns:")) {
                        continue;
                    }
                    attrMap.put(name, attr.getValue());
                }
            }
            if (!attrMap.isEmpty()) {
                map.put("attributes", attrMap);
            }
        }
        NodeList children = element.getChildNodes();
        List<Map<String, Object>> childList = new ArrayList<>();
        for (int i = 0; i < children.getLength(); i++) {
            Node child = children.item(i);
            if (child instanceof Element childElement) {
                childList.add(anyElementToValue(childElement));
            }
        }
        if (!childList.isEmpty()) {
            map.put("children", childList);
        }
        return map;
    }

    private static void appendChild(Map<String, Object> map, String key, Object value) {
        Object existing = map.get(key);
        if (existing == null) {
            List<Object> list = new ArrayList<>();
            list.add(value);
            map.put(key, list);
            return;
        }
        if (existing instanceof List<?>) {
            @SuppressWarnings("unchecked")
            List<Object> list = (List<Object>) existing;
            list.add(value);
            return;
        }
        List<Object> list = new ArrayList<>();
        list.add(existing);
        list.add(value);
        map.put(key, list);
    }

    private static void collapseWhitespace(Object value) {
        if (value instanceof List<?>) {
            for (Object item : (List<?>) value) {
                collapseWhitespace(item);
            }
            return;
        }
        if (value instanceof Map<?, ?> rawMap) {
            @SuppressWarnings("unchecked")
            Map<String, Object> map = (Map<String, Object>) rawMap;
            for (Map.Entry<String, Object> entry : map.entrySet()) {
                Object item = entry.getValue();
                String key = entry.getKey();
                if (item instanceof String str && (key.endsWith("_attribute") || COLLAPSE_ATTRS.contains(key))) {
                    entry.setValue(str.replace('\n', ' ').replace('\r', ' ').replace('\t', ' '));
                } else {
                    collapseWhitespace(item);
                }
            }
        }
    }

    private static boolean pruneEmpty(Object value, String key) {
        if (value instanceof Map<?, ?> rawMap) {
            @SuppressWarnings("unchecked")
            Map<String, Object> map = (Map<String, Object>) rawMap;
            List<String> keys = new ArrayList<>(map.keySet());
            for (String childKey : keys) {
                Object item = map.get(childKey);
                if (pruneEmpty(item, childKey) && !ALWAYS_KEEP.contains(childKey)) {
                    map.remove(childKey);
                }
            }
            return map.isEmpty() && (key == null || !ALWAYS_KEEP.contains(key));
        }
        if (value instanceof List<?> rawList) {
            @SuppressWarnings("unchecked")
            List<Object> list = (List<Object>) rawList;
            if (!ALWAYS_KEEP.contains(key)) {
                list.removeIf(item -> pruneEmpty(item, key));
            } else {
                for (Object item : list) {
                    pruneEmpty(item, key);
                }
            }
            return list.isEmpty() && !ALWAYS_KEEP.contains(key);
        }
        if (value == null) {
            return true;
        }
        if (value instanceof String) {
            return false;
        }
        return false;
    }

    private static boolean pruneEmpty(Object value) {
        return pruneEmpty(value, null);
    }

    private static void pruneEmpty(Map<String, Object> map) {
        pruneEmpty((Object) map);
    }

    private static Element mapToElement(Document doc, String name, Map<String, Object> map) {
        if ("scxml".equals(name) && map.size() == 1 && map.containsKey("content")) {
            Object content = map.get("content");
            if (content instanceof List<?> list && list.size() == 1 && list.get(0) instanceof Map<?, ?> nested) {
                @SuppressWarnings("unchecked")
                Map<String, Object> nestedMap = (Map<String, Object>) nested;
                return mapToElement(doc, "scxml", nestedMap);
            }
        }
        String elementName = name;
        Object qname = map.get("qname");
        if (qname instanceof String str && !str.isEmpty()) {
            elementName = str;
        }
        Element element = doc.createElement(elementName);
        if ("scxml".equals(name)) {
            element.setAttribute("xmlns", "http://www.w3.org/2005/07/scxml");
        } else if (!elementName.contains(":" ) && !elementName.contains("{") && !SCXML_ELEMENTS.contains(elementName)) {
            element.setAttribute("xmlns", "");
        }
        Object textValue = map.get("text");
        if (textValue instanceof String str && !str.isEmpty()) {
            element.appendChild(doc.createTextNode(str));
        }
        Object attrValue = map.get("attributes");
        if (attrValue instanceof Map<?, ?> rawAttrs) {
            @SuppressWarnings("unchecked")
            Map<String, Object> attrs = (Map<String, Object>) rawAttrs;
            for (Map.Entry<String, Object> entry : attrs.entrySet()) {
                String key = entry.getKey();
                Object val = entry.getValue();
                if (val != null) {
                    element.setAttribute(key, val.toString());
                }
            }
        }

        for (Map.Entry<String, Object> entry : map.entrySet()) {
            String key = entry.getKey();
            if ("qname".equals(key) || "text".equals(key) || "attributes".equals(key)) {
                continue;
            }
            Object value = entry.getValue();
            if ("content".equals(key)) {
                appendContent(doc, element, name, value);
                continue;
            }
            if (key.endsWith("_attribute")) {
                String attr = key.substring(0, key.length() - "_attribute".length());
                String joined = joinTokens(value);
                if (joined != null) {
                    element.setAttribute(attr, joined);
                }
                continue;
            }
            if ("datamodel_attribute".equals(key)) {
                String joined = joinTokens(value);
                if (joined != null) {
                    element.setAttribute("datamodel", joined);
                }
                continue;
            }
            if ("type_value".equals(key)) {
                String joined = joinTokens(value);
                if (joined != null) {
                    element.setAttribute("type", joined);
                }
                continue;
            }
            if ("transition".equals(name) && "target".equals(key)) {
                String joined = joinTokens(value);
                if (joined != null) {
                    element.setAttribute("target", joined);
                }
                continue;
            }
            if ("delay".equals(key) || "event".equals(key)) {
                String joined = joinTokens(value);
                if (joined != null) {
                    element.setAttribute(key, joined);
                }
                continue;
            }
            String joined = joinTokens(value);
            if (joined != null) {
                element.setAttribute(key, joined);
                continue;
            }
            if (value instanceof List<?>) {
                handleList(doc, element, key, (List<?>) value);
                continue;
            }
            if (value instanceof Map<?, ?> rawChild) {
                @SuppressWarnings("unchecked")
                Map<String, Object> child = (Map<String, Object>) rawChild;
                String childName = mapStructuralKey(key);
                Element childElement = mapToElement(doc, childName, child);
                element.appendChild(childElement);
                continue;
            }
            if (value instanceof String str) {
                if ("version".equals(key)) {
                    element.setAttribute("version", str);
                } else if (!str.isEmpty()) {
                    Element child = mapToElement(doc, mapStructuralKey(key), new LinkedHashMap<>());
                    child.appendChild(doc.createTextNode(str));
                    element.appendChild(child);
                }
                continue;
            }
            if (value instanceof Number num) {
                if ("version".equals(key)) {
                    element.setAttribute("version", num.toString());
                }
            }
        }
        return element;
    }

    private static void handleList(Document doc, Element parent, String key, List<?> list) {
        String childName = mapStructuralKey(key);
        for (Object item : list) {
            if (item instanceof Map<?, ?> rawChild) {
                @SuppressWarnings("unchecked")
                Map<String, Object> child = (Map<String, Object>) rawChild;
                Element childElement = mapToElement(doc, childName, child);
                parent.appendChild(childElement);
            } else if (item instanceof String str) {
                if (!str.isEmpty()) {
                    Element childElement = mapToElement(doc, childName, new LinkedHashMap<>());
                    childElement.appendChild(doc.createTextNode(str));
                    parent.appendChild(childElement);
                } else {
                    parent.appendChild(mapToElement(doc, childName, new LinkedHashMap<>()));
                }
            } else if (item instanceof Number num) {
                Element childElement = mapToElement(doc, childName, new LinkedHashMap<>());
                childElement.appendChild(doc.createTextNode(num.toString()));
                parent.appendChild(childElement);
            }
        }
    }

    private static void appendContent(Document doc, Element parent, String parentName, Object value) {
        if (value instanceof List<?>) {
            for (Object item : (List<?>) value) {
                appendContent(doc, parent, parentName, item);
            }
            return;
        }
        if (value instanceof Map<?, ?> rawChild) {
            @SuppressWarnings("unchecked")
            Map<String, Object> child = (Map<String, Object>) rawChild;
            String childName = isLikelyScxmlObject(child) ? "scxml" : "content";
            Element childElement = mapToElement(doc, childName, child);
            parent.appendChild(childElement);
            return;
        }
        if (value instanceof String str) {
            if ("script".equals(parentName)) {
                parent.appendChild(doc.createTextNode(str));
            } else if ("invoke".equals(parentName)) {
                Element content = doc.createElement("content");
                if (!str.isEmpty()) {
                    content.appendChild(doc.createTextNode(str));
                }
                parent.appendChild(content);
            } else if (str.isEmpty()) {
                parent.appendChild(doc.createTextNode(str));
            } else {
                parent.appendChild(doc.createTextNode(str));
            }
            return;
        }
        if (value instanceof Number num) {
            parent.appendChild(doc.createTextNode(num.toString()));
        }
    }

    private static String mapStructuralKey(String key) {
        return switch (key) {
            case "if_value" -> "if";
            case "else_value" -> "else";
            case "raise_value" -> "raise";
            default -> key;
        };
    }

    private static boolean isLikelyScxmlObject(Map<String, Object> map) {
        for (String candidate : List.of("state", "parallel", "final", "history")) {
            if (map.containsKey(candidate)) {
                return true;
            }
        }
        return map.containsKey("version") || map.containsKey("datamodel_attribute");
    }

    private static String joinTokens(Object value) {
        if (value instanceof String str) {
            return str;
        }
        if (value instanceof Number num) {
            return num.toString();
        }
        if (value instanceof List<?> list) {
            List<String> parts = new ArrayList<>();
            for (Object item : list) {
                if (item instanceof String str) {
                    parts.add(str);
                } else if (item instanceof Number num) {
                    parts.add(num.toString());
                } else {
                    return null;
                }
            }
            return String.join(" ", parts);
        }
        return null;
    }

    private static List<String> splitTokens(String value) {
        String trimmed = value.trim();
        if (trimmed.isEmpty()) {
            return List.of();
        }
        String[] parts = trimmed.split("\\s+");
        List<String> tokens = new ArrayList<>(parts.length);
        for (String part : parts) {
            tokens.add(part);
        }
        return tokens;
    }

    private static String writeDocument(Document doc) throws Exception {
        TransformerFactory factory = TransformerFactory.newInstance();
        Transformer transformer = factory.newTransformer();
        transformer.setOutputProperty(OutputKeys.OMIT_XML_DECLARATION, "no");
        transformer.setOutputProperty(OutputKeys.ENCODING, "UTF-8");
        transformer.setOutputProperty(OutputKeys.INDENT, "no");
        StringWriter buffer = new StringWriter();
        transformer.transform(new DOMSource(doc), new StreamResult(buffer));
        return buffer.toString();
    }
}
