---
description: Initialize a ticket workspace under `tasks/<TICKET-ID>/` with standard planning and tracking artifacts.
handoffs:
  - label: Create Ticket Plan
    agent: speckit.ticket-plan
    prompt: Create planning documents for this ticket
scripts:
  sh: scripts/bash/create-new-ticket.sh --json "{ARGS}"
  ps: scripts/powershell/create-new-ticket.ps1 -Json "{ARGS}"
---

## User Input

```text
$ARGUMENTS
```

## Goal

Create a new ticket folder under `tasks/` and populate:
- `ticket.md`
- `planning/initial-plan.md`
- `planning/what-has-been-done.md`
- `references/` and `reviews/` directories
- optional `metadata.yaml` (omit with `--no-metadata` / `-NoMetadata`)

## Operating constraints

- SAFE / NON-DESTRUCTIVE: Do not overwrite existing files.
- Emit JSON with absolute paths when invoked with `--json`/`-Json`.

## Outline

1. Run `{SCRIPT}` from repo root with the provided ticket id (e.g., `TOUR-7328`).
2. Parse JSON result for:
   - `TICKET_DIR`
   - `TICKET_FILE`
   - `PLANNING_DIR`, `INITIAL_PLAN`, `WHAT_DONE`
3. Report created paths and remind the user to paste raw ticket content into `ticket.md`.
