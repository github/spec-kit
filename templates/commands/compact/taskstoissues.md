---
description: Convert tasks into GitHub issues for the feature.
tools: ['github/github-mcp-server/issue_write']
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
  ps: scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
---

## Input

```text
$ARGUMENTS
```

Consider user input before proceeding (if not empty).

## Workflow

1. Run `{SCRIPT}`, parse FEATURE_DIR. Extract tasks path.
2. Get Git remote: `git config --get remote.origin.url`
3. **ONLY proceed if remote is a GitHub URL.**
4. For each task: create GitHub issue in the matching repository.

**NEVER create issues in repositories that don't match the remote URL.**
