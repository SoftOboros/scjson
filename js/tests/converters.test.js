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
