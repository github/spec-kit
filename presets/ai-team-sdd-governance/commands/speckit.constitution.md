---
description: Amend the baseline project constitution incrementally; seed from preset template when memory still has placeholders.
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Pre-Execution Checks

**Check for extension hooks (before constitution update)**:
- Check if `.specify/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under the `hooks.before_constitution` key
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

    Wait for the result of the hook command before proceeding to the Outline.
    ```
    After emitting the block above you MUST actually invoke the hook and wait for it to finish before continuing. Run it the same way you would run the command yourself in this agent/session (the invocation may differ from the literal `{command}` id shown above, e.g. a skills-mode agent runs it as `/skill:speckit-...` or `$speckit-...`). Emitting the block alone does not run the hook.
- If no hooks are registered or `.specify/extensions.yml` does not exist, skip silently

## Outline

You are updating the project constitution at `.specify/memory/constitution.md`.

**Default mode is amend-first**: start from the existing baseline and apply only the
changes the user requested. Do **not** rewrite the entire document unless the user
explicitly asks to reset or replace the constitution.

### 1. Load or seed the constitution

1. If `.specify/memory/constitution.md` is missing, create it from the best available
   baseline template (see resolution order below).

2. Load `.specify/memory/constitution.md` and detect whether it is still an unfilled
   template: any token matching `[ALL_CAPS_IDENTIFIER]` (e.g. `[PROJECT_NAME]`,
   `[PRINCIPLE_1_NAME]`).

3. **If unfilled placeholders are present**, seed from baseline before amending:
   - `.specify/templates/overrides/constitution-template.md` (if present)
   - `.specify/presets/*/templates/constitution-template.md` from installed presets
     (when multiple exist, prefer the preset with the lowest priority number in
     `.specify/presets/.registry`)
   - `.specify/templates/constitution-template.md` (core fallback)

   Copy the resolved baseline into memory, then fill only the remaining placeholders
   from user input and repo context (README, docs, project name). Do not discard
   pre-filled principles from the baseline template.

4. **If no unresolved placeholders remain**, treat the file as the authoritative
   baseline and proceed in amend mode (step 2).

### 2. Amend mode (default)

When the user supplies changes — including partial updates (e.g., one principle only):

- Apply **only** the requested additions, revisions, or removals.
- Preserve all unmentioned sections **verbatim** (wording, order, headings).
- Do **not** re-derive or rewrite principles the user did not mention.
- Do **not** remove HTML comments unless they are replaced by concrete content.
- If the user asks to add a principle, follow the existing heading hierarchy and
  numbering style in the document.
- If the user asks to remove a principle, remove it and note the removal in the
  Sync Impact Report; bump MAJOR unless the user marks it as deprecated/optional.

When user input is empty and the constitution is already complete (no placeholders),
summarize the current constitution and ask what the user wants to amend — do not
rewrite the file.

**Full reset** only when the user explicitly requests it (e.g., "reset constitution",
"replace entire constitution", "start from scratch"). In that case, re-seed from the
baseline template (step 1.3) and apply any additional user guidance.

### 3. Version and dates

Read the current version from the constitution footer or Governance section.

`CONSTITUTION_VERSION` must increment according to semantic versioning:

- **MAJOR**: Backward incompatible governance/principle removals or redefinitions.
- **MINOR**: New principle/section added or materially expanded guidance.
- **PATCH**: Clarifications, wording, typo fixes, non-semantic refinements.

- `LAST_AMENDED_DATE`: set to today (ISO `YYYY-MM-DD`) when any change is made;
  otherwise keep the previous value.

If the bump type is ambiguous, state your reasoning before finalizing.

### 4. Consistency propagation (when principles changed)

Only when the amendment adds, removes, or materially changes a principle:

- Read `.specify/templates/plan-template.md` — align Constitution Check gates if needed.
- Read `.specify/templates/spec-template.md` — align mandatory sections if needed.
- Read `.specify/templates/tasks-template.md` — align task categories if needed.
- Flag templates that need manual follow-up; update them only when the change clearly
  requires it.

Skip this step for PATCH-only wording changes unless the user asks for propagation.

### 5. Sync Impact Report

Prepend an HTML comment at the top of the updated constitution:

- Version change: old → new (with bump rationale)
- Modified principles (old title → new title if renamed)
- Added / removed sections
- Templates: ✅ updated / ⚠ pending (with paths)
- Deferred TODOs if any fields intentionally left incomplete

### 6. Validation

- No unexplained `[ALL_CAPS]` bracket tokens left (unless user explicitly deferred).
- Version line matches the report.
- Dates in ISO `YYYY-MM-DD` format.
- Principles are declarative and testable; prefer MUST/SHOULD over vague "should".

### 7. Write and summarize

1. Write the updated constitution to `.specify/memory/constitution.md` (overwrite).
2. Output a summary: new version, what changed, files flagged for follow-up,
   suggested commit message (e.g., `docs: amend constitution to vX.Y.Z (...)`).

### Formatting

- Keep Markdown heading levels consistent with the existing document.
- One blank line between sections; no trailing whitespace.

Do not create a new template file; always operate on `.specify/memory/constitution.md`.

## Post-Execution Checks

**Check for extension hooks (after constitution update)**:
Check if `.specify/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under the `hooks.after_constitution` key
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
    After emitting the block above you MUST actually invoke the hook and wait for it to finish before continuing. Run it the same way you would run the command yourself in this agent/session (the invocation may differ from the literal `{command}` id shown above, e.g. a skills-mode agent runs it as `/skill:speckit-...` or `$speckit-...`). Emitting the block alone does not run the hook.
- If no hooks are registered or `.specify/extensions.yml` does not exist, skip silently
