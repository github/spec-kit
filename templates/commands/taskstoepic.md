---
description: Convert SpecKit tasks.md into beads (and optional gastown convoy) for the current feature.
scripts:
  sh: scripts/bash/taskstoepic-helper.sh
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

1. Run `{SCRIPT}` from repo root, passing `$ARGUMENTS` through unchanged.
2. If the helper script reports missing prerequisites, stop and show the error.
3. On success, report created bead IDs, skipped duplicates, and convoy details (if any).

Context for run: $ARGUMENTS
