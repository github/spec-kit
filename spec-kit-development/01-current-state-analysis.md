# 01 — Current State Analysis (spec-kit in this workspace)

## Scope
Analyze the vendored Spec Kit located at:
- `C:\Environment\Engagement\tasks\spec-kit`

Goal: identify where to add a parallel “ticket-mode” workflow without breaking existing `/speckit.*` commands.

---

## What Spec Kit currently provides (observed from workspace)

### Core artifacts (feature-mode)
Spec Kit is centered around a **feature directory** that contains:
- `spec.md`
- `plan.md`
- `tasks.md`

And optional supporting artifacts:
- `research.md`
- `data-model.md`
- `quickstart.md`
- `contracts/`

The scripts and command templates expect this feature directory and are designed to:
1) create the feature directory (and branch) (`/speckit.specify`)
2) populate a technical plan and design artifacts (`/speckit.plan`)
3) generate actionable tasks (`/speckit.tasks`)
4) analyze consistency across artifacts (`/speckit.analyze`) — read-only

### Command templates (where behavior lives)
Spec Kit command behavior is largely defined in:
- `spec-kit/templates/commands/*.md`

Notable command templates in this workspace:
- `specify.md` — creates branch + spec, writes spec content, creates a checklist
- `clarify.md` — asks targeted questions and writes back into spec
- `plan.md` — uses a plan template and generates phase artifacts
- `tasks.md` — produces a task list with strict formatting rules
- `analyze.md` — read-only cross-artifact analysis
- `checklist.md` — generates checklists in `checklists/`
- `implement.md` — drives phased execution based on tasks

These templates rely on scripts to discover paths and copy templates.

### Scripts (how paths and files are created)
Spec Kit uses:
- `spec-kit/scripts/bash/*.sh`
- `spec-kit/scripts/powershell/*.ps1`

Common pattern:
- a script runs from repo root
- emits JSON describing detected paths (FEATURE_DIR, SPEC path, etc.)
- command template consumes those paths and then writes/updates markdown artifacts

Important: there is already a robust **path discovery** layer:
- `scripts/*/check-prerequisites.*` parses branch and provides derived paths

### Templates (content scaffolding)
Spec Kit templates are in:
- `spec-kit/templates/*.md`

These provide the standard structure for:
- spec
- plan
- tasks
- checklists

---

## Where Engagement ticket-workflow differs

Engagement workflow is **ticket-centric, not feature-centric**:

- Root: `tasks/<TICKET-ID>/`
- Inputs: `ticket.md` + `references/`
- Planning: `planning/initial-plan.md` + `planning/what-has-been-done.md` (+ optional step files)
- In-flight feedback: `reviews/` append-only logs
- Optional coordination: `metadata.yaml`

Key deltas vs Spec Kit feature-mode:
1) Directory naming is ticket-id driven instead of numeric feature branch.
2) Artifacts are stage-based subfolders (`planning/`, `reviews/`) vs all-in-one feature folder.
3) Reviews are explicit append-only artifacts.

---

## Extension points (recommended)

### A) Add a parallel “ticket-mode” path resolver
Spec Kit relies on **scripts producing JSON**. We can add a new script pair:
- `scripts/bash/create-new-ticket.sh --json ...`
- `scripts/powershell/create-new-ticket.ps1 -Json ...`

Outputs:
- TICKET_ID
- TICKET_DIR
- paths to ticket.md / planning docs / review docs

### B) Add a new command set (ticket-mode) without touching existing ones
Add new command templates:
- `templates/commands/ticket.md`
- `templates/commands/ticket-plan.md`
- `templates/commands/ticket-reviews.md`
- `templates/commands/ticket-analyze.md`

### C) Reuse Spec Kit conventions
- Keep the JSON “paths contract” style.
- Keep read-only vs write commands explicit.
- Keep templates as the source-of-truth scaffolding.

---

## Risks / constraints

- Spec Kit upstream conventions expect `specs/<feature>/...`. Ticket-mode must not disrupt that.
- Need to support Windows PowerShell paths cleanly.
- Need to keep commands composable (ticket → plan → reviews) like specify → plan → tasks.

---

## Deliverables for this initiative

- New commands (ticket-mode)
- New templates (ticket + planning + reviews + metadata)
- New scripts (bash + powershell)
- Lightweight analysis command for ticket artifacts
- Docs updates: add “Ticket-mode” to quickstart / docs index
