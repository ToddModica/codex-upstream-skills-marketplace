#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

function buildOutput(event, root, codex) {
  const skill = path.join(root, 'skills', 'no-negative-echo', 'SKILL.md');
  const instructions = fs.readFileSync(skill, 'utf8')
    .replace(/^\uFEFF?---\r?\n[\s\S]*?\r?\n---\r?\n/, '')
    .trim();
  const context = `NO_NEGATIVE_ECHO:ACTIVE\n\n${instructions}`;
  return codex ? JSON.stringify({
    systemMessage: 'NO_NEGATIVE_ECHO:ACTIVE',
    hookSpecificOutput: { hookEventName: event, additionalContext: context },
  }) : context;
}

if (require.main === module) {
  const event = process.argv[2] || 'SessionStart';
  const root = process.env.CLAUDE_PLUGIN_ROOT || path.resolve(__dirname, '..');
  process.stdout.write(buildOutput(event, root, Boolean(process.env.PLUGIN_DATA)));
}

module.exports = { buildOutput };
