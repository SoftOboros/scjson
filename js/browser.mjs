/**
 * Agent Name: js-browser
 *
 * Part of the scjson project.
 * Developed by Softoboros Technology Inc.
 * Licensed under the BSD 1-Clause License.
 */

/**
 * @file Browser friendly utilities for converting SCXML to scjson and back.
 */

import { XMLParser, XMLBuilder } from 'fast-xml-parser';
import Ajv from 'ajv';
import schema from '../scjson.schema.json' assert { type: 'json' };

const ajv = new Ajv({ useDefaults: true, strict: false });
const validate = ajv.compile(schema);

/**
 * Remove nulls and empty containers from values recursively.
 *
 * @param {*} value - Candidate value.
 * @returns {*} Sanitised value.
 */
export function removeEmpty(value) {
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
  if (value === null || value === '') {
    return undefined;
  }
  return value;
}

/**
 * Convert an SCXML string to scjson.
 *
 * @param {string} xmlStr - XML input.
 * @param {boolean} [omitEmpty=true] - Remove empty values when true.
 * @returns {string} JSON representation.
 */
export function xmlToJson(xmlStr, omitEmpty = true) {
  const parser = new XMLParser({ ignoreAttributes: false });
  let obj = parser.parse(xmlStr);
  if (obj.scxml) {
    obj = obj.scxml;
  }
  if (omitEmpty) {
    obj = removeEmpty(obj) || {};
  }
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
export function jsonToXml(jsonStr) {
  const builder = new XMLBuilder({ ignoreAttributes: false, format: true });
  const obj = JSON.parse(jsonStr);
  if (!validate(obj)) {
    throw new Error('Invalid scjson');
  }
  return builder.build({ scxml: obj });
}
