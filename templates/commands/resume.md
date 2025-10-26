---
description: Reload feature context and recommend the next implementation actions based on remaining tasks.
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
  ps: scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
---

## Strict Contract

- **Required Inputs**
  - Feature metadata from `{SCRIPT}` including `FEATURE_DIR`, `BRANCH_NAME`, and task inventory.
  - Optional `$ARGUMENTS` highlighting developer preferences (e.g., focus area).
- **Allowed Tools**
  - Execute `{SCRIPT}` exactly once from repo root.
  - Read `spec.md`, `plan.md`, `tasks.md`, `research.md`, `data-model.md`, `contracts/`, and `quickstart.md`.
  - Read-only command; do **not** modify repository files.
- **Outputs**
  - Emit a JSON code block:

    ```json
    {
      "status": "success" | "error",
      "branch": "<branch-name>",
      "context_files": ["<path>", "..."] ,
      "next_tasks": ["T010", "T011"],
      "blocked_by": {
        "T020": ["T015"]
      },
      "suggested_checks": ["<command>", "..."]
    }
    ```

- **Idempotency**
  - Re-running produces the same recommendations unless task completion state changes.
- **Stop Conditions**
  - Abort with `status = error` if `tasks.md` is missing or contains no unchecked items.
  - Finish after emitting JSON summary; do not request follow-up input.

## Execution Flow

1. **Initialize**
   - Run `{SCRIPT}` once; gather absolute paths and verify that `tasks.md` exists.
   - Shell guidance:
     - **Bash**: Use double quotes for arguments (escape embedded quotes with `\"`).
     - **PowerShell**: Use double quotes and escape embedded quotes by doubling them.

2. **Load Artifacts**
   - Parse `spec.md` for priorities and success criteria.
   - Review `plan.md` for architecture decisions and exit criteria.
   - Inspect `tasks.md` to determine completed vs. remaining tasks, dependency metadata, and phase ordering.
   - Optionally consult supporting docs (`research.md`, `data-model.md`, `contracts/`, `quickstart.md`) to contextualize tasks.

3. **Determine Current State**
   - Identify the highest priority phase with incomplete tasks.
   - Detect blocking dependencies by parsing `DependsOn` annotations.
   - Map tasks to user stories and highlight the next unblocked task(s) per story.

4. **Recommend Next Actions**
   - Choose up to five actionable tasks to tackle next, prioritizing by story priority (P1 > P2 > ...), dependency readiness, and user input.
   - Suggest validation steps (tests, scripts) required after completing the recommended tasks.
   - If no tasks remain, advise running `/speckit.analyze` or beginning QA handoff.

5. **Respond**
   - Populate the JSON schema with context files consulted, recommended task IDs, dependency map for blocked tasks, and suggested follow-up checks or commands.
