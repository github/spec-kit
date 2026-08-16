---
description: "Revise the current feature spec in place (add/remove ACs, FRs, stories) and cascade the change into plan and tasks."
handoffs:
  - label: Implement Revision Tasks
    agent: speckit.implement
    prompt: Implement only the new and cleanup tasks from the latest revision phase
  - label: Create Tasks
    agent: speckit.tasks
    prompt: Only if tasks.md does not exist. Never regenerate an existing task list — revise already appended a Revision phase.
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --paths-only
  ps: scripts/powershell/check-prerequisites.ps1 -Json -PathsOnly
  py: scripts/python/check_prerequisites.py --json --paths-only
---

The user is changing requirements on the **current** feature. That is why this command exists.

Do **not** rewrite `spec.md`. Do **not** rewrite `plan.md`. Do **not** rewrite `tasks.md`. Mid-flight requirement changes used to do that — wipe the file and regenerate — and it destroyed history. You only mark old lines, append new ones, and add a short log.

This is not `__SPECKIT_COMMAND_SPECIFY__` (new `specs/` folder). Not `__SPECKIT_COMMAND_PLAN__` or `__SPECKIT_COMMAND_TASKS__` (those rebuild artifacts). Not `__SPECKIT_COMMAND_CONVERGE__` (spec unchanged, code lagged). You do not write application code; `__SPECKIT_COMMAND_IMPLEMENT__` does.

## Input

```text
$ARGUMENTS
```

Use it if it isn't empty. Empty → ask what changed, or stop. Don't invent a delta.

New product (different user, different outcome, no shared stories) → `__SPECKIT_COMMAND_SPECIFY__`.

## Before you start (and again after you write)

If `.specify/extensions.yml` exists, run `hooks.before_revise` now and `hooks.after_revise` after writes, before you report.

Skip if the file is missing or invalid. Skip `enabled: false`. Skip hooks with a `condition`. Missing `enabled` means on.

Mandatory (`optional: false`) — print this and **run** it. Skills-mode names may differ. The block alone is not enough.

```text
## Extension Hooks
**Automatic Pre-Hook**: {extension}
Executing: `/{command}`
EXECUTE_COMMAND: {command}
```

Optional (`optional: true`):

```text
## Extension Hooks
**Optional Pre-Hook**: {extension}
Command: `/{command}`
Description: {description}
Prompt: {prompt}
To execute: `/{command}`
```

After writes, drop "Pre-" from the labels.

## The point

Stay in this feature folder. Never create a new `specs/` directory.

`spec.md` is the contract. Live lines are unmarked. Keep old lines visible as `SUPERSEDED by {new-id} (R{N})` or `RETIRED (R{N})`. Never two live items that contradict.

Don't edit a live FR/AC/SC in place to mean something else. That hides the change. **Supersede or add.** Reword only for typos / tighter wording of the *same* behavior, and only if nothing has been implemented for it yet.

`revisions.md` is a dated log, not a spec. One sentence + IDs.

Don't renumber. Don't reuse IDs. Next ID = highest ever used + 1 (struck lines and the log count).

Spec stays functional (what/why, not stack). Drop anything that violates a constitution `MUST`. Ignore an empty constitution template.

## Already implemented?

An ID is implemented only if a task that **references that ID** is `[x]` / `[X]`, or they said that behavior already shipped. A checked setup or foundational task does **not** mean later stories shipped. Any `[x]` on the feature is only a hint that *some* code exists — not a blanket remove-code trigger.

| Change | Spec | If that ID is not implemented yet | If that ID is already implemented |
|---|---|---|---|
| New requirement | Add a new ID | Plan + tasks to **build** it | Same: plan + tasks to **add** the new code |
| Replaces a live item | SUPERSEDE old, add new ID | Plan + tasks for the new behavior; cancel open tasks for the old ID | Plan + tasks to **add** new code **and remove** the old code |
| No longer valid | RETIRE the old line; no new ID | Cancel open tasks for that ID | Plan + tasks to **remove** the old code |

## Classify

- Named `FR-004` / `US1/AC2` → that ID.
- Description matches one live item → that item.
- Ambiguous → ask. Don't guess.
- Same idea, clearer words, **not** implemented → reword, keep the ID.
- Swaps or contradicts a live item → supersede (old stays, new ID).
- Drop, nothing replaces it → retire.
- New, no conflict → add. New AC goes on the story they named, or the only story that fits.

Already true on a **live** line (or same as last `R#`) is a duplicate. Skip it. All duplicates → stop, write nothing, don't bump `R{N}`. Mixed → do the new parts only.

## Do the work

1. Run `{SCRIPT}` once. Need `spec.md`. Also read `plan.md`, `tasks.md`, `revisions.md`, `constitution.md` if present. No spec → `__SPECKIT_COMMAND_SPECIFY__`. Quotes: `'I'\''m Groot'`.

2. List live stories, ACs, FRs, SCs. Remember every ID ever issued. If `tasks.md` exists, note next T-id, next phase, and which IDs already have a referencing task marked `[x]`.

3. Turn the input into add / reword / supersede / remove. Drop duplicates and constitution clashes. Nothing left → stop.

4. Preview only if they asked, or a retire would wipe the last AC on a P1 story. `N` = 1 or last `R#`+1.

5. **spec.md — append and mark, never replace the file.**
   - add: next ID (AC holes are fine).
   - reword: only the live sentence, same ID.
   - supersede: `- **FR-004** ~~password login~~ — SUPERSEDED by **FR-008** (R2)` plus a new FR-008 line.
   - remove: strike + `RETIRED (R2)`.
   - Set `**Last Revised**: {today} (R{N})`. Leave `**Created**`.

6. **plan.md — only if it exists. Never regenerate.**
   - New / supersede: a short bullet for **adding** the new behavior.
   - Supersede or retire **and that old ID is implemented**: a short bullet for **removing** the old behavior (what to delete, not a new architecture).
   - Supersede or retire **and that old ID is not implemented**: no remove-code bullet; just stop planning the old thing.
   - Strike the old plan bullet (`SUPERSEDED` / `RETIRED`). Don't delete it.
   - Don't send them to `__SPECKIT_COMMAND_PLAN__` to rebuild. If you truly can't patch, set `plan_status: needs-rebuild` in the report — still don't wipe the file.
   - No plan yet → `plan_status: missing`; next command is `__SPECKIT_COMMAND_PLAN__`.

7. **tasks.md — only if it exists. Never regenerate. Only append.**
   - Add `## Phase {n}: Revision R{N}`.
   - New/supersede: tasks to **write the new code**.
   - That old ID is implemented + supersede/retire: tasks to **delete or stop using the old code**.
   - Open task for an old ID: `- [ ] ~~T012~~ SUPERSEDED (R{N} → T020)` or `CANCELLED` if nothing replaces it. Don't delete the line.
   - Finished task for an old ID: leave `[x]`; add the cleanup task in the new phase.
   - No tasks file yet → `__SPECKIT_COMMAND_TASKS__` (or plan first). Do not invent a full task list here. Never hand off to tasks when `tasks.md` already exists.

8. Append to `revisions.md` (create with a one-line header: spec.md is the source of truth):

   ```markdown
   ## R{N} — {YYYY-MM-DD}
   {one sentence}
   - added: {id}
   - superseded: {old} → {new}
   - retired: {id}
   - reworded: {id}
   ```

   Skip empty bullets. Don't edit old entries. Don't append on a no-op.

9. Refresh `checklists/requirements.md` if it exists, **before** after-hooks.

10. Run `hooks.after_revise`.

Tell them once what was marked, what was added, and whether implement should **add** code, **remove** code, or both. Always include `plan_status:` as one of `patched` (plan bullets added or struck), `needs-rebuild` (could not patch safely), `missing` (no `plan.md`), or `unchanged` (no-op or plan needed no edit). Next is usually `__SPECKIT_COMMAND_IMPLEMENT__` (or plan/tasks if those files are still missing).

## Done When

- [ ] Same folder; spec was not rewritten from scratch
- [ ] Old requirements SUPERSEDED or RETIRED; new ones are new IDs
- [ ] `tasks.md` / `plan.md` were not regenerated — only patched or skipped
- [ ] After implement: tasks exist to add new code and/or remove old code
- [ ] Dated log only if something changed; no application code
- [ ] Hooks handled; short report
