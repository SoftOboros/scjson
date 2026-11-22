/** Exercise the public converters on original Alex Z charts and ordered payloads. */
const fs = require('fs');
const path = require('path');
const { xmlToJson, jsonToXml } = require('../dist/converters');

const ns = 'http://www.w3.org/2005/07/scxml';
const chart = actions => `<scxml xmlns="${ns}"><state id="s"><onentry>${actions}</onentry></state></scxml>`;
function read(xml) {
  const output = xmlToJson(xml);
  expect(output.errors).toBeNull();
  return JSON.parse(output.result);
}
function write(doc) {
  const output = jsonToXml(JSON.stringify(doc));
  expect(output.errors).toBeNull();
  expect(output.result).not.toContain('execution_order');
  expect(output.result).not.toContain('region_order');
  expect(output.result).not.toContain('state_order');
  return output.result;
}

const mixedRegions = `<scxml xmlns="${ns}"><parallel id="p">
  <parallel id="first"><state id="leaf"/></parallel><onentry><log/></onentry>
  <state id="second"/><state id="third"/></parallel></scxml>`;

test('raw SCJSON action spellings cannot be silently dropped', () => {
  for (const tag of ['raise', 'if', 'else']) {
    for (const key of [tag, tag + 'Value']) {
      const doc = read(chart('<if cond="false"><else/><raise event="go"/></if>'));
      const block = doc.state[0].onentry[0].if_value[0];
      block[key] = block[tag + '_value'] || [];
      delete block[tag + '_value'];
      const output = jsonToXml(JSON.stringify(doc));
      expect(output.valid).toBe(false);
      expect(output.result).toBe('');
      expect(output.errors[0].message).toContain(tag + '_value');
    }
  }
});

test('preserves implicit and explicit initial targets, anonymous children and legacy grouping', () => {
  const doc = read(`<scxml xmlns="${ns}" initial="owner"><final/><state id="owner">
    <initial><transition target="p"/></initial><parallel id="p"><state id="leaf"/></parallel>
    <final/><state id="s"/></state></scxml>`);
  expect(doc.state_order).toEqual(['final', 'state']);
  expect(doc.state[0].state_order).toEqual(['parallel', 'final', 'state']);
  const round = read(write(doc));
  expect(round.state_order).toEqual(doc.state_order);
  expect(round.initial).toEqual(['owner']);
  expect(round.state[0].initial).toEqual(doc.state[0].initial);
  expect(round.state[0].state_order).toEqual(doc.state[0].state_order);
  delete doc.state_order;
  delete doc.state[0].state_order;
  const legacy = read(write(doc));
  expect(legacy.state_order).toEqual(['state', 'final']);
  expect(legacy.state[0].state_order).toEqual(['state', 'parallel', 'final']);
});

test('validates structural lists at their owner, including an invoked chart', () => {
  const nested = read(`<scxml xmlns="${ns}"><state><invoke><content>
    <scxml><final/><state/></scxml></content></invoke></state></scxml>`);
  const child = nested.state[0].invoke[0].content[0].content[0];
  expect(child.state_order).toEqual(['final', 'state']);
  expect(read(write(nested)).state[0].invoke[0].content[0].content[0].state_order).toEqual(child.state_order);
  for (const value of [null, 'state', ['state'], ['state', 'state'], ['history', 'final']]) {
    child.state_order = value;
    expect(jsonToXml(JSON.stringify(nested)).valid).toBe(false);
  }
  for (const wrong of [{parallel: [{state_order: []}]}, {state: [{region_order: []}]}]) {
    expect(jsonToXml(JSON.stringify(wrong)).valid).toBe(false);
  }
});

test('restores mixed parallel regions, same-kind occurrences, and legacy grouping', () => {
  const doc = read(mixedRegions);
  const p = doc.parallel[0];
  expect(p.region_order).toEqual(['parallel', 'state', 'state']);
  expect(read(write(doc)).parallel[0].region_order).toEqual(p.region_order);
  p.region_order = ['state', 'parallel', 'state'];
  const xml = write(doc);
  expect(xml.indexOf('id="second"')).toBeLessThan(xml.indexOf('id="first"'));
  expect(xml.indexOf('id="first"')).toBeLessThan(xml.indexOf('id="third"'));
  delete p.region_order;
  doc.parallel[0] = {parallel: p.parallel, ...p};
  expect(read(write(doc)).parallel[0].region_order).toEqual(['state', 'state', 'parallel']);
});

test.each([null, 'state', ['history'], ['state'], ['parallel', 'parallel', 'state']])(
  'rejects malformed region order %j', order => {
    const doc = read(mixedRegions);
    doc.parallel[0].region_order = order;
    expect(jsonToXml(JSON.stringify(doc))).toMatchObject({valid: false, result: ''});
  });

test('validates ownership and includes region order inside an invoked document', () => {
  const doc = read(mixedRegions);
  doc.parallel[0].state[0].region_order = [];
  expect(jsonToXml(JSON.stringify(doc)).valid).toBe(false);
  const nested = read(`<scxml xmlns="${ns}"><state id="s"><invoke><content>${mixedRegions}</content></invoke></state></scxml>`);
  const child = nested.state[0].invoke[0].content[0].content[0];
  expect(child.parallel[0].region_order).toEqual(['parallel', 'state', 'state']);
  expect(read(write(nested))).toEqual(nested);
});

test('anonymous regions and foreign namesakes retain their identity', () => {
  const doc = read(`<scxml xmlns="${ns}"><parallel><parallel/><state/>
    <f:state xmlns:f="urn:test" id="foreign"/><parallel xmlns="" id="opaque"/>
  </parallel></scxml>`);
  const p = doc.parallel[0];
  expect(p.region_order).toEqual(['parallel', 'state']);
  expect(p.other_element.map(item => item.qname)).toEqual(['{urn:test}state', 'parallel']);
  expect(read(write(doc)).parallel).toEqual(doc.parallel);
});
function orders(obj) {
  if (!obj || typeof obj !== 'object') return [];
  return [ ...(obj.execution_order ? [obj.execution_order] : []), ...Object.values(obj).flatMap(orders) ];
}

const corpus = path.join(__dirname, '../../tutorial/Tests');
const corpusTest = fs.existsSync(corpus) ? test : test.skip;
corpusTest.each(['ecma', 'python'].flatMap(dialect =>
  [153, 457, 459].map(number => [dialect, number])))('%s %s retains every action sequence', (dialect, number) => {
  const suite = number === 153 ? 'Mandatory' : 'Optional';
  const xml = fs.readFileSync(path.join(corpus, dialect, 'W3C', suite, 'Auto', `test${number}.scxml`), 'utf8');
  const model = read(xml);
  expect(orders(model).length).toBeGreaterThan(0);
  expect(orders(read(write(model)))).toEqual(orders(model));
});

test('different programs with the same grouped assignments remain distinguishable', () => {
  const assignment = '<assign location="x" expr="1"/>';
  const one = read(chart(assignment + '<log/>' + assignment));
  const two = read(chart(assignment + assignment + '<log/>'));
  expect(orders(one)).toEqual([['assign', 'log', 'assign']]);
  expect(orders(two)).toEqual([['assign', 'assign', 'log']]);
  expect(orders(read(write(one)))).toEqual(orders(one));
  delete one.state[0].onentry[0].execution_order;
  expect(write(one)).toContain('location="x"');
});

test('condition markers and namespace-qualified extension payloads round-trip', () => {
  const model = read(chart('<if cond="true"><log/><elseif cond="false"/><elseif cond="true"/><else/><log/></if>'
    + '<a:log xmlns:a="urn:ext" xmlns:b="urn:attr" b:x="1">pre<a:n/>tail</a:log><log/>'));
  const entry = model.state[0].onentry[0];
  expect(entry.execution_order).toEqual(['if', '{urn:ext}log', 'log']);
  expect(entry.if_value[0].execution_order).toEqual(['log', 'elseif', 'elseif', 'else', 'log']);
  expect(entry.other_element[0].attributes).toEqual({ '{urn:attr}x': '1' });
  const round = read(write(model)).state[0].onentry[0];
  expect(round.other_element).toEqual(entry.other_element);
  expect(round.if_value).toEqual(entry.if_value);
});

test.each([null, [], ['log'], ['log', 'log'], ['log', 'bogus'], 'log'])(
  'rejects malformed order %j on SCJSON intake', order => {
    const doc = read(chart('<log/><raise event="go"/>'));
    doc.state[0].onentry[0].execution_order = order;
    expect(jsonToXml(JSON.stringify(doc))).toMatchObject({ valid: false, result: '' });
  });

test('rejects misplaced and repeated conditional markers', () => {
  for (const body of ['<else/><elseif cond="true"/>', '<else/><else/>']) {
    expect(xmlToJson(chart('<if cond="true">' + body + '</if>')).valid).toBe(false);
  }
});

test.each(['  42\n', '   \n ', '[1, 2]', 'before <p:x xmlns:p="urn:x">a<p:y/>c</p:x> tail'])(
  'preserves significant send and donedata payload %j', content => {
    const xml = `<scxml xmlns="${ns}"><state id="s"><onentry><send event="go"><content>${content}</content></send></onentry></state><final id="f"><donedata><content>${content}</content></donedata></final></scxml>`;
    const doc = read(xml);
    const payload = doc.state[0].onentry[0].send[0].content[0];
    expect(payload).toEqual(doc.final[0].donedata[0].content);
    if (content.includes('<')) expect(payload.content[1]).toMatchObject({ qname: '{urn:x}x', tail: ' tail' });
    else expect(payload.content).toEqual([content]);
    const round = read(write(doc));
    expect(round.state[0].onentry[0].send[0].content[0]).toEqual(payload);
    expect(round.final[0].donedata[0].content).toEqual(payload);
  });
