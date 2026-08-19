---
description: Execute the implementation plan by processing all tasks in tasks.md.
---

## User Input

```text
$ARGUMENTS
```

## Outline

1. Read `.specify/feature.json` to get the feature directory path.

2. **Load context**: `.specify/memory/constitution.md` and `<feature_directory>/spec.md` and `<feature_directory>/plan.md` and `<feature_directory>/tasks.md`.

3. **Execute tasks** in order:
   - Skip any task line that contains `CANCELLED`, `SUPERSEDED`, or a struck-through task ID (`~~T012~~`), even when the checkbox is still `- [ ]`. Do not implement them, do not mark them `[x]`, and do not count them as remaining work.
   - Prefer the latest `Revision R#` phase plus any cleanup tasks it added
   - Complete each remaining live task before moving to the next
   - Mark completed tasks by changing `- [ ]` to `- [x]` in `<feature_directory>/tasks.md`
   - Halt on failure and report the issue

4. **Validate**: Verify all **live** (non-cancelled, non-superseded) tasks are completed and the implementation matches **live** items in the spec (struck `SUPERSEDED` / `RETIRED` lines are not required).
