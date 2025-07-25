/**
 * Agent Name: js-cli
 *
 * Part of the scjson project.
 * Developed by Softoboros Technology Inc.
 * Licensed under the BSD 1-Clause License.
 */

/**
 * @file Command line interface for converting SCXML and scjson files.
 */

const fs = require('fs');
const path = require('path');
const { Command } = require('commander');
const {
  xmlToJson,
  jsonToXml,
} = require('./converters.js');


const program = new Command();



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

/**
 * Convert all SCXML files in a directory to scjson.
 *
 * @param {string} inputDir - Directory containing SCXML files.
 * @param {string} outputDir - Destination directory for scjson output.
 * @param {boolean} recursive - Recurse into subdirectories when true.
 * @param {boolean} verify - Verify conversion without writing output.
 * @param {boolean} keepEmpty - Keep null or empty elements when true.
 * @returns {boolean} True if all files converted successfully.
 */
function convertDirectoryJson(inputDir, outputDir, recursive, verify, keepEmpty) {
  const pattern = recursive ? '**/*.scxml' : '*.scxml';
  const files = require('glob').sync(pattern, { cwd: inputDir, nodir: true });
  let success = true;
  files.forEach(f => {
    const src = path.join(inputDir, f);
    const dest = path.join(outputDir, f.replace(/\.scxml$/, '.scjson'));
    if (!convertScxmlFile(src, dest, verify, keepEmpty)) {
      success = false;
    }
  });
  return success;
}

/**
 * Convert all scjson files in a directory to SCXML.
 *
 * @param {string} inputDir - Directory containing scjson files.
 * @param {string} outputDir - Destination directory for SCXML output.
 * @param {boolean} recursive - Recurse into subdirectories when true.
 * @param {boolean} verify - Verify conversion without writing output.
 * @param {boolean} keepEmpty - Keep null or empty elements when true.
 * @returns {boolean} True if all files converted successfully.
 */
function convertDirectoryXml(inputDir, outputDir, recursive, verify, keepEmpty) {
  const pattern = recursive ? '**/*.scjson' : '*.scjson';
  const files = require('glob').sync(pattern, { cwd: inputDir, nodir: true });
  let success = true;
  files.forEach(f => {
    const src = path.join(inputDir, f);
    const dest = path.join(outputDir, f.replace(/\.scjson$/, '.scxml'));
    if (!convertScjsonFile(src, dest, verify, keepEmpty)) {
      success = false;
    }
  });
  return success;
}

/**
 * Convert a single SCXML file to scjson.
 *
 * @param {string} src - Path to the source SCXML file.
 * @param {string} dest - Output path for the scjson file.
 * @param {boolean} verify - Verify conversion without writing output.
 * @param {boolean} keepEmpty - Keep null or empty elements when true.
 * @returns {boolean} True if the conversion succeeded.
 */
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
    return true;
  } catch (e) {
    if (e.errors) {
      console.error(`Failed to convert ${src}: ${e.message}\n${JSON.stringify(e.errors, null, 2)}`);
    } else {
      console.error(`Failed to convert ${src}: ${e.message}`);
    }
    return false;
  }
}

/**
 * Convert a single scjson file to SCXML.
 *
 * @param {string} src - Path to the source scjson file.
 * @param {string} dest - Output path for the SCXML file.
 * @param {boolean} verify - Verify conversion without writing output.
 * @returns {boolean} True if the conversion succeeded.
 */
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
    return true;
  } catch (e) {
    if (e.errors) {
      console.error(`Failed to convert ${src}: ${e.message}\n${JSON.stringify(e.errors, null, 2)}`);
    } else {
      console.error(`Failed to convert ${src}: ${e.message}`);
    }
    return false;
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
