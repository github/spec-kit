# 04 — Commands and scripts (implementation plan)

## Goal
Define exactly what needs to be added/changed in Spec Kit to support ticket-mode.

---

## New commands (templates)

Add new command templates under `spec-kit/templates/commands/`:

1) `ticket.md`
- Description: initialize a ticket directory under `tasks/`.
- Script: new `create-new-ticket` script (bash + PowerShell)
- Action: copy templates for `ticket.md`, create references folder, optionally metadata.

2) `ticket-plan.md`
- Description: create planning docs from the ticket.
- Script: re-use `check-prerequisites` with a new “ticket paths” mode OR add a new `check-ticket` script.
- Action: generate `planning/initial-plan.md` and `planning/what-has-been-done.md` if missing.

3) `ticket-reviews.md`
- Description: initialize review logs.
- Script: ticket path resolver.
- Action: create `reviews/` folder + 4 files if missing.

4) `ticket-step.md` (optional)
- Description: create a numbered step doc under `planning/steps/`.

5) `ticket-analyze.md` (read-only)
- Description: validate cross-artifact consistency in ticket-mode.

---

## New scripts

### A) `create-new-ticket` (bash + PowerShell)
Location:
- `spec-kit/scripts/bash/create-new-ticket.sh`
- `spec-kit/scripts/powershell/create-new-ticket.ps1`

Inputs:
- ticket id (required)
- optional title/slug

Behavior:
- Create `tasks/<TICKET-ID>/` (relative to repo root)
- Create `references/` and `planning/` (and optionally `planning/steps/`)
- Copy templates into:
  - `ticket.md`
  - optional `metadata.yaml`

JSON output contract (example):
```json
{
  "TICKET_ID": "TOUR-7328",
  "TICKET_DIR": "C:/.../tasks/TOUR-7328",
  "TICKET_FILE": ".../ticket.md",
  "REFERENCES_DIR": ".../references",
  "PLANNING_DIR": ".../planning",
  "INITIAL_PLAN": ".../planning/initial-plan.md",
  "WHAT_DONE": ".../planning/what-has-been-done.md",
  "REVIEWS_DIR": ".../reviews"
}
```

### B) `check-ticket` (optional)
If reusing existing `check-prerequisites` is hard (because it assumes feature branches), add:
- `scripts/bash/check-ticket.sh --json`
- `scripts/powershell/check-ticket.ps1 -Json`

This script should:
- validate ticket folder existence
- derive all expected file paths
- return JSON

---

## Templates to add inside spec-kit

Create `spec-kit/templates/ticket-mode/` and add:
- `ticket.template.md`
- `planning-initial-plan.template.md`
- `planning-what-has-been-done.template.md`
- `planning-step.template.md`
- `reviews-pr-review.template.md`
- `reviews-pr-response.template.md`
- `reviews-copilot-review.template.md`
- `reviews-copilot-response.template.md`
- `metadata.template.yaml`

---

## Agent integrations / handoffs

Ticket commands can optionally chain via `handoffs:` like existing commands:
- `ticket` → handoff to `ticket-plan`
- `ticket-plan` → handoff to `ticket-reviews` (optional)

---

## Compatibility considerations

- Avoid assumptions about git branch naming conventions.
- Ticket-mode should work even when not in a git repo (like Spec Kit already does for feature-mode).
- Windows paths must be absolute in JSON results.
