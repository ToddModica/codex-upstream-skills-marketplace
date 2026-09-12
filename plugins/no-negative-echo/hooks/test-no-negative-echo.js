#!/usr/bin/env node
const assert = require('assert');
const path = require('path');
const { buildOutput } = require('./no-negative-echo');

const root = path.resolve(__dirname, '..');
const parsed = JSON.parse(buildOutput('SubagentStart', root, true));
assert.equal(parsed.systemMessage, 'NO_NEGATIVE_ECHO:ACTIVE');
assert.equal(parsed.hookSpecificOutput.hookEventName, 'SubagentStart');
assert.match(parsed.hookSpecificOutput.additionalContext, /No Negative Echo/);
console.log('no-negative-echo hook: OK');
