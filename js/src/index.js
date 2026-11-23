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

// Yield relative source names. A recursive conversion does not follow
// directory symlinks or include hidden files.
function* inputFiles(directory, recursive, prefix = '') {
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    if (entry.name.startsWith('.')) continue;
    const relative = path.join(prefix, entry.name);
    const full = path.join(directory, entry.name);
    if (entry.isDirectory()) {
      if (recursive) yield* inputFiles(full, true, relative);
    } else if (entry.isFile() || (entry.isSymbolicLink() && fs.statSync(full, { throwIfNoEntry: false })?.isFile())) {
      yield relative;
    }
  }
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
      if (p.endsWith('.scxml') && !convertScxmlFile(p, undefined, true, false)) {
        success = false;
      } else if (p.endsWith('.scjson') && !convertScjsonFile(p, undefined, true)) {
        success = false;
      }
    }

    if (fs.statSync(src).isDirectory()) {
      for (const f of inputFiles(src, options.recursive)) validateFile(path.join(src, f));
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
  let success = true;
  for (const f of inputFiles(inputDir, recursive)) {
    if (!f.endsWith('.scxml')) continue;
    const src = path.join(inputDir, f);
    const dest = path.join(outputDir, f.replace(/\.scxml$/, '.scjson'));
    if (!convertScxmlFile(src, dest, verify, keepEmpty)) {
      success = false;
    }
  }
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
  let success = true;
  for (const f of inputFiles(inputDir, recursive)) {
    if (!f.endsWith('.scjson')) continue;
    const src = path.join(inputDir, f);
    const dest = path.join(outputDir, f.replace(/\.scjson$/, '.scxml'));
    if (!convertScjsonFile(src, dest, verify, keepEmpty)) {
      success = false;
    }
  }
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
    const { result: jsonStr, valid, errors } = xmlToJson(xmlStr, !keepEmpty);
    if (!valid) {
      console.warn(
        `Validation failed in xmlToJson for ${src}: ${JSON.stringify(errors, null, 2)}`,
      );
      if (verify || !jsonStr) return false;
    }
    if (verify) {
      const { valid: xmlValid, errors: xmlErrors } = jsonToXml(jsonStr);
      if (!xmlValid) {
        console.warn(
          `Validation failed in jsonToXml for ${src}: ${JSON.stringify(xmlErrors, null, 2)}`,
        );
        return false;
      }
    } else {
      fs.mkdirSync(path.dirname(dest), { recursive: true });
      fs.writeFileSync(dest, jsonStr);
    }
    if (verify) console.log(`Verified ${src}`);
    return true;
  } catch (e) {
    const failure = verify ? 'Validation failed for' : 'Failed to convert';
    if (e.errors) {
      console.error(`${failure} ${src}: ${e.message}\n${JSON.stringify(e.errors, null, 2)}`);
    } else {
      console.error(`${failure} ${src}: ${e.message}`);
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
    const { result: xmlStr, valid, errors } = jsonToXml(jsonStr);
    if (!valid) {
      console.warn(
        `Validation failed in jsonToXml for ${src}: ${JSON.stringify(errors, null, 2)}`,
      );
      if (verify || !xmlStr) return false;
    }
    if (verify) {
      const { valid: jsonValid, errors: jsonErrors } = xmlToJson(xmlStr);
      if (!jsonValid) {
        console.warn(
          `Validation failed in xmlToJson for ${src}: ${JSON.stringify(jsonErrors, null, 2)}`,
        );
        return false;
      }
    } else {
      fs.mkdirSync(path.dirname(dest), { recursive: true });
      fs.writeFileSync(dest, xmlStr);
    }
    if (verify) console.log(`Verified ${src}`);
    return true;
  } catch (e) {
    const failure = verify ? 'Validation failed for' : 'Failed to convert';
    if (e.errors) {
      console.error(`${failure} ${src}: ${e.message}\n${JSON.stringify(e.errors, null, 2)}`);
    } else {
      console.error(`${failure} ${src}: ${e.message}`);
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
      const success = convertDirectoryJson(src, out, opts.recursive, opts.verify, opts.keepEmpty);
      if (!success) process.exitCode = 1;
    } else {
      const dest = opts.output && !opts.output.endsWith('.json') && !opts.output.endsWith('.scjson')
        ? path.join(out, path.basename(src).replace(/\.scxml$/, '.scjson'))
        : (opts.output || src.replace(/\.scxml$/, '.scjson'));
      const success = convertScxmlFile(src, dest, opts.verify, opts.keepEmpty);
      if (!success) process.exitCode = 1;
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
      const success = convertDirectoryXml(src, out, opts.recursive, opts.verify, opts.keepEmpty);
      if (!success) process.exitCode = 1;
    } else {
      const dest = opts.output && !opts.output.endsWith('.xml') && !opts.output.endsWith('.scxml')
        ? path.join(out, path.basename(src).replace(/\.scjson$/, '.scxml'))
        : (opts.output || src.replace(/\.scjson$/, '.scxml'));
      const success = convertScjsonFile(src, dest, opts.verify, opts.keepEmpty);
      if (!success) process.exitCode = 1;
    }
  });

if (require.main === module) {
  program.parse(process.argv);
}

module.exports = { program, xmlToJson, jsonToXml };
