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
const schema = require('./scjson.schema.json');

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
  const text = element.textContent?.trim();
  if (text && element.children.length === 0) {
    result.content = [text];
  }

  return result;
}

/**
 * Keys that should never be pruned even when empty.
 */
const ALWAYS_KEEP = new Set(['else_value', 'final']);

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
        value[k] = v.replace(/[\n\r\t]/g, ' ');
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
        if (parent !== 'history') {
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
      if (parent !== 'history') {
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
      value.content = arr;
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
    if (Object.prototype.hasOwnProperty.call(value, 'send')) {
      const arr = Array.isArray(value.send) ? value.send : [value.send];
      arr.forEach(s => {
        if (Object.prototype.hasOwnProperty.call(s, 'content')) {
          const cArr = Array.isArray(s.content) ? s.content : [s.content];
          s.content = cArr.map(c => {
            if (typeof c !== 'object') {
              return { content: [String(c)] };
            }
            if (c && typeof c === 'object') {
              if (typeof c.content === 'string' || typeof c.content === 'number' || typeof c.content === 'boolean') {
                c.content = [String(c.content)];
              }
              fixSendContent(c);
              return c;
            }
            return c;
          });
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
      value.content[0].content.every(x => typeof x !== 'object')
    ) {
      value.content = [value.content[0].content.join('')];
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
    return arr.length > 0 ? arr : undefined;
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
    if (
      key &&
      (key.endsWith('_attribute') ||
       key.endsWith('_value') ||
       ['expr', 'cond', 'event', 'target', 'id', 'name', 'label'].includes(key))
    ) {
      return '';
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
  fixNestedScxml(obj);
  fixEmptyElse(obj);
  obj = collapseWhitespace(obj);
  splitTokenAttrs(obj);
  ensureArrays(obj);
  fixScripts(obj);
  fixAssignDefaults(obj);
  fixSendDefaults(obj);
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
  const valid = validate(obj);
  const errors = valid ? null : validate.errors;
  if (omitEmpty) {
    obj = removeEmpty(obj) || {};
  }
  let out = JSON.stringify(obj, null, 2);
  out = out.replace(/"version": 1(?=[,\n])/g, '"version": 1.0');
  return { result: out, valid, errors };
}

/**
 * Convert a scjson string to SCXML.
 *
 * Removes empty objects so that the generated XML does not include spurious
 * `<content/>` elements. The function validates the input against the SCJSON
 * schema before conversion.
 *
 * @param {string} jsonStr - JSON input.
 * @returns {{result: string, valid: boolean, errors: object[]|null}} Conversion outcome.
 */
function jsonToXml(jsonStr) {
  const builder = new XMLBuilder({
    ignoreAttributes: false,
    format: true,
    suppressEmptyNode: true,
  });
  let obj = JSON.parse(jsonStr);
  flattenContent(obj);
  obj = removeEmpty(obj) || {};
  const valid = validate(obj);
  const errors = valid ? null : validate.errors;
  function restoreKeys(value) {
    if (Array.isArray(value)) {
      return value.map(restoreKeys);
    }
    if (value && typeof value === 'object') {
      if (
        Object.keys(value).length === 1 &&
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
        return { scxml: restoreKeys(value.content[0]) };
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
  if (restored['@_xmlns'] === undefined) {
    restored['@_xmlns'] = 'http://www.w3.org/2005/07/scxml';
  }
  return { result: builder.build({ scxml: restored }), valid, errors };
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
  flattenContent,
  splitTokenAttrs,
  fixEmptyElse,
  stripRootTransitions,
  stripQnameNs,
  reorderScxml,
};
