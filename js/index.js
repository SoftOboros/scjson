const fs = require('fs');
const path = require('path');
const { Command } = require('commander');
const { XMLParser, XMLBuilder } = require('fast-xml-parser');
const Ajv = require('ajv');

const program = new Command();
const schema = require('../scjson.schema.json');

program
  .name('scjson')
  .description('SCXML <-> scjson converter and validator');

program.command('validate')
  .description('validate a scjson file against the schema')
  .argument('<file>', 'scjson file path')
  .action((file) => {
    const data = JSON.parse(fs.readFileSync(file, 'utf8'));
    const ajv = new Ajv();
    const validate = ajv.compile(schema);
    if (validate(data)) {
      console.log('Valid scjson');
    } else {
      console.error('Invalid scjson');
      console.error(validate.errors);
      process.exitCode = 1;
    }
  });

program.command('convert')
  .description('convert between scxml and scjson')
  .requiredOption('--from <format>', 'source format (scxml|scjson)')
  .requiredOption('--to <format>', 'target format (scxml|scjson)')
  .requiredOption('--input <file>', 'input file path')
  .requiredOption('--output <file>', 'output file path')
  .action((opts) => {
    const from = opts.from.toLowerCase();
    const to = opts.to.toLowerCase();
    if (from === 'scxml' && to === 'scjson') {
      const xml = fs.readFileSync(opts.input, 'utf8');
      const parser = new XMLParser();
      const obj = parser.parse(xml);
      fs.writeFileSync(opts.output, JSON.stringify(obj, null, 2));
    } else if (from === 'scjson' && to === 'scxml') {
      const json = JSON.parse(fs.readFileSync(opts.input, 'utf8'));
      const builder = new XMLBuilder({ ignoreAttributes: false, format: true });
      const xml = builder.build(json);
      fs.writeFileSync(opts.output, xml);
    } else {
      console.error('Unsupported conversion');
      process.exitCode = 1;
    }
  });

if (require.main === module) {
  program.parse(process.argv);
}

module.exports = { program };
