/**
 * Agent Name: js-browser
 *
 * Part of the scjson project.
 * Developed by Softoboros Technology Inc.
 * Licensed under the BSD 1-Clause License.
 */

/**
 * @file Browser friendly utilities re-exporting the core converters.
 */

import core from './converters.js';

export const { xmlToJson, jsonToXml, removeEmpty, normaliseKeys, ensureArrays } = core;
