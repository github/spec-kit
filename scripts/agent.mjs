#!/usr/bin/env node
// Minimal comment-triggered agent for Diagnose / Patch (cheap-mode).
// Requires Node 20+ (fetch is built in).

import { execSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';

const {
  GITHUB_EVENT_PATH,
  GITHUB_REPOSITORY,
  GITHUB_TOKEN,
  MODEL_PROVIDER = 'openai',
  MODEL_API_KEY,
  MODEL_NAME = 'gpt-4o-mini',
  ALLOWLIST = 'server/** ui/** scripts/**',
  DIFF_CAP = '50',
} = process.env;

if (!GITHUB_EVENT_PATH) {
  console.error('GITHUB_EVENT_PATH missing.');
  process.exit(1);
}

// Parse the issue_comment event payload
const event = JSON.parse(readFileSync(GITHUB_EVENT_PATH, 'utf8'));
const commentBody = event.comment?.body?.trim() || '';
const repoFull = event.repository?.full_name || GITHUB_REPOSITORY || '';
const [owner, repo] = repoFull.split('/');
const issueNumber = event.issue?.number;
const isDiagnose = commentBody.startsWith('/agent diagnose');
const isPatch = commentBody.startsWith('/agent patch');
if (!isDiagnose && !isPatch) process.exit(0);

// Extract the user’s goal text after the command
const goal = commentBody.replace(/^\/agent (diagnose|patch)/, '').trim() || '(no goal provided)';

// Post a reply to the PR as an issue comment
async function postComment(body) {
  const url = `https://api.github.com/repos/${owner}/${repo}/issues/${issueNumber}/comments`;
  await fetch(url, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${GITHUB_TOKEN}`,
      'Accept': 'application/vnd.github+json',
    },
    body: JSON.stringify({ body }),
  });
}

// List files under allowlisted globs using git
function listFiles() {
  const specs = ALLOWLIST.split(/\s+/).filter(Boolean);
  const args = ['ls-files', '--'].concat(specs);
  try {
    const out = execSync(`git ${args.map(a => `"${a}"`).join(' ')}`, { encoding: 'utf8' });
    return out.split('\n').map(s => s.trim()).filter(Boolean);
  } catch {
    return [];
  }
}

// Read truncated snippets for each file (cost control)
function readSnippets(files, perFileLimit = 2000, totalLimit = 12000) {
  let used = 0;
  const chunks = [];
  for (const f of files) {
    try {
      const raw = readFileSync(f, 'utf8');
      const slice = raw.slice(0, perFileLimit);
      const header = `\n=== FILE: ${f} (first ${slice.length} chars) ===\n`;
      if (used + header.length + slice.length > totalLimit) break;
      chunks.push(header + slice);
      used += header.length + slice.length;
    } catch {}
  }
  return chunks.join('');
}

// Build the prompt for the model
function buildPrompt(phase, goalText, files, snippets) {
  const fileList = files.map(f => `- ${f}`).join('\n') || '(none found under allowlist)';
  if (phase === 'diagnose') {
    return {
      system: 'You are a cost-optimized repo agent. Be terse, precise, and safe.',
      user: [
        `Goal: Identify the minimal root cause of: ${goalText}`,
        `File Scope (strict):\n${fileList}`,
        `Phase: Diagnose Only`,
        `Rules:\n- One pass only. No edits. No installs.\n- Read only files in File Scope.\n- Keep output tiny.`,
        `Deliverables:\n- Exactly 3 concise bullets: (a) suspected cause, (b) precise file/line/region, (c) smallest fix idea. Nothing else.`,
        `Context snippets (truncated for cost):\n${snippets || '(no snippets)'}`,
      ].join('\n\n'),
    };
  }
  // For patch phase
  return {
    system: 'You are a cost-optimized repo agent. Output a unified diff only, then a 2–3 sentence rationale. No extra text.',
    user: [
      `Goal: Apply the minimal fix for: ${goalText}`,
      `File Scope (strict):\n${fileList}`,
      `Phase: Patch Only`,
      `Rules:\n- Output a single unified diff patch only; target only File Scope.\n- No refactors. No formatting sweeps. No package installs.\n- Keep diff as small as possible.`,
      `Deliverables:\n- Unified diff patch (git apply compatible) + 2–3 sentence rationale. Nothing else.`,
      `Context snippets (truncated for cost):\n${snippets || '(no snippets)'}`,
    ].join('\n\n'),
  };
}

// Call the chosen model; only OpenAI is implemented here
async function callModel({ system, user }) {
  if (MODEL_PROVIDER !== 'openai') throw new Error(`Unsupported MODEL_PROVIDER: ${MODEL_PROVIDER}`);
  const res = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${MODEL_API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: MODEL_NAME,
      messages: [
        { role: 'system', content: system },
        { role: 'user', content: user },
      ],
      temperature: 0.2,
      max_tokens: 800,
    }),
  });
  if (!res.ok) throw new Error(`Model error ${res.status}: ${await res.text()}`);
  const data = await res.json();
  return data.choices?.[0]?.message?.content?.trim() || '';
}

function withinDiffCap(diff, cap) {
  const lines = diff.split('\n').filter(l => l.startsWith('+') || l.startsWith('-'));
  const changes = lines.filter(l => !l.startsWith('+++') && !l.startsWith('---')).length;
  return changes <= cap;
}

function onlyTouchesAllowlist(diff, allowGlobs) {
  const allowedRoots = allowGlobs.split(/\s+/).map(g => g.split('/')[0]).filter(Boolean);
  const bad = [];
  for (const line of diff.split('\n')) {
    if (line.startsWith('+++ ') || line.startsWith('--- ')) {
      const path = line.replace(/^\(\+\+\+|---\)\s+[ab]\//, '').trim();
      if (path !== '/dev/null' && !allowedRoots.some(root => path.startsWith(`${root}/`))) {
        bad.push(path);
      }
    }
  }
  return bad.length === 0;
}

(async () => {
  const files = listFiles();
  const snippets = readSnippets(files);
  const phase = isDiagnose ? 'diagnose' : 'patch';
  const prompt = buildPrompt(phase, goal, files, snippets);
  const output = await callModel(prompt);

  if (isDiagnose) {
    await postComment(output);
    return;
  }

  // Separate diff from rationale (look for 'diff --git' marker)
  const idx = output.indexOf('diff --git');
  let diff = output;
  let rationale = '';
  if (idx >= 0) {
    diff = output.slice(idx);
    rationale = output.slice(0, idx).trim();
  }

  const cap = parseInt(DIFF_CAP, 10) || 50;
  const okCap = withinDiffCap(diff, cap);
  const okScope = onlyTouchesAllowlist(diff, ALLOWLIST);

  if (!okCap || !okScope) {
    await postComment(
      [
        '**Agent Patch (REJECTED by safety checks)**',
        '',
        `• Diff within cap? ${okCap} (cap=${cap} changed lines)`,
        `• Paths within allowlist (${ALLOWLIST})? ${okScope}`,
        '',
        '—— Proposed diff (not applied) ——',
        '```diff',
        diff.slice(0, 65000),
        '```',
        rationale ? `\n**Rationale:** ${rationale}` : '',
      ].join('\n')
    );
    return;
  }

  // Safe preview: just comment the diff + rationale
  const tag = createHash('sha1').update(diff).digest('hex').slice(0, 7);
  await postComment(
    [
      `**Agent Patch (SAFE preview, tag ${tag})**`,
      '',
      '```diff',
      diff.slice(0, 65000),
      '```',
      rationale ? `\n**Rationale:** ${rationale}` : '',
    ].join('\n')
  );
})();