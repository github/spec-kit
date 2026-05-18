---
description: Deep codebase audit. Runs the regex-based audit script, then layers in tsc --noEmit, eslint, npm audit, file-level read-throughs, and cross-file LLM analysis to confirm and correlate findings. Slower than /speckit.audit but materially higher signal.
handoffs:
  - label: Open Remediation Plan
    agent: speckit.plan
    prompt: Build a plan from the deep audit findings. Sequence by criticality, group by area, scope per release.
---

## User Input

```text
$ARGUMENTS
```

You **MAY** consider the user input as scope hints (paths, severity floor, sections, rule filters, max findings per rule). The deep audit honors the same flags as `/speckit.audit`. If empty, audit the whole repository at default settings.

## Pre-Execution Checks

**Check for extension hooks (before deep audit)**:

- Check if `.specify/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under `hooks.before_audit_deep` first, then `hooks.before_audit`.
- If the YAML cannot be parsed or is invalid, skip hook checking silently and continue normally.
- Filter out hooks where `enabled` is explicitly `false`. Treat hooks without an `enabled` field as enabled by default.
- For each remaining hook, do **not** attempt to interpret or evaluate hook `condition` expressions:
  - If the hook has no `condition` field, or it is null/empty, treat the hook as executable.
  - If the hook defines a non-empty `condition`, skip the hook and leave condition evaluation to the HookExecutor implementation.
- For each executable hook, output the following based on its `optional` flag:
  - **Optional hook** (`optional: true`):
    ```
    ## Extension Hooks

    **Optional Pre-Hook**: {extension}
    Command: `/{command}`
    Description: {description}

    Prompt: {prompt}
    To execute: `/{command}`
    ```
  - **Mandatory hook** (`optional: false`):
    ```
    ## Extension Hooks

    **Automatic Pre-Hook**: {extension}
    Executing: `/{command}`
    EXECUTE_COMMAND: {command}

    Wait for the result of the hook command before proceeding to the Outline.
    ```
- If no hooks are registered or `.specify/extensions.yml` does not exist, skip silently.

## Outline

A **deep audit** is the regex-based audit *plus* four extra layers:

1. **Compiler ground truth** — `tsc --noEmit` against the project.
2. **Lint ground truth** — `eslint .` (or the project's configured lint script).
3. **Dependency posture** — `npm audit --json` (or `pnpm audit` / `yarn npm audit`), if a lockfile is present.
4. **LLM confirmation & cross-file analysis** — read flagged files in full, dedupe false positives, correlate patterns across modules, and inspect every `"use server"` file for the parse → authorize → ownership → DTO recipe.

The deep audit is **slower** than the standard one. Treat it as the pre-release gate, not the pre-commit gate.

Follow this flow:

### 1. Parse scope hints from `$ARGUMENTS`

Same rules as `/speckit.audit`. Translate into `--paths` / `--rules` / `--sections` / `--severity` / `--max-findings-per-rule` flags for the audit script.

### 2. Run the regex audit (Layer 1)

```bash
bash .specify/presets/nextjs/scripts/bash/audit-codebase.sh --json [flags...]
```

(or `pwsh .specify/presets/nextjs/scripts/powershell/audit-codebase.ps1 -Json [...]`)

Capture the JSON output. This is the **baseline finding set**.

### 3. Run tsc (Layer 2)

If `package.json` exists and a `typescript` dependency is present (use the inventory from `scan-repo.sh` if recent — otherwise check `package.json` directly):

```bash
npx --no-install tsc --noEmit --pretty false
```

Fall back to the project's own typecheck script when defined (`npm run typecheck` / `npm run type-check`) — prefer that, since it carries the project's actual project-references topology.

Capture stdout and stderr. If `tsc` is not installed, **report this as a finding** under `INFRA.CI.missing-typecheck-job` rather than failing silently.

Parse the tsc output into a structured list. Each diagnostic becomes an additional finding under a synthetic rule:

- `rule_id`: `TS.COMPILER.tsc-diagnostic`
- `severity`: `critical` (any tsc error blocks release per the constitution)
- `section`: `TypeScript / Compiler ground truth`
- `phase`: `P2`
- `directive`: "Treat type errors as build failures in CI; never merge with tsc errors"
- `file`, `line`, `snippet`, plus the original tsc message text.

Cap at 200 diagnostics in the report; if more, note the truncation and instruct the user to re-run scoped to a path.

### 4. Run eslint (Layer 3)

If a lint config is detected (any of `.eslintrc*`, `eslint.config.*`, or `biome.json[c]`), run:

```bash
# ESLint
npx --no-install eslint . --format json

# Or, when Biome is configured:
npx --no-install biome check . --formatter json
```

Prefer the project's `lint` script if defined. Parse the output and convert each diagnostic into a finding:

- `rule_id`: `TS.LINT.<eslint-rule-id>` (preserve the upstream rule ID after `TS.LINT.`)
- `severity`: map ESLint `error` → `high`, `warning` → `medium`. (The constitution treats warnings as errors on protected branches, but for a single audit pass we keep the upstream severity distinction so the team can triage.)
- `section`: `TypeScript / Lint ground truth`
- `phase`: `P1`
- `directive`: "Enforce one linter; warnings are errors on protected branches"
- `file`, `line`, `column`, `snippet`, `message`.

Cap at 500 lint findings total; truncate and warn beyond that.

### 5. Dependency vulnerability scan (Layer 4)

If a lockfile is present (`package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`), run the matching audit command and parse JSON:

```bash
npm audit --json --omit=dev          # if package-lock.json
pnpm audit --json --prod             # if pnpm-lock.yaml
yarn npm audit --recursive --json    # if yarn.lock (Berry)
```

Each vulnerability with `severity` of `high` or `critical` becomes a finding:

- `rule_id`: `SEC.DEPS.cve-<package>`
- `severity`: passthrough (`critical`/`high`/`moderate`→`medium`/`low`)
- `section`: `Security / Dependency posture`
- `phase`: `P3`
- `directive`: "Pin and audit dependencies; vulnerability scan every PR; patch CVEs promptly"
- File: `package.json` (or the lockfile path).
- Snippet: short CVE summary plus advisory URL.

If the audit command is unavailable or the lockfile is absent, emit one informational finding under `SEC.DEPS.no-audit-available` and continue.

### 6. LLM confirmation & cross-file analysis (Layer 5)

This layer is the reason the deep audit exists. The regex pass produces leads; this pass turns leads into verdicts.

For **every Critical finding** and **up to 20 High findings sampled across rules**, do this:

1. **Read the flagged file in full** (or, for large files, the surrounding ±50 lines around the flagged line).
2. **Confirm or refute** the finding:
   - "Confirmed" if the violation holds in context.
   - "False positive" if context shows the regex was misled (e.g. `any` inside a string literal, `as Foo` inside a comment, `<img>` inside an SVG `<text>` block).
   - "Confirmed but mitigated" if surrounding code already neutralizes the risk (e.g. `dangerouslySetInnerHTML` with a sanitized payload from a trusted server-side renderer — note the mitigation and downgrade severity by one step).
3. **Propose a concrete fix** (file path + minimal diff sketch), not just a directive restatement.
4. **Correlate across files**:
   - Group `BE.DAL.missing-server-only` findings — propose a single PR that adds the import to every flagged file.
   - For `FE.RSC.use-client-at-page-or-layout`: identify the smallest interactive leaf in each flagged tree and propose where the boundary should move.
   - For `SEC.SESSION.localstorage-auth`: trace every reader/writer of the affected key and propose a session-cookie migration plan.
   - For `TS.TYPE.any-usage`: list the **top 5 files by `any` density**; recommend tackling those first.

For every **`"use server"` file** in the project (use the inventory's `directives.use_server_files` count to scope), inspect each Server Action:

- **Parse** — does it run input through a schema (zod, valibot, yup, or an equivalent) at the top of the function?
- **Authorize** — does it re-verify identity inside the action (not just at the page or layout)?
- **Ownership** — does it check the actor owns the resource (not just that they are signed in)?
- **DTO** — does it return only the fields the client needs?

If any of the four is missing, emit a finding under:

- `rule_id`: `BE.ACTION.recipe-violation`
- `severity`: `critical` (Server Actions are public POST endpoints per the constitution).

### 7. Persist the deep audit JSON

Merge all five layers into one document with the same schema as the regex audit, plus a `layers` field describing which layers ran and any that were skipped (with reason).

Write to:

```
.specify/audits/deep/audit-<ISO timestamp YYYYMMDD-HHMMSS>.json
```

Also update `.specify/audits/deep/latest.json`. Mirror `latest.json` from the regex audit at `.specify/audits/latest.json` only if no separate regex audit ran in this command (here: do nothing — the deep audit owns `deep/latest.json`, the standard audit owns `latest.json`).

### 8. Produce the deep report

Output to the user in this exact structure:

```
# Deep Codebase Quality Audit

**Scope**: <paths or "whole repository">
**Files scanned (regex)**: <N>
**Layers run**: regex audit · tsc (<diag count>) · eslint (<lint count>) · deps (<vuln count>) · LLM confirmation (<files reviewed>)
**Layers skipped**: <list with reason, or "none">
**Findings**: <total> (critical: <c> · high: <h> · medium: <m> · low: <l>)
**Confirmed**: <c'> · **False positives**: <fp> · **Mitigated**: <m'>
**Persisted**: `.specify/audits/deep/audit-YYYYMMDD-HHMMSS.json` (also `deep/latest.json`)

## Critical, confirmed (block release)

### <rule_id> — <directive>
*Constitution: <section> / <phase> / <criticality> · Scope: <FE|BE|Both>*

- `<file>:<line>` — `<snippet>`
  - **Confirmed**: <one sentence describing why this is real in context>
  - **Fix**: <concrete change, sometimes a minimal diff in fenced code>

### <next rule_id> ...

## High, confirmed

... same shape ...

## False positives (regex misled — no action needed)

### <rule_id> — <reason category>

- `<file>:<line>` — <why this is not a violation>

## Mitigated (do not block, but document)

### <rule_id>

- `<file>:<line>` — <mitigation, e.g. "payload sanitized via X server-side">

## Cross-file patterns

- **<pattern name>** affects <N> files across <areas>. Recommended: single PR `<short title>`.
- ...

## Server Action recipe compliance

| File | Parse | Authorize | Ownership | DTO |
|---|---|---|---|---|
| app/x/action.ts | ✓ | ✓ | ✗ | ✓ |
| ... |

Findings under `BE.ACTION.recipe-violation`: <N>.

## Top 5 prioritized actions

1. <action with file paths and rule IDs covered>
2. ...
```

Omit any section that's empty.

### 9. Recommendations

End with a short list:

- If **any** confirmed Critical remains, recommend **not merging** until those are resolved or formally waived.
- If `tsc` is failing, recommend a single config-tightening PR (no feature work) until `tsc` is green.
- If `eslint` is failing on protected branches, recommend wiring `--max-warnings 0` in CI.
- If dependency CVEs exist at Critical/High, recommend treating them as production incidents.
- Recommend re-running `/speckit.audit.deep` after the next batch of fixes to verify progress.

### 10. Validation before final output

- Every finding listed appears in the persisted JSON.
- No invented findings; every confirmation traces back to a regex/tsc/eslint/audit diagnostic that the script or tools actually produced.
- File paths match what tools returned (do not normalize them).
- The "False positives" section accounts only for entries that the regex pass produced and the LLM confirmed are not violations — never use it to silently drop real findings.
- Layers that were skipped (e.g. no eslint config, no lockfile) are listed under "Layers skipped" with a short reason.

## Formatting & Style Requirements

- Use Markdown headings exactly as shown; do not invent new top-level sections.
- Snippets stay on a single line (~200 chars max).
- Wrap rationale and remediation around 100 characters; do not break paths or identifiers.
- Avoid trailing whitespace.
- The report is read by a release reviewer — favor scannable bullets and short tables over paragraphs.

## Post-Execution Checks

**Check for extension hooks (after deep audit)**:

Check if `.specify/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under `hooks.after_audit_deep` first, then `hooks.after_audit`.
- If the YAML cannot be parsed or is invalid, skip hook checking silently and continue normally.
- Filter out hooks where `enabled` is explicitly `false`. Treat hooks without an `enabled` field as enabled by default.
- For each remaining hook, do **not** attempt to interpret or evaluate hook `condition` expressions:
  - If the hook has no `condition` field, or it is null/empty, treat the hook as executable.
  - If the hook defines a non-empty `condition`, skip the hook and leave condition evaluation to the HookExecutor implementation.
- For each executable hook, output the following based on its `optional` flag:
  - **Optional hook** (`optional: true`):
    ```
    ## Extension Hooks

    **Optional Hook**: {extension}
    Command: `/{command}`
    Description: {description}

    Prompt: {prompt}
    To execute: `/{command}`
    ```
  - **Mandatory hook** (`optional: false`):
    ```
    ## Extension Hooks

    **Automatic Hook**: {extension}
    Executing: `/{command}`
    EXECUTE_COMMAND: {command}
    ```
- If no hooks are registered or `.specify/extensions.yml` does not exist, skip silently.
