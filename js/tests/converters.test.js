/**
 * Agent Name: js-converters-tests
 *
 * Part of the scjson project.
 * Developed by Softoboros Technology Inc.
 * Licensed under the BSD 1-Clause License.
 */

const fs = require('fs');
const path = require('path');
const {
  xmlToJson,
  jsonToXml,
  removeEmpty,
  ensureArrays,
  ARRAY_KEYS,
  STRUCTURAL_METADATA_KEYS,
} = require('../dist/converters.js');

/**
 * Basic test ensuring that script elements are normalised correctly.
 */
test('script text becomes object with content', () => {
  const xml = '<scxml xmlns="http://www.w3.org/2005/07/scxml"><script>foo</script></scxml>';
  const { result: jsonStr, valid } = xmlToJson(xml);
  expect(valid).toBe(true);
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
  const { result: jsonStr, valid } = xmlToJson(xml);
  expect(valid).toBe(true);
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
  const { result: jsonStr, valid } = xmlToJson(xml);
  expect(valid).toBe(true);
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
  const { result: jsonStr, valid } = xmlToJson(xml);
  expect(valid).toBe(true);
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
  const { result: jsonStr, valid } = xmlToJson(xml);
  expect(valid).toBe(true);
  const obj = JSON.parse(jsonStr);
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
  const { result: jsonStr, valid } = xmlToJson(xml);
  expect(valid).toBe(true);
  const obj = JSON.parse(jsonStr);
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
  const { result: jsonStr, valid } = xmlToJson(xml);
  expect(valid).toBe(true);
  const obj = JSON.parse(jsonStr);
  const assign = obj.state[0].onentry[0].assign[0];
  expect(assign.content[0]).toHaveProperty('final');
  expect(assign.content[0].final).toEqual([{}]);
});

/**
 * Root level transitions are ignored like the Python converter.
 */
test('root transitions are dropped', () => {
  const xml =
    '<scxml xmlns="http://www.w3.org/2005/07/scxml"><transition target="s"/><state id="s"/></scxml>';
  const { result: jsonStr2, valid: valid2 } = xmlToJson(xml);
  expect(valid2).toBe(true);
  const obj = JSON.parse(jsonStr2);
  expect(obj).not.toHaveProperty('transition');
  expect(obj.state[0].id).toBe('s');
});

/* ------------------------------------------------------------------------- */
/* CONV-E: help_text first-class field tests.                                 */
/*                                                                            */
/* Parity with py/tests/test_help_text_round_trip.py (commit 9008639). The    */
/* JS converter MUST treat ``help_text`` as a known structural metadata key   */
/* parallel to ``other_attributes`` — distinct bucket, preserved as an array, */
/* never collapsed to scalar, omitted when empty, never folded into           */
/* ``other_attributes`` or generic ``content``.                               */
/*                                                                            */
/* XML-side emission is covered by CONV-F comment-promotion tests; this       */
/* section keeps the JSON-side metadata contract focused and explicit.        */
/* ------------------------------------------------------------------------- */

const REPO_ROOT = path.resolve(__dirname, '..', '..');
const ROOT_SCHEMA_PATH = path.join(REPO_ROOT, 'scjson.schema.json');
const JS_SCHEMA_PATH = path.join(REPO_ROOT, 'js', 'scjson.schema.json');
const JAVA_SCHEMA_PATH = path.join(
  REPO_ROOT,
  'java',
  'src',
  'main',
  'resources',
  'scjson.schema.json'
);

/**
 * Schema parity: assert help_text exists with {type: array, items: string}
 * on the load-bearing SCJSON element families. Mirrors the Python
 * ``test_canonical_schema_exposes_help_text`` parametrised test.
 */
describe('CONV-E schema surface', () => {
  const schema = JSON.parse(fs.readFileSync(ROOT_SCHEMA_PATH, 'utf8'));
  const defs = schema.$defs;

  test.each(['Scxml', 'State', 'Transition', 'Data'])(
    'canonical schema exposes help_text on %s',
    (cls) => {
      expect(defs[cls]).toBeDefined();
      const props = defs[cls].properties;
      expect(props).toHaveProperty('help_text');
      expect(props.help_text.type).toBe('array');
      expect(props.help_text.items).toEqual({ type: 'string' });
    }
  );

  test('enumeration $defs do not advertise help_text', () => {
    const enums = [
      'AssignTypeDatatype',
      'BindingDatatype',
      'BooleanDatatype',
      'ExmodeDatatype',
      'HistoryTypeDatatype',
      'TransitionTypeDatatype',
    ];
    for (const name of enums) {
      expect(defs[name]).toBeDefined();
      expect(defs[name]).not.toHaveProperty('properties');
    }
  });

  test('schema mirrors (root, js, java) are byte-identical', () => {
    const root = fs.readFileSync(ROOT_SCHEMA_PATH);
    const js = fs.readFileSync(JS_SCHEMA_PATH);
    const java = fs.readFileSync(JAVA_SCHEMA_PATH);
    expect(js.equals(root)).toBe(true);
    expect(java.equals(root)).toBe(true);
  });

  test('help_text registered as an array key on the JS surface', () => {
    expect(ARRAY_KEYS.has('help_text')).toBe(true);
    expect(STRUCTURAL_METADATA_KEYS.has('help_text')).toBe(true);
  });
});

describe('CONV-E JSON normalization round-trip', () => {
  /**
   * Build the canonical JS shape the round-trip tests start from.
   */
  function buildHelpTextDoc() {
    return {
      name: 'm1',
      version: 1.0,
      datamodel_attribute: 'null',
      help_text: ['doc1', 'doc2'],
      state: [
        {
          id: 'S1',
          help_text: ['state S1 doc'],
          transition: [
            {
              event: 'go',
              target: ['S2'],
              help_text: ['t1', 't2'],
            },
          ],
        },
        { id: 'S2' },
      ],
    };
  }

  test('removeEmpty preserves help_text arrays on Scxml + State + Transition', () => {
    const doc = buildHelpTextDoc();
    const cleaned = removeEmpty(doc);
    expect(cleaned.help_text).toEqual(['doc1', 'doc2']);
    expect(cleaned.state[0].help_text).toEqual(['state S1 doc']);
    expect(cleaned.state[0].transition[0].help_text).toEqual(['t1', 't2']);
    // Untouched state has no help_text key in canonical output.
    expect(cleaned.state[1]).not.toHaveProperty('help_text');
  });

  test('ensureArrays leaves help_text untouched when already an array', () => {
    const doc = buildHelpTextDoc();
    ensureArrays(doc);
    expect(Array.isArray(doc.help_text)).toBe(true);
    expect(doc.help_text).toEqual(['doc1', 'doc2']);
  });

  test('ensureArrays wraps scalar help_text into an array', () => {
    // help_text in ARRAY_KEYS guarantees scalar entries are wrapped.
    const obj = { name: 'm', help_text: 'only', state: [] };
    ensureArrays(obj);
    expect(Array.isArray(obj.help_text)).toBe(true);
    expect(obj.help_text).toEqual(['only']);
  });

  test('entry order preserved across removeEmpty', () => {
    const ordered = { help_text: ['a', 'b', 'c'] };
    const cleaned = removeEmpty(ordered);
    expect(cleaned.help_text).toEqual(['a', 'b', 'c']);
  });

  test('single-entry help_text array is not collapsed to a scalar', () => {
    const single = { help_text: ['only'] };
    const cleaned = removeEmpty(single);
    expect(Array.isArray(cleaned.help_text)).toBe(true);
    expect(cleaned.help_text).toEqual(['only']);
  });

  test('empty help_text array is omitted from canonical output', () => {
    const empty = { name: 'm', help_text: [], state: [] };
    const cleaned = removeEmpty(empty) || {};
    expect(cleaned).not.toHaveProperty('help_text');
  });

  test('missing help_text key is absent from canonical output', () => {
    const none = { name: 'm', state: [{ id: 'S1' }] };
    const cleaned = removeEmpty(none);
    expect(cleaned).not.toHaveProperty('help_text');
    expect(cleaned.state[0]).not.toHaveProperty('help_text');
  });
});

describe('CONV-H root-reachable inclusion and communication surface', () => {
  test('xmlToJson preserves invoke, send, external data, script, and donedata fields', () => {
    const xml = `
      <scxml xmlns="http://www.w3.org/2005/07/scxml" datamodel="python" initial="s">
        <datamodel><data id="external" src="external.json"/></datamodel>
        <script src="logic.js"/>
        <state id="s">
          <invoke id="childBySrc" type="scxml" src="child.scxml">
            <param name="seed" expr="1"/>
          </invoke>
          <invoke type="scxml">
            <content>
              <scxml datamodel="python" initial="inner"><state id="inner"/></scxml>
            </content>
            <finalize><assign location="done" expr="true"/></finalize>
          </invoke>
          <onentry>
            <send event="hello" target="#_parent">
              <param name="payload" expr="42"/>
              <content expr="payload_expr"/>
            </send>
          </onentry>
          <transition target="f"/>
        </state>
        <final id="f">
          <donedata>
            <content expr="result"/>
            <param name="status" expr="'ok'"/>
          </donedata>
        </final>
      </scxml>`;

    const { result, valid } = xmlToJson(xml);
    expect(valid).toBe(true);
    const obj = JSON.parse(result);

    expect(obj.datamodel[0].data[0].src).toBe('external.json');
    expect(obj.script[0].src).toBe('logic.js');
    expect(obj.state[0].invoke[0].src).toBe('child.scxml');
    expect(obj.state[0].invoke[0].param[0].name).toBe('seed');
    expect(
      obj.state[0].invoke[1].content[0].content[0].state[0].id
    ).toBe('inner');
    expect(obj.state[0].invoke[1].finalize[0].assign[0].location).toBe('done');
    expect(obj.state[0].onentry[0].send[0].target).toBe('#_parent');
    expect(obj.state[0].onentry[0].send[0].param[0].name).toBe('payload');
    expect(obj.final[0].donedata[0].content.expr).toBe('result');
    expect(obj.final[0].donedata[0].param[0].name).toBe('status');
  });

  test('schema validation rejects non-empty send and raise under finalize', () => {
    const withSend = {
      version: 1.0,
      datamodel_attribute: 'null',
      state: [
        {
          id: 's',
          invoke: [{ finalize: [{ send: [{ event: 'bad' }] }] }],
        },
      ],
    };
    const withRaise = {
      version: 1.0,
      datamodel_attribute: 'null',
      state: [
        {
          id: 's',
          invoke: [{ finalize: [{ raise_value: [{ event: 'bad' }] }] }],
        },
      ],
    };

    expect(jsonToXml(JSON.stringify(withSend)).valid).toBe(false);
    expect(jsonToXml(JSON.stringify(withRaise)).valid).toBe(false);
  });

  test('XInclude preserve mode keeps include directive as extension content', () => {
    const xml = `
      <scxml xmlns="http://www.w3.org/2005/07/scxml"
             xmlns:xi="http://www.w3.org/2001/XInclude"
             initial="s">
        <xi:include href="child.scxml"/>
        <state id="s"/>
      </scxml>`;

    const { result, valid } = xmlToJson(xml);
    expect(valid).toBe(true);
    const obj = JSON.parse(result);

    expect(obj.other_element[0].qname).toBe(
      '{http://www.w3.org/2001/XInclude}include'
    );
    expect(obj.other_element[0].attributes.href).toBe('child.scxml');
    expect(obj.state[0].id).toBe('s');

    const xmlOut = jsonToXml(result).result;
    expect(xmlOut).toContain('<xi:include');
    expect(xmlOut).toContain('href="child.scxml"');
    expect(xmlOut).not.toContain('<other_element>');
  });

  test('XInclude resolve mode converts the assembled SCXML tree', () => {
    const xml = `
      <scxml xmlns="http://www.w3.org/2005/07/scxml"
             xmlns:xi="http://www.w3.org/2001/XInclude"
             initial="included">
        <xi:include href="child.scxml"/>
      </scxml>`;

    const { result, valid } = xmlToJson(xml, {
      xinclude: 'resolve',
      xincludeLoader: href => {
        expect(href).toBe('child.scxml');
        return '<state xmlns="http://www.w3.org/2005/07/scxml" id="included"/>';
      },
    });
    expect(valid).toBe(true);
    const obj = JSON.parse(result);

    expect(obj.other_element).toBeUndefined();
    expect(obj.state[0].id).toBe('included');
    expect(obj.initial).toEqual(['included']);
  });
});

describe('CONV-E help_text distinct from other_attributes', () => {
  test('round-trip keeps both fields separate (no cross-pollination)', () => {
    const input = {
      name: 'm1',
      version: 1.0,
      datamodel_attribute: 'null',
      help_text: ['doc'],
      other_attributes: { position: '1,2', description: 'legacy' },
      state: [
        {
          id: 'S1',
          help_text: ['state doc'],
          other_attributes: { position: '3,4' },
        },
      ],
    };
    const cleaned = removeEmpty(input);
    // help_text is preserved verbatim on both nesting levels.
    expect(cleaned.help_text).toEqual(['doc']);
    expect(cleaned.state[0].help_text).toEqual(['state doc']);
    // other_attributes contents are preserved verbatim.
    expect(cleaned.other_attributes).toEqual({
      position: '1,2',
      description: 'legacy',
    });
    expect(cleaned.state[0].other_attributes).toEqual({ position: '3,4' });
    // CRITICAL: help_text MUST NOT leak into other_attributes.
    expect(cleaned.other_attributes).not.toHaveProperty('help_text');
    expect(cleaned.state[0].other_attributes).not.toHaveProperty('help_text');
  });
});

describe('CONV-F SCXML emission (comment promotion)', () => {
  test('jsonToXml emits help_text as leading XML comments, not attributes', () => {
    // CONV-F replaces the CONV-E deferral: ``help_text`` MUST emit as one
    // leading ``<!-- ... -->`` per entry, in array order, immediately
    // before the owning element. The negative invariants from the CONV-E
    // landing remain: ``help_text`` MUST NOT appear as an ``@_help_text``
    // XML attribute, MUST NOT be folded into a generic ``<content>``
    // child, and MUST NOT corrupt sibling SCXML output.
    const input = {
      name: 'm1',
      version: 1.0,
      datamodel_attribute: 'null',
      help_text: ['doc1', 'doc2'],
      state: [
        {
          id: 'S1',
          help_text: ['state doc'],
          transition: [
            { event: 'go', target: ['S2'], help_text: ['t1'] },
          ],
        },
        { id: 'S2' },
      ],
    };
    const { result: xmlStr, valid } = jsonToXml(JSON.stringify(input));
    expect(valid).toBe(true);
    // No attribute leakage.
    expect(xmlStr).not.toContain('help_text=');
    // No element leakage either.
    expect(xmlStr).not.toContain('<help_text');
    expect(xmlStr).not.toContain('</help_text');
    // Sibling SCXML output is intact.
    expect(xmlStr).toContain('<scxml');
    expect(xmlStr).toContain('id="S1"');
    expect(xmlStr).toContain('id="S2"');
    expect(xmlStr).toContain('event="go"');
    expect(xmlStr).toContain('target="S2"');
    // Comments now appear as leading siblings (CONV-F emission rule).
    expect(xmlStr).toContain('<!--doc1-->');
    expect(xmlStr).toContain('<!--doc2-->');
    expect(xmlStr).toContain('<!--state doc-->');
    expect(xmlStr).toContain('<!--t1-->');
  });

  test('jsonToXml leaves other_attributes alone when help_text is also present', () => {
    const input = {
      name: 'm1',
      version: 1.0,
      datamodel_attribute: 'null',
      help_text: ['doc'],
      other_attributes: { position: '1,2' },
      state: [{ id: 'S1' }],
    };
    const { result: xmlStr, valid } = jsonToXml(JSON.stringify(input));
    expect(valid).toBe(true);
    // other_attributes survives as a real XML attribute.
    expect(xmlStr).toContain('position="1,2"');
    // help_text still suppressed.
    expect(xmlStr).not.toContain('help_text=');
  });
});
