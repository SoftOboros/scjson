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
  'target',
  'transition',
]);

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
      const nk = k.startsWith('@_') ? k.slice(2) : k;
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
    if (Array.isArray(v)) {
      v.forEach(ensureArrays);
    } else if (typeof v === 'object') {
      ensureArrays(v);
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
  if (obj['@_xmlns']) {
    delete obj['@_xmlns'];
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
};
