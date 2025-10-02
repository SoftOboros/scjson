--[[
Agent Name: lua-scjson

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Canonical SCXML ↔ scjson conversion routines mirroring the reference
Python, TypeScript, and Rust implementations.
]]

---
-- Minimal SCXML ↔ scjson conversion utilities.
-- @module scjson

local lom = require('lxp.lom')
local json = require('dkjson')

local scjson = {}

---
-- Determine whether a table behaves like an array (1-indexed sequence).
-- @param value table value to test
-- @return boolean true when the table is an array
local function is_array(value)
    if type(value) ~= 'table' then
        return false
    end
    local n = #value
    if n == 0 then
        return value[1] ~= nil
    end
    for i = 1, n do
        if value[i] == nil then
            return false
        end
    end
    return true
end

local SCXML_ELEMS = {
    scxml = true,
    state = true,
    parallel = true,
    final = true,
    history = true,
    transition = true,
    invoke = true,
    finalize = true,
    datamodel = true,
    data = true,
    onentry = true,
    onexit = true,
    log = true,
    send = true,
    cancel = true,
    raise = true,
    assign = true,
    script = true,
    foreach = true,
    param = true,
    ['if'] = true,
    ['elseif'] = true,
    ['else'] = true,
    content = true,
    donedata = true,
    initial = true,
}

local COLLAPSE_ATTRS = {
    expr = true,
    cond = true,
    event = true,
    target = true,
    delay = true,
    location = true,
    name = true,
    src = true,
    id = true,
}

local ALWAYS_KEEP = {
    else_value = true,
    ['else'] = true,
    final = true,
    onentry = true,
}

local KEEP_EMPTY_STRING_KEYS = {
    expr = true,
    cond = true,
    event = true,
    target = true,
    id = true,
    name = true,
    label = true,
    text = true,
}

local function normalize_key_name(key)
    if not key then
        return nil
    end
    if key:sub(1, 2) == '@_' then
        key = key:sub(3)
    end
    return key
end

---
-- Append a value to a map entry, promoting scalars to arrays when needed.
-- @param map table destination map
-- @param key string map key
-- @param value any value to append
local function append_child(map, key, value)
    local existing = map[key]
    if existing == nil then
        map[key] = { value }
        return
    end
    if type(existing) == 'table' and is_array(existing) then
        table.insert(existing, value)
        return
    end
    map[key] = { existing, value }
end

---
-- Convert an arbitrary XML element into the generic AnyElement structure.
-- @param node table LOM element node
-- @return table representation containing qname/text/attributes/children
local function any_element_to_value(node)
    local result = { qname = node.tag }
    if node.attr and next(node.attr) then
        local attrs = {}
        for k, v in pairs(node.attr) do
            if type(k) == 'string' then
                attrs[k] = v
            end
        end
        result.attributes = attrs
    end
    local text_parts = {}
    local children = {}
    for _, child in ipairs(node) do
        if type(child) == 'table' then
            table.insert(children, any_element_to_value(child))
        elseif type(child) == 'string' and child:match('%S') then
            table.insert(text_parts, child)
        end
    end
    result.text = table.concat(text_parts)
    if #children > 0 then
        result.children = children
    end
    return result
end

---
-- Convert a transition target attribute into an array of tokens.
-- @param value string attribute content
-- @return table array of tokens
local function split_tokens(value)
    local out = {}
    for token in value:gmatch('%S+') do
        table.insert(out, token)
    end
    return out
end

---
-- Convert an XML element node into the canonical scjson map structure.
-- @param node table LOM element node
-- @return table canonical representation
local function element_to_map(node)
    local map = {}
    local attrs = node.attr or {}
    for k, v in pairs(attrs) do
        if type(k) ~= 'string' then
            -- lxp.lom provides numeric indices recording attribute order; ignore them.
        elseif node.tag == 'transition' and k == 'target' then
            map.target = split_tokens(v)
        elseif k == 'initial' then
            if node.tag == 'scxml' then
                map.initial = split_tokens(v)
            else
                map.initial_attribute = split_tokens(v)
            end
        elseif k == 'version' then
            local num = tonumber(v)
            if num then
                map.version = num
            else
                map.version = v
            end
        elseif k == 'datamodel' then
            map.datamodel_attribute = v
        elseif k == 'type' then
            map.type_value = v
        elseif k == 'raise' then
            map.raise_value = v
        elseif k == 'xmlns' or (k:sub(1, 6) == 'xmlns:') then
            -- skip namespace bookkeeping
        else
            map[k] = v
        end
    end

    if node.tag == 'assign' and map.type_value == nil then
        map.type_value = 'replacechildren'
    end
    if node.tag == 'send' then
        if map.type_value == nil then
            map.type_value = 'scxml'
        end
        if map.delay == nil then
            map.delay = '0s'
        end
    end
    if node.tag == 'invoke' then
        if map.type_value == nil then
            map.type_value = 'scxml'
        end
        if map.autoforward == nil then
            map.autoforward = 'false'
        end
    end

    local text_items = {}
    for _, child in ipairs(node) do
        if type(child) == 'table' then
            local tag = child.tag
            if SCXML_ELEMS[tag] then
                local key
                if tag == 'if' then
                    key = 'if_value'
                elseif tag == 'else' then
                    key = 'else_value'
                elseif tag == 'raise' then
                    key = 'raise_value'
                else
                    key = tag
                end
                local child_map = element_to_map(child)
                local target_key
                if tag == 'scxml' and node.tag ~= 'scxml' then
                    target_key = 'content'
                elseif node.tag == 'content' and tag == 'scxml' then
                    target_key = 'content'
                else
                    target_key = key
                end
                if key == 'else_value' or key == 'elseif' then
                    if next(child_map) == nil then
                        setmetatable(child_map, { __jsontype = 'object' })
                    end
                    if map[target_key] == nil then
                        map[target_key] = child_map
                    else
                        local existing = map[target_key]
                        if type(existing) == 'table' and is_array(existing) then
                            table.insert(existing, child_map)
                        else
                            map[target_key] = { existing, child_map }
                        end
                    end
                elseif (node.tag == 'initial' or node.tag == 'history') and tag == 'transition' then
                    map[target_key] = child_map
                else
                    append_child(map, target_key, child_map)
                end
            else
                append_child(map, 'content', any_element_to_value(child))
            end
        elseif type(child) == 'string' and child:match('%S') then
            table.insert(text_items, child)
        end
    end

    for _, text in ipairs(text_items) do
        append_child(map, 'content', text)
    end

    if node.tag == 'scxml' then
        if map.version == nil then
            map.version = 1.0
        end
        if map.datamodel_attribute == nil then
            map.datamodel_attribute = 'null'
        end
    elseif node.tag == 'donedata' then
        local content = map.content
        if type(content) == 'table' and is_array(content) and #content == 1 then
            map.content = content[1]
        end
    end

    if next(map) == nil then
        setmetatable(map, { __jsontype = 'object' })
    end

    return map
end

---
-- Collapse control characters in attribute values recursively.
-- @param value any value to normalise in place
local function collapse_whitespace(value)
    if type(value) == 'table' then
        if is_array(value) then
            for i = 1, #value do
                collapse_whitespace(value[i])
            end
            return
        end
        for k, v in pairs(value) do
            if type(v) == 'string' and (k:sub(-10) == '_attribute' or COLLAPSE_ATTRS[k]) then
                if v:sub(1, 1) == '\n' then
                    value[k] = '\n' .. v:sub(2):gsub('[\n\r\t]', ' ')
                else
                    value[k] = v:gsub('[\n\r\t]', ' ')
                end
            else
                collapse_whitespace(v)
            end
        end
    end
end

---
-- Recursively remove empty containers, strings, and nil values.
-- @param value any value to clean in place
-- @return boolean true when the value should be dropped by its parent
local function remove_empty(value, key)
    if type(value) == 'table' then
        if is_array(value) then
            local i = 1
            while i <= #value do
                if remove_empty(value[i], key) then
                    table.remove(value, i)
                else
                    i = i + 1
                end
            end
            return #value == 0 and not ALWAYS_KEEP[key]
        else
            for k, v in pairs(value) do
                if remove_empty(v, k) then
                    value[k] = nil
                end
            end
            return next(value) == nil and not ALWAYS_KEEP[key]
        end
    elseif value == nil then
        return not ALWAYS_KEEP[key]
    elseif type(value) == 'string' then
        if value == '' or value:match('^%s*$') then
            local base = normalize_key_name(key)
            if base then
                if base:sub(-10) == '_attribute' or base:sub(-6) == '_value' or KEEP_EMPTY_STRING_KEYS[base] then
                    return false
                end
            end
            return not ALWAYS_KEEP[key]
        end
        return false
    end
    return false
end

---
-- Join array or scalar values into a whitespace separated string.
-- @param value any value to flatten
-- @return string|nil joined string or ``nil`` when unsupported
local function join_tokens(value)
    if type(value) == 'table' then
        if is_array(value) then
            local out = {}
            for _, item in ipairs(value) do
                if type(item) == 'string' or type(item) == 'number' then
                    table.insert(out, tostring(item))
                else
                    return nil
                end
            end
            return table.concat(out, ' ')
        else
            return nil
        end
    elseif type(value) == 'string' or type(value) == 'number' then
        return tostring(value)
    end
    return nil
end

---
-- Escape XML attribute content.
-- @param value any value convertible to string
-- @return string escaped attribute value
local function escape_attr(value)
    local s = tostring(value)
    s = s:gsub('&', '&amp;'):gsub('"', '&quot;'):gsub('<', '&lt;'):gsub('>', '&gt;')
    return s
end

---
-- Escape XML text content.
-- @param value any value convertible to string
-- @return string escaped text
local function escape_text(value)
    local s = tostring(value)
    s = s:gsub('&', '&amp;'):gsub('<', '&lt;'):gsub('>', '&gt;')
    return s
end

---
-- Build an element representation from a scjson map.
-- @param name string XML element tag
-- @param map table scjson object
-- @return table element descriptor with ``name``, ``attributes`` and ``children``
local function map_to_element(name, map)
    if name == 'scxml' and type(map) == 'table' and not is_array(map) then
        local content = map.content
        if type(content) == 'table' and is_array(content) and #content == 1 and type(content[1]) == 'table' then
            return map_to_element('scxml', content[1])
        end
    end

    local elem_name = map.qname or name
    local elem = { name = elem_name, attributes = {}, children = {} }

    if name == 'scxml' then
        elem.attributes.xmlns = 'http://www.w3.org/2005/07/scxml'
    elseif not elem_name:find(':', 1, true) and not elem_name:find('{', 1, true) and not SCXML_ELEMS[elem_name] then
        elem.attributes.xmlns = ''
    end

    if type(map.text) == 'string' and map.text ~= '' then
        table.insert(elem.children, map.text)
    end

    if type(map.attributes) == 'table' then
        for k, v in pairs(map.attributes) do
            if type(v) == 'string' or type(v) == 'number' then
                elem.attributes[k] = tostring(v)
            end
        end
    end

    for k, v in pairs(map) do
        if k == 'qname' or k == 'text' or k == 'attributes' then
            -- handled above
        elseif k == 'content' then
            if type(v) == 'table' then
                if is_array(v) then
                    for _, item in ipairs(v) do
                        if type(item) == 'string' then
                            if name == 'script' then
                                table.insert(elem.children, item)
                            elseif name == 'invoke' then
                                local child = { name = 'content', attributes = {}, children = { item } }
                                table.insert(elem.children, child)
                            else
                                table.insert(elem.children, item)
                            end
                        elseif type(item) == 'table' then
                            local child_name
                            if item.state or item.final or item.version or item.datamodel_attribute then
                                child_name = 'scxml'
                            else
                                child_name = 'content'
                            end
                            table.insert(elem.children, map_to_element(child_name, item))
                        end
                    end
                else
                    local child_name
                    if v.state or v.final or v.version or v.datamodel_attribute then
                        child_name = 'scxml'
                    else
                        child_name = 'content'
                    end
                    table.insert(elem.children, map_to_element(child_name, v))
                end
            elseif type(v) == 'string' then
                if name == 'script' then
                    table.insert(elem.children, v)
                else
                    table.insert(elem.children, { name = 'content', attributes = {}, children = { v } })
                end
            end
        elseif k:sub(-10) == '_attribute' then
            local attr_name = k:sub(1, -11)
            local tokens = join_tokens(v)
            if tokens then
                elem.attributes[attr_name] = tokens
            end
        elseif k == 'datamodel_attribute' then
            local tokens = join_tokens(v)
            if tokens then
                elem.attributes.datamodel = tokens
            end
        elseif k == 'type_value' then
            local tokens = join_tokens(v)
            if tokens then
                elem.attributes.type = tokens
            end
        elseif name == 'transition' and k == 'target' then
            local tokens = join_tokens(v)
            if tokens then
                elem.attributes.target = tokens
            end
        elseif (k == 'delay' or k == 'event' or k == 'initial') and join_tokens(v) ~= nil then
            local tokens = join_tokens(v)
            if tokens then
                elem.attributes[k] = tokens
            end
        else
            local actual = k
            if k == 'if_value' then
                actual = 'if'
            elseif k == 'else_value' then
                actual = 'else'
            elseif k == 'raise_value' then
                actual = 'raise'
            end
            local tokens = join_tokens(v)
            if tokens then
                elem.attributes[actual] = tokens
            elseif type(v) == 'table' then
                if is_array(v) then
                    for _, item in ipairs(v) do
                        if type(item) == 'table' then
                            table.insert(elem.children, map_to_element(actual, item))
                        elseif type(item) == 'string' then
                            table.insert(elem.children, map_to_element(actual, { content = { item } }))
                        end
                    end
                else
                    table.insert(elem.children, map_to_element(actual, v))
                end
            elseif type(v) == 'string' then
                table.insert(elem.children, map_to_element(actual, { content = { v } }))
            elseif type(v) == 'number' then
                elem.attributes[actual] = tostring(v)
            end
        end
    end

    return elem
end

---
-- Render an element descriptor into XML.
-- @param element table element descriptor
-- @param indent string current indentation
-- @return string XML fragment
local function render_element(element, indent)
    indent = indent or ''
    local parts = { indent, '<', element.name }
    for k, v in pairs(element.attributes) do
        if v ~= nil then
            parts[#parts + 1] = ' '
            parts[#parts + 1] = k
            parts[#parts + 1] = '="'
            parts[#parts + 1] = escape_attr(v)
            parts[#parts + 1] = '"'
        end
    end
    local children = element.children or {}
    if #children == 0 then
        parts[#parts + 1] = '/>'
        return table.concat(parts)
    end
    parts[#parts + 1] = '>'
    local has_element_child = false
    for _, child in ipairs(children) do
        if type(child) == 'table' then
            has_element_child = true
            parts[#parts + 1] = '\n'
            parts[#parts + 1] = render_element(child, indent .. '  ')
        else
            if has_element_child then
                parts[#parts + 1] = '\n'
                parts[#parts + 1] = indent .. '  '
            end
            parts[#parts + 1] = escape_text(child)
        end
    end
    if has_element_child then
        parts[#parts + 1] = '\n'
        parts[#parts + 1] = indent
    end
    parts[#parts + 1] = '</'
    parts[#parts + 1] = element.name
    parts[#parts + 1] = '>'
    return table.concat(parts)
end

---
-- Convert an SCXML string to scjson.
-- @param xml_str string XML document
-- @param omit_empty boolean remove empty values when true
-- @return string scjson representation
function scjson.xml_to_json(xml_str, omit_empty)
    local ok, root = pcall(lom.parse, xml_str)
    if not ok then
        error(root)
    end
    if type(root) ~= 'table' or root.tag ~= 'scxml' then
        error('Unsupported document: root element must be <scxml>')
    end
    local data = element_to_map(root)
    collapse_whitespace(data)
    if omit_empty == nil then
        omit_empty = true
    end
    if omit_empty then
        remove_empty(data, nil)
    end
    local encoded, err = json.encode(data, { indent = '  ' })
    if not encoded then
        error(err)
    end
    return encoded
end

---
-- Convert a scjson string to an SCXML string.
-- @param json_str string scjson document
-- @param omit_empty boolean remove empty values prior to serialisation
-- @return string XML representation
function scjson.json_to_xml(json_str, omit_empty)
    if omit_empty == nil then
        omit_empty = true
    end
    local obj, pos, err = json.decode(json_str, 1, nil)
    if err then
        error(err)
    end
    if type(obj) ~= 'table' or is_array(obj) then
        error('Expected root object for scjson document')
    end
    if omit_empty then
        remove_empty(obj, nil)
    end
    local element = map_to_element('scxml', obj)
    local xml = '<?xml version="1.0" encoding="UTF-8"?>\n' .. render_element(element, '')
    return xml
end

return scjson
