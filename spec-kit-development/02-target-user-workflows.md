# 02 — Target user workflows (Ticket-mode)

## Goal
Define how a developer uses Spec Kit to execute an Engagement-style ticket workflow.

---

## Workflow A: Standard ticket (manual Jira paste)

### Inputs
- Ticket ID (e.g., `TOUR-7328`)
- Ticket text pasted manually
- Optional reference files (YAMLs, screenshots, links)

### Command sequence (proposed)
1) `/speckit.ticket TOUR-7328`
   - Creates `tasks/TOUR-7328/`
   - Creates `ticket.md` from template
   - Creates `references/`
   - (optional) creates `metadata.yaml`

2) User pastes Jira content into `ticket.md` and adds files to `references/`

3) `/speckit.ticket-plan`
   - Reads `ticket.md` + `references/*`
   - Creates/updates:
     - `planning/initial-plan.md`
     - `planning/what-has-been-done.md`

4) (Optional) `/speckit.ticket-step "Opt-in pool refactor"`
   - Creates `planning/steps/<N>-<Title>.md` using the 13-section step template

5) Implementation proceeds in repo; on PR start:
   - `/speckit.ticket-reviews`
   - Creates `reviews/` + four append-only logs

6) (Optional) `/speckit.ticket-analyze`
   - Read-only checks:
     - plan vs ticket alignment
     - review closure completeness
     - evidence present for ACs

---

## Workflow B: Ticket with multiple repos

Same as A, but ticket.md contains:
- multiple repos under “Affected repository/area”

Planning output should include:
- per-repo file touch list
- explicit split into sub-work items

---

## Workflow C: Brownfield/maintenance (minimal planning)

1) `/speckit.ticket <ID>`
2) Fill ticket.md
3) `/speckit.ticket-plan --minimal`
   - Creates a smaller initial-plan (scope + files + tests + rollback)
4) `/speckit.ticket-reviews`

---

## Output structure (must match Engagement conventions)

```
<TICKET-ID>/
  ticket.md
  metadata.yaml (optional)
  references/
  planning/
    initial-plan.md
    what-has-been-done.md
    steps/ (optional)
  reviews/
    pr-review.md
    pr-response.md
    copilot-review.md
    copilot-response.md
```

---

## Non-functional requirements

- Must work on Windows (PowerShell + paths)
- Commands must be safe if rerun:
  - do not delete user content
  - only create missing files
  - if overwriting templates, prefer “preserve user edits” strategy (see Step 03)
