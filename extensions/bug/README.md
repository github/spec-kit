# Bug Triage Workflow Extension

A three-step bug triage workflow for Spec Kit: assess, fix, and validate. Each bug lives in its own directory under `.specify/bugs/<slug>/`, with one Markdown report per stage.

## Overview

This extension delivers an opinionated, repeatable bug workflow that any AI coding agent can drive:

1. **Assess** — read a bug report (pasted text or a URL), judge whether it is a real bug, locate suspected code paths, and propose a remediation.
2. **Fix** — apply the proposed remediation and record exactly what changed.
3. **Test** — re-run the reproduction and any added tests, then record the verification result.

The three stages communicate through three Markdown files in a single per-bug directory:

```
.specify/bugs/<slug>/
├── assessment.md   # written by speckit.bug.assess
├── fix.md          # written by speckit.bug.fix
└── test.md         # written by speckit.bug.test
```

## Commands

| Command | Description | Output |
|---------|-------------|--------|
| `speckit.bug.assess` | Triages a bug report (pasted text or URL) against the codebase. | `.specify/bugs/<slug>/assessment.md` |
| `speckit.bug.fix` | Applies the remediation from the assessment. | `.specify/bugs/<slug>/fix.md` |
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
# 1. Triage a bug from a pasted stack trace
/speckit.bug.assess "TypeError: cannot read properties of undefined (reading 'token') at /auth/callback"

# 2. Triage a bug from a GitHub issue URL
/speckit.bug.assess https://github.com/example/repo/issues/1234 slug=callback-token

# 3. Apply the proposed fix
/speckit.bug.fix slug=callback-token

# 4. Validate the fix
/speckit.bug.test slug=callback-token
```

## Guardrails

- `speckit.bug.assess` and `speckit.bug.test` **never modify source code**. They read the repository and write only inside `.specify/bugs/<slug>/`.
- `speckit.bug.fix` is the only command that edits source code, and it stays within the files listed in the assessment unless new evidence requires expanding scope (which is logged in `fix.md` under **Deviations from Assessment**).
- None of the commands overwrite an existing report file without explicit confirmation; in automated mode they refuse and pick a new unique slug instead.
- Verdicts and verification results are never over-claimed: a reproduction that was not actually performed is reported as `partial` or `not-run`, not `verified`.

## Hooks

This extension registers no hooks of its own. The three commands are always invoked explicitly by the user, but expose lifecycle events for other extensions:

| Command | Before event | After event |
|---------|--------------|-------------|
| `speckit.bug.assess` | `before_bug_assess` | `after_bug_assess` |
| `speckit.bug.fix` | `before_bug_fix` | `after_bug_fix` |
| `speckit.bug.test` | `before_bug_test` | `after_bug_test` |

Pre-hooks run after slug resolution and prerequisites, before execution. For assessment, the bug directory already exists before the pre-hook runs. Post-hooks run after `assessment.md`, `fix.md`, or `test.md` is written and before reporting completion. Pre-hooks see the resolved `BUG_SLUG` and `BUG_DIR`; post-hooks additionally see the written report.

For example, an installed intake extension can register a hook in `.specify/extensions.yml`:

```yaml
hooks:
  before_bug_assess:
    - extension: intake
      command: speckit.intake.collect
      enabled: true
      optional: false
      description: Collect evidence in the resolved bug directory
```

Mandatory hooks are invoked and awaited; optional hooks are presented for the user to run. Disabled hooks and hooks with non-empty conditions are skipped by the command templates. With no registered hooks, the workflow proceeds as before. See the [Extension API Reference](../EXTENSION-API-REFERENCE.md#hook-events) for the shared hook contract.
