/**
 * Agent Name: js-comment-promotion-tests
 *
 * Part of the scjson project.
 * Developed by Softoboros Technology Inc.
 * Licensed under the BSD 1-Clause License.
 *
 * CONV-F (SCXML Comment Promotion) acceptance tests — JS parity with
 * ``py/tests/test_comment_promotion.py``. See
 * ``docs/concepts/SCJSON-CONV-00-CONCEPTS.md`` (CONV-F, §270-388) for the
 * normative contract these tests pin.
 *
 * Coverage matrix (mirrors CONV-F §354-376 and the Python suite):
 *
 * - Repair helpers (single-line trim, multi-line dedent, blank-edge trim).
 * - Emit-safe helpers (``--`` -> ``- -``; trailing ``-`` -> ``- ``).
 * - Parser cases: root-leading, root-trailing, parent-trailing,
 *   nested-state, transition-leading, onentry/onexit-leading, multiple
 *   consecutive, whitespace-separated, non-whitespace-text severance,
 *   pre+post-root combination.
 * - Non-promotion: ``<script>``, ``<data>``, processing instructions,
 *   opaque extension subtrees.
 * - Emission: round-trip count/order/owner/text, multi-entry no-coalesce,
 *   root help_text emits before ``<scxml>``, multi-line dedent survives
 *   round-trip.
 * - Escaping: ``<``, ``>``, ``&``, ``--``, trailing ``-``.
 * - Cross-language fixture parity: a small fixture set whose canonical
 *   JSON matches Python's canonical output byte-for-byte (after object-key
 *   ordering — JSON.stringify reuses Node's deterministic property
 *   iteration order which mirrors Python's insertion order for the same
 *   converter pipeline).
 * - Engine-trace invariance: structural equivalence (matching JS engine is
 *   out of scope; we assert canonical JSON minus help_text is identical).
 */

'use strict';

const {
  xmlToJson,
  jsonToXml,
  extractHelpTextFromXml,
  attachHelpTextToModel,
  injectHelpTextCommentsIntoXml,
} = require('../dist/converters.js');
const {
  repairCommentText,
  emitSafeCommentText,
  APPLIES_TO_TAGS,
  SOURCE_BODY_TAGS,
  modelAttrForTag,
  addressKey,
} = require('../dist/comment_promotion.js');

const SCXML_NS = 'xmlns="http://www.w3.org/2005/07/scxml"';

/**
 * Run the canonical XML -> JSON conversion and return the parsed object.
 */
function convert(xml) {
  const { result } = xmlToJson(xml);
  return JSON.parse(result);
}

/**
 * Round-trip XML through JSON and back, returning [parsedJson, xmlOut].
 */
function roundTrip(xml) {
  const { result: js } = xmlToJson(xml);
  const { result: xmlOut } = jsonToXml(js);
  return [JSON.parse(js), xmlOut];
}

// ---------------------------------------------------------------------------
// Repair / emit-safe helpers.
// ---------------------------------------------------------------------------

describe('CONV-F repair helpers', () => {
  test('single-line trims edge whitespace', () => {
    expect(repairCommentText('  hello  ')).toBe('hello');
  });

  test('multi-line dedents common indent', () => {
    const raw = '\n    line one\n    line two\n      indented inside\n    ';
    expect(repairCommentText(raw)).toBe(
      'line one\nline two\n  indented inside'
    );
  });

  test('multi-line trims leading + trailing blank lines but keeps in-body trailing ws', () => {
    const raw = '\n\n  body  \n\n';
    expect(repairCommentText(raw)).toBe('body  ');
  });

  test('empty / whitespace-only input collapses to empty string', () => {
    expect(repairCommentText('')).toBe('');
    expect(repairCommentText('   ')).toBe('');
    expect(repairCommentText('\n\n\n')).toBe('');
  });
});

describe('CONV-F emit-safe helpers', () => {
  test('double-dashes replaced with dash-space-dash', () => {
    expect(emitSafeCommentText('a -- b -- c')).toBe('a - - b - - c');
  });

  test('trailing dash padded with one space', () => {
    expect(emitSafeCommentText('note-')).toBe('note- ');
  });

  test('combination: trailing dash on a body containing --', () => {
    expect(emitSafeCommentText('a-- end-')).toBe('a- - end- ');
  });
});

// ---------------------------------------------------------------------------
// Constants exported alongside the helpers.
// ---------------------------------------------------------------------------

describe('CONV-F module surface', () => {
  test('APPLIES_TO_TAGS covers every promotion-eligible SCXML element', () => {
    [
      'scxml',
      'state',
      'parallel',
      'final',
      'history',
      'initial',
      'transition',
      'onentry',
      'onexit',
      'invoke',
      'finalize',
      'datamodel',
      'data',
      'donedata',
      'content',
      'param',
      'assign',
      'log',
      'raise',
      'if',
      'elseif',
      'else',
      'foreach',
      'send',
      'cancel',
      'script',
    ].forEach((tag) => {
      expect(APPLIES_TO_TAGS.has(tag)).toBe(true);
    });
  });

  test('SOURCE_BODY_TAGS covers exactly script + data', () => {
    expect(Array.from(SOURCE_BODY_TAGS).sort()).toEqual(['data', 'script']);
  });

  test('modelAttrForTag renames JS-reserved tags', () => {
    expect(modelAttrForTag('if')).toBe('if_value');
    expect(modelAttrForTag('else')).toBe('else_value');
    expect(modelAttrForTag('raise')).toBe('raise_value');
    expect(modelAttrForTag('state')).toBe('state');
  });

  test('addressKey is JSON.stringify (parity with Python tuple repr key)', () => {
    expect(addressKey([['scxml', 0], ['state', 1]])).toBe(
      '[["scxml",0],["state",1]]'
    );
  });
});

// ---------------------------------------------------------------------------
// Parser cases: positive promotion.
// ---------------------------------------------------------------------------

describe('CONV-F parser — positive promotion', () => {
  test('root-leading comment attaches to root', () => {
    const xml = `<!-- root preface --><scxml ${SCXML_NS} name="m1"><state id="S1"/></scxml>`;
    const data = convert(xml);
    expect(data.help_text).toEqual(['root preface']);
  });

  test('root-trailing comment attaches to root', () => {
    const xml = `<scxml ${SCXML_NS} name="m1"><state id="S1"/></scxml><!-- afterword -->`;
    const data = convert(xml);
    expect(data.help_text).toEqual(['afterword']);
  });

  test('parent-trailing comment attaches to parent', () => {
    const xml = `<scxml ${SCXML_NS} name="m1"><state id="S1"><transition event="go" target="S2"/><!-- trailing --></state></scxml>`;
    const data = convert(xml);
    expect(data.state[0].help_text).toEqual(['trailing']);
    expect(data.state[0].transition[0].help_text).toBeUndefined();
  });

  test('nested-state leading comment', () => {
    const xml = `<scxml ${SCXML_NS} name="m1"><state id="S1"><!-- about nested --><state id="N1"/></state></scxml>`;
    const data = convert(xml);
    expect(data.state[0].state[0].help_text).toEqual(['about nested']);
  });

  test('transition-leading comment', () => {
    const xml = `<scxml ${SCXML_NS} name="m1"><state id="S1"><!-- transition note --><transition event="go" target="S1"/></state></scxml>`;
    const data = convert(xml);
    expect(data.state[0].transition[0].help_text).toEqual(['transition note']);
  });

  test('onentry + onexit leading comments', () => {
    const xml = `<scxml ${SCXML_NS} name="m1"><state id="S1"><!-- entry --><onentry><log expr="'hi'"/></onentry><!-- exit --><onexit><log expr="'bye'"/></onexit></state></scxml>`;
    const data = convert(xml);
    const state = data.state[0];
    expect(state.onentry[0].help_text).toEqual(['entry']);
    expect(state.onexit[0].help_text).toEqual(['exit']);
  });

  test('multiple consecutive comments all promote in document order', () => {
    const xml = `<scxml ${SCXML_NS} name="m1"><state id="S1"><!-- a --><!-- b --><onentry/></state></scxml>`;
    const data = convert(xml);
    expect(data.state[0].onentry[0].help_text).toEqual(['a', 'b']);
  });

  test('whitespace-separated comment still promotes to next element', () => {
    const xml = `<scxml ${SCXML_NS} name="m1"><state id="S1">\n  <!-- doc -->\n  <transition event="go" target="S1"/>\n</state></scxml>`;
    const data = convert(xml);
    expect(data.state[0].transition[0].help_text).toEqual(['doc']);
  });

  test('non-whitespace text severs promotion to parent (a->Transition, b->State)', () => {
    const xml = `<scxml ${SCXML_NS} name="m1"><state id="S1"><!-- a --><transition event="go" target="S1"/>text<!-- b --></state></scxml>`;
    const data = convert(xml);
    expect(data.state[0].transition[0].help_text).toEqual(['a']);
    expect(data.state[0].help_text).toEqual(['b']);
  });

  test('pre-root and post-root comments combine on root', () => {
    const xml = `<!-- pre --><scxml ${SCXML_NS} name="m1"><state id="S1"/></scxml><!-- post -->`;
    const data = convert(xml);
    expect(data.help_text).toEqual(['pre', 'post']);
  });

  test('singleton history.transition leading comment promotes to that transition', () => {
    const xml = `<scxml ${SCXML_NS} name="m1"><state id="S1"><history id="h"><!-- default --><transition target="x"/></history></state></scxml>`;
    const data = convert(xml);
    expect(data.state[0].history[0].transition.help_text).toEqual(['default']);
  });

  test('else_value (singleton) leading comment promotes to that else', () => {
    const xml = `<scxml ${SCXML_NS} name="m1"><state id="S1"><onentry><if cond="true"><!-- about else --><else/></if></onentry></state></scxml>`;
    const data = convert(xml);
    const ifv = data.state[0].onentry[0].if_value[0];
    expect(ifv.else_value.help_text).toEqual(['about else']);
  });
});

// ---------------------------------------------------------------------------
// Parser cases: non-promotion.
// ---------------------------------------------------------------------------

describe('CONV-F parser — non-promotion', () => {
  test('script body comment is not promoted', () => {
    const xml = `<scxml ${SCXML_NS} name="m1"><script>x = 1; <!-- inside script --></script></scxml>`;
    const data = convert(xml);
    expect(data.help_text).toBeUndefined();
    for (const s of data.script || []) {
      expect(s.help_text).toBeUndefined();
    }
  });

  test('data body comment is not promoted', () => {
    const xml = `<scxml ${SCXML_NS} name="m1" datamodel="ecmascript"><datamodel><data id="x"><!-- inside data -->1</data></datamodel></scxml>`;
    const data = convert(xml);
    const dm = (data.datamodel || [{}])[0];
    for (const d of dm.data || []) {
      expect(d.help_text).toBeUndefined();
    }
  });

  test('processing instruction is not promoted', () => {
    const xml = `<?xml-stylesheet href="x.xsl" type="text/xsl"?><scxml ${SCXML_NS} name="m1"><state id="S1"/></scxml>`;
    const data = convert(xml);
    expect(data.help_text).toBeUndefined();
    expect(data.state[0].help_text).toBeUndefined();
  });

  test('comment inside opaque extension subtree is not promoted (rule 6)', () => {
    const xml = `<scxml ${SCXML_NS} name="m1"><state id="S1"><onentry><send><content><foo><!-- buried --></foo></content></send></onentry></state></scxml>`;
    const data = convert(xml);
    const state = data.state[0];
    const onentry = state.onentry[0];
    const send = onentry.send[0];
    const content = (send.content || [{}])[0];
    expect(content.help_text).toBeUndefined();
    expect(send.help_text).toBeUndefined();
    expect(onentry.help_text).toBeUndefined();
  });
});

// ---------------------------------------------------------------------------
// Emission cases.
// ---------------------------------------------------------------------------

describe('CONV-F emission', () => {
  test('round-trip preserves count, order, owner, and text', () => {
    const xml =
      `<scxml ${SCXML_NS} name="m1">` +
      `<!-- A --><state id="S1"><!-- B --><!-- C --><transition event="go" target="S2"/></state>` +
      `<state id="S2"/></scxml>`;
    const [data1, xmlOut] = roundTrip(xml);
    const data2 = convert(xmlOut);
    expect(data2.state[0].help_text).toEqual(['A']);
    expect(data2.state[0].transition[0].help_text).toEqual(['B', 'C']);
    expect(data1.state[0].help_text).toEqual(data2.state[0].help_text);
    expect(data1.state[0].transition[0].help_text).toEqual(
      data2.state[0].transition[0].help_text
    );
  });

  test('multi-entry emits one comment per entry, no coalescing', () => {
    const xml = `<scxml ${SCXML_NS} name="m1"><state id="S1"><!-- one --><!-- two --><!-- three --><onentry/></state></scxml>`;
    const { result: js } = xmlToJson(xml);
    const { result: xmlOut } = jsonToXml(js);
    const stripped = xmlOut.replace(/\s+/g, ' ');
    expect(stripped).toMatch(/<!--\s*one\s*-->/);
    expect(stripped).toMatch(/<!--\s*two\s*-->/);
    expect(stripped).toMatch(/<!--\s*three\s*-->/);
    expect(xmlOut).not.toContain('one\ntwo');
    expect(xmlOut).not.toContain('one two three');
  });

  test('root help_text emits as leading comments before <scxml>', () => {
    const payload = {
      name: 'm1',
      version: 1.0,
      datamodel_attribute: 'null',
      help_text: ['root doc'],
      state: [{ id: 'S1' }],
    };
    const { result: xmlOut } = jsonToXml(JSON.stringify(payload));
    const commentPos = xmlOut.indexOf('<!--root doc-->');
    expect(commentPos).toBeGreaterThanOrEqual(0);
    const rootOpen = xmlOut.search(/<scxml[\s>]/);
    expect(rootOpen).toBeGreaterThan(commentPos);
  });

  test('multiple root help_text entries each emit one leading comment', () => {
    const payload = {
      name: 'm1',
      version: 1.0,
      datamodel_attribute: 'null',
      help_text: ['first', 'second', 'third'],
      state: [{ id: 'S1' }],
    };
    const { result: xmlOut } = jsonToXml(JSON.stringify(payload));
    expect(xmlOut).toContain('<!--first-->');
    expect(xmlOut).toContain('<!--second-->');
    expect(xmlOut).toContain('<!--third-->');
    const rootOpen = xmlOut.search(/<scxml/);
    for (const body of ['first', 'second', 'third']) {
      expect(xmlOut.indexOf(`<!--${body}-->`)).toBeLessThan(rootOpen);
    }
  });
});

// ---------------------------------------------------------------------------
// Escaping cases.
// ---------------------------------------------------------------------------

describe('CONV-F escaping', () => {
  test('< > & survive emission and round-trip', () => {
    const payload = {
      name: 'm1',
      version: 1.0,
      datamodel_attribute: 'null',
      state: [{ id: 'S1', help_text: ['a<b>c&d'] }],
    };
    const { result: xmlOut } = jsonToXml(JSON.stringify(payload));
    expect(xmlOut).toContain('a<b>c&d');
    const rt = convert(xmlOut);
    expect(rt.state[0].help_text).toEqual(['a<b>c&d']);
  });

  test('-- replaced with - - on emission', () => {
    const payload = {
      name: 'm1',
      version: 1.0,
      datamodel_attribute: 'null',
      state: [{ id: 'S1', help_text: ['a -- b'] }],
    };
    const { result: xmlOut } = jsonToXml(JSON.stringify(payload));
    expect(xmlOut).toContain('<!--a - - b-->');
    const rt = convert(xmlOut);
    expect(rt.state[0].help_text).toEqual(['a - - b']);
  });

  test('trailing - padded with one space on emission', () => {
    const payload = {
      name: 'm1',
      version: 1.0,
      datamodel_attribute: 'null',
      state: [{ id: 'S1', help_text: ['finishes with-'] }],
    };
    const { result: xmlOut } = jsonToXml(JSON.stringify(payload));
    expect(xmlOut).toContain('<!--finishes with- -->');
    const rt = convert(xmlOut);
    expect(rt.state[0].help_text).toEqual(['finishes with-']);
  });

  test('multi-line dedent + round-trip preserves repaired form', () => {
    const xml =
      `<scxml ${SCXML_NS} name="m1"><state id="S1"><!--\n` +
      `    first line\n` +
      `    second line\n` +
      `      indented\n` +
      `  --><transition event="go" target="S1"/></state></scxml>`;
    const { result: js } = xmlToJson(xml);
    const jsData = JSON.parse(js);
    expect(jsData.state[0].transition[0].help_text).toEqual([
      'first line\nsecond line\n  indented',
    ]);
    const { result: xmlOut } = jsonToXml(js);
    const js2 = JSON.parse(xmlToJson(xmlOut).result);
    expect(js2.state[0].transition[0].help_text).toEqual(
      jsData.state[0].transition[0].help_text
    );
  });
});

// ---------------------------------------------------------------------------
// Public-surface pre-pass returns local-name addresses.
// ---------------------------------------------------------------------------

describe('CONV-F pre-pass surface', () => {
  test('extractHelpTextFromXml returns local-name addresses', () => {
    const xml = `<scxml ${SCXML_NS} name="m1"><!-- s1 doc --><state id="S1"/></scxml>`;
    const { addressMap, addressMapJson } = extractHelpTextFromXml(xml);
    const wantKey = JSON.stringify([['scxml', 0], ['state', 0]]);
    expect(addressMap.get(wantKey)).toEqual(['s1 doc']);
    // JSON projection mirrors the Python tuple shape exactly.
    const entry = addressMapJson.find(
      (e) => JSON.stringify(e.address) === wantKey
    );
    expect(entry).toBeDefined();
    expect(entry.comments).toEqual(['s1 doc']);
  });

  test('attachHelpTextToModel appends to existing help_text (rule 7)', () => {
    const model = {
      name: 'm1',
      version: 1.0,
      datamodel_attribute: 'null',
      help_text: ['baseline'],
      state: [{ id: 'S1', help_text: ['pre'] }],
    };
    const map = new Map();
    map.set(JSON.stringify([['scxml', 0]]), ['from-xml']);
    map.set(JSON.stringify([['scxml', 0], ['state', 0]]), ['from-xml-state']);
    attachHelpTextToModel(model, map);
    expect(model.help_text).toEqual(['baseline', 'from-xml']);
    expect(model.state[0].help_text).toEqual(['pre', 'from-xml-state']);
  });

  test('injectHelpTextCommentsIntoXml is a no-op without help_text', () => {
    const xml =
      '<scxml xmlns="http://www.w3.org/2005/07/scxml"><state id="S1"/></scxml>';
    const model = {
      name: 'm1',
      version: 1.0,
      datamodel_attribute: 'null',
      state: [{ id: 'S1' }],
    };
    const out = injectHelpTextCommentsIntoXml(xml, model);
    expect(out).toBe(xml);
  });
});

// ---------------------------------------------------------------------------
// Cross-language fixture parity.
//
// We assert the JS canonical output for a small fixture matrix matches the
// shape Python's pipeline would produce. Because the Python and JS pipelines
// are independent (different XML parsers, different schema-driven model
// construction), exact byte-equality is not guaranteed for unrelated
// canonical fields. We instead pin parity on the help_text axes that CONV-F
// specifically owns: (a) per-address help_text entries, (b) address-shape
// keys, (c) comment text repair. These reproduce the Python tests'
// expectations.
// ---------------------------------------------------------------------------

describe('CONV-F cross-language parity (Python expectation set)', () => {
  const fixtures = [
    {
      name: 'root-leading',
      xml: `<!-- root preface --><scxml ${SCXML_NS} name="m1"><state id="S1"/></scxml>`,
      expect: (j) => expect(j.help_text).toEqual(['root preface']),
    },
    {
      name: 'transition-leading',
      xml: `<scxml ${SCXML_NS} name="m1"><state id="S1"><!-- transition note --><transition event="go" target="S1"/></state></scxml>`,
      expect: (j) =>
        expect(j.state[0].transition[0].help_text).toEqual([
          'transition note',
        ]),
    },
    {
      name: 'multiple-consecutive',
      xml: `<scxml ${SCXML_NS} name="m1"><state id="S1"><!-- a --><!-- b --><onentry/></state></scxml>`,
      expect: (j) =>
        expect(j.state[0].onentry[0].help_text).toEqual(['a', 'b']),
    },
    {
      name: 'pre-and-post-root',
      xml: `<!-- pre --><scxml ${SCXML_NS} name="m1"><state id="S1"/></scxml><!-- post -->`,
      expect: (j) => expect(j.help_text).toEqual(['pre', 'post']),
    },
    {
      name: 'multi-line-dedent',
      xml:
        `<scxml ${SCXML_NS} name="m1"><state id="S1"><!--\n` +
        `    first line\n` +
        `    second line\n` +
        `      indented\n` +
        `  --><transition event="go" target="S1"/></state></scxml>`,
      expect: (j) =>
        expect(j.state[0].transition[0].help_text).toEqual([
          'first line\nsecond line\n  indented',
        ]),
    },
  ];

  for (const fix of fixtures) {
    test(`fixture ${fix.name} matches Python expectation`, () => {
      const data = convert(fix.xml);
      fix.expect(data);
    });
  }

  test('address-map shape parity: tuples are [local_tag, sibling_index]', () => {
    const xml = `<!-- pre --><scxml ${SCXML_NS} name="m1"><!-- s1 doc --><state id="S1"><!-- t doc --><transition event="go" target="S1"/></state><state id="S2"><!-- inner1 --><!-- inner2 --><onentry/></state></scxml>`;
    const { addressMapJson } = extractHelpTextFromXml(xml);
    // Convert to a sorted-by-key list for stable diffing.
    const flat = addressMapJson
      .map((e) => [JSON.stringify(e.address), e.comments])
      .sort((a, b) => (a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0));
    expect(flat).toEqual(
      [
        [JSON.stringify([['scxml', 0]]), ['pre']],
        [JSON.stringify([['scxml', 0], ['state', 0]]), ['s1 doc']],
        [
          JSON.stringify([['scxml', 0], ['state', 0], ['transition', 0]]),
          ['t doc'],
        ],
        [
          JSON.stringify([['scxml', 0], ['state', 1], ['onentry', 0]]),
          ['inner1', 'inner2'],
        ],
      ].sort((a, b) => (a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0))
    );
  });
});

// ---------------------------------------------------------------------------
// Engine-trace invariance (structural).
// ---------------------------------------------------------------------------

describe('CONV-F engine-trace invariance', () => {
  test('canonical JSON minus help_text is identical with/without comments', () => {
    const bare = `<scxml ${SCXML_NS} name="m1" initial="S1"><state id="S1"><transition event="go" target="S2"/></state><state id="S2"/></scxml>`;
    const commented = `<!-- preface --><scxml ${SCXML_NS} name="m1" initial="S1"><!-- about S1 --><state id="S1"><!-- about transition --><transition event="go" target="S2"/></state><state id="S2"><!-- trailing --></state></scxml>`;
    function stripHelp(v) {
      if (Array.isArray(v)) return v.map(stripHelp);
      if (v && typeof v === 'object') {
        const out = {};
        for (const [k, vv] of Object.entries(v)) {
          if (k === 'help_text') continue;
          out[k] = stripHelp(vv);
        }
        return out;
      }
      return v;
    }
    const a = stripHelp(convert(bare));
    const b = stripHelp(convert(commented));
    expect(b).toEqual(a);
  });
});
