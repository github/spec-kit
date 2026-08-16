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

The user is changing the **current** feature spec — not starting a new one.

Edit `spec.md` in place. Patch `plan.md` and `tasks.md` only if they already exist. Do not write application code; leave that to `__SPECKIT_COMMAND_IMPLEMENT__`.

This is not `__SPECKIT_COMMAND_SPECIFY__` (that opens a new `specs/` folder). It is not `__SPECKIT_COMMAND_CONVERGE__` (that assumes the spec is stable and the code lagged).

## Input

```text
$ARGUMENTS
```

Use it if it isn't empty. If it is empty, ask what changed (or stop if nobody is there). Don't invent a delta.

If they described a new product — different user, different outcome, no shared stories — stop and point them at `__SPECKIT_COMMAND_SPECIFY__`.

## Before you start (and again after you write)

If `.specify/extensions.yml` exists, run hooks for `hooks.before_revise` now, and `hooks.after_revise` after the files are written, before you report.

Skip the file if it's missing or invalid. Skip any hook with `enabled: false`. Skip a hook that has a `condition` (don't evaluate it). Missing `enabled` means on.

Mandatory hook (`optional: false`) — print this and **actually run** it. Skills-mode names may differ from `{command}`. Waiting on the block alone is not enough.

```text
## Extension Hooks
**Automatic Pre-Hook**: {extension}
Executing: `/{command}`
EXECUTE_COMMAND: {command}
```

Optional hook (`optional: true`):

```text
## Extension Hooks
**Optional Pre-Hook**: {extension}
Command: `/{command}`
Description: {description}
Prompt: {prompt}
To execute: `/{command}`
```

After the write, use **Automatic Hook** / **Optional Hook** (drop "Pre-").

## How to think about it

Stay in this feature directory. Do **not** create a new `specs/` folder.

`spec.md` is the contract. Only unmarked lines are live. Keep `SUPERSEDED` / `RETIRED` lines so people can see what changed, but don't treat them as current. Never leave two live items that contradict.

`revisions.md` is a dated log, not a spec. One sentence and IDs. No copied AC text.

Don't renumber live IDs. Don't reuse a retired or superseded ID. The next number is one past the highest ID ever used (including struck lines and the log).

Keep the spec functional — what and why, not stack or file paths.

If a new requirement breaks a constitution `MUST`, drop that part. Ignore an unfilled constitution template.

Don't regenerate the plan or the whole task list. Don't delete task lines or uncheck finished work.

## What kind of change is this?

- Same idea, better wording → **reword**. Keep the ID.
- Replaces something live ("SSO instead of password") → **supersede**. Strike the old line (`SUPERSEDED by FR-008 (R2)`) and add a new ID. Don't delete the old line.
- Gone, nothing replaces it → **remove**. Strike it and mark `RETIRED (R2)`.
- Brand new, no conflict → **add**. Next free ID. A new AC goes on the story they named, or the only story that fits.

If they named `FR-004` / `US1/AC2`, use that. If the description matches exactly one live item, use that. If it's ambiguous, ask — don't guess.

Already true in the live spec (or the same as the last `R#`) is a duplicate. Skip it. If everything is a duplicate, stop: say so, write nothing, don't bump `R{N}`. If only part is new, do that part and mention what you skipped.

## Do the work

1. Run `{SCRIPT}` once. Read `FEATURE_DIR` and `FEATURE_SPEC`. You need `spec.md`. Also look at `plan.md`, `tasks.md`, `revisions.md`, and `/memory/constitution.md` if they're there. No spec → `__SPECKIT_COMMAND_SPECIFY__`. Awkward quotes: `'I'\''m Groot'`.

2. List live stories, ACs (`US{n}/AC{i}`), FRs, SCs. Remember every ID ever issued. Note the next task id and phase if `tasks.md` exists.

3. Turn the input into changes. Drop duplicates and constitution clashes. Nothing left → stop.

4. Only preview if they asked, or if a remove would wipe the last AC on a P1 story. Otherwise just do it. `N` is 1, or last `R#` plus one.

5. Edit `spec.md`. Holes in AC numbers are fine. Set `**Last Revised**: {today} (R{N})`. Leave `**Created**` alone.

   Supersede looks like: `- **FR-004** ~~password login~~ — SUPERSEDED by **FR-008** (R2)`

6. If `plan.md` exists, strike the old bullet and add a small new one. If the architecture is actually invalid, don't rewrite the plan — say `needs-rebuild` and send them to `__SPECKIT_COMMAND_PLAN__`. No plan → that's the next command.

7. If `tasks.md` exists, append `## Phase {n}: Revision R{N}` with new T-ids.
   - Open task for an old ID: `- [ ] ~~T012~~ SUPERSEDED (R{N} → T020)` and add T020. Or `CANCELLED` if nothing replaces it.
   - Finished work for an old ID: one cleanup task.
   - No tasks file → `__SPECKIT_COMMAND_TASKS__` (or plan first).

8. Append to `revisions.md` (create it if needed: title + "spec.md is the source of truth"):

   ```markdown
   ## R{N} — {YYYY-MM-DD}
   {one sentence}
   - added: {id}
   - superseded: {old} → {new}
   - retired: {id}
   - reworded: {id}
   ```

   Skip empty bullets. Don't edit old entries. Don't append on a no-op.

9. If `checklists/requirements.md` exists, update its checkboxes before after-hooks so a git commit includes them.

10. Run `hooks.after_revise`.

Then tell them once what changed, and what to run next (`__SPECKIT_COMMAND_IMPLEMENT__`, `__SPECKIT_COMMAND_PLAN__`, or `__SPECKIT_COMMAND_TASKS__`). If it was a no-op, say that.

## Done When

- [ ] Same feature folder; spec updated or you said it was already true
- [ ] New `R{N}` only when something actually changed
- [ ] Old lines marked SUPERSEDED/RETIRED; new IDs added; none reused
- [ ] Plan/tasks patched or skipped; no application code
- [ ] Hooks handled; user got a short report
