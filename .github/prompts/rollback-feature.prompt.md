---
description: "Safely undo the most recent feature or task using Git history."
---

User input: $ARGUMENTS

1. Run .specify/scripts/bash/rollback-feature.sh --json "$ARGUMENTS" to analyze the Git history and identify the last action.
2. If the request is safe (latest action), present options to revert or reset the commit.
3. If the request is unsafe (older action), refuse to proceed and provide a detailed impact analysis.
4. Execute the user's chosen Git command.
