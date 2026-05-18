---
description: Audit the codebase against the TypeScript and Next.js behavioral directives in the constitution. Runs the audit script, summarizes findings by section and severity, and proposes prioritized fixes.
handoffs:
  - label: Deep Audit
    agent: speckit.audit.deep
    prompt: Run the deep audit on the same scope. Add tsc, eslint, npm audit, and cross-file analysis.
  - label: Rebuild Constitution from Findings
    agent: speckit.constitution.scan
    prompt: Re-scan the repo and refresh the constitution Sync Impact Report against the latest audit findings.
---

## User Input

```text
$ARGUMENTS
```

You **MAY** consider the user input as scope hints (e.g. "audit only `src/app` and `src/lib`", "ignore PERF rules for now", "treat Highs as Critical", "exclude tests"). If empty, audit the whole repository with default settings.

## Pre-Execution Checks

**Check for extension hooks (before audit)**:

- Check if `.specify/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under the `hooks.before_audit` key.
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

You are running a **codebase quality audit** against the behavioral directives in the project constitution (`.specify/memory/constitution.md`). Output goes to the user as a structured report; nothing is written to disk except the audit JSON, which is left under `.specify/audits/`.

Follow this flow:

### 1. Parse user input for scope hints

Look for:

- **Paths** — narrow the audit to a subset (e.g. "only `src/app`, `src/lib`"). Translate into `--paths app,src` for the script.
- **Severity floor** — phrases like "ignore mediums", "criticals only" map to `--severity critical` (or `high`).
- **Section filters** — phrases like "skip PERF" or "only security" map to `--sections SEC` (positive) or to a follow-up filter on findings (negative).
- **Rule filters** — explicit rule IDs (e.g. `TS.TYPE.any-usage`) map to `--rules <ids>`.
- **Max findings per rule** — "cap at 20 per rule" → `--max-findings-per-rule 20`.

Default values when nothing is specified: scan the whole repo, severity floor `low`, max 50 per rule.

### 2. Run the audit script

Invoke it in JSON mode. The script lives in the installed preset; both shell variants exist.

- **POSIX**:
  ```bash
  bash .specify/presets/nextjs/scripts/bash/audit-codebase.sh --json \
      [--paths ...] [--rules ...] [--sections ...] \
      [--severity critical|high|medium|low] [--max-findings-per-rule N]
  ```
- **PowerShell**:
  ```powershell
  pwsh .specify/presets/nextjs/scripts/powershell/audit-codebase.ps1 -Json \
      [-Paths ...] [-Rules ...] [-Sections ...] \
      [-Severity ...] [-MaxFindingsPerRule N]
  ```

Capture stdout into a variable; this is the **audit report**.

If the script is unavailable, **stop and tell the user** — do not improvise an audit by reading files directly. The script is the source of truth.

### 3. Persist the audit JSON

Create `.specify/audits/` if it does not exist. Write the captured JSON to:

```
.specify/audits/audit-<ISO timestamp YYYYMMDD-HHMMSS>.json
```

Also update `.specify/audits/latest.json` (overwrite) to always point at the most recent audit. These files are read-only artifacts — never edit them by hand.

### 4. Interpret findings

Map every finding's directive back to the constitution:

- `rule_id` prefix → constitution section (`TS.` → TypeScript Engineering · `FE.` → Frontend Behaviors · `BE.` → Backend Behaviors · `SEC.` → Security Behaviors · `PERF.` → Performance Behaviors · `INFRA.` → Infrastructure & Operations).
- `phase` + `criticality` are already on the finding.

Group findings:

1. **By severity** — `critical` first, then `high`, `medium`, `low`.
2. **Within each severity, by section**, then by `rule_id`, then by file.
3. **Collapse identical snippets** in the same file under one line if the script returned multiple lines.

### 5. Produce the report

Output to the user in this exact structure:

```
# Codebase Quality Audit

**Scope**: <paths or "whole repository">
**Files scanned**: <N>
**Rules evaluated**: <N>
**Findings**: <total> (critical: <c> · high: <h> · medium: <m> · low: <l>)
**Persisted**: `.specify/audits/audit-YYYYMMDD-HHMMSS.json` (also `latest.json`)

## Critical findings (block release)

### <rule_id> — <directive>
*Constitution: <section> / <phase> / <criticality> · Scope: <FE|BE|Both>*

- `<file>:<line>` — `<snippet>`
- `<file>:<line>` — `<snippet>`

**Remediation:** <one line from rule.remediation, expanded with one sentence of context>.

### <next rule_id> ...

## High findings (need exception or fix)

... same shape ...

## Medium findings

... same shape ...

## Low findings (track, don't block)

... same shape ...

## Top 5 prioritized actions

1. <action with specific file paths> — fixes <N> findings under <rule_id(s)>.
2. ...
```

Rules with **zero findings** are not listed. If a section is empty at a severity level, omit that severity heading entirely.

### 6. Recommendations

End the report with a short, opinionated **next-step** block:

- If there are any **Critical** findings, recommend `/speckit.audit.deep` for cross-file confirmation before opening PRs.
- If `TS.COMPILER.*` Criticals exist, recommend a single config-tightening PR before any code refactor (tighten the compiler, see what else breaks, then triage).
- If `SEC.SESSION.localstorage-auth` or `SEC.SECRET.public-env-prefix` exists, recommend treating them as production incidents and rotating any exposed values.
- If `BE.DAL.missing-server-only` exists, recommend a small PR that adds `import 'server-only';` to every flagged DAL module before any further backend work.
- If no Criticals or Highs, congratulate the team and suggest scheduling the next audit per release cadence.

### 7. Validation before final output

- Every finding listed in the report appears in the JSON file.
- No invented findings; do not extrapolate beyond what the script returned.
- File paths in the report match what the script returned (do not rewrite them).
- If the script returned `findings_total: 0`, the report says so explicitly and recommends keeping the cadence.

## Formatting & Style Requirements

- Use Markdown headings exactly as shown above; do not invent new top-level sections.
- Keep snippets to a single line; if the script returned a long line, the script already truncated to ~200 chars.
- Wrap rationale and remediation lines around 100 characters; do not break paths or identifiers.
- Avoid trailing whitespace.
- The report is read by humans triaging the codebase — favor scannable bullets over paragraphs.

## Post-Execution Checks

**Check for extension hooks (after audit)**:

Check if `.specify/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under the `hooks.after_audit` key.
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
