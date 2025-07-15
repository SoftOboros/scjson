/**
 * Agent Name: js-cli-tests
 *
 * Part of the scjson project.
 * Developed by Softoboros Technology Inc.
 * Licensed under the BSD 1-Clause License.
 */

const fs = require('fs');
const os = require('os');
const path = require('path');
const { execSync } = require('child_process');

const cliPath = path.resolve(__dirname, '../bin/scjson.js');

function createScxml() {
  return '<scxml xmlns="http://www.w3.org/2005/07/scxml"/>';
}

function createScjson() {
  const json = {
    version: 1,
    datamodel_attribute: 'null',
  };
  return JSON.stringify(json, null, 2);
}

describe('scjson CLI', () => {
  test('shows help', () => {
    const out = execSync(`node ${cliPath} --help`).toString();
    expect(out).toMatch(/scjson/);
  });

  test('single json conversion', () => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'scjson-'));
    const xmlPath = path.join(dir, 'sample.scxml');
    fs.writeFileSync(xmlPath, createScxml());

    execSync(`node ${cliPath} json ${xmlPath}`);

    const outPath = path.join(dir, 'sample.scjson');
    expect(fs.existsSync(outPath)).toBe(true);
    const data = JSON.parse(fs.readFileSync(outPath, 'utf8'));
    expect(data.version).toBe(1);
  });

  test('directory json conversion', () => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'scjson-'));
    const srcDir = path.join(dir, 'src');
    fs.mkdirSync(srcDir);
    ['a', 'b'].forEach(n => {
      fs.writeFileSync(path.join(srcDir, `${n}.scxml`), createScxml());
    });

    execSync(`node ${cliPath} json ${srcDir}`);

    ['a', 'b'].forEach(n => {
      expect(fs.existsSync(path.join(srcDir, `${n}.scjson`))).toBe(true);
    });
  });

  test('single xml conversion', () => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'scjson-'));
    const jsonPath = path.join(dir, 'sample.scjson');
    fs.writeFileSync(jsonPath, createScjson());

    execSync(`node ${cliPath} xml ${jsonPath}`);

    const outPath = path.join(dir, 'sample.scxml');
    expect(fs.existsSync(outPath)).toBe(true);
    const data = fs.readFileSync(outPath, 'utf8');
    expect(data).toMatch(/scxml/);
  });

  test('directory xml conversion', () => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'scjson-'));
    const srcDir = path.join(dir, 'jsons');
    fs.mkdirSync(srcDir);
    ['x', 'y'].forEach(n => {
      fs.writeFileSync(path.join(srcDir, `${n}.scjson`), createScjson());
    });

    execSync(`node ${cliPath} xml ${srcDir}`);

    ['x', 'y'].forEach(n => {
      expect(fs.existsSync(path.join(srcDir, `${n}.scxml`))).toBe(true);
    });
  });

  function buildDataset(base) {
    const d1 = path.join(base, 'level1');
    const d2 = path.join(d1, 'level2');
    fs.mkdirSync(d2, { recursive: true });
    ['a', 'b'].forEach(n => {
      fs.writeFileSync(path.join(d1, `${n}.scxml`), createScxml());
      fs.writeFileSync(path.join(d2, `${n}.scxml`), createScxml());
    });
  }

  test('recursive conversion', () => {
    const dataset = fs.mkdtempSync(path.join(os.tmpdir(), 'scjson-'));
    buildDataset(dataset);
    const scjsonDir = path.join(dataset, 'outjson');
    const scxmlDir = path.join(dataset, 'outxml');

    execSync(`node ${cliPath} json ${dataset} -o ${scjsonDir} -r`);
    execSync(`node ${cliPath} xml ${scjsonDir} -o ${scxmlDir} -r`);

    const jsonFiles = require('glob').sync('**/*.scjson', { cwd: scjsonDir, nodir: true });
    const xmlFiles = require('glob').sync('**/*.scxml', { cwd: scxmlDir, nodir: true });

    expect(jsonFiles.length).toBeGreaterThan(0);
    expect(xmlFiles.length).toBeGreaterThan(0);
    expect(xmlFiles.length).toBeLessThanOrEqual(jsonFiles.length);
  });

  test('recursive validation', () => {
    const dataset = fs.mkdtempSync(path.join(os.tmpdir(), 'scjson-'));
    buildDataset(dataset);
    const scjsonDir = path.join(dataset, 'outjson');
    const scxmlDir = path.join(dataset, 'outxml');

    execSync(`node ${cliPath} json ${dataset} -o ${scjsonDir} -r`);
    execSync(`node ${cliPath} xml ${scjsonDir} -o ${scxmlDir} -r`);

    // Corrupt one file to trigger failure
    fs.writeFileSync(path.join(scjsonDir, 'corrupt.scjson'), 'bad');

    let failed = false;
    try {
      execSync(`node ${cliPath} validate ${dataset} -r`, { stdio: 'pipe' });
    } catch {
      failed = true;
    }
    expect(failed).toBe(true);
  });

  test('recursive verify', () => {
    const dataset = fs.mkdtempSync(path.join(os.tmpdir(), 'scjson-'));
    buildDataset(dataset);
    const scjsonDir = path.join(dataset, 'outjson');
    const scxmlDir = path.join(dataset, 'outxml');

    execSync(`node ${cliPath} json ${dataset} -o ${scjsonDir} -r`);
    execSync(`node ${cliPath} xml ${scjsonDir} -o ${scxmlDir} -r`);

    execSync(`node ${cliPath} json ${scxmlDir} -r -v`);
    execSync(`node ${cliPath} xml ${scjsonDir} -r -v`);
  });
});
