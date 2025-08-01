/**
 * Agent Name: js-converters
 *
 * Part of the scjson project.
 * Developed by Softoboros Technology Inc.
 * Licensed under the BSD 1-Clause License.
 */

/**
 * @file Core conversion utilities shared between Node and browser builds.
 */

const { XMLParser, XMLBuilder } = require('fast-xml-parser');
const Ajv = require('ajv');
const schema = require('../scjson.schema.json');

/**
 * Keys that should always be represented as arrays.
 *
 * These are derived from `scjson.schema.json` where the corresponding
 * properties have a ``type`` of ``array``. The parser used here will
 * collapse single elements into objects, so we normalise the structure
 * back to arrays in order to maintain canonical output that matches the
 * reference Python implementation.
 */
const ARRAY_KEYS = new Set([
  'assign',
  'cancel',
  'content',
  'data',
  'datamodel',
  'donedata',
  'final',
  'finalize',
  'foreach',
  'history',
  'if_value',
  'initial',
  'invoke',
  'log',
  'onentry',
  'onexit',
  'other_element',
  'parallel',
  'param',
  'raise_value',
  'script',
  'send',
  'state',
]);

/// Known SCXML structural fields that should be pulled out of `content[]`
const STRUCTURAL_FIELDS = new Set([
  'state', 'parallel', 'final', 'history',
  'transition', 'onentry', 'onexit', 'invoke',
  'datamodel', 'data', 'initial', 'script',
  'log', 'assign', 'send', 'cancel',
  'param', 'if', 'elseif', 'else',
  'foreach', 'raise', 'content'
]);

/**
 * Recursively convert an XML Element to SCJSON-compliant JS object.
 */
function convert(element) {
  const result = {
    tag: element.tagName,
    ...Object.fromEntries(Array.from(element.attributes).map(attr => [attr.name, attr.value]))
  };

  // Initialize known structural containers if needed
  STRUCTURAL_FIELDS.forEach(field => {
    if (element.querySelector(field)) {
      result[field] = [];
    }
  });

  for (const child of element.children) {
    const converted = convert(child);
    const tag = child.tagName;

    if (STRUCTURAL_FIELDS.has(tag)) {
      // Attach to known field
      result[tag] = result[tag] || [];
      result[tag].push(converted);
    } else {
      // Fallback to generic 'content' array
      result.content = result.content || [];
      result.content.push(converted);
    }
  }

  // Handle text content if present
  const rawText = element.textContent;
  if (rawText && element.children.length === 0 && rawText.trim() !== '') {
    result.content = [rawText];
  }

  return result;
}

/**
 * Keys that should never be pruned even when empty.
 */
const ALWAYS_KEEP = new Set(['else_value', 'else', 'final', 'onentry']);

/**
 * Remove transition elements directly under the <scxml> root.
 *
 * The reference Python implementation ignores these top level
 * transitions entirely. To maintain parity we drop them during
 * conversion.
 *
 * @param {object} obj - Parsed SCXML object.
 */
function stripRootTransitions(obj) {
  if (obj && typeof obj === 'object' && Array.isArray(obj.transition)) {
    delete obj.transition;
  }
}

/**
 * Map of attribute names to their scjson property equivalents.
 */
const ATTRIBUTE_MAP = {
  datamodel: 'datamodel_attribute',
  initial: 'initial_attribute',
  type: 'type_value',
  raise: 'raise_value',
};

/**
 * Attributes whose whitespace should be collapsed.
 */
const COLLAPSE_ATTRS = new Set([
  'expr',
  'cond',
  'event',
  'target',
  'delay',
  'location',
  'name',
  'src',
  'id',
]);

/**
 * Collapse whitespace in attribute string values recursively.
 *
 * @param {object|Array|string} value - Value to normalise.
 * @returns {object|Array|string} Normalised value.
 */
function collapseWhitespace(value) {
  if (Array.isArray(value)) {
    return value.map(collapseWhitespace);
  }
  if (value && typeof value === 'object') {
    for (const [k, v] of Object.entries(value)) {
      if ((k.endsWith('_attribute') || COLLAPSE_ATTRS.has(k)) && typeof v === 'string') {
        if (v.startsWith('\n')) {
          value[k] = '\n' + v.slice(1).replace(/[\n\r\t]/g, ' ');
        } else {
          value[k] = v.replace(/[\n\r\t]/g, ' ');
        }
      } else {
        value[k] = collapseWhitespace(v);
      }
    }
    return value;
  }
  return value;
}

/**
 * Split whitespace-separated token attributes.
 *
 * Attributes such as ``initial`` and ``target`` can contain multiple
 * identifiers separated by spaces. This function mirrors the Python
 * implementation by splitting those values into arrays before further
 * normalisation.
 *
 * @param {object|Array} value - Parsed value to adjust in place.
 */
function splitTokenAttrs(value, parent) {
  if (Array.isArray(value)) return value.forEach(v => splitTokenAttrs(v, parent));
  if (value && typeof value === 'object') {
    for (const [k, v] of Object.entries(value)) {
      if ((k === 'initial' || k === 'initial_attribute') && typeof v === 'string') {
        value[k] = v.trim().split(/\s+/);
        continue;
      }
      if (k === 'transition') {
        if (parent !== 'history' && parent !== 'initial') {
          const arr = Array.isArray(v) ? v : [v];
          arr.forEach(tr => {
            if (typeof tr.target === 'string') tr.target = tr.target.trim().split(/\s+/);
            splitTokenAttrs(tr, k);
          });
          value[k] = arr;
        } else {
          if (typeof v.target === 'string') v.target = v.target.trim().split(/\s+/);
          splitTokenAttrs(v, k);
        }
        continue;
      }
      splitTokenAttrs(v, k);
    }
  }
}

/**
 * Reorder SCXML object keys to match canonical output.
 *
 * ``datamodel`` elements and the attributes ``version`` and
 * ``datamodel_attribute`` are appended to the end of their
 * respective objects so that JSON generated by this converter
 * matches the reference Python implementation.
 *
 * @param {object|Array} value - Parsed object to adjust in place.
 */
function reorderScxml(value) {
  if (Array.isArray(value)) {
    value.forEach(reorderScxml);
    return;
  }
  if (value && typeof value === 'object') {
    for (const v of Object.values(value)) {
      reorderScxml(v);
    }
    if (Object.prototype.hasOwnProperty.call(value, 'datamodel')) {
      const dm = value.datamodel;
      delete value.datamodel;
      value.datamodel = dm;
    }
    if (Object.prototype.hasOwnProperty.call(value, 'version')) {
      const ver = value.version;
      delete value.version;
      value.version = ver;
    }
    if (Object.prototype.hasOwnProperty.call(value, 'datamodel_attribute')) {
      const attr = value.datamodel_attribute;
      delete value.datamodel_attribute;
      value.datamodel_attribute = attr;
    }
    if (
      Object.prototype.hasOwnProperty.call(value, 'item') &&
      Object.prototype.hasOwnProperty.call(value, 'index')
    ) {
      const item = value.item;
      const index = value.index;
      delete value.item;
      delete value.index;
      value.item = item;
      value.index = index;
    }
  }
}

/**
 * Recursively rename XML parser keys to match the scjson schema.
 *
 * - Attribute names prefixed with ``@_`` are stripped of the prefix.
 * - Text content keys ``#text`` are converted to a ``content`` array.
 *
 * @param {object|Array} value - Parsed value to normalise.
 * @returns {object|Array} Normalised value.
 */
function normaliseKeys(value) {
  if (Array.isArray(value)) {
    return value.map(normaliseKeys);
  }
  if (value && typeof value === 'object') {
    const out = {};
    for (const [k, v] of Object.entries(value)) {
      if (k === '#text') {
        const text = normaliseKeys(v);
        if (text !== undefined) {
          if (Array.isArray(out.content)) {
            if (Array.isArray(text)) {
              out.content.push(...text);
            } else {
              out.content.push(text);
            }
          } else if (out.content !== undefined) {
            out.content = Array.isArray(text)
              ? [out.content, ...text]
              : [out.content, text];
          } else {
            out.content = Array.isArray(text) ? text : [text];
          }
        }
        continue;
      }
      let nk = k;
      if (k.startsWith('@_')) {
        const attr = k.slice(2);
        nk = ATTRIBUTE_MAP[attr] || attr;
      } else if (k === 'if') {
        nk = 'if_value';
      } else if (k === 'raise') {
        nk = 'raise_value';
      }
      out[nk] = normaliseKeys(v);
    }
    return out;
  }
  return value;
}

/**
 * Recursively normalise values that should be arrays.
 *
 * @param {object} obj - Parsed object to adjust in place.
 */
function ensureArrays(obj, parent) {
  if (!obj || typeof obj !== 'object') return;
  for (const [k, v] of Object.entries(obj)) {
    if (ARRAY_KEYS.has(k) && v !== undefined) {
      Array.isArray(v)
        ? v.forEach(o => ensureArrays(o, k))
        : (obj[k] = [v], ensureArrays(obj[k][0], k));
      continue;
    }
    if (k === 'transition' && v && typeof v === 'object') {
      if (parent !== 'history' && parent !== 'initial') {
        const arr = Array.isArray(v) ? v : [v];
        arr.forEach(tr => {
          if (tr.target !== undefined && !Array.isArray(tr.target)) tr.target = [tr.target];
          ensureArrays(tr, k);
        });
        obj[k] = arr;
      } else {
        if (v.target !== undefined && !Array.isArray(v.target)) v.target = [v.target];
        ensureArrays(v, k);
      }
      continue;
    }
    Array.isArray(v) ? v.forEach(o => ensureArrays(o, k)) : typeof v === 'object' && ensureArrays(v, k);
  }
}

/**
 * Convert ``else`` elements to the ``else_value`` schema key.
 *
 * Empty ``<else/>`` tags become an object literal so they survive
 * subsequent calls to :func:`removeEmpty`.
 *
 * @param {object|Array} value - Parsed object to adjust in place.
 */
function fixEmptyElse(value) {
  if (Array.isArray(value)) {
    value.forEach(v => fixEmptyElse(v));
    return;
  }
  if (value && typeof value === 'object') {
    for (const [k, v] of Object.entries(value)) {
      if (k === 'else') {
        value.else_value = v === '' ? {} : v;
        delete value.else;
        fixEmptyElse(value.else_value);
        continue;
      }
      fixEmptyElse(v);
    }
  }
}

/**
 * Normalise empty ``onentry`` and ``onexit`` elements.
 *
 * The XML parser represents empty tags as an empty string. The Python
 * reference output preserves these elements as empty objects so they
 * survive subsequent cleaning steps. This helper mirrors that behaviour.
 *
 * @param {object|Array} value - Parsed object to adjust in place.
 */
function fixEmptyOnentry(value) {
  if (Array.isArray(value)) {
    value.forEach(fixEmptyOnentry);
    return;
  }
  if (value && typeof value === 'object') {
    for (const [k, v] of Object.entries(value)) {
      if (
        (k === 'onentry' || k === 'onexit') &&
        Array.isArray(v) &&
        v.length === 1 &&
        typeof v[0] === 'string' &&
        v[0].trim() === ''
      ) {
        value[k] = [{}];
        continue;
      }
      fixEmptyOnentry(v);
    }
  }
}

/**
 * Decode HTML entities in string values.
 *
 * Fast XML parser leaves character references intact. This helper matches the
 * Python implementation by converting entities like ``&#xA;`` to their literal
 * characters.
 *
 * @param {object|Array|string} value - Parsed value to normalise.
 * @returns {object|Array|string} Normalised value.
 */
function decodeEntities(value) {
  if (Array.isArray(value)) {
    return value.map(decodeEntities);
  }
  if (value && typeof value === 'object') {
    for (const [k, v] of Object.entries(value)) {
      value[k] = decodeEntities(v);
    }
    return value;
  }
  if (typeof value === 'string') {
    return value
      .replace(/&#x([0-9a-fA-F]+);/g, (_, h) => String.fromCharCode(parseInt(h, 16)))
      .replace(/&#([0-9]+);/g, (_, d) => String.fromCharCode(parseInt(d, 10)))
      .replace(/&quot;/g, '"')
      .replace(/&apos;/g, "'")
      .replace(/&amp;/g, '&')
      .replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>');
  }
  return value;
}

/**
 * Normalise script elements after parsing.
 *
 * Ensures that each ``script`` entry is an object with a ``content`` array
 * as required by the schema.
 *
 * @param {object|Array} value - Parsed object to adjust in place.
 */
function fixScripts(value) {
  if (Array.isArray(value)) {
    value.forEach(fixScripts);
    return;
  }
  if (value && typeof value === 'object') {
    for (const [k, v] of Object.entries(value)) {
      if (k === 'script') {
        if (Array.isArray(v)) {
          value[k] = v.map(s =>
            typeof s === 'string' ? { content: [s] } : (fixScripts(s), s)
          );
        } else if (typeof v === 'string') {
          value[k] = { content: [v] };
        } else {
          fixScripts(v);
        }
        continue;
      }
      fixScripts(v);
    }
  }
}

/**
 * Normalise nested SCXML documents within invoke content.
 *
 * XML parser output represents nested ``<scxml>`` elements as a key
 * named ``scxml`` inside the ``content`` element. The reference
 * Python implementation instead stores the nested machine under a
 * ``content`` array. This helper replicates that behaviour.
 *
 * @param {object|Array} value - Parsed object to adjust in place.
 */
function fixNestedScxml(value) {
  if (Array.isArray(value)) {
    value.forEach(fixNestedScxml);
    return;
  }
  if (value && typeof value === 'object') {
    if (Object.prototype.hasOwnProperty.call(value, 'scxml')) {
      const sub = value.scxml;
      delete value.scxml;
      const arr = Array.isArray(sub) ? sub : [sub];
      arr.forEach(v => {
        if (Object.prototype.hasOwnProperty.call(v, 'final') && v.final === '') {
          v.final = [{}];
        }
        if (v.initial_attribute !== undefined && v.initial === undefined) {
          v.initial = v.initial_attribute;
          delete v.initial_attribute;
        }
        if (typeof v.version === 'string') {
          const n = parseFloat(v.version);
          if (!Number.isNaN(n)) v.version = n;
        }
        if (v.version === undefined) {
          v.version = 1.0;
        }
        for (const k of Object.keys(v)) {
          if (k === '@_xmlns' || k.startsWith('xmlns')) {
            delete v[k];
          }
        }
        if (v.datamodel_attribute === undefined) {
          v.datamodel_attribute = 'null';
        }
        fixNestedScxml(v);
      });
      value.content = [{ content: arr }];
    }
    for (const v of Object.values(value)) {
      fixNestedScxml(v);
    }
  }
}

/**
 * Apply default values for assign elements.
 *
 * The scjson schema expects ``assign`` elements to include a
 * ``type_value`` attribute with a default of ``replacechildren``.
 * This helper ensures the attribute is present when not specified in
 * the original XML.
 *
 * @param {object|Array} value - Parsed object to adjust in place.
 */
function fixAssignDefaults(value) {
  if (Array.isArray(value)) {
    value.forEach(fixAssignDefaults);
    return;
  }
  if (value && typeof value === 'object') {
    if (Object.prototype.hasOwnProperty.call(value, 'assign')) {
      const arr = Array.isArray(value.assign) ? value.assign : [value.assign];
      arr.forEach(a => {
        if (a.type_value === undefined) {
          a.type_value = 'replacechildren';
        }
        fixAssignDefaults(a);
      });
      value.assign = arr;
    }
    for (const v of Object.values(value)) {
      fixAssignDefaults(v);
    }
  }
}

/**
 * Hoist unexpected attributes into ``other_attributes``.
 *
 * Handles the ``id`` attribute on ``assign`` elements and the
 * misspelled ``intial`` attribute on ``state`` elements so that
 * generated scjson matches the reference Python output.
 *
 * @param {object|Array} value - Parsed object to adjust in place.
 */
// Avoid infinite recursion on cyclic structures
const VISITED_FLAG = Symbol('fixOtherAttributesVisited');

function fixOtherAttributes(value) {
  if (Array.isArray(value)) {
    value.forEach(fixOtherAttributes);
    return;
  }
  if (value && typeof value === 'object') {
    if (value[VISITED_FLAG]) {
      return;
    }
    value[VISITED_FLAG] = true;
    if (Object.prototype.hasOwnProperty.call(value, 'assign')) {
      const arr = Array.isArray(value.assign) ? value.assign : [value.assign];
      arr.forEach(a => {
        if (a.id !== undefined) {
          a.other_attributes = a.other_attributes || {};
          a.other_attributes.id = a.id;
          delete a.id;
        }
        fixOtherAttributes(a);
      });
      value.assign = arr;
    }
    if (value.intial !== undefined) {
      value.other_attributes = value.other_attributes || {};
      value.other_attributes.intial = value.intial;
      delete value.intial;
    }
    for (const [k, v] of Object.entries(value)) {
      if (v === value || k === 'other_attributes') continue;
      fixOtherAttributes(v);
    }
    delete value[VISITED_FLAG];
  }
}

/**
 * Apply default values for send elements.
 *
 * The SCXML specification defines ``type="scxml"`` and ``delay="0s"``
 * as defaults. This mirrors the behaviour of the Python converter so
 * round-trip conversions remain consistent.
 *
 * @param {object|Array} value - Parsed object to adjust in place.
 */
function fixSendDefaults(value) {
  if (Array.isArray(value)) {
    value.forEach(fixSendDefaults);
    return;
  }
  if (value && typeof value === 'object') {
    if (Object.prototype.hasOwnProperty.call(value, 'send')) {
      const arr = Array.isArray(value.send) ? value.send : [value.send];
      arr.forEach(s => {
        if (s.type_value === undefined) {
          s.type_value = 'scxml';
        }
        if (s.delay === undefined) {
          s.delay = '0s';
        }
        fixSendContent(s);
        fixSendDefaults(s);
      });
      value.send = arr;
    }
    for (const v of Object.values(value)) {
      fixSendDefaults(v);
    }
  }
}

/**
 * Normalise inline content elements under ``send``.
 *
 * ``<content>`` children inside ``<send>`` should always be objects with a
 * ``content`` array according to the scjson schema. The fast-xml-parser library
 * collapses simple text nodes to strings which leads to mismatches when
 * compared with the Python implementation. This helper wraps such strings in an
 * object structure.
 *
 * @param {object|Array} value - Parsed object to adjust in place.
 */
function fixSendContent(value) {
  if (Array.isArray(value)) {
    value.forEach(fixSendContent);
    return;
  }
  if (value && typeof value === 'object') {
    if (Object.prototype.hasOwnProperty.call(value, 'qname')) {
      if (Object.prototype.hasOwnProperty.call(value, 'version')) {
        delete value.version;
      }
      if (Object.prototype.hasOwnProperty.call(value, 'datamodel_attribute')) {
        delete value.datamodel_attribute;
      }
    }
    if (Object.prototype.hasOwnProperty.call(value, 'send')) {
      const arr = Array.isArray(value.send) ? value.send : [value.send];
      arr.forEach(s => {
        if (Object.prototype.hasOwnProperty.call(s, 'content')) {
          const cArr = Array.isArray(s.content) ? s.content : [s.content];
          const mapped = cArr.map(c => {
            if (typeof c !== 'object') {
              const raw = String(c);
              if (raw.trim() === '') return null;
              return { content: [{ content: [raw] }] };
            }
            if (c && typeof c === 'object') {
              if (typeof c.content === 'string' || typeof c.content === 'number' || typeof c.content === 'boolean') {
                c.content = [String(c.content)];
              }
              if (Array.isArray(c.content)) {
                c.content = c.content
                  .map(i => (typeof i === 'string' ? String(i) : i))
                  .filter(i => !(typeof i === 'string' && i.trim() === '') && i !== null && i !== undefined);
                if (c.content.length === 0) delete c.content;
              }
              // Convert raw XML objects into canonical content structures
              if (!c.qname && !c.expr && !c.content && Object.keys(c).length === 1) {
                const [k, v] = Object.entries(c)[0];
                c = { content: [convertDataNode(k, v)] };
              } else {
                fixSendContent(c);
              }
              if (c.qname && c.version !== undefined) delete c.version;
              if (c.qname && c.datamodel_attribute !== undefined) delete c.datamodel_attribute;
              return c;
            }
            return null;
          }).filter(x => x !== null);
          s.content = mapped;
        }
        fixSendContent(s);
      });
      value.send = arr;
    }
    for (const v of Object.values(value)) {
      fixSendContent(v);
    }
  }
}

/**
 * Normalise inline content elements under ``donedata``.
 *
 * ``<content>`` children inside ``<donedata>`` should always be objects with a
 * ``content`` array so that round-trips match the reference Python
 * implementation. Strings are wrapped in an object accordingly.
 *
 * @param {object|Array} value - Parsed object to adjust in place.
 */
function fixDonedataContent(value) {
  if (Array.isArray(value)) {
    value.forEach(fixDonedataContent);
    return;
  }
  if (value && typeof value === 'object') {
    if (Object.prototype.hasOwnProperty.call(value, 'donedata')) {
      const arr = Array.isArray(value.donedata) ? value.donedata : [value.donedata];
      arr.forEach(d => {
        if (Object.prototype.hasOwnProperty.call(d, 'content')) {
          const cArr = Array.isArray(d.content) ? d.content : [d.content];
          const mapped = cArr.map(c => {
            if (typeof c !== 'object') {
              const raw = String(c);
              if (raw.trim() === '') return null;
              return { content: [raw] };
            }
            if (c && typeof c === 'object') {
              if (
                typeof c.content === 'string' ||
                typeof c.content === 'number' ||
                typeof c.content === 'boolean'
              ) {
                c.content = [String(c.content)];
              }
              // Convert raw XML objects into canonical content structures
              if (!c.qname && !c.expr && !c.content && Object.keys(c).length === 1) {
                const [k, v] = Object.entries(c)[0];
                c = { content: [convertDataNode(k, v)] };
              } else {
                fixDonedataContent(c);
              }
              if (c.qname && c.version !== undefined) delete c.version;
              if (c.qname && c.datamodel_attribute !== undefined) delete c.datamodel_attribute;
              return c;
            }
            return null;
          });
          const clean = mapped.filter(x => x !== null);
          d.content = clean.length === 1 ? clean[0] : clean;
        }
        fixDonedataContent(d);
      });
      value.donedata = arr;
    }
    for (const v of Object.values(value)) {
      fixDonedataContent(v);
    }
  }
}

/**
 * Convert arbitrary objects parsed under ``<data>`` elements into
 * canonical content structures.
 *
 * The fast-xml-parser library represents child elements of ``<data>`` as
 * direct properties on the data object. This helper converts those
 * properties to the schema's ``content`` array with ``qname``,
 * ``attributes`` and ``children`` fields so that round-trips match the
 * Python implementation.
 *
 * @param {string} name - Element name.
 * @param {*} node - Parsed element value.
 * @returns {object} Canonical content object.
 */
function convertDataNode(name, node) {
  if (Array.isArray(node)) {
    return node.map(n => convertDataNode(name, n));
  }
  if (node && typeof node === 'object') {
    const attrs = {};
    const children = [];
    let text = '';
    for (const [k, v] of Object.entries(node)) {
      if (k === 'content') {
        if (Array.isArray(v)) {
          if (v.every(x => typeof x !== 'object')) {
            text += v.join('');
          } else {
            v.forEach(sub => {
              if (typeof sub === 'object' && Object.keys(sub).length === 1) {
                const [ck, cv] = Object.entries(sub)[0];
                const c = convertDataNode(ck, cv);
                Array.isArray(c) ? children.push(...c) : children.push(c);
              }
            });
          }
        } else if (typeof v === 'string') {
          text += v;
        }
        continue;
      }
      if (v && typeof v === 'object') {
        const c = convertDataNode(k, v);
        Array.isArray(c) ? children.push(...c) : children.push(c);
      } else {
        attrs[k] = String(v);
      }
    }
    const out = { qname: name, text };
    if (children.length) out.children = children;
    if (Object.keys(attrs).length) out.attributes = attrs;
    if (out.text === undefined) out.text = '';
    return out;
  }
  return { qname: name, text: String(node) };
}

/**
 * Recursively normalise ``<data>`` elements that contain inline XML.
 *
 * @param {object|Array} value - Parsed object to adjust in place.
 */
function fixDataContent(value) {
  if (Array.isArray(value)) {
    value.forEach(fixDataContent);
    return;
  }
  if (value && typeof value === 'object') {
    if (Object.prototype.hasOwnProperty.call(value, 'data')) {
      const arr = Array.isArray(value.data) ? value.data : [value.data];
      arr.forEach(d => {
        const content = [];
        for (const [k, v] of Object.entries(d)) {
          if (!['id', 'src', 'expr', 'otherAttributes', 'content'].includes(k)) {
            const c = convertDataNode(k, v);
            Array.isArray(c) ? content.push(...c) : content.push(c);
            delete d[k];
          }
        }
        if (content.length) d.content = content;
      });
      value.data = arr;
    }
    for (const v of Object.values(value)) {
      fixDataContent(v);
    }
  }
}

/**
 * Convert a canonical content object back into XML element format.
 *
 * ``jsonToXml`` relies on this helper to rebuild inline XML stored under
 * ``<data>`` elements. Objects with ``qname``, ``attributes``, and ``children``
 * fields are translated to the structure expected by ``fast-xml-parser``.
 *
 * @param {object} node - Canonical content object.
 * @returns {object} XML builder structure keyed by element name.
 */
function restoreDataNode(node) {
  const out = {};
  if (node.attributes) {
    for (const [k, v] of Object.entries(node.attributes)) {
      out[`@_${k}`] = v;
    }
  }
  if (node.text !== undefined && node.text !== '') {
    out['#text'] = node.text;
  }
  if (Array.isArray(node.children)) {
    node.children.forEach(c => {
      const r = restoreDataNode(c);
      const [ck, cv] = Object.entries(r)[0];
      if (out[ck]) {
        if (Array.isArray(out[ck])) {
          out[ck].push(cv);
        } else {
          out[ck] = [out[ck], cv];
        }
      } else {
        out[ck] = cv;
      }
    });
  }
  if (!node.qname.includes(':') && !node.qname.startsWith('{') && node.qname !== 'scxml') {
    out['@_xmlns'] = '';
  }
  return { [node.qname]: out };
}

/**
 * Remove namespace URIs from ``qname`` fields.
 *
 * @param {object|Array} value - Parsed object to adjust in place.
 */
function stripQnameNs(value) {
  if (Array.isArray(value)) {
    value.forEach(stripQnameNs);
    return;
  }
  if (value && typeof value === 'object') {
    for (const [k, v] of Object.entries(value)) {
      if (k === 'qname' && typeof v === 'string') {
        value[k] = v.replace(/^\{[^}]+\}/, '');
        continue;
      }
      stripQnameNs(v);
    }
  }
}

/**
 * Recursively remove ``xmlns`` attributes from nested objects.
 *
 * @param {object|Array} value - Parsed object to adjust in place.
 */
function stripXmlns(value) {
  if (Array.isArray(value)) {
    value.forEach(stripXmlns);
    return;
  }
  if (value && typeof value === 'object') {
    for (const k of Object.keys(value)) {
      if (k === '@_xmlns' || k.startsWith('xmlns')) {
        delete value[k];
      } else {
        stripXmlns(value[k]);
      }
    }
  }
}

/**
 * Collapse nested ``content`` wrappers created during parsing.
 *
 * A ``content`` array may contain a single object with its own
 * ``content`` array when the original XML element only held text.
 * This helper flattens that structure so that round-tripping through
 * XML does not introduce spurious elements.
 *
 * @param {object|Array} value - Parsed object to adjust in place.
 */
function flattenContent(value) {
  if (Array.isArray(value)) {
    value.forEach(flattenContent);
    return;
  }
  if (value && typeof value === 'object') {
    if (
      Array.isArray(value.content) &&
      value.content.length === 1 &&
      value.content[0] &&
      typeof value.content[0] === 'object' &&
      Object.keys(value.content[0]).length === 1 &&
      Array.isArray(value.content[0].content) &&
      value.content[0].content.length === 1 &&
      value.content[0].content[0] &&
      typeof value.content[0].content[0] === 'object' &&
      !Object.prototype.hasOwnProperty.call(value.content[0].content[0], 'qname')
    ) {
      value.content = [value.content[0].content[0]];
    }
    for (const v of Object.values(value)) {
      flattenContent(v);
    }
  }
}
/**
 * Remove nulls and empty containers from values recursively.
 *
 * Certain keys like ``final`` must always be preserved even when they
 * would otherwise be considered empty. The caller provides the key so we
 * can decide whether to keep an empty object.
 *
 * @param {*} value - Candidate value.
 * @param {string} [key] - Key name associated with ``value`` in the parent.
 * @returns {*} Sanitised value.
 */
function removeEmpty(value, key) {
  if (Array.isArray(value)) {
    const arr = value.map(v => removeEmpty(v, key)).filter(v => v !== undefined);
    if (arr.length > 0 || ALWAYS_KEEP.has(key)) {
      return arr;
    }
    return undefined;
  }
  if (value && typeof value === 'object') {
    const obj = {};
    for (const [k, v] of Object.entries(value)) {
      const r = removeEmpty(v, k);
      if (r !== undefined) obj[k] = r;
    }
    if (Object.keys(obj).length > 0 || ALWAYS_KEEP.has(key)) {
      return obj;
    }
    return undefined;
  }
  if (value === null) {
    return undefined;
  }
  if (typeof value === 'string' && value.trim() === '') {
    if (key) {
      const base = key.startsWith('@_') ? key.slice(2) : key;
      if (
        base.endsWith('_attribute') ||
        base.endsWith('_value') ||
        ['expr', 'cond', 'event', 'target', 'id', 'name', 'label', 'text'].includes(base) ||
        key === '@_xmlns'
      ) {
        return '';
      }
    }
    return undefined;
  }
  return value;
}

const ajv = new Ajv({ useDefaults: true, strict: false });
const validate = ajv.compile(schema);

/**
 * Convert an SCXML string to scjson.
 *
 * @param {string} xmlStr - XML input.
 * @param {boolean} [omitEmpty=true] - Remove empty values when true.
 * @returns {{result: string, valid: boolean, errors: object[]|null}} Conversion outcome.
 *
 * Removes the XML namespace attribute and injects default values
 * expected by the schema.
 */
/**
 * Recursively strip default attributes from nested data nodes.
 *
 * Any object with a ``qname`` property other than ``scxml`` may have
 * ``version`` or ``datamodel_attribute`` inserted during validation.
 * This helper removes those keys so that nested structures match the
 * canonical Python output.
 *
 * @param {object|Array} value - Parsed object to adjust in place.
 */
function stripNestedDataAttrs(value) {
  if (Array.isArray(value)) {
    value.forEach(stripNestedDataAttrs);
    return;
  }
  if (value && typeof value === 'object') {
    if (
      Object.prototype.hasOwnProperty.call(value, 'qname') &&
      value.qname !== 'scxml'
    ) {
      delete value.version;
      delete value.datamodel_attribute;
    }
    for (const v of Object.values(value)) {
      stripNestedDataAttrs(v);
    }
  }
}

function xmlToJson(xmlStr, omitEmpty = true) {
  const parser = new XMLParser({
    ignoreAttributes: false,
    trimValues: false,
    parseTagValue: false,
  });
  let obj = parser.parse(xmlStr);
  if (obj.scxml) {
    obj = obj.scxml;
  }
  obj = normaliseKeys(obj);
  obj = decodeEntities(obj);
  fixNestedScxml(obj);
  fixEmptyElse(obj);
  obj = collapseWhitespace(obj);
  splitTokenAttrs(obj);
  ensureArrays(obj);
  fixOtherAttributes(obj);
  fixScripts(obj);
  fixAssignDefaults(obj);
  fixSendDefaults(obj);
  fixSendContent(obj);
  fixDonedataContent(obj);
  fixDataContent(obj);
  fixEmptyOnentry(obj);
  fixSendContent(obj);
  flattenContent(obj);
  stripRootTransitions(obj);
  obj = collapseWhitespace(obj);
  if (omitEmpty) {
    obj = removeEmpty(obj) || {};
  }
  if (obj.initial_attribute !== undefined && obj.initial === undefined) {
    obj.initial = obj.initial_attribute;
    delete obj.initial_attribute;
  }
  for (const k of Object.keys(obj)) {
    if (k === '@_xmlns' || k.startsWith('xmlns')) {
      delete obj[k];
    }
  }
  if (obj.datamodel !== undefined) {
    if (typeof obj.datamodel === 'string') {
      obj.datamodel_attribute = obj.datamodel;
      delete obj.datamodel;
    } else if (Array.isArray(obj.datamodel) &&
               obj.datamodel.length === 1 &&
               typeof obj.datamodel[0] === 'string') {
      obj.datamodel_attribute = obj.datamodel[0];
      delete obj.datamodel;
    }
  }
  if (typeof obj.version === 'string') {
    const n = parseFloat(obj.version);
    if (!Number.isNaN(n)) obj.version = n;
  }
  if (obj.version === undefined) {
    obj.version = 1.0;
  }
  if (obj.datamodel_attribute === undefined) {
    obj.datamodel_attribute = 'null';
  }
  stripQnameNs(obj);
  reorderScxml(obj);
  stripNestedDataAttrs(obj);
  stripXmlns(obj);
  const valid = validate(obj);
  const errors = valid ? null : validate.errors;
  if (omitEmpty) {
    obj = removeEmpty(obj) || {};
    fixDataContent(obj);
    stripQnameNs(obj);
    stripNestedDataAttrs(obj);
    stripXmlns(obj);
  }
  let out = JSON.stringify(obj, null, 2);
  out = out.replace(/"version": 1(?=[,\n])/g, '"version": 1.0');
  return { result: out, valid, errors };
}

/**
 * Convert a scjson string to SCXML.
 *
 * Removes empty objects so that the generated XML does not include spurious
 * `<content/>` elements. Nested SCXML documents are also normalised after
 * restoring attribute names to ensure no stray wrapper nodes remain. The
 * function validates the input against the SCJSON schema before conversion.
 *
 * @param {string} jsonStr - JSON input.
 * @returns {{result: string, valid: boolean, errors: object[]|null}} Conversion outcome.
 */
function jsonToXml(jsonStr) {
  const builder = new XMLBuilder({
    ignoreAttributes: false,
    format: true,
    suppressEmptyNode: true,
    suppressBooleanAttributes: false,
  });
  let obj = JSON.parse(jsonStr);
  flattenContent(obj);
  obj = removeEmpty(obj) || {};
  const valid = validate(obj);
  const errors = valid ? null : validate.errors;
  // Remove defaults injected by validation that would misidentify
  // arbitrary XML content blocks as nested SCXML documents. Ajv
  // populates ``version`` and ``datamodel_attribute`` for objects
  // matching the ``Scxml`` schema. When the original JSON only
  // contains a ``qname`` field these defaults lead to erroneous
  // ``<scxml>`` wrappers being generated on output. Stripping the
  // fields prior to conversion preserves parity with the Python
  // implementation.
  stripNestedDataAttrs(obj);
  function restoreKeys(value) {
    if (Array.isArray(value)) {
      return value.map(restoreKeys);
    }
    if (value && typeof value === 'object') {
      if (Object.prototype.hasOwnProperty.call(value, 'qname')) {
        return restoreDataNode(value);
      }
      if (
        Object.keys(value).every(k => k === 'content' || k.endsWith('_value') || k === 'location' || k === 'expr' || k === 'src') &&
        Array.isArray(value.content) &&
        value.content.length === 1 &&
        value.content[0] &&
        typeof value.content[0] === 'object' &&
        (
          value.content[0].state ||
          value.content[0].parallel ||
          value.content[0].final ||
          value.content[0].datamodel ||
          value.content[0].datamodel_attribute !== undefined
        )
      ) {
        const outObj = {};
        for (const [k, v] of Object.entries(value)) {
          if (k !== 'content') {
            outObj[k.startsWith('@_') ? k : `@_${k}`] = v;
          }
        }
        outObj.scxml = restoreKeys(value.content[0]);
        return outObj;
      }
      const out = {};
      for (const [k, v] of Object.entries(value)) {
        let nk = k;
        if (k === 'if_value') {
          nk = 'if';
        } else if (k === 'raise_value') {
          nk = 'raise';
        } else if (k === 'else_value') {
          nk = 'else';
        }
        if (nk === 'other_attributes') {
          if (v && typeof v === 'object') {
            for (const [ak, av] of Object.entries(v)) {
              out[`@_${ak}`] = av;
            }
          }
          continue;
        }
        for (const [attr, prop] of Object.entries(ATTRIBUTE_MAP)) {
          if (prop === nk) {
            nk = `@_${attr}`;
            break;
          }
      }
        if (nk === 'script') {
          if (Array.isArray(v)) {
            out[nk] = v.map(item => {
              if (
                item &&
                typeof item === 'object' &&
                Array.isArray(item.content) &&
                item.content.every(x => typeof x === 'string')
              ) {
                return item.content.join('');
              }
              return restoreKeys(item);
            });
          } else {
            out[nk] = v;
          }
        } else if (nk === 'content') {
          if (Array.isArray(v)) {
            if (v.every(item => item && typeof item === 'object' && Object.prototype.hasOwnProperty.call(item, 'qname'))) {
              v.forEach(item => {
                const r = restoreDataNode(item);
                const [ck, cv] = Object.entries(r)[0];
                if (out[ck]) {
                  if (Array.isArray(out[ck])) {
                    out[ck].push(cv);
                  } else {
                    out[ck] = [out[ck], cv];
                  }
                } else {
                  out[ck] = cv;
                }
              });
              continue;
            }
            if (
              value.location !== undefined &&
              v.length === 1 &&
              v[0] &&
              typeof v[0] === 'object' &&
              (v[0].state || v[0].parallel || v[0].final || v[0].datamodel ||
                v[0].datamodel_attribute !== undefined)
            ) {
              const cv = restoreKeys(v[0]);
              out.scxml = cv;
              continue;
            }
            out[nk] = v.map(item => {
              if (
                item &&
                typeof item === 'object' &&
                (item.state || item.parallel || item.final || item.datamodel ||
                 item.datamodel_attribute !== undefined)
              ) {
                return { scxml: restoreKeys(item) };
              }
              if (
                item &&
                typeof item === 'object' &&
                Object.keys(item).length === 1 &&
                Array.isArray(item.content) &&
                item.content.every(x => typeof x !== 'object')
              ) {
                return item.content.join('');
              }
              return restoreKeys(item);
            });
          } else if (
            v &&
            typeof v === 'object' &&
            (v.state || v.parallel || v.final || v.datamodel ||
             v.datamodel_attribute !== undefined)
          ) {
            out[nk] = { scxml: restoreKeys(v) };
          } else if (
            v &&
            typeof v === 'object' &&
            Object.keys(v).length === 1 &&
            Array.isArray(v.content) &&
            v.content.every(x => typeof x !== 'object')
          ) {
            out[nk] = v.content.join('');
          } else {
            out[nk] = restoreKeys(v);
          }
        } else if (Array.isArray(v) && v.every(x => typeof x !== 'object')) {
          const val = v.join(' ');
          if (nk.startsWith('@_')) {
            out[nk] = val;
          } else {
            out[`@_${nk}`] = val;
          }
        } else if (v === null || typeof v !== 'object') {
          if (nk.startsWith('@_')) {
            out[nk] = v;
          } else {
            out[`@_${nk}`] = v;
          }
        } else {
          out[nk] = restoreKeys(v);
        }
      }
      if (
        Array.isArray(out.content) &&
        out.content.every(x => typeof x !== 'object')
      ) {
        const others = Object.keys(out).filter(
          k => k !== 'content' && !k.startsWith('@_')
        );
        const attrs = Object.keys(out).filter(k => k.startsWith('@_'));
        const sendAttrs = [
          '@_event',
          '@_eventexpr',
          '@_target',
          '@_targetexpr',
          '@_type',
          '@_type_value',
          '@_delay',
          '@_delayexpr',
          '@_namelist',
        ];
        const isSend = attrs.some(a => sendAttrs.includes(a));
        if (others.length === 0 && !isSend) {
          out['#text'] = out.content.join('');
          delete out.content;
        }
      }
      return out;
    }
    return value;
  }
  const restored = restoreKeys(obj);
  const cleaned = removeEmpty(restored) || {};
  if (cleaned['@_xmlns'] === undefined) {
    cleaned['@_xmlns'] = 'http://www.w3.org/2005/07/scxml';
  }
  return { result: builder.build({ scxml: cleaned }), valid, errors };
}

module.exports = {
  xmlToJson,
  jsonToXml,
  removeEmpty,
  normaliseKeys,
  ensureArrays,
  fixScripts,
  fixNestedScxml,
  fixAssignDefaults,
  fixSendDefaults,
  fixSendContent,
  fixDonedataContent,
  fixOtherAttributes,
  decodeEntities,
  restoreDataNode,
  flattenContent,
  splitTokenAttrs,
  fixEmptyElse,
  fixEmptyOnentry,
  stripRootTransitions,
  stripQnameNs,
  reorderScxml,
  stripNestedDataAttrs,
  stripXmlns,
};
