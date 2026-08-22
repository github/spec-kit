# Bug Triage Workflow Extension

An end-to-end bug triage workflow for Spec Kit: assess, report (GitHub issue), fix, open a PR, and validate. Each bug lives in its own directory under `.specify/bugs/<slug>/`, with one Markdown report per stage.

## Overview

This extension delivers an opinionated, repeatable bug workflow that any AI coding agent can drive:

1. **Assess** — read a bug report (pasted text or a URL), judge whether it is a real bug, locate suspected code paths, and propose a remediation. `assess` writes a *local* assessment only; it does **not** file a GitHub issue.
2. **Load** (alternative entry point) — `speckit.bug.fetch` pulls an *existing* GitHub issue (by number, URL, or `owner/repo#n`) via `gh`, records it as `issue.md`, and seeds an `assessment.md` draft. Use this when the bug is already tracked on GitHub and you want to triage and fix it here — instead of starting from a pasted report.
3. **Report** (optional) — `speckit.bug.issue` turns an assessment into a tracked GitHub issue via `gh`, recording the issue link. `assess` can auto-trigger this with `--issue` or the `auto_create_issue` config. `fetch` already produces `issue.md`, so `issue` is normally skipped after a load.
3. **Fix** — apply the proposed remediation and record exactly what changed. Pass `--branch` (or `--worktree`) to isolate the fix on its own git branch.
4. **Open PR** (optional) — `speckit.bug.pr` opens a pull request from the fix branch, linking the issue.
5. **Test** — re-run the reproduction and any added tests, then record the verification result.

The stages communicate through Markdown files in a single per-bug directory:

```
.specify/bugs/<slug>/
├── assessment.md    # written by speckit.bug.assess
├── issue.md         # written by speckit.bug.issue or speckit.bug.fetch (issue number + URL)
├── issue-body.md    # issue body draft used by speckit.bug.issue
├── issue-draft.md   # fallback when gh/GitHub is unavailable
├── fix.md           # written by speckit.bug.fix
├── pr.md            # written by speckit.bug.pr (PR number + URL)
├── pr-body.md       # PR body draft used by speckit.bug.pr
├── pr-draft.md      # fallback when gh/GitHub is unavailable
└── test.md          # written by speckit.bug.test
```

## Commands

| Command | Description | Output |
|---------|-------------|--------|
| `speckit.bug.assess` | Triages a bug report (pasted text or URL) against the codebase. | `.specify/bugs/<slug>/assessment.md` |
| `speckit.bug.issue` | Files a GitHub issue from the assessment (the "report" phase). | `.specify/bugs/<slug>/issue.md` |
| `speckit.bug.fetch` | Loads an existing GitHub issue (`issue.md`) and seeds a triage draft. | `.specify/bugs/<slug>/issue.md` + `assessment.md` |
| `speckit.bug.fix` | Applies the remediation from the assessment (`--branch`/`--worktree` to isolate). | `.specify/bugs/<slug>/fix.md` |
| `speckit.bug.pr` | Opens a PR for the fix, linking the issue. | `.specify/bugs/<slug>/pr.md` |
| `speckit.bug.test` | Validates the fix and records the verification report. | `.specify/bugs/<slug>/test.md` |

## Slug Conventions

A *slug* is the per-bug directory name under `.specify/bugs/`. It is the only handle the three commands share.

- **User-provided**: any shape the user wants, normalized to lowercase kebab-case (e.g. `login-timeout`, `cve-2026-001`, `oauth-redirect-500`). The slug is preserved verbatim after normalization — no timestamps or numbers are appended automatically.
- **Asked for**: in interactive use, `speckit.bug.assess` asks for a slug when none is supplied, suggesting a kebab-case default derived from the bug summary.
- **Automated**: when no human is available to answer, the agent generates a slug itself. The generated slug **MUST** produce a unique directory — if `.specify/bugs/<slug>/` already exists, the agent appends the shortest disambiguating suffix needed (`-2`, `-3`, …) or a short date (`-20260605`). Existing bug directories are never overwritten.

## Installation

```bash
# Install the bundled bug extension (no network required)
specify extension add bug
```

## Disabling

```bash
# Disable the bug extension
specify extension disable bug

# Re-enable it
specify extension enable bug
```

## Typical Flow

```bash
# 1. Triage a bug from a pasted stack trace (or pass --issue to file the GitHub issue now)
/speckit.bug.assess "TypeError: cannot read properties of undefined (reading 'token') at /auth/callback"

# 2. Triage a bug from a GitHub issue URL
/speckit.bug.assess https://github.com/example/repo/issues/1234 slug=callback-token

# 3. File the GitHub issue (the "report" phase) — skipped if assess ran with --issue
/speckit.bug.issue slug=callback-token

# 4. Apply the proposed fix on its own branch (or pass --worktree for a separate worktree)
/speckit.bug.fix slug=callback-token --branch

# 5. Open a PR from the fix branch, linking the issue
/speckit.bug.pr slug=callback-token

# 6. Validate the fix
/speckit.bug.test slug=callback-token

# --- Alternative entry point: load an issue that already exists on GitHub ---
# Load issue #1234 (from the current repo) and seed a triage draft
/speckit.bug.fetch 1234

# Load by URL or owner/repo#n
/speckit.bug.fetch https://github.com/example/repo/issues/1234
/speckit.bug.fetch example/repo#1234

# Then proceed straight to the fix on its own branch
/speckit.bug.fix slug=callback-token --branch
/speckit.bug.pr slug=callback-token
```

## Configuration

The extension reads `.specify/extensions/bug/bug-config.yml` (copied from `config-template.yml` on install). Options:

- `auto_create_issue` (`false`) — when `true`, `speckit.bug.assess` files the GitHub issue automatically after writing the assessment. The `--issue` flag overrides this per run.
- `branch_prefix` (`"fix"`) — prefix for the fix branch created by `speckit.bug.fix --branch` / `--worktree` (branch is `<prefix>/<slug>`, e.g. `fix/login-timeout`).
- `default_host` (`"github"`) — Git host used when creating issues/PRs.

## Branch Isolation

`speckit.bug.fix --branch` creates `<prefix>/<slug>` and checks it out before editing, so the fix is isolated like feature work from `specify spec`. `--worktree` instead runs `git worktree add` into a sibling directory. If Git is unavailable, the fix is applied to the current branch with a warning. `speckit.bug.pr` then opens a PR from that branch.

## Assess vs Load vs Report

- **Assess** means *triage a report into a local `assessment.md`* — it never touches GitHub. Use it for a bug described in pasted text or a URL.
- **Load** (`speckit.bug.fetch`) means *pull an issue that already exists on GitHub* into `issue.md` and seed an `assessment.md` draft. Use it when the bug is already tracked and you want to work on it here. It is the read-only complement of "Report".
- **Report** (`speckit.bug.issue`) means *file the bug as a new GitHub issue* from an assessment. After a `fetch`, the issue is already loaded, so "Report" is normally skipped — `fetch` and `issue` both produce `issue.md`, and `bug.issue` refuses to create a duplicate when one already exists.

This separation keeps triage read-only and lets you decide per bug whether it is worth tracking.

## Guardrails

- `speckit.bug.assess` and `speckit.bug.test` **never modify source code**. They read the repository and write only inside `.specify/bugs/<slug>/`.
- `speckit.bug.issue` and `speckit.bug.pr` are opt-in **external** actions (they call the `gh` CLI). They never edit repository source; when `gh`/GitHub is unavailable they write a local draft (`issue-draft.md` / `pr-draft.md`) instead of erroring.
- `speckit.bug.fix` is the only command that edits source code, and it stays within the files listed in the assessment unless new evidence requires expanding scope (which is logged in `fix.md` under **Deviations from Assessment**).
- None of the commands overwrite an existing report file without explicit confirmation; in automated mode they refuse and pick a new unique slug instead.
- Verdicts and verification results are never over-claimed: a reproduction that was not actually performed is reported as `partial` or `not-run`, not `verified`.

## Hooks

This extension registers no hooks. The commands are always invoked explicitly by the user.
