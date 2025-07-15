--[[
Agent Name: lua-scjson

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.
]]

---
-- Minimal SCXML ↔ scjson conversion utilities.
-- @module scjson

local lxp = require('lxp.lom')
local json = require('dkjson')

local scjson = {}

--- Recursively remove nil, empty strings, and empty tables.
-- @param value any value to clean
-- @return any sanitized value or nil
local function remove_empty(value)
    if type(value) == 'table' then
        local is_array = #value > 0
        if is_array then
            local arr = {}
            for _, v in ipairs(value) do
                local r = remove_empty(v)
                if r ~= nil then
                    table.insert(arr, r)
                end
            end
            if #arr == 0 then
                return nil
            end
            return arr
        else
            local obj = {}
            for k, v in pairs(value) do
                local r = remove_empty(v)
                if r ~= nil then
                    obj[k] = r
                end
            end
            if next(obj) == nil then
                return nil
            end
            return obj
        end
    elseif value == nil or value == '' then
        return nil
    else
        return value
    end
end

--- Convert an lxp element to a Lua table.
-- @param node table parsed lxp node
-- @return table equivalent Lua table
local function elem_to_table(node)
    local t = {}
    if node.attr then
        for k, v in pairs(node.attr) do
            if type(k) == 'string' then
                t[k] = v
            end
        end
    end
    for _, child in ipairs(node) do
        if type(child) == 'table' then
            local val = elem_to_table(child)
            if t[child.tag] then
                if type(t[child.tag]) == 'table' and t[child.tag][1] then
                    table.insert(t[child.tag], val)
                else
                    t[child.tag] = { t[child.tag], val }
                end
            else
                t[child.tag] = val
            end
        elseif type(child) == 'string' then
            local text = child:match('^%s*(.-)%s*$')
            if text ~= '' then
                if t.text then
                    t.text = t.text .. text
                else
                    t.text = text
                end
            end
        end
    end
    return t
end

--- Convert an SCXML string to a scjson string.
-- @param xml_str string XML document
-- @param omit_empty boolean remove empty values when true
-- @return string scjson representation
function scjson.xml_to_json(xml_str, omit_empty)
    local root = lxp.parse(xml_str)
    local obj = elem_to_table(root)
    obj.xmlns = nil
    if obj.datamodel then
        obj.datamodel_attribute = obj.datamodel
        obj.datamodel = nil
    end
    if not obj.version then
        obj.version = 1.0
    end
    if not obj.datamodel_attribute then
        obj.datamodel_attribute = 'null'
    end
    if omit_empty == nil then
        omit_empty = true
    end
    if omit_empty then
        obj = remove_empty(obj) or {}
    end
    return json.encode(obj, { indent = true })
end

--- Convert a scjson string to an SCXML string.
-- @param json_str string scjson document
-- @return string XML representation
function scjson.json_to_xml(json_str)
    local obj, pos, err = json.decode(json_str, 1, nil)
    if err then error(err) end
    if obj.datamodel_attribute then
        obj.datamodel = obj.datamodel_attribute
        obj.datamodel_attribute = nil
    end
    obj.xmlns = obj.xmlns or 'http://www.w3.org/2005/07/scxml'
    local function build(tag, tbl, indent)
        indent = indent or ''
        local attrs = {}
        local children = {}
        local text = tbl.text
        for k, v in pairs(tbl) do
            if k ~= 'text' then
                if type(v) == 'table' then
                    children[k] = v
                else
                    table.insert(attrs, string.format(' %s="%s"', k, tostring(v)))
                end
            end
        end
        local parts = { indent, '<', tag, table.concat(attrs), '>' }
        if text then
            table.insert(parts, text)
        end
        for k, v in pairs(children) do
            if v[1] then
                for _, item in ipairs(v) do
                    table.insert(parts, '\n')
                    table.insert(parts, build(k, item, indent .. '  '))
                end
            else
                table.insert(parts, '\n')
                table.insert(parts, build(k, v, indent .. '  '))
            end
        end
        if next(children) then
            table.insert(parts, '\n' .. indent)
        end
        table.insert(parts, '</' .. tag .. '>')
        return table.concat(parts)
    end
    return build('scxml', obj, '')
end

return scjson
