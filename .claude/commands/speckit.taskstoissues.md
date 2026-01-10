---
description: Convert existing tasks into actionable, dependency-ordered GitHub issues for the feature based on available design artifacts.
tools: ['github/github-mcp-server/issue_write']
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
  ps: scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Flags

Parse the following flags from user input:

| Flag | Default | Description |
|------|---------|-------------|
| `--sequential` | false | Force single-agent mode (no subagents, current behavior) |

## Execution Mode Detection

**BEFORE creating issues**, determine execution mode:

1. Check if `--sequential` flag is present → **Sequential Mode**
2. Otherwise → **Parallel Mode** (default)

### Parallel Mode (default)

When `--sequential` is NOT set, create all issues concurrently:

```
[speckit] Parallel mode: N issues
[speckit] Max concurrent subagents: unlimited
```

**Parse tasks.md** and extract all tasks.

**Spawn N subagents** (one per task):
```
Task(
  subagent_type: "general-purpose",
  prompt: "Create GitHub issue for task:

           Task ID: {task_id}
           Description: {task_description}
           Phase: {phase}
           Dependencies: {dependencies}

           Repository: {repo_from_git_remote}

           Create issue with:
           - Title: [{task_id}] {short_description}
           - Body: Full task details, acceptance criteria, dependencies
           - Labels: speckit, phase-{n}

           Handle rate limits:
           - If 403/429 error, wait with exponential backoff (1s, 2s, 4s)
           - Max 3 retry attempts

           Write result to: .claude/workspace/results/issue-{task_id}-result.md
           Include: issue URL, creation status",
  description: "taskstoissues:{task_id}"
)
```

**Progress reporting**:
```
[████████░░] 12/15 issues created
  ✓ T001 (1.2s) - #123
  ✓ T002 (1.1s) - #124
  ✓ T003 (1.3s) - #125
  ...
  ⏳ T014...
  ⏳ T015...
```

**Rate limit handling**:
```
[speckit] ⚠ Rate limit approaching (remaining: 5)
[speckit] ⟳ Backing off for 2s...
```

**Result collection**: After all subagents complete:
1. Read all result files from `.claude/workspace/results/issue-*-result.md`
2. Collect all created issue URLs
3. Report summary: N issues created, any failures

### Sequential Mode (fallback)

When `--sequential` is set:

```
[speckit] Sequential mode: single-agent execution
```

Proceed with current behavior (create issues one at a time in main agent).

---

## Outline

1. Run `{SCRIPT}` from repo root and parse FEATURE_DIR and AVAILABLE_DOCS list. All paths must be absolute. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").
1. From the executed script, extract the path to **tasks**.
1. Get the Git remote by running:

```bash
git config --get remote.origin.url
```

> [!CAUTION]
> ONLY PROCEED TO NEXT STEPS IF THE REMOTE IS A GITHUB URL

1. For each task in the list, use the GitHub MCP server to create a new issue in the repository that is representative of the Git remote.

> [!CAUTION]
> UNDER NO CIRCUMSTANCES EVER CREATE ISSUES IN REPOSITORIES THAT DO NOT MATCH THE REMOTE URL
