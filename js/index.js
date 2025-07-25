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

function convertDirectoryJson(inputDir, outputDir, recursive, verify, keepEmpty) {
  const pattern = recursive ? '**/*.scxml' : '*.scxml';
  const files = require('glob').sync(pattern, { cwd: inputDir, nodir: true });
  let success = true;
  files.forEach(f => {
    const src = path.join(inputDir, f);
    const dest = path.join(outputDir, f.replace(/\.scxml$/, '.scjson'));
    success = convertScxmlFile(src, dest, verify, keepEmpty) && success;
  });
  if (verify && !success) {
    process.exitCode = 1;
  }
  return success;
}

function convertDirectoryXml(inputDir, outputDir, recursive, verify, keepEmpty) {
  const pattern = recursive ? '**/*.scjson' : '*.scjson';
  const files = require('glob').sync(pattern, { cwd: inputDir, nodir: true });
  let success = true;
  files.forEach(f => {
    const src = path.join(inputDir, f);
    const dest = path.join(outputDir, f.replace(/\.scjson$/, '.scxml'));
    success = convertScjsonFile(src, dest, verify, keepEmpty) && success;
  });
  if (verify && !success) {
    process.exitCode = 1;
  }
  return success;
}

function convertScxmlFile(src, dest, verify, keepEmpty) {
  const xmlStr = fs.readFileSync(src, 'utf8');
  try {
    const { result: jsonStr, valid, errors } = xmlToJson(xmlStr, !keepEmpty);
    if (!valid) {
      console.warn(
        `Validation failed in xmlToJson for ${src}: ${JSON.stringify(errors, null, 2)}`,
      );
    }
    if (verify) {
      const { valid: xmlValid, errors: xmlErrors } = jsonToXml(jsonStr);
      if (!xmlValid) {
        console.warn(
          `Validation failed in jsonToXml for ${src}: ${JSON.stringify(xmlErrors, null, 2)}`,
        );
      }
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

function convertScjsonFile(src, dest, verify) {
  const jsonStr = fs.readFileSync(src, 'utf8');
  try {
    const { result: xmlStr, valid, errors } = jsonToXml(jsonStr);
    if (!valid) {
      console.warn(
        `Validation failed in jsonToXml for ${src}: ${JSON.stringify(errors, null, 2)}`,
      );
    }
    if (verify) {
      const { valid: jsonValid, errors: jsonErrors } = xmlToJson(xmlStr);
      if (!jsonValid) {
        console.warn(
          `Validation failed in xmlToJson for ${src}: ${JSON.stringify(jsonErrors, null, 2)}`,
        );
      }
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
      const success = convertDirectoryJson(src, out, opts.recursive, opts.verify, opts.keepEmpty);
      if (opts.verify && !success) process.exitCode = 1;
    } else {
      const dest = opts.output && !opts.output.endsWith('.json') && !opts.output.endsWith('.scjson')
        ? path.join(out, path.basename(src).replace(/\.scxml$/, '.scjson'))
        : (opts.output || src.replace(/\.scxml$/, '.scjson'));
      const success = convertScxmlFile(src, dest, opts.verify, opts.keepEmpty);
      if (opts.verify && !success) process.exitCode = 1;
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
      if (opts.verify && !success) process.exitCode = 1;
    } else {
      const dest = opts.output && !opts.output.endsWith('.xml') && !opts.output.endsWith('.scxml')
        ? path.join(out, path.basename(src).replace(/\.scjson$/, '.scxml'))
        : (opts.output || src.replace(/\.scjson$/, '.scxml'));
      const success = convertScjsonFile(src, dest, opts.verify, opts.keepEmpty);
      if (opts.verify && !success) process.exitCode = 1;
    }
  });

if (require.main === module) {
  program.parse(process.argv);
}

module.exports = { program, xmlToJson, jsonToXml };
