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
const { spawnSync } = require('child_process');

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
    const res = spawnSync('node', [cliPath, '--help'], { encoding: 'utf8' });
    expect(res.stderr).not.toMatch(/Failed to convert/);
    expect(res.status).toBe(0);
    expect(res.stdout).toMatch(/scjson/);
  });

  test('single json conversion', () => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'scjson-'));
    const xmlPath = path.join(dir, 'sample.scxml');
    fs.writeFileSync(xmlPath, createScxml());

    const res = spawnSync('node', [cliPath, 'json', xmlPath], { encoding: 'utf8' });
    expect(res.stderr).not.toMatch(/Failed to convert/);
    expect(res.status).toBe(0);

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

    const res = spawnSync('node', [cliPath, 'json', srcDir], { encoding: 'utf8' });
    expect(res.stderr).not.toMatch(/Failed to convert/);
    expect(res.status).toBe(0);

    ['a', 'b'].forEach(n => {
      expect(fs.existsSync(path.join(srcDir, `${n}.scjson`))).toBe(true);
    });
  });

  test('single xml conversion', () => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'scjson-'));
    const jsonPath = path.join(dir, 'sample.scjson');
    fs.writeFileSync(jsonPath, createScjson());

    const res = spawnSync('node', [cliPath, 'xml', jsonPath], { encoding: 'utf8' });
    expect(res.stderr).not.toMatch(/Failed to convert/);
    expect(res.status).toBe(0);

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

    const res = spawnSync('node', [cliPath, 'xml', srcDir], { encoding: 'utf8' });
    expect(res.stderr).not.toMatch(/Failed to convert/);
    expect(res.status).toBe(0);

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

    let res = spawnSync('node', [cliPath, 'json', dataset, '-o', scjsonDir, '-r'], { encoding: 'utf8' });
    expect(res.stderr).not.toMatch(/Failed to convert/);
    expect(res.status).toBe(0);
    res = spawnSync('node', [cliPath, 'xml', scjsonDir, '-o', scxmlDir, '-r'], { encoding: 'utf8' });
    expect(res.stderr).not.toMatch(/Failed to convert/);
    expect(res.status).toBe(0);

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

    let res = spawnSync('node', [cliPath, 'json', dataset, '-o', scjsonDir, '-r'], { encoding: 'utf8' });
    expect(res.stderr).not.toMatch(/Failed to convert/);
    expect(res.status).toBe(0);
    res = spawnSync('node', [cliPath, 'xml', scjsonDir, '-o', scxmlDir, '-r'], { encoding: 'utf8' });
    expect(res.stderr).not.toMatch(/Failed to convert/);
    expect(res.status).toBe(0);

    // Corrupt one file to trigger failure
    fs.writeFileSync(path.join(scjsonDir, 'corrupt.scjson'), 'bad');

    const validateRes = spawnSync('node', [cliPath, 'validate', dataset, '-r'], { encoding: 'utf8' });
    expect(validateRes.stderr).toMatch(/Validation failed/);
    expect(validateRes.status).not.toBe(0);
  });

  test('recursive verify', () => {
    const dataset = fs.mkdtempSync(path.join(os.tmpdir(), 'scjson-'));
    buildDataset(dataset);
    const scjsonDir = path.join(dataset, 'outjson');
    const scxmlDir = path.join(dataset, 'outxml');

    let res = spawnSync('node', [cliPath, 'json', dataset, '-o', scjsonDir, '-r'], { encoding: 'utf8' });
    expect(res.stderr).not.toMatch(/Failed to convert/);
    expect(res.status).toBe(0);
    res = spawnSync('node', [cliPath, 'xml', scjsonDir, '-o', scxmlDir, '-r'], { encoding: 'utf8' });
    expect(res.stderr).not.toMatch(/Failed to convert/);
    expect(res.status).toBe(0);

    res = spawnSync('node', [cliPath, 'json', scxmlDir, '-r', '-v'], { encoding: 'utf8' });
    expect(res.stderr).not.toMatch(/Failed to convert/);
    expect(res.status).toBe(0);
    res = spawnSync('node', [cliPath, 'xml', scjsonDir, '-r', '-v'], { encoding: 'utf8' });
    expect(res.stderr).not.toMatch(/Failed to convert/);
    expect(res.status).toBe(0);
  });
});
