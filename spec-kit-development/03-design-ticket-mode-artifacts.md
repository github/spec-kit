# 03 — Design: Ticket-mode artifacts

## Goal
Define the canonical formats for ticket-mode artifacts and how the write commands should behave.

---

## Artifact set

### A) `ticket.md`
- Structured sections: Summary, Background, Objective, Scope, AC, Repo/Area, Testing, Risks/Rollback, Dependencies, Links, Notes
- Include a clear `RAW`/`INFO` section for pasting full Jira text

Write rule:
- Safe to create if missing.
- If exists: do not overwrite; only optionally append “RAW” section if absent.

### B) `metadata.yaml` (optional)
- Stored at `<TICKET-ID>/metadata.yaml`
- Goals:
  - track status, links, sub-tickets, PRs
  - give automation a stable structure

Write rule:
- Create if missing.
- Never overwrite if present.

### C) `planning/initial-plan.md`
- Derived from ticket + references.
- Needs to remain editable by humans.

Write rule:
- Create if missing.
- If exists: append a new “Revision” section (dated), or provide a `--overwrite` flag (default off).

### D) `planning/what-has-been-done.md`
- Operational checklist + results log; append-only for results.

Write rule:
- Create if missing.
- If exists: do not delete user content; add missing sections only.

### E) `planning/steps/*.md`
- Use a dedicated step template (13-section checklist).

Write rule:
- Create new file per invocation; never overwrite.

### F) `reviews/*.md`
- Four append-only logs:
  - `pr-review.md`, `pr-response.md`, `copilot-review.md`, `copilot-response.md`

Write rule:
- Create missing files from templates.
- Never overwrite.

---

## Templating strategy

Spec Kit currently uses templates copied on generation. For ticket-mode:

- Keep templates in `spec-kit/templates/ticket-mode/` (new folder) to avoid mixing with feature-mode.
- Each command should copy the corresponding template(s) only if missing.

---

## Preservation strategy (important)

Ticket-mode is likely to be rerun as the ticket evolves.

Recommended rules:
- “Create if missing” for most artifacts
- For `initial-plan.md`:
  - default: do not overwrite
  - offer `--append-revision` behavior instead
- For “what has been done”:
  - only ensure required headings exist
  - do not reorder or truncate

---

## Mapping from Engagement templates

These already exist under `tasks/config/templates/` (outside spec-kit). For spec-kit changes:
- replicate the *concepts* (not necessarily hardcode Engagement paths)
- keep placeholders generic (`<TICKET-ID>`) and keep paths relative

---

## Success definition

- Running ticket-mode commands yields deterministic structure
- Reruns are safe and non-destructive
- Review+narrative artifacts remain append-only where intended
