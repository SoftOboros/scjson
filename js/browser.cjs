/**
 * Agent Name: js-cli
 *
 * Part of the scjson project.
 * Developed by Softoboros Technology Inc.
 * Licensed under the BSD 1-Clause License.
 */

const fs = require('fs');
const path = require('path');
const { Command } = require('commander');
const { XMLParser, XMLBuilder } = require('fast-xml-parser');
const Ajv = require('ajv');

const program = new Command();
const schema = require('./scjson.schema.json');

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
function jsonToXml(jsonStr) {
  const builder = new XMLBuilder({ ignoreAttributes: false, format: true });
  const obj = JSON.parse(jsonStr);
  if (!validate(obj)) {
    throw new Error('Invalid scjson');
  }
  return builder.build({ scxml: obj });
}

program
  .name('scjson')
  .description('SCXML <-> scjson converter and validator');

program
  .command('validate')
  .description('validate a scjson or SCXML file by round-tripping it')
  .argument('<file>', 'file path')
  .option('-r, --recursive', 'recurse into directories')
  .action((file, options) => {
    const src = path.resolve(file);
    let success = true;

    function validateFile(p) {
      const data = fs.readFileSync(p, 'utf8');
      try {
        if (p.endsWith('.scxml')) {
          const json = xmlToJson(data);
          jsonToXml(json);
        } else if (p.endsWith('.scjson')) {
          const xml = jsonToXml(data);
          xmlToJson(xml);
        } else {
          return;
        }
      } catch (e) {
        console.error(`Validation failed for ${p}: ${e.message}`);
        success = false;
      }
    }

    if (fs.statSync(src).isDirectory()) {
      const pattern = options.recursive ? '**/*' : '*';
      const files = require('glob').sync(pattern, { cwd: src, nodir: true });
      files.forEach(f => validateFile(path.join(src, f)));
    } else {
      validateFile(src);
    }

    if (!success) {
      process.exitCode = 1;
    }
  });

function convertDirectoryJson(inputDir, outputDir, recursive, verify, keepEmpty) {
  const pattern = recursive ? '**/*.scxml' : '*.scxml';
  const files = require('glob').sync(pattern, { cwd: inputDir, nodir: true });
  files.forEach(f => {
    const src = path.join(inputDir, f);
    const dest = path.join(outputDir, f.replace(/\.scxml$/, '.scjson'));
    convertScxmlFile(src, dest, verify, keepEmpty);
  });
}

function convertDirectoryXml(inputDir, outputDir, recursive, verify, keepEmpty) {
  const pattern = recursive ? '**/*.scjson' : '*.scjson';
  const files = require('glob').sync(pattern, { cwd: inputDir, nodir: true });
  files.forEach(f => {
    const src = path.join(inputDir, f);
    const dest = path.join(outputDir, f.replace(/\.scjson$/, '.scxml'));
    convertScjsonFile(src, dest, verify, keepEmpty);
  });
}

function convertScxmlFile(src, dest, verify, keepEmpty) {
  const xmlStr = fs.readFileSync(src, 'utf8');
  try {
    const jsonStr = xmlToJson(xmlStr, !keepEmpty);
    if (verify) {
      jsonToXml(jsonStr);
    } else {
      fs.mkdirSync(path.dirname(dest), { recursive: true });
      fs.writeFileSync(dest, jsonStr);
    }
    if (verify) console.log(`Verified ${src}`);
  } catch (e) {
    console.error(`Failed to convert ${src}: ${e.message}`);
  }
}

function convertScjsonFile(src, dest, verify) {
  const jsonStr = fs.readFileSync(src, 'utf8');
  try {
    const xmlStr = jsonToXml(jsonStr);
    if (verify) {
      xmlToJson(xmlStr);
    } else {
      fs.mkdirSync(path.dirname(dest), { recursive: true });
      fs.writeFileSync(dest, xmlStr);
    }
    if (verify) console.log(`Verified ${src}`);
  } catch (e) {
    console.error(`Failed to convert ${src}: ${e.message}`);
  }
}

program
  .command('json')
  .argument('<path>', 'SCXML file or directory')
  .option('-o, --output <path>', 'output file or directory')
  .option('-r, --recursive', 'recurse into directories')
  .option('-v, --verify', 'verify conversion without writing output')
  .option('--keep-empty', 'keep null or empty items when producing JSON')
  .action((p, opts) => {
    const src = path.resolve(p);
    const out = opts.output ? path.resolve(opts.output) : src;

    if (fs.statSync(src).isDirectory()) {
      convertDirectoryJson(src, out, opts.recursive, opts.verify, opts.keepEmpty);
    } else {
      const dest = opts.output && !opts.output.endsWith('.json') && !opts.output.endsWith('.scjson')
        ? path.join(out, path.basename(src).replace(/\.scxml$/, '.scjson'))
        : (opts.output || src.replace(/\.scxml$/, '.scjson'));
      convertScxmlFile(src, dest, opts.verify, opts.keepEmpty);
    }
  });

program
  .command('xml')
  .argument('<path>', 'scjson file or directory')
  .option('-o, --output <path>', 'output file or directory')
  .option('-r, --recursive', 'recurse into directories')
  .option('-v, --verify', 'verify conversion without writing output')
  .option('--keep-empty', 'keep null or empty items when producing JSON')
  .action((p, opts) => {
    const src = path.resolve(p);
    const out = opts.output ? path.resolve(opts.output) : src;

    if (fs.statSync(src).isDirectory()) {
      convertDirectoryXml(src, out, opts.recursive, opts.verify, opts.keepEmpty);
    } else {
      const dest = opts.output && !opts.output.endsWith('.xml') && !opts.output.endsWith('.scxml')
        ? path.join(out, path.basename(src).replace(/\.scjson$/, '.scxml'))
        : (opts.output || src.replace(/\.scjson$/, '.scxml'));
      convertScjsonFile(src, dest, opts.verify, opts.keepEmpty);
    }
  });

if (require.main === module) {
  program.parse(process.argv);
}

module.exports = { program, xmlToJson, jsonToXml };
