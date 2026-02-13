# Spec Kit Development (Engagement extensions)

This folder contains planning documents for extending the vendored `tasks/spec-kit` to support the Engagement ticket workflow (ticket intake → planning → implementation → reviews) alongside Spec Kit’s existing feature/spec workflow.

## Goals
- Add a **ticket-mode** workflow (create ticket folder + ticket.md, planning docs, review logs).
- Add standardized **append-only review artifacts** (human + agent) and closure tracking.
- Add optional **metadata.yaml** support for ticket tracking.
- Add additional **analysis/validation** that checks cross-artifact consistency in ticket-mode.

## Planning steps
1. `01-current-state-analysis.md`
2. `02-target-user-workflows.md`
3. `03-design-ticket-mode-artifacts.md`
4. `04-commands-and-scripts.md`
5. `05-analyze-ticket-mode.md`
6. `06-rollout-and-testing.md`

## Non-goals (for this iteration)
- Jira API integration (future).
- Changes to `tasks/config/*` (those are treated as external process docs).
