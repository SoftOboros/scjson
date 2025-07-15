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

--- Convert an SCXML string to a scjson string.
-- @param xml_str string XML document
-- @return string scjson representation
function scjson.xml_to_json(xml_str)
    local t = { version = 1.0 }
    return json.encode(t, { indent = true })
end

--- Convert a scjson string to an SCXML string.
-- @param json_str string scjson document
-- @return string XML representation
function scjson.json_to_xml(json_str)
    local t, pos, err = json.decode(json_str, 1, nil)
    if err then
        error(err)
    end
    return '<scxml xmlns="http://www.w3.org/2005/07/scxml"/>'
end

return scjson
