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

Apply a **requirement delta** to the **current** feature. Edit `spec.md` in place. Cascade `plan.md` / `tasks.md` only if they exist.

Not `__SPECKIT_COMMAND_SPECIFY__` (new feature folder). Not `__SPECKIT_COMMAND_CONVERGE__` (code lagged an unchanged spec).

## User Input

```text
$ARGUMENTS
```

You **MUST** use the input if not empty. Empty → ask (interactive) or stop (automated). Do not invent a delta. New product (different user + outcome, no shared stories) → stop; recommend `__SPECKIT_COMMAND_SPECIFY__`.

## Hook protocol

Use for `hooks.before_revise` (now) and `hooks.after_revise` (after writes, before the Completion Report).

If `.specify/extensions.yml` is missing or unreadable, skip. Read that event key. Skip `enabled: false`. Skip hooks with a non-empty `condition` (leave those to HookExecutor). No `enabled` → enabled.

- **Mandatory** (`optional: false`): emit and **run** the hook (skills-mode invocation may differ from `{command}`):

  ```text
  ## Extension Hooks
  **Automatic Pre-Hook**: {extension}
  Executing: `/{command}`
  EXECUTE_COMMAND: {command}
  ```

  Wait for it. Emitting the block is not enough.

- **Optional** (`optional: true`):

  ```text
  ## Extension Hooks
  **Optional Pre-Hook**: {extension}
  Command: `/{command}`
  Description: {description}
  Prompt: {prompt}
  To execute: `/{command}`
  ```

After writes, the same protocol uses **Automatic Hook** / **Optional Hook** labels (not Pre-Hook).

## Rules

| | |
|---|---|
| Folder | Same `FEATURE_DIR`. Do **not** create a new `specs/` folder, branch, or spec file. |
| **NO APPLICATION CODE** | No product source. Implement/cleanup is `__SPECKIT_COMMAND_IMPLEMENT__`. |
| **STABLE IDS** | Never renumber live IDs. Never reuse a retired/superseded ID. Next ID = max ever issued (include log + marked lines). |
| Contract | `spec.md` is the only current contract. Functional only (no stack/APIs/paths). |
| Log | `revisions.md` is a **dated log**, not a spec. IDs + one sentence. No AC prose. |
| Live vs dead | Unmarked lines are live. `SUPERSEDED` / `RETIRED` stay visible but are not current. Never two **live** items that contradict. |
| Constitution | Reject `add`/`supersede` that violate a `MUST`. Skip if constitution is an unfilled template. |
| Plan/tasks | Patch only. Do not regenerate. Do not delete or uncheck completed tasks. |

**Ops:** `add` | `reword` | `supersede` | `remove`

- Same wording, tighter → `reword` (keep ID).
- New behavior contradicts a live item, or swap ("SSO instead of password") → `supersede`: mark old `SUPERSEDED by {new-id} (R{N})`, **add** new ID.
- Drop, no replacement → `remove`: mark `RETIRED (R{N})`, do not delete the line.
- Named ID wins. Else unique live match. Ambiguous → ask or stop. New AC → named story, or the one story that fits.

**DUPLICATES ARE A NO-OP** (compare to **live** `spec.md`, not the log):

- add already live / remove already dead / reword unchanged / same as latest `R#` → drop.
- All duplicates → STOP. Report already-true items. Write nothing. Do **not** bump `R{N}`.
- Mixed → apply only new parts; mention skips.

## Steps

1. **Resolve.** Run `{SCRIPT}` once. Parse `FEATURE_DIR`, `FEATURE_SPEC`. Paths: `spec.md`, `plan.md`, `tasks.md`, `revisions.md`, `/memory/constitution.md`. Missing spec → `__SPECKIT_COMMAND_SPECIFY__`. Quotes: `'I'\''m Groot'`.

2. **Load.** Inventory live stories/`US{n}/AC{i}`, `FR-###`, `SC-###`, edge/out-of-scope. Count issued IDs including `SUPERSEDED`/`RETIRED` and the log. Load plan headings/IDs if present; task IDs/checkboxes/phases if present (next T-id and phase). Load constitution MUST/SHOULD if real.

3. **Classify.** Build `Change{op, kind, target, replaces, text}`. Drop duplicates. Constitution-invalid items out; rest stay. Nothing left → stop, no writes.

4. **Preview** only if user asked or a `remove` would empty a P1 story's last AC. Else continue. `N` = 1 or last `R#`+1.

5. **Write `spec.md`.**
   - `add` AC: next index on that story (holes OK). `add` FR/SC: next unused ID.
   - `reword`: replace live text; same ID.
   - `supersede`: keep old line, strike it, add new:

     `- **FR-004** ~~password login~~ — SUPERSEDED by **FR-008** (R2)`
   - `remove`: strike + `RETIRED (R2)`.
   - Set `**Last Revised**: {date} (R{N})`. Do not change `**Created**`. No new sections, no checklists in the spec.

6. **Cascade (files that exist only).**
   - `plan.md`: strike old (`SUPERSEDED by {new}` / `RETIRED (R{N})`); add smallest new bullet. Architecture break → do not rewrite; `needs-rebuild` → `__SPECKIT_COMMAND_PLAN__`. Missing plan → next is plan.
   - `tasks.md`: append `## Phase {n}: Revision R{N}`. New T-ids from max+1.
     - supersede open task: `- [ ] ~~T012~~ SUPERSEDED (R{N} → T020)` and add T020.
     - remove open task: `- [ ] ~~T012~~ CANCELLED (R{N}: retired {id})`.
     - completed work on old ID → one cleanup task.
     Missing tasks → `__SPECKIT_COMMAND_TASKS__` (or plan if no plan).

7. **Log.** Create `revisions.md` if needed (`# Spec Revisions` + one line: spec is truth). Append only:

   ```markdown
   ## R{N} — {YYYY-MM-DD}
   {one sentence}
   - added: {id}
   - superseded: {old} → {new}
   - retired: {id}
   - reworded: {id}
   ```

   Omit empty bullets. Never edit prior `R#`. No-op → do not append.

8. If `checklists/requirements.md` exists, refresh pass/fail **before** after-hooks (so git commit includes it).

9. Run **after_revise** via Hook protocol.

## Completion Report

Once, after hooks:

```text
## Revision R{N} Applied
Feature: {FEATURE_DIR}
| Op | ID | Result |
Next: {command}
```

Next is `__SPECKIT_COMMAND_IMPLEMENT__`, `__SPECKIT_COMMAND_PLAN__`, or `__SPECKIT_COMMAND_TASKS__`. On no-op, say so and skip hooks that would commit empty work if none ran.

## Done When

- [ ] Same feature dir; `spec.md` updated or explicit no-op
- [ ] New `R{N}` only if something changed; IDs not reused
- [ ] Dead lines marked SUPERSEDED/RETIRED; replacements added
- [ ] Plan/tasks patched or skipped; no app code
- [ ] Hooks run or skipped; user reported
