const { execSync } = require('child_process');
const path = require('path');

test('shows help', () => {
  const cliPath = path.resolve(__dirname, '../bin/scjson.js');
  const out = execSync(`node ${cliPath} --help`).toString();
  expect(out).toMatch(/convert/);
});
