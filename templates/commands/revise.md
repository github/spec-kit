---
description: "Revise the current feature spec in place (add/remove ACs, FRs, stories) and cascade the change into plan and tasks."
handoffs:
  - label: Implement Revision Tasks
    agent: speckit.implement
    prompt: Implement the open tasks from the latest revision phase
  - label: Rebuild Technical Plan
    agent: speckit.plan
    prompt: Rebuild the plan so it matches the revised spec
  - label: Create Tasks
    agent: speckit.tasks
    prompt: Create tasks from the revised spec and plan
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --paths-only
  ps: scripts/powershell/check-prerequisites.ps1 -Json -PathsOnly
  py: scripts/python/check_prerequisites.py --json --paths-only
---

# Revise Current Spec

Apply a **requirement delta** to the **current** feature specification. Edit `spec.md` in place, record the change in `revisions.md`, and cascade into `plan.md` / `tasks.md` when those files exist.

This command is for living-spec edits: adding or removing acceptance criteria, functional requirements, user stories, success criteria, or scope. It is **not** `__SPECKIT_COMMAND_SPECIFY__` (that starts a new feature) and **not** `__SPECKIT_COMMAND_CONVERGE__` (that finds code that lagged an unchanged spec).

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

Treat the input as a delta against the current spec. Typical shapes:

- Add an acceptance criterion / scenario (Given / When / Then, or a short behavior).
- Remove an acceptance criterion, FR, SC, user story, or edge case. The user may name an ID (`FR-004`, `US2/AC1`, `SC-003`) or describe the behavior.
- Change the wording of an existing item without changing its ID.
- Mix of the above in one request.

If the input is empty: ask what to add, remove, or change (interactive), or stop with a note that there is nothing to revise (automated). Do **not** invent a revision.

If the request is clearly a **new feature** (different user, different outcome, no shared stories with the current spec), STOP and recommend `__SPECKIT_COMMAND_SPECIFY__` instead of forcing it into this spec.

## Pre-Execution Checks

**Check for extension hooks (before revision)**:

- Check if `.specify/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under the `hooks.before_revise` key
- If the YAML cannot be parsed or is invalid, skip hook checking silently and continue normally
- Filter out hooks where `enabled` is explicitly `false`. Treat hooks without an `enabled` field as enabled by default.
- For each remaining hook, do **not** attempt to interpret or evaluate hook `condition` expressions:
  - If the hook has no `condition` field, or it is null/empty, treat the hook as executable
  - If the hook defines a non-empty `condition`, skip the hook and leave condition evaluation to the HookExecutor implementation
- For each executable hook, output the following based on its `optional` flag:
  - **Optional hook** (`optional: true`):

    ```text
    ## Extension Hooks

    **Optional Pre-Hook**: {extension}
    Command: `/{command}`
    Description: {description}

    Prompt: {prompt}
    To execute: `/{command}`
    ```

  - **Mandatory hook** (`optional: false`):

    ```text
    ## Extension Hooks

    **Automatic Pre-Hook**: {extension}
    Executing: `/{command}`
    EXECUTE_COMMAND: {command}

    Wait for the result of the hook command before proceeding to the Goal.
    ```

    After emitting the block above you MUST actually invoke the hook and wait for it to finish before continuing. Run it the same way you would run the command yourself in this agent/session (the invocation may differ from the literal `{command}` id shown above, e.g. a skills-mode agent runs it as `/skill:speckit-...` or `$speckit-...`). Emitting the block alone does not run the hook.

- If no hooks are registered or `.specify/extensions.yml` does not exist, skip silently

## Goal

Keep one feature directory as the source of truth while the contract changes. After this command:

- `spec.md` describes the **new** intended behavior
- `revisions.md` lists exactly what was added, removed, or reworded
- `plan.md` (if present) no longer describes retired behavior
- `tasks.md` (if present) has new work for additions and cancelled open tasks for removals
- no application code has been edited

## Operating Constraints

**IN-PLACE, SAME FEATURE DIRECTORY**: Do **not** create a new `specs/` folder, a new branch, or a new spec file. All writes stay inside the current `FEATURE_DIR`.

**NO APPLICATION CODE**: Do not create, modify, or delete product source. Completing new tasks is `__SPECKIT_COMMAND_IMPLEMENT__`. Cleaning up code that implemented a *removed* AC is also implement (via a cancellation/cleanup task), not this command.

**STABLE IDS — NEVER REUSE**:

- Do not renumber existing `FR-###`, `SC-###`, user-story numbers, or acceptance-scenario indexes that remain.
- Do not reuse a retired ID for a new item. If `FR-004` is removed, the next new requirement is `FR-008` (or whatever the next unused number is), never a new `FR-004`.
- New items take the next free number after the highest ID **ever issued** in this spec, including IDs listed as retired in `revisions.md`.

**SPEC STAYS FUNCTIONAL**: Write what users need and why. No tech stack, libraries, APIs, or file paths in `spec.md`. Those belong in `plan.md`.

**CONSTITUTION AUTHORITY**: `/memory/constitution.md` is non-negotiable. A new requirement that violates a `MUST` principle is rejected: report the conflict and do not apply that part of the delta. If the constitution is an unfilled template, skip this check.

**MINIMAL PLAN/TASKS EDITS**:

- Do not regenerate `plan.md` or rewrite `tasks.md` from scratch.
- Patch only sections the delta affects.
- Do not reorder, renumber, or delete existing task IDs. Cancel an open task by marking it in place (see Step 6). Leave completed tasks checked.

## Execution Steps

### 1. Resolve the current feature

Run `{SCRIPT}` from repo root **once** (combined `--json --paths-only` mode / `-Json -PathsOnly`). Parse minimal JSON payload fields:

- `FEATURE_DIR`
- `FEATURE_SPEC`

Derive:

- `SPEC` = `FEATURE_DIR/spec.md`
- `PLAN` = `FEATURE_DIR/plan.md`
- `TASKS` = `FEATURE_DIR/tasks.md`
- `REVISIONS` = `FEATURE_DIR/revisions.md`
- `CONSTITUTION` = `/memory/constitution.md` (if present)

If JSON parsing fails, or `spec.md` is missing, STOP and instruct the user to run `__SPECKIT_COMMAND_SPECIFY__` first.

For single quotes in args like "I'm Groot", use escape syntax: e.g `'I'\''m Groot'` (or double-quote if possible: `"I'm Groot"`).

### 2. Load artifacts

Read `spec.md` in full. From it, inventory:

- User stories (number, title, priority) and each **Acceptance Scenario** (stable key `US{n}/AC{i}`)
- Functional Requirements (`FR-###`)
- Success Criteria (`SC-###`)
- Edge cases, out-of-scope, assumptions (if present)
- Highest issued ID per series

If `revisions.md` exists, load retired IDs so they stay retired.

If `plan.md` exists, load section headings and any references to FR/SC/story IDs.

If `tasks.md` exists, load every task ID, checkbox state, phase heading, and which requirement/story it traces to. Compute the next task ID and the next phase number.

If `CONSTITUTION` exists and is not an unfilled template, load `MUST` / `SHOULD` principles.

### 3. Classify the delta

Turn the user input into a list of `Change` records. Each record has:

- `op`: `add` | `remove` | `reword`
- `kind`: `acceptance-scenario` | `functional-requirement` | `success-criterion` | `user-story` | `edge-case` | `scope`
- `target`: existing ID if the user named or uniquely described one; empty for a new item
- `text`: the new wording (add/reword) or the retired wording (remove)

Resolution rules:

- If the user names `FR-004`, `SC-002`, `US1`, or `US2/AC1`, use that ID.
- If they describe behavior ("password login", "CSV export") and exactly one inventory item matches, use that item.
- If several items match, ask (interactive) or STOP listing the candidates (automated). Do not guess.
- Adding an AC: attach it to the user story the user named. If they did not name a story and exactly one story fits, use that. Otherwise ask / STOP.
- Removing a whole user story also removes its ACs (each AC is its own `remove` record).
- Reword vs remove+add: if the user is tightening wording of the same behavior, `reword` and **keep the ID**. If they are replacing behavior with different behavior, `remove` the old ID and `add` a new ID.

Reject any `add` that conflicts with a constitution `MUST`. Leave the rest of the delta intact if some items are valid.

If after classification there are zero changes, STOP and say so. Do not write files.

### 4. Show the planned revision (before writes)

Output a compact table and wait only if the user asked to preview or if any `remove` targets a P1 story's last remaining AC (that would empty the MVP). Otherwise proceed.

```text
## Planned Revision R{N}

| Op | Kind | ID | Summary |
|----|------|----|---------|
| add | acceptance-scenario | US1/AC3 | Expired session → SSO redirect |
| remove | functional-requirement | FR-004 | Password login |
```

`N` is 1 if `revisions.md` does not exist, otherwise one more than the highest `R#` already recorded.

### 5. Edit `spec.md`

Apply every `Change` to `spec.md`:

- **add AC**: append a numbered **Given / When / Then** scenario under that story's Acceptance Scenarios. Use the next index for that story only (`US1/AC3` if AC1 and AC2 exist). Do not renumber earlier ACs.
- **remove AC**: delete that numbered scenario from the story. Do **not** renumber the ACs that remain (a hole such as AC1, AC3 is correct). If the story now has zero ACs, keep the story and add an HTML comment `<!-- no remaining acceptance scenarios; see revisions.md R{N} -->` so the gap is visible.
- **add FR / SC**: append with the next unused ID.
- **remove FR / SC / story / edge case**: delete the item from the active spec.
- **reword**: replace the text; keep the ID and position.

Also:

- Set or update `**Last Revised**: {today's date} (R{N})` near the spec header. Do not change `**Created**`.
- If `**Status**` is `Draft` and a plan already exists, leave Status as-is unless the spec had a custom status; do not invent a new status vocabulary.
- Keep the spec's existing section structure. Do not add a "changelog" section inside `spec.md` — that belongs in `revisions.md`.
- Do not embed implementation checklists in the spec.

### 6. Cascade to plan and tasks (only if those files exist)

**`plan.md` present:**

- Remove or strike bullets that exist only to serve a `remove` target.
- Add the smallest possible bullets for each `add` that the plan must acknowledge (data, flow, or constraint — still no new stack unless the user asked for a technical change).
- If the delta cannot be expressed as a small patch (for example it invalidates the chosen architecture), do **not** rewrite the plan. Record `plan_status: needs-rebuild` in the revision entry and tell the user to run `__SPECKIT_COMMAND_PLAN__`.

**`plan.md` absent:** skip. Next step after this command is `__SPECKIT_COMMAND_PLAN__`.

**`tasks.md` present:**

- **Additions**: append a new section at the bottom:

  ```markdown
  ## Phase {next}: Revision R{N}

  **Goal**: Implement spec changes from revision R{N}

  - [ ] T{next} [US{{n}}] {concrete task with file path if plan has one}
  ```

  One task per added AC or FR unless two adds are the same code change. Continue task IDs from the current maximum (`T014` after `T013`). Do not reuse cancelled IDs.

- **Removals**: for each open (`- [ ]`) task that traces only to a removed ID, mark it cancelled **in place**:

  ```markdown
  - [ ] ~~T012~~ CANCELLED (R{N}: removed US1/AC2)
  ```

  Do not delete the line. Do not uncheck a completed task. If a **completed** task implemented a removed AC, append one new task under the Revision phase: `Review/remove leftover behavior for {retired ID}` so implement can clean it up.

**`tasks.md` absent:** skip. Next step is `__SPECKIT_COMMAND_TASKS__` (or `__SPECKIT_COMMAND_PLAN__` if there is no plan either).

### 7. Append `revisions.md`

Create the file if it does not exist:

```markdown
# Spec Revisions: {feature name}

Append-only history of in-place spec changes. IDs listed under **Retired** must never be reused.
```

Then append:

```markdown
## R{N} — {YYYY-MM-DD}

**Summary**: {one sentence}

**Added**:
- `{new-id}`: {text}

**Removed (retired)**:
- `{old-id}`: {full previous text}

**Reworded**:
- `{id}`: {old text} → {new text}

**Cascade**:
- plan.md: patched | needs-rebuild | skipped (missing)
- tasks.md: appended Phase {n} | cancelled {id list} | skipped (missing)

**Next**: `__SPECKIT_COMMAND_IMPLEMENT__` | `__SPECKIT_COMMAND_PLAN__` | `__SPECKIT_COMMAND_TASKS__`
```

Omit empty subsections. Never edit or delete earlier `R#` entries.

### 8. Report

```text
## Revision R{N} Applied

Feature: {FEATURE_DIR}
Spec: {SPEC}

| Op | ID | Result |
|----|----|--------|
| add | US1/AC3 | written to spec.md |
| remove | FR-004 | retired; T012 cancelled |

Next: {command}

Open revision tasks: {task ids or "none"}
```

## Mandatory Post-Execution Hooks

**You MUST complete this section before reporting completion to the user.**

Check if `.specify/extensions.yml` exists in the project root.
- If it does not exist, or no hooks are registered under `hooks.after_revise`, skip to the Completion Report.
- If it exists, read it and look for entries under the `hooks.after_revise` key.
- If the YAML cannot be parsed or is invalid, skip hook checking silently and continue to the Completion Report.
- Filter out hooks where `enabled` is explicitly `false`. Treat hooks without an `enabled` field as enabled by default.
- For each remaining hook, do **not** attempt to interpret or evaluate hook `condition` expressions:
  - If the hook has no `condition` field, or it is null/empty, treat the hook as executable
  - If the hook defines a non-empty `condition`, skip the hook and leave condition evaluation to the HookExecutor implementation
- For each executable hook, output the following based on its `optional` flag:
  - **Mandatory hook** (`optional: false`) — **You MUST emit `EXECUTE_COMMAND:` for each mandatory hook**:
    ```
    ## Extension Hooks

    **Automatic Hook**: {extension}
    Executing: `/{command}`
    EXECUTE_COMMAND: {command}
    ```
    After emitting the block above you MUST actually invoke the hook and wait for it to finish before continuing. Run it the same way you would run the command yourself in this agent/session (the invocation may differ from the literal `{command}` id shown above, e.g. a skills-mode agent runs it as `/skill:speckit-...` or `$speckit-...`). Emitting the block alone does not run the hook.
  - **Optional hook** (`optional: true`):
    ```
    ## Extension Hooks

    **Optional Hook**: {extension}
    Command: `/{command}`
    Description: {description}

    Prompt: {prompt}
    To execute: `/{command}`
    ```

## Completion Report

Report completion to the user with:
- `FEATURE_DIR` / `SPEC_FILE`
- Revision number `R{N}`
- Added / removed / reworded IDs
- Cascade result for `plan.md` and `tasks.md`
- Next command (`__SPECKIT_COMMAND_IMPLEMENT__`, `__SPECKIT_COMMAND_PLAN__`, or `__SPECKIT_COMMAND_TASKS__`)

If `FEATURE_DIR/checklists/requirements.md` exists, re-evaluate its items against the revised spec and update pass/fail markers. Do not invent a new checklist.

## Done When

- [ ] `spec.md` reflects the requested delta; no new feature directory was created
- [ ] `revisions.md` has a new `R{N}` entry listing added, removed (retired), and reworded IDs
- [ ] Retired IDs were not reused
- [ ] `plan.md` was patched or marked `needs-rebuild` (or skipped if missing)
- [ ] `tasks.md` gained a Revision phase and/or cancelled obsolete open tasks (or skipped if missing)
- [ ] No application code was edited
- [ ] Extension hooks dispatched or skipped according to the rules above
- [ ] Completion reported to the user

## Quick Guidelines

- Prefer the smallest delta that captures the user's request.
- Adding an AC to an existing story is the common case — do that, don't invent a new story.
- Removing an AC does not delete shipped code; it retires the requirement and leaves a cleanup task if the code already exists.
- If you are unsure whether two phrasings are the same requirement, `reword` (keep the ID). If they are different behaviors, `remove` + `add`.
- When in doubt, ask one question rather than applying a guessed delta.
