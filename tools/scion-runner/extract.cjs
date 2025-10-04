#!/usr/bin/env node
// Agent Name: scion-runner-extract
//
// Part of the scjson project.
// Developed by Softoboros Technology Inc.
// Licensed under the BSD 1-Clause License.

const fs = require('fs');
const path = require('path');
const zlib = require('zlib');

function extractTarGz(tgzPath, outDir, files) {
  try {
    const { execSync } = require('child_process');
    execSync(
      `tar -xzf ${JSON.stringify(tgzPath)} -C ${JSON.stringify(outDir)} ${files.map(f => 'package/' + f).join(' ')}`,
      { stdio: 'ignore' }
    );
    return true;
  } catch (_e) {
    try {
      const gzData = fs.readFileSync(tgzPath);
      const tarData = zlib.gunzipSync(gzData);
      let offset = 0;
      const BLOCK = 512;
      const targets = new Set(files.map(f => 'package/' + f));
      const writes = {};
      while (offset + BLOCK <= tarData.length && targets.size > 0) {
        const header = tarData.subarray(offset, offset + BLOCK);
        const name = header.subarray(0, 100).toString().replace(/\0+$/, '');
        if (!name) break;
        const sizeOct = header.subarray(124, 136).toString().replace(/\0+$/, '').trim();
        const size = parseInt(sizeOct || '0', 8);
        offset += BLOCK;
        if (targets.has(name)) {
          writes[name] = tarData.subarray(offset, offset + size);
          targets.delete(name);
        }
        const pad = Math.ceil(size / BLOCK) * BLOCK;
        offset += pad;
      }
      for (const rel of Object.keys(writes)) {
        const dest = path.resolve(outDir, rel);
        fs.mkdirSync(path.dirname(dest), { recursive: true });
        fs.writeFileSync(dest, writes[rel]);
      }
      return files.every(f => fs.existsSync(path.resolve(outDir, 'package', f)));
    } catch (_) {
      return false;
    }
  }
}

function main() {
  const base = path.resolve(__dirname, 'vendor');
  const tgz = path.resolve(base, 'scxml-5.0.4.tgz');
  const outScxml = path.resolve(base, 'package', 'dist', 'scxml.js');
  const outCore = path.resolve(base, 'package', 'dist', 'core.js');
  if (fs.existsSync(outScxml) && fs.existsSync(outCore)) {
    return;
  }
  if (!fs.existsSync(tgz)) {
    // Nothing to do; vendored bundle not present in this checkout
    return;
  }
  extractTarGz(tgz, base, ['dist/scxml.js', 'dist/core.js']);
}

main();

