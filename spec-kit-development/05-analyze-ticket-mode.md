# 05 — Ticket-mode analysis (proposed `/speckit.ticket-analyze`)

## Goal
Provide a read-only analysis report that ensures ticket-mode artifacts are consistent and ready for implementation/review.

---

## Inputs
Required:
- `tasks/<TICKET-ID>/ticket.md`
- `tasks/<TICKET-ID>/planning/initial-plan.md`
- `tasks/<TICKET-ID>/planning/what-has-been-done.md`

Optional:
- `references/*`
- `reviews/*`
- `metadata.yaml`

---

## Checks (deep but deterministic)

### A) Ticket ↔ plan alignment
- Each acceptance criteria item from `ticket.md` should map to at least one:
  - plan “Expected outcomes” / “Success criteria” item
  - or a planned task/work breakdown bullet

Flag:
- ACs with no mapping
- plan items not traceable to ticket objective (scope creep)

### B) Plan ↔ progress tracker alignment
- Ensure `what-has-been-done.md` includes:
  - phases
  - testing sections
  - results log sections

Flag:
- missing sections
- status indicates “Done” but no results/evidence links

### C) Review lifecycle completeness (if `reviews/` exists)
- If review files exist:
  - `pr-review.md` should either have a closure log OR clearly open comments
  - `pr-response.md` should have responses matching comment ids
  - `copilot-review.md` and `copilot-response.md` same pattern

Heuristics:
- detect “Comment N” headings
- ensure response references same N

Flag:
- review points without responses
- responses without matching review point

### D) Metadata sanity (if present)
- `ticket_id` matches folder name
- status is valid enum
- branch / PR links look plausible

---

## Output (report format)

- Summary (counts of issues by severity)
- Tables:
  - AC coverage table
  - Review coverage table
  - Evidence links table
- Next actions:
  - specific edits recommended (but do not apply them)

---

## Severity model
- CRITICAL: missing required files, missing AC coverage, prod run required but no RFC info
- MEDIUM: missing evidence links, plan lacks rollback/testing detail
- LOW: formatting inconsistencies, duplication, minor clarity issues
