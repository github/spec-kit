---
description: "Intelligently resume an interrupted /implement run."
---

User input: $ARGUMENTS

1. Run .specify/scripts/bash/sync-tasks.sh --json to analyze tasks.md against the filesystem.
2. Identify the last completed task and the point of failure.
3. Detect any partially created files.
4. Present the user with safe options for continuation (e.g., re-run failed task, skip, etc.).
