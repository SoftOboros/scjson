/**
 * Agent Name: js-converters-tests
 *
 * Part of the scjson project.
 * Developed by Softoboros Technology Inc.
 * Licensed under the BSD 1-Clause License.
 */

const { xmlToJson } = require('../converters.js');

/**
 * Basic test ensuring that script elements are normalised correctly.
 */
test('script text becomes object with content', () => {
  const xml = '<scxml xmlns="http://www.w3.org/2005/07/scxml"><script>foo</script></scxml>';
  const jsonStr = xmlToJson(xml);
  const obj = JSON.parse(jsonStr);
  expect(obj.script).toBeDefined();
  expect(Array.isArray(obj.script)).toBe(true);
  expect(obj.script[0].content[0]).toBe('foo');
});

/**
 * Ensure whitespace token attributes are split into arrays.
 */
test('transition target tokens split correctly', () => {
  const xml = '<scxml xmlns="http://www.w3.org/2005/07/scxml"><state id="s1"><transition target="a b"/></state></scxml>';
  const jsonStr = xmlToJson(xml);
  const obj = JSON.parse(jsonStr);
  const trans = obj.state[0].transition[0];
  expect(Array.isArray(trans.target)).toBe(true);
  expect(trans.target).toEqual(['a', 'b']);
});

/**
 * Ensure nested SCXML documents are placed under a content array.
 */
test('invoke content scxml normalised', () => {
  const xml =
    '<scxml xmlns="http://www.w3.org/2005/07/scxml"><state id="s"><invoke><content><scxml><state id="i"/></scxml></content></invoke></state></scxml>';
  const jsonStr = xmlToJson(xml);
  const obj = JSON.parse(jsonStr);
  const invoke = obj.state[0].invoke[0];
  expect(invoke.content).toBeDefined();
  expect(Array.isArray(invoke.content)).toBe(true);
  expect(invoke.content[0].content[0]).toHaveProperty('state');
});

/**
 * Verify initial attributes map correctly for root and nested states.
 */
test('initial attributes map to correct keys', () => {
  const xml =
    '<scxml xmlns="http://www.w3.org/2005/07/scxml" initial="s0"><state id="s0" initial="s1"><state id="s1"/></state></scxml>';
  const jsonStr = xmlToJson(xml);
  const obj = JSON.parse(jsonStr);
  expect(obj.initial).toEqual(['s0']);
  expect(obj.state[0].initial_attribute).toEqual(['s1']);
});

/**
 * Ensure default attributes for assign and send are present.
 */
test('assign and send defaults are applied', () => {
  const xml =
    '<scxml xmlns="http://www.w3.org/2005/07/scxml"><state id="s"><onentry><assign location="foo" expr="1"/><send event="e"/></onentry></state></scxml>';
  const obj = JSON.parse(xmlToJson(xml));
  const entry = obj.state[0].onentry[0];
  expect(entry.assign[0].type_value).toBe('replacechildren');
  expect(entry.send[0].type_value).toBe('scxml');
  expect(entry.send[0].delay).toBe('0s');
});

/**
 * Ensure empty ``else`` blocks are preserved.
 */
test('empty else becomes object', () => {
  const xml =
    '<scxml xmlns="http://www.w3.org/2005/07/scxml"><state id="s"><onentry><if cond="true"><else/></if></onentry></state></scxml>';
  const obj = JSON.parse(xmlToJson(xml));
  const entry = obj.state[0].onentry[0];
  expect(entry.if_value[0]).toHaveProperty('else_value');
  expect(entry.if_value[0].else_value).toEqual({});
});

/**
 * Preserve empty ``final`` elements nested in other actions.
 */
test('empty final element survives cleanup', () => {
  const xml =
    '<scxml xmlns="http://www.w3.org/2005/07/scxml"><state id="s"><onentry><assign location="x"><scxml><final/></scxml></assign></onentry></state></scxml>';
  const obj = JSON.parse(xmlToJson(xml));
  const assign = obj.state[0].onentry[0].assign[0];
  expect(assign.content[0]).toHaveProperty('final');
  expect(assign.content[0].final).toEqual([{}]);
});
