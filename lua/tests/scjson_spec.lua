--[[
Agent Name: lua-cli-tests

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.
]]

describe('cli', function()
    package.path = 'lua/?.lua;' .. package.path
    local scjson = require('scjson')

    it('converts xml to json with defaults', function()
        local xml = '<scxml xmlns="http://www.w3.org/2005/07/scxml"/>'
        local j = scjson.xml_to_json(xml)
        local data = require("dkjson").decode(j)
        assert.are.equal(1.0, data.version)
        assert.are.equal('null', data.datamodel_attribute)
    end)

    it('roundtrips json and xml', function()
        local obj = { version = 1.0, datamodel_attribute = 'null', state = { id = 'a' } }
        local json_str = require('dkjson').encode(obj)
        local xml = scjson.json_to_xml(json_str)
        assert.is.truthy(xml:find('<scxml'))
        local back = scjson.xml_to_json(xml)
        assert.is.truthy(back:find('"state"'))
    end)
end)
