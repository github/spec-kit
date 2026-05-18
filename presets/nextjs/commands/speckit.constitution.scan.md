---
description: Scan the repository (Markdown docs, package.json, tsconfig, Next.js structure, tooling, CI) and export a properly-structured Next.js project constitution at .specify/memory/constitution.md.
handoffs:
  - label: Refine Constitution Interactively
    agent: speckit.constitution
    prompt: Refine the scanned constitution. Adjust principles, criticality, or phases based on...
  - label: Build Specification
    agent: speckit.specify
    prompt: Implement the feature specification based on the scanned constitution. I want to build...
---

## User Input

```text
$ARGUMENTS
```

You **MAY** consider the user input as additional context (e.g. "treat auth as Critical from P1", "default product is single-tenant", "ratification date 2026-05-18"). If empty, proceed with sensible defaults inferred from the scan.

## Pre-Execution Checks

**Check for extension hooks (before constitution scan)**:

- Check if `.specify/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under the `hooks.before_constitution` key.
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

You are producing the project constitution at `.specify/memory/constitution.md` by **scanning the repository for evidence** and then mapping that evidence onto the Next.js phased / criticality-tagged constitution template.

The template lives in the resolution stack as `constitution-template`. With this preset installed, it resolves to the Next.js variant under `.specify/presets/nextjs/templates/constitution-template.md`. Use that file as the structural skeleton; do **not** invent new sections or reorder existing ones.

Follow this execution flow exactly:

### 1. Run the scan script

Execute the scan script and capture its JSON output. The script lives under the installed preset's scripts directory; both shell variants accept `--json` (default) and `--text`.

- **POSIX shell**:
  ```bash
  bash .specify/presets/nextjs/scripts/bash/scan-repo.sh --json
  ```
- **PowerShell**:
  ```powershell
  pwsh .specify/presets/nextjs/scripts/powershell/scan-repo.ps1 -Json
  ```

If the preset path is not present (preset was added with a non-default install location), fall back to invoking the file by its location on disk relative to `$REPO_ROOT`. Do not silently skip the scan — if the script cannot be found or fails, stop and tell the user.

The script output conforms to the schema documented in `.specify/presets/nextjs/scripts/SCHEMA.md` (`schema_version: "1.0"`). Treat it as your **inventory** for the rest of this command. Do not run the scan more than once per invocation.

### 2. Read the relevant Markdown evidence

From the scan's `markdown.known_docs` list, read the following when present (in this order):

1. `README.md` — purpose, scope, install/run instructions, screenshots.
2. `ARCHITECTURE.md` — architectural intent if it exists.
3. `CONTRIBUTING.md` — workflow norms, branch rules, review rules.
4. `SECURITY.md` — declared security posture.
5. `AGENTS.md` / `CLAUDE.md` / `.github/copilot-instructions.md` — existing agent directives (will be re-aligned with the new constitution).
6. Up to 10 additional `.md` files from `markdown.files` that look like product/engineering specs (paths under `docs/`, `specs/`, or with headings that match "Architecture", "Design", "Spec", "RFC", "ADR").

Skip files larger than ~50 KB; the scan already gives you size, head excerpt, and headings. Use those summaries when the file is too large to read in full.

### 3. Derive concrete values from the inventory

From `inventory.package_json`:

- `[PROJECT_NAME]` ← `package_json.name` if present; otherwise the basename of `repo_root`.
- Capture `version`, `private`, `package_manager`, `scripts`, `next_version`, `react_version`, `ts_version`, and `node_engine` — surface them in the Sync Impact Report but do **not** rewrite principle wording around them (the constitution is behavioral, not stack-locked).
- Use `package_json.signals` to decide which **evidence notes** to add to the Sync Impact Report (e.g. "ESLint detected", "Zod detected; schema validation pattern available", "Argon2 detected; password hashing path available"). **Do not promote tooling to principles.** Principles stay behavioral.

From `inventory.tsconfig`:

- If `strict !== true` or `noUncheckedIndexedAccess !== true`, mark the corresponding P1 Critical TypeScript directives as **NOT MET** in the Sync Impact Report.
- If `tsconfig.present === false`, flag the entire TypeScript & Code Quality section as **UNVERIFIED**.

From `inventory.nextjs`:

- If `has_app_dir === true`, App Router is in use — Frontend Server-First directives apply as written.
- If `has_pages_dir === true` and `has_app_dir === false`, add a Sync Impact Report note: "Pages Router detected; constitution principles are written for App Router. Document the migration path or scope an exception with an expiry."
- If `has_middleware === true`, add a Sync Impact Report note linking to the Security principle "Never rely on middleware as a security boundary."

From `inventory.directives`:

- `use_client_files` and `use_server_files` go into the Sync Impact Report as raw counts.
- `server_only_imports === 0` while `use_server_files > 0` → flag the Backend P1 directive "Mark sensitive modules `server-only` so client imports fail the build" as **NOT MET**.

From `inventory.data_access.has_dal_directory`:

- If `false`, flag the Backend P1 Critical directive "Centralize all data access behind a single Data Access Layer" as **NOT MET**.

From `inventory.tooling`, `inventory.testing`, `inventory.environment`, and `inventory.git`:

- Missing CI workflows → flag the Infrastructure P1 High directive "CI runs typecheck, lint, test, and build on every PR" as **NOT MET**.
- Missing `.env.example` (or similar) → note as a Medium gap in the Sync Impact Report.
- Missing pinned Node version (`node_version_file` is null and `package_json.node_engine` is null) → flag the Infrastructure P1 Critical directive "Reproducible builds: lockfile committed, pinned runtime version" as **PARTIALLY MET** if a lockfile exists, otherwise **NOT MET**.

### 4. Decide the operating phase

If `inventory.constitution.exists === false` and no production deployment evidence is found in scanned docs, default to **P1 — Foundation** as the current phase. Otherwise infer the phase from evidence:

- Mentions of "paying customers", "production users", "SLA", "PCI/HIPAA/SOC2" in scanned docs → **P3 — Hardening** at minimum.
- A live production URL in `README.md` or deploy workflow → **P2 — MVP** at minimum.
- Otherwise → **P1 — Foundation**.

Record the chosen phase, the evidence trail, and a one-line justification at the top of the Sync Impact Report. If the user input from `$ARGUMENTS` explicitly states a phase, use that and note it as **user-overridden**.

### 5. Draft the constitution

Resolve the Next.js constitution template:

- Prefer `.specify/presets/nextjs/templates/constitution-template.md`.
- If unavailable, fall back to `.specify/templates/constitution-template.md`.

Fill the template precisely:

- Replace `[PROJECT_NAME]` everywhere.
- Replace `[CONSTITUTION_VERSION]`, `[RATIFICATION_DATE]`, `[LAST_AMENDED_DATE]`:
  - `CONSTITUTION_VERSION`: if no prior constitution, start at `1.0.0`. If amending, bump per the existing rules (MAJOR for principle redefinition, MINOR for additions, PATCH for clarifications).
  - `RATIFICATION_DATE`: if the user provided one, use it. Else use today (ISO `YYYY-MM-DD`) and note "first ratification by scan."
  - `LAST_AMENDED_DATE`: today.
- **Do not rewrite the Frontend / Backend / Security / Performance / TypeScript & Code Quality / Infrastructure tables.** They are the source of truth. The scan informs the Sync Impact Report, not the matrix.
- **Do not add technology names to the Core Principles section.** The constitution stays behavioral.

### 6. Produce the Sync Impact Report

Prepend an HTML comment block at the top of the constitution containing:

```
<!--
Sync Impact Report — generated by /speckit.constitution.scan
-----------------------------------------------------------
Scan timestamp:       <ISO UTC>
Schema version:       <inventory.schema_version>
Repo root:            <inventory.repo_root>
Chosen phase:         P1 | P2 | P3 | P4   (justification: ...)
Constitution version: <old> → <new>   (bump rationale: ...)
Ratification date:    <ISO>
Last amended date:    <ISO>

## Inventory snapshot
- Project name:        ...
- Package manager:     ...
- Next.js version:     ...
- React version:       ...
- TypeScript version:  ...
- Node engine:         ...
- App Router:          true|false
- Pages Router:        true|false
- Middleware:          true|false
- Route handlers:      <n>
- "use client" files:  <n>
- "use server" files:  <n>
- server-only imports: <n>
- DAL directory:       true|false
- ESLint / Prettier / Biome: ...
- CI workflows:        <count>
- .env example files:  <list or "none">
- Node version pinned: <file or "no">
- Tests directory:     true|false
- Constitution found:  true|false
- Markdown files:      <total> (listed <n>, truncated <bool>)

## Directive compliance (from scan)
- [Frontend / P1 / Critical] Default to Server Components — <MET|UNVERIFIED|NOT MET> (<evidence>)
- [Backend / P1 / Critical] Single Data Access Layer — <MET|NOT MET> (<evidence>)
- [Backend / P1 / Critical] `server-only` on sensitive modules — <MET|NOT MET> (<evidence>)
- [TS&CQ / P1 / Critical] Strict TS (`strict`, `noUncheckedIndexedAccess`, ...) — <MET|NOT MET> (<evidence>)
- [Infra / P1 / Critical] Reproducible builds + pinned runtime — <MET|PARTIAL|NOT MET> (<evidence>)
- [Infra / P1 / High] CI runs typecheck/lint/test/build — <MET|NOT MET> (<evidence>)
- ... include every Critical P1 directive at minimum; add Highs when evidence speaks to them.

## Markdown evidence consulted
- README.md (...)
- ARCHITECTURE.md (...)
- ...

## Follow-ups (TODO)
- TODO(<area>): <action>, owner=<unknown>, due=<next release>
-->
```

A directive's status is one of:

- **MET** — direct evidence in the scan supports it.
- **NOT MET** — direct evidence shows it is violated or missing.
- **PARTIAL** — some but not all sub-criteria are evidenced.
- **UNVERIFIED** — no signal either way; mark for follow-up.

Always emit a status for every **Critical** directive in P1 and any earlier phase relative to the chosen phase. Highs are listed when the scan speaks to them.

### 7. Consistency propagation

After writing the constitution:

- Read `.specify/templates/plan-template.md`, `.specify/templates/spec-template.md`, `.specify/templates/tasks-template.md`, and every command file under `.specify/templates/commands/*.md`. If any reference principles that contradict this constitution (e.g. assume Pages Router, ignore DAL, treat caching as implicit), flag them in the Sync Impact Report under **Templates requiring updates** with ✅/⚠ markers — do not silently edit them.
- Read `AGENTS.md`, `CLAUDE.md`, `.github/copilot-instructions.md` (whichever exist) and confirm they point at `.specify/memory/constitution.md` and (if available) `.specify/presets/nextjs/templates/agent-context.md`. If they don't, flag a follow-up to wire them — do not auto-rewrite the agent context here.

### 8. Validation before write

Before overwriting `.specify/memory/constitution.md`:

- No remaining unexplained `[BRACKET]` tokens.
- Version line matches the Sync Impact Report.
- Dates in ISO `YYYY-MM-DD` format.
- Principle wording is declarative ("MUST", "SHALL"), not vague ("should consider").
- Every Critical directive has a status in the Sync Impact Report.

If `.specify/memory/` does not exist, create it.

### 9. Write the constitution

Write the completed file to `.specify/memory/constitution.md` (overwrite if present).

### 10. Output summary

Print to the user:

- New version and bump rationale (or `1.0.0` if first ratification).
- Chosen operating phase and justification.
- Count of Critical directives **MET / NOT MET / PARTIAL / UNVERIFIED**.
- A 3–7 line summary of the most urgent follow-ups (P1 Critical "NOT MET" first).
- The exact path to the written file: `.specify/memory/constitution.md`.
- A suggested commit message, e.g.:
  `docs(constitution): scan-derived ratification v1.0.0 — phase P1, <n> directives MET, <m> NOT MET`

## Formatting & Style Requirements

- Use Markdown headings exactly as in the Next.js constitution template (do not demote/promote levels).
- Keep a single blank line between sections.
- Wrap rationale lines around 100 characters where readable; do not hard-break sentences awkwardly.
- Avoid trailing whitespace.
- The Sync Impact Report is an HTML comment — keep its content scannable; bullets over paragraphs.

## Post-Execution Checks

**Check for extension hooks (after constitution scan)**:

Check if `.specify/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under the `hooks.after_constitution` key.
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
