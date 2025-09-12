#!/usr/bin/env node
// Apply a unified diff safely; run with Node if you want auto-apply later.
import { readFileSync, writeFileSync } from 'node:fs';
import { execSync } from 'node:child_process';

const {
  ALLOWLIST = 'server/** ui/** scripts/**',
  DIFF_FILE = 'agent.patch',
  DIFF_CAP = '50',
} = process.env;

function onlyTouchesAllowlist(diff, allowGlobs) {
  const allowedRoots = allowGlobs.split(/\s+/).map(g => g.split('/')[0]).filter(Boolean);
  for (const line of diff.split('\n')) {
    if (line.startsWith('+++ ') || line.startsWith('--- ')) {
      const path = line.replace(/^\(\+\+\+|---\)\s+[ab]\//, '').trim();
      if (path !== '/dev/null' && !allowedRoots.some(root => path.startsWith(`${root}/`))) return false;
    }
  }
  return true;
}

function withinDiffCap(diff, cap) {
  const lines = diff.split('\n').filter(l => l.startsWith('+') || l.startsWith('-'));
  const changes = lines.filter(l => !l.startsWith('+++') && !l.startsWith('---')).length;
  return changes <= cap;
}

const diff = readFileSync(DIFF_FILE, 'utf8');
const cap = parseInt(DIFF_CAP, 10) || 50;

if (!withinDiffCap(diff, cap)) {
  console.error('Diff exceeds cap; abort.');
  process.exit(2);
}
if (!onlyTouchesAllowlist(diff, ALLOWLIST)) {
  console.error('Diff touches files outside allowlist; abort.');
  process.exit(3);
}

writeFileSync('.agent.patch', diff);
execSync('git apply --index .agent.patch', { stdio: 'inherit' });
execSync('git config user.name "repo-agent" && git config user.email "repo-agent@users.noreply.github.com"', { stdio: 'inherit' });
execSync('git commit -m "repo-agent: minimal patch"', { stdio: 'inherit' });
console.log('Patch applied and committed. Push separately to share the change.');