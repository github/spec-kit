---
description: "Validate current ticket branch and expose ticket context"
---

# Validate Ticket Branch

Validate that the current Git branch follows the team ticket-branch convention. This
command handles **branch validation only** — it does not create branches. Developers
must create or switch branches explicitly before running `__SPECKIT_COMMAND_SPECIFY__`.

## Branch Policy

Default accepted branch forms:

- `GDEV-1234`
- `MSPS-1234`
- `feature/GDEV-1234`
- `fix/MSPS-1234`
- `hotfix/GDEV-1234`
- `chore/MSPS-1234`

The effective branch name must be a ticket key matching `[A-Z]+-[0-9]+`. Allowed
prefixes are `feature`, `fix`, `hotfix`, and `chore`.

## Prerequisites

- Verify Git is available by running `git rev-parse --is-inside-work-tree 2>/dev/null`
- If Git is not available, fail with a clear error. Ticket branch workflow requires an
  existing Git branch.

## Execution

Run the appropriate script based on your platform:

- **Bash**: `.specify/extensions/git/scripts/bash/validate-ticket-branch.sh --json`
- **PowerShell**: `.specify/extensions/git/scripts/powershell/validate-ticket-branch.ps1 -Json`

The script exits non-zero when the current branch is invalid. Stop the workflow and
show the error to the user instead of continuing.

## Output

The script outputs JSON with:

- `BRANCH_NAME`: The current raw Git branch name
- `TICKET_KEY`: The extracted ticket key, e.g. `GDEV-1234`
- `BRANCH_PREFIX`: The optional branch prefix, e.g. `feature`
- `BRANCH_STRATEGY`: `existing-ticket`

`__SPECKIT_COMMAND_SPECIFY__` uses `TICKET_KEY` plus its generated feature slug to
create the spec directory, e.g. `specs/GDEV-1234-add-login`.
