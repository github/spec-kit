import assert from 'node:assert/strict';
import { readFileSync, unlinkSync, writeFileSync } from 'node:fs';
import { test } from 'node:test';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(fileURLToPath(new URL('.', import.meta.url)), '..');
const workflow = readFileSync(join(root, '.github', 'workflows', 'community-assess.md'), 'utf8');
const cleanupWorkflow = readFileSync(join(root, '.github', 'workflows', 'community-assess-cleanup.yml'), 'utf8');

function extractScript(text, marker) {
  const lines = text.split(/\r?\n/);
  const markerIndex = lines.findIndex((line) => line.includes(marker));
  const scriptIndex = lines.findIndex((line, index) => index > markerIndex && line.trim() === 'script: |');
  assert.notEqual(scriptIndex, -1, `script for ${marker} not found`);
  const indent = lines[scriptIndex + 1].match(/^\s*/)[0].length;
  const body = [];
  for (const line of lines.slice(scriptIndex + 1)) {
    if (line.trim() && line.match(/^\s*/)[0].length < indent) break;
    body.push(line.slice(indent));
  }
  return body.join('\n');
}

const publishScript = extractScript(workflow, 'Validate and publish SHA-qualified assessment');
const cleanupScript = extractScript(cleanupWorkflow, 'Remove workflow-owned outcome labels');

function fakeGitHub({ sha, state = 'open', labels = [] } = {}) {
  const data = { state, head: { sha }, labels: labels.map((name) => ({ name })) };
  const calls = { comments: [], added: [], removed: [], gets: 0 };
  const github = {
    rest: {
      pulls: {
        get: async () => {
          calls.gets += 1;
          return { data: structuredClone(data) };
        },
      },
      issues: {
        createComment: async ({ body }) => calls.comments.push(body),
        removeLabel: async ({ name }) => {
          calls.removed.push(name);
          data.labels = data.labels.filter((item) => item.name !== name);
        },
        getLabel: async () => ({ data: {} }),
        addLabels: async ({ labels: names }) => {
          calls.added.push(...names);
          data.labels.push(...names.map((name) => ({ name })));
        },
      },
    },
  };
  return { github, calls };
}

async function runPublish({ item, sha, state = 'open', labels = [], action = 'labeled', labelName = 'community-review' }) {
  const { github, calls } = fakeGitHub({ sha, state, labels });
  const outputPath = join(root, 'tests', '.community-assess-agent-output.json');
  writeFileSync(outputPath, JSON.stringify({ items: item ? [item] : [] }));
  const fakeFs = {
    existsSync: (path) => path === outputPath,
    readFileSync: (path) => readFileSync(path),
  };
  const fakeRequire = (name) => (name === 'fs' ? fakeFs : (() => { throw new Error(`unexpected require ${name}`); })());
  const env = { GH_AW_AGENT_OUTPUT: outputPath, GH_AW_EXPECTED_HEAD_SHA: sha, GH_AW_PR_NUMBER: '7' };
  const context = { eventName: 'pull_request', payload: { action, label: { name: labelName } }, repo: { owner: 'github', repo: 'spec-kit' } };
  const core = { info() {}, warning() {} };
  const run = new Function('require', 'process', 'context', 'github', 'core', `return (async () => {\n${publishScript}\n})();`);
  await run(fakeRequire, { env }, context, github, core);
  unlinkSync(outputPath);
  return calls;
}

test('valid output publishes one comment and one current outcome label', async () => {
  const sha = 'a'.repeat(40);
  const calls = await runPublish({ sha, item: { type: 'community_assess_publish', expected_head_sha: sha, outcome: 'fits-project', body: 'evidence' } });
  assert.equal(calls.comments.length, 1);
  assert.deepEqual(calls.added, ['community-assessment-fits']);
  assert.ok(calls.gets >= 4);
});

test('stale SHA clears old outcomes without publishing', async () => {
  const sha = 'b'.repeat(40);
  const calls = await runPublish({ sha, labels: ['community-assessment-fits'], item: { type: 'community_assess_publish', expected_head_sha: 'c'.repeat(40), outcome: 'fits-project', body: 'stale' } });
  assert.equal(calls.comments.length, 0);
  assert.deepEqual(calls.added, []);
  assert.deepEqual(calls.removed, ['community-assessment-fits']);
});

test('closed PR fails the fresh check and clears current outcomes', async () => {
  const sha = 'd'.repeat(40);
  const calls = await runPublish({ sha, state: 'closed', labels: ['community-assessment-invalid'], item: { type: 'community_assess_publish', expected_head_sha: sha, outcome: 'invalid', body: 'closed' } });
  assert.equal(calls.comments.length, 0);
  assert.deepEqual(calls.removed, ['community-assessment-invalid']);
});

test('invalid output is ignored without a GitHub mutation', async () => {
  const sha = 'e'.repeat(40);
  const calls = await runPublish({ sha, labels: ['community-assessment-fits'], item: { type: 'community_assess_publish', expected_head_sha: sha, outcome: 'not-allowed', body: 'invalid' } });
  assert.equal(calls.comments.length, 0);
  assert.deepEqual(calls.added, []);
  assert.deepEqual(calls.removed, []);
});

test('retrigger removes the previous outcome before applying the new one', async () => {
  const sha = 'f'.repeat(40);
  const calls = await runPublish({ sha, labels: ['community-assessment-out-of-scope'], item: { type: 'community_assess_publish', expected_head_sha: sha, outcome: 'needs-clarification', body: 'new' } });
  assert.deepEqual(calls.removed, ['community-assessment-out-of-scope']);
  assert.deepEqual(calls.added, ['community-assessment-needs-clarification']);
});

async function runCleanup({ currentSha, eventSha, action = 'synchronize', labels = [] }) {
  const { github, calls } = fakeGitHub({ sha: currentSha, labels });
  const context = {
    payload: { action, pull_request: { number: 7, head: { sha: eventSha } } },
    repo: { owner: 'github', repo: 'spec-kit' },
  };
  const core = { info() {} };
  const run = new Function('context', 'github', 'core', `return (async () => {\n${cleanupScript}\n})();`);
  await run(context, github, core);
  return calls;
}

test('mechanical cleanup removes fixed labels and skips stale synchronize events', async () => {
  assert.match(cleanupScript, /pulls\.get/);
  assert.match(cleanupScript, /removeLabel/);
  assert.doesNotMatch(cleanupScript, /GH_AW_AGENT_OUTPUT|agent_output/);
  const sha = '1'.repeat(40);
  const removed = await runCleanup({ currentSha: sha, eventSha: sha, labels: ['community-assessment-fits', 'community-assessment-invalid'] });
  assert.deepEqual(removed.removed, ['community-assessment-fits', 'community-assessment-invalid']);
  const stale = await runCleanup({ currentSha: '2'.repeat(40), eventSha: '3'.repeat(40), labels: ['community-assessment-fits'] });
  assert.deepEqual(stale.removed, []);
});
