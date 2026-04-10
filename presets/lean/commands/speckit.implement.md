---
description: Execute the implementation plan by processing all tasks in tasks.md.
---

## User Input

```text
$ARGUMENTS
```

## Outline

1. Read `.specify/feature.json` to get the feature directory path.

2. **Load context**: `.specify/memory/constitution.md` and `spec.md` and `plan.md` and `tasks.md`.

3. **Execute tasks** phase by phase:
   - Complete each phase before moving to the next
   - Respect dependencies: sequential tasks in order, `[P]` tasks can run together
   - Mark completed tasks as `[X]` in tasks.md
   - Halt on failure for sequential tasks; continue and report for parallel tasks

4. **Validate**: Verify all tasks are completed and the implementation matches the spec.
