---
description: Summarize Spec Kit workflow status across all specs without modifying files.
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Pre-Execution Checks

**Check for extension hooks (before status reporting)**:
- Check if `.specify/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under the `hooks.before_status` key
- If the YAML cannot be parsed or is invalid, skip hook checking silently and continue normally
- Filter out hooks where `enabled` is explicitly `false`. Treat hooks without an `enabled` field as enabled by default.
- For each remaining hook, do **not** attempt to interpret or evaluate hook `condition` expressions:
  - If the hook has no `condition` field, or it is null/empty, treat the hook as executable
  - If the hook defines a non-empty `condition`, skip the hook and leave condition evaluation to the HookExecutor implementation
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

    Wait for the result of the hook command before proceeding to the Goal.
    ```
- If no hooks are registered or `.specify/extensions.yml` does not exist, skip silently

## Goal

Produce a read-only status report for every Spec Kit feature under `specs/`, including artifact availability, task progress, checklist progress, inferred workflow phase, and the next suggested command.

## Operating Constraints

**STRICTLY READ-ONLY**: Do **not** modify any files. Do not create, update, or delete specs, plans, tasks, checklists, branches, or configuration.

**Repository Scope**: Work from the repository root. Prefer the current working directory if it contains `.specify/` or `specs/`; otherwise, walk upward until a directory with `.specify/` or `specs/` is found. If neither is found, report that this does not appear to be a Spec Kit project.

**Input Handling**: If the user input is empty, report all specs. If the user input names a feature id, feature directory, branch, or substring, filter the report to matching spec directories and state the filter used.

## Execution Steps

### 1. Discover Project and Specs

- Locate the project root.
- Locate `specs/` under the project root.
- Enumerate direct child directories under `specs/`.
- Treat each child directory as one feature spec. Prefer directories whose names look like `NNN-feature-name`, but do not hide other directories if they contain Spec Kit artifacts.
- Sort features by numeric prefix when present, then by directory name.
- If `specs/` does not exist or no feature directories are found, output a concise empty-state report and stop.

### 2. Identify the Active Feature

- Try to detect the current git branch with `git branch --show-current`.
- If git is unavailable, the command fails, or the project is not a git repository, continue without an active feature marker.
- Mark a feature as active when its directory name exactly matches the current branch, or when the branch name ends with the feature directory name.

### 3. Inspect Artifacts

For each feature directory, inspect only file existence and compact metadata:

- Required workflow artifacts:
  - `spec.md`
  - `plan.md`
  - `tasks.md`
- Optional design artifacts:
  - `research.md`
  - `data-model.md`
  - `contracts/` with at least one file
  - `quickstart.md`
  - `checklists/` with at least one `.md` file

Do not load full artifact contents. For `tasks.md` and checklist files, read only enough to count checklist item states.

### 4. Calculate Progress

For each `tasks.md`, count task items matching:

- Complete: lines that begin with `- [x]` or `- [X]`
- Incomplete: lines that begin with `- [ ]`

For each checklist file under `checklists/`, count checklist items with the same checkbox pattern.

Derive task progress:

- `n/a` when `tasks.md` is missing
- `0/0` when `tasks.md` exists but has no checkbox items
- `{completed}/{total}` otherwise

Derive checklist status:

- `n/a` when no checklist files exist
- `PASS {completed}/{total}` when all checklist items are complete and total is greater than zero
- `FAIL {completed}/{total}` when at least one checklist item is incomplete
- `0/0` when checklist files exist but contain no checkbox items

### 5. Infer Workflow Phase

Use the following precedence:

- `Missing spec` when `spec.md` is absent
- `Specified` when `spec.md` exists and `plan.md` is absent
- `Planned` when `plan.md` exists and `tasks.md` is absent
- `Ready` when `tasks.md` exists and has task checkboxes but none are complete
- `In progress` when some, but not all, task checkboxes are complete
- `Complete` when all task checkboxes are complete and total is greater than zero
- `Tasked` when `tasks.md` exists but has no task checkboxes

### 6. Suggest Next Action

Use this default mapping, adjusting only when the inspected artifacts clearly indicate a better next action:

- `Missing spec` -> `/speckit.specify`
- `Specified` -> `/speckit.plan`
- `Planned` -> `/speckit.tasks`
- `Ready` -> `/speckit.implement`
- `In progress` -> `/speckit.implement`
- `Tasked` -> Review `tasks.md` formatting
- `Complete` -> Review or ship

If checklist status is `FAIL`, add `complete checklist items` to the next action.

### 7. Produce the Status Report

Output a Markdown report with this structure:

```markdown
## Spec Kit Status

| Active | Feature | Phase | Artifacts | Tasks | Checklists | Next |
|--------|---------|-------|-----------|-------|------------|------|
| * | 001-example | In progress | spec, plan, research, tasks | 12/20 | PASS 8/8 | /speckit.implement |

**Summary**

- Total specs: N
- Active feature: FEATURE_NAME or n/a
- Complete: N
- In progress: N
- Ready for implementation: N
- Missing next artifact: N
```

Artifact display rules:

- List present artifacts by short names: `spec`, `plan`, `research`, `data-model`, `contracts`, `quickstart`, `tasks`, `checklists`
- If an expected workflow artifact is missing, include `missing: spec`, `missing: plan`, or `missing: tasks`
- Keep each row compact; do not include raw artifact content

### 8. Check for Extension Hooks

After reporting, check if `.specify/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under the `hooks.after_status` key
- If the YAML cannot be parsed or is invalid, skip hook checking silently and continue normally
- Filter out hooks where `enabled` is explicitly `false`. Treat hooks without an `enabled` field as enabled by default.
- For each remaining hook, do **not** attempt to interpret or evaluate hook `condition` expressions:
  - If the hook has no `condition` field, or it is null/empty, treat the hook as executable
  - If the hook defines a non-empty `condition`, skip the hook and leave condition evaluation to the HookExecutor implementation
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
- If no hooks are registered or `.specify/extensions.yml` does not exist, skip silently

## Context

{ARGS}
