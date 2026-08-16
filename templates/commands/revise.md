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

- `spec.md` is the **only** current contract
- `revisions.md` is a **small dated log** of what changed (not a second spec)
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

**REVISIONS.MD IS A LOG, NOT SOURCE OF TRUTH**:
- `spec.md` decides what is required now. Never treat `revisions.md` as the spec.
- Each entry is one short dated block: `R{N}`, date, one-line summary, IDs only.
- Do not copy AC/FR prose, plan notes, or next-command instructions into the log.
- Implement / analyze / converge read `spec.md` (and `CANCELLED` tasks). They may consult the log only for **retired IDs**.

**DUPLICATES ARE A NO-OP**:
- Compare the requested delta to the **current** `spec.md` (not to the log).
- `add` of behavior already in the spec → drop that change (duplicate).
- `remove` of an ID already absent / already retired → drop that change.
- `reword` that does not change meaning or text → drop that change.
- Same delta as the latest `R#` (re-run) → drop the whole request.
- If every change is a duplicate, STOP. Report which items were already true. Do **not** write `spec.md`, `revisions.md`, `plan.md`, or `tasks.md`. Do **not** bump `R{N}`.
- Partial request: apply only the non-duplicate changes; mention skipped duplicates in the report.

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

- `op`: `add` | `remove` | `reword` | `supersede`
- `kind`: `acceptance-scenario` | `functional-requirement` | `success-criterion` | `user-story` | `edge-case` | `scope`
- `target`: existing ID if the user named or uniquely described one; empty for a new item
- `replaces`: old ID when `op` is `supersede`
- `text`: the new wording (add/reword/supersede) or the retired wording (remove)

Ignore inventory lines already marked `SUPERSEDED` or `RETIRED` when matching current behavior. Still count those IDs as issued so they are never reused.

Resolution rules:

- If the user names `FR-004`, `SC-002`, `US1`, or `US2/AC1`, use that ID.
- If they describe behavior ("password login", "CSV export") and exactly one **live** inventory item matches, use that item.
- If several items match, ask (interactive) or STOP listing the candidates (automated). Do not guess.
- Adding an AC: attach it to the user story the user named. If they did not name a story and exactly one story fits, use that. Otherwise ask / STOP.
- **Conflict / replacement (prefer this over silent delete):** if the new behavior **contradicts** a live item, or the user is swapping one behavior for another ("SSO instead of password"), use `supersede`: keep the old ID in place marked `SUPERSEDED by {new-id} (R{N})`, and **add** a new ID for the new text. Do not leave two live items that disagree.
- Tightening wording of the **same** behavior → `reword` (keep the ID). Do not supersede.
- Dropping something with **no** replacement → `remove` (mark `RETIRED (R{N})`, do not delete the line).
- Removing a whole user story: `remove` the story and `remove` or `supersede` each of its ACs depending on whether replacements were given.

Reject any `add` that conflicts with a constitution `MUST`. Leave the rest of the delta intact if some items are valid.

Drop duplicates using the **DUPLICATES ARE A NO-OP** rules above. If nothing remains, STOP. Do not write files and do not append a revision entry.

### 4. Show the planned revision (before writes)

Output a compact table and wait only if the user asked to preview or if any `remove` targets a P1 story's last remaining AC (that would empty the MVP). Otherwise proceed.

```text
## Planned Revision R{N}

| Op | Kind | ID | Summary |
|----|------|----|---------|
| supersede | functional-requirement | FR-004 → FR-008 | Password login → SSO only |
| add | acceptance-scenario | US1/AC3 | Expired session → SSO redirect |
```

`N` is 1 if `revisions.md` does not exist, otherwise one more than the highest `R#` already recorded.

### 5. Edit `spec.md`

Apply every `Change` to `spec.md`. **Live** items are unmarked lines. `SUPERSEDED` / `RETIRED` lines stay visible but are **not** current requirements.

- **add AC**: append a numbered **Given / When / Then** under that story. Next index for that story only. Do not renumber earlier ACs (holes are correct).
- **add FR / SC**: append with the next unused ID.
- **reword**: replace the live text; keep the ID and position. Do not add a sibling ID.
- **supersede**: do **not** delete the old line. Strike it and point at the new ID, then add the new item next to it (or at the end of that section):

  ```markdown
  - **FR-004** ~~Users MUST sign in with email and password~~ — SUPERSEDED by **FR-008** (R2)
  - **FR-008**: Users MUST sign in with company SSO only
  ```

  Same pattern for ACs (`US1/AC2` → `US1/AC4`) and SCs (`SC-001` → `SC-005`).
- **remove** (no replacement): do **not** delete the line. Strike it and mark retired:

  ```markdown
  - **SC-003** ~~90% first-attempt success~~ — RETIRED (R2)
  ```

Also:

- Set or update `**Last Revised**: {today's date} (R{N})` near the spec header. Do not change `**Created**`.
- If `**Status**` is `Draft` and a plan already exists, leave Status as-is unless the spec had a custom status; do not invent a new status vocabulary.
- Keep the spec's existing section structure. Do not add a changelog section — `revisions.md` stays the small dated log.
- Do not embed implementation checklists in the spec.
- Never leave two **live** items that contradict each other.

### 6. Cascade to plan and tasks (only if those files exist)

**`plan.md` present:**

- For `supersede` / `remove`: strike the old bullet in place and mark `SUPERSEDED by {new}` or `RETIRED (R{N})`. Do not delete it.
- For `add` / `supersede`: add the smallest new bullet the plan must acknowledge (data, flow, or constraint — still no new stack unless the user asked for a technical change).
- If the delta cannot be expressed as a small patch (for example it invalidates the chosen architecture), do **not** rewrite the plan. Record `plan_status: needs-rebuild` and tell the user to run `__SPECKIT_COMMAND_PLAN__`.

**`plan.md` absent:** skip. Next step after this command is `__SPECKIT_COMMAND_PLAN__`.

**`tasks.md` present:**

- **Additions**: append a new section at the bottom:

  ```markdown
  ## Phase {next}: Revision R{N}

  **Goal**: Implement spec changes from revision R{N}

  - [ ] T{next} [US{{n}}] {concrete task with file path if plan has one}
  ```

  One task per added or superseding AC/FR unless two changes are the same code change. Continue task IDs from the current maximum (`T014` after `T013`). Do not reuse cancelled or superseded IDs.

- **Supersede**: for each open (`- [ ]`) task that traces only to the old ID, mark it **in place** (do not delete, do not uncheck completed work):

  ```markdown
  - [ ] ~~T012~~ SUPERSEDED (R{N} → T020)
  ```

  Add `T020` in the Revision phase for the new ID.
- **Remove** (no replacement): mark open tasks cancelled:

  ```markdown
  - [ ] ~~T012~~ CANCELLED (R{N}: retired US1/AC2)
  ```

  If a **completed** task implemented a retired or superseded ID, append one cleanup task under the Revision phase: `Review/remove leftover behavior for {old-id}`.

**`tasks.md` absent:** skip. Next step is `__SPECKIT_COMMAND_TASKS__` (or `__SPECKIT_COMMAND_PLAN__` if there is no plan either).

### 7. Append `revisions.md`

This file is a **dated index**, not a spec. Create it if it does not exist:

```markdown
# Spec Revisions

Dated log of in-place edits. `spec.md` is the source of truth. Retired IDs must not be reused.
```

Then append **only** this small block (IDs and a one-line summary — no full AC text, no cascade, no next-command):

```markdown
## R{N} — {YYYY-MM-DD}

{one sentence}

- added: {id, id}
- superseded: {old-id} → {new-id}
- retired: {id, id}
- reworded: {id, id}
```

Omit empty bullets. Never edit or delete earlier `R#` entries. If this revision was a no-op (all duplicates), do not append anything.

If `FEATURE_DIR/checklists/requirements.md` exists, re-evaluate its items against the revised spec and update pass/fail markers **before** post-execution hooks so a git auto-commit includes those edits. Do not invent a new checklist.

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

After hooks, report completion once:

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

Also include:
- Cascade result for `plan.md` and `tasks.md`
- Next command (`__SPECKIT_COMMAND_IMPLEMENT__`, `__SPECKIT_COMMAND_PLAN__`, or `__SPECKIT_COMMAND_TASKS__`)

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
