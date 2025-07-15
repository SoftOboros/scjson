--[[
Agent Name: lua-cli-tests

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.
]]

describe('cli', function()
    package.path = 'lua/?.lua;' .. package.path
    local scjson = require('scjson')

    it('converts xml to json', function()
        local xml = '<scxml xmlns="http://www.w3.org/2005/07/scxml"/>'
        local json = scjson.xml_to_json(xml)
        assert.is.truthy(json:find('"version"'))
    end)

    it('converts json to xml', function()
        local json = '{"version":1.0}'
        local xml = scjson.json_to_xml(json)
        assert.is.truthy(xml:find('scxml'))
    end)
end)
