#!/usr/bin/env node
/**
 * Agent Name: js-cli-runner
 *
 * Part of the scjson project.
 * Developed by Softoboros Technology Inc.
 * Licensed under the BSD 1-Clause License.
 */

const { program } = require('../dist/index.js');
program.parse(process.argv);
