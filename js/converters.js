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
  'initial_attribute',
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
 * Collapse whitespace in string values recursively.
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
      value[k] = collapseWhitespace(v);
    }
    return value;
  }
  if (typeof value === 'string') {
    return value.replace(/[\n\r\t]/g, ' ');
  }
  return value;
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
          out.content = out.content || [];
          if (Array.isArray(text)) {
            out.content.push(...text);
          } else {
            out.content.push(text);
          }
        }
        continue;
      }
      let nk = k;
      if (k.startsWith('@_')) {
        const attr = k.slice(2);
        nk = ATTRIBUTE_MAP[attr] || attr;
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
function ensureArrays(obj) {
  if (!obj || typeof obj !== 'object') {
    return;
  }
  for (const [k, v] of Object.entries(obj)) {
    if (ARRAY_KEYS.has(k) && v !== undefined) {
      if (Array.isArray(v)) {
        v.forEach(ensureArrays);
      } else {
        obj[k] = [v];
        ensureArrays(obj[k][0]);
      }
      continue;
    }
    if (k === 'transition' && v && typeof v === 'object') {
      const arr = Array.isArray(v) ? v : [v];
      arr.forEach(tr => {
        if (tr.target !== undefined && !Array.isArray(tr.target)) {
          tr.target = [tr.target];
        }
        ensureArrays(tr);
      });
      obj[k] = arr;
      continue;
    }
    if (Array.isArray(v)) {
      v.forEach(ensureArrays);
    } else if (typeof v === 'object') {
      ensureArrays(v);
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
 * Remove nulls and empty containers from values recursively.
 *
 * @param {*} value - Candidate value.
 * @returns {*} Sanitised value.
 */
function removeEmpty(value) {
  if (Array.isArray(value)) {
    const arr = value.map(removeEmpty).filter(v => v !== undefined);
    return arr.length > 0 ? arr : undefined;
  }
  if (value && typeof value === 'object') {
    const obj = {};
    for (const [k, v] of Object.entries(value)) {
      const r = removeEmpty(v);
      if (r !== undefined) obj[k] = r;
    }
    return Object.keys(obj).length > 0 ? obj : undefined;
  }
  if (value === null) {
    return undefined;
  }
  if (value === '') {
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
 * @returns {string} JSON representation.
 *
 * Removes the XML namespace attribute and injects default values
 * expected by the schema.
 */
function xmlToJson(xmlStr, omitEmpty = true) {
  const parser = new XMLParser({ ignoreAttributes: false });
  let obj = parser.parse(xmlStr);
  if (obj.scxml) {
    obj = obj.scxml;
  }
  obj = normaliseKeys(obj);
  if (omitEmpty) {
    obj = removeEmpty(obj) || {};
  }
  ensureArrays(obj);
  fixScripts(obj);
  obj = collapseWhitespace(obj);
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
  if (!validate(obj)) {
    throw new Error('Invalid scjson');
  }
  if (omitEmpty) {
    obj = removeEmpty(obj) || {};
  }
  return JSON.stringify(obj, null, 2);
}

/**
 * Convert a scjson string to SCXML.
 *
 * @param {string} jsonStr - JSON input.
 * @returns {string} XML output.
 */
function jsonToXml(jsonStr) {
  const builder = new XMLBuilder({ ignoreAttributes: false, format: true });
  const obj = JSON.parse(jsonStr);
  if (!validate(obj)) {
    throw new Error('Invalid scjson');
  }
  return builder.build({ scxml: obj });
}

module.exports = {
  xmlToJson,
  jsonToXml,
  removeEmpty,
  normaliseKeys,
  ensureArrays,
  fixScripts,
};
