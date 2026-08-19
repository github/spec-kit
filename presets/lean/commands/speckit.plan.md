---
description: Create a plan and store it in plan.md.
---

## User Input

```text
$ARGUMENTS
```

## Outline

1. Read `.specify/feature.json` to get the feature directory path.

2. **Load context**: `.specify/memory/constitution.md` and `<feature_directory>/spec.md`.

3. Create an implementation plan and store it in `<feature_directory>/plan.md`.
   - Only plan **live** (unmarked) FRs, ACs, and SCs. Lines marked `SUPERSEDED` or `RETIRED` are historical — do not restore them.
   - If `plan.md` already exists and `revisions.md` is present, do **not** overwrite it unless the latest `revisions.md` entry has `plan_status: needs-rebuild` (or the user asked). Even then, do not resurrect retired IDs.
   - Technical context: tech stack, dependencies, project structure
   - Design decisions, architecture, file structure
