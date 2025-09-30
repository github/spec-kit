---
description: "Intelligently resume an interrupted /implement run."
scripts:
  sh: scripts/bash/sync-tasks.sh --json
  ps: scripts/powershell/sync-tasks.ps1 -Json
---

User input: $ARGUMENTS

1. Run {SCRIPT} to analyze tasks.md against the filesystem.
2. Identify the last completed task and the point of failure.
3. Detect any partially created files.
4. Present the user with safe options for continuation (e.g., re-run failed task, skip, etc.).