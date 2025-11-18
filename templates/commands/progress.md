---
description: Generate and update progress tracking files (PROGRESS.md and STATUS.md) from tasks.md
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-tasks
  ps: scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

1. Run `{SCRIPT}` from repo root and parse FEATURE_DIR and AVAILABLE_DOCS list. All paths must be absolute. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. **Load configuration** (if `.specify/config.json` exists):
   - Read `.specify/config.json` to check progress tracking settings
   - If file doesn't exist, use default settings (autoTracking: false)
   - Extract `progress.autoTracking`, `progress.updateOnTaskComplete`, `progress.updateOnPhaseComplete` values

3. **Load tasks.md**:
   - **REQUIRED**: Read FEATURE_DIR/tasks.md for the complete task list
   - Parse all tasks with format: `- [ ]` or `- [X]` or `- [x]` followed by task ID, labels, and description
   - Extract phase information from section headers (e.g., "## Phase 1: Setup", "## Phase 2: Foundational", "## Phase 3: User Story 1")
   - Count completed vs total tasks per phase

4. **Calculate progress metrics**:
   - **Total tasks**: Count all lines matching task format
   - **Completed tasks**: Count lines with `- [X]` or `- [x]`
   - **Remaining tasks**: Total - Completed
   - **Overall percentage**: (Completed / Total) * 100
   - **Per-phase metrics**: Calculate completed/total/percentage for each phase
   - **Current phase**: Identify the phase with the most recent activity (last completed task)

5. **Generate PROGRESS.md**:
   - Use `.specify/templates/progress-template.md` as structure
   - Replace placeholders:
     - `[FEATURE_NAME]`: Extract from tasks.md header or FEATURE_DIR name
     - `[TIMESTAMP]`: Current date/time in ISO format
     - `[TOTAL]`: Total task count
     - `[COMPLETED]`: Completed task count
     - `[REMAINING]`: Remaining task count
     - `[PERCENTAGE]`: Overall progress percentage (rounded to 1 decimal)
     - `[PHASE_STATUS_LIST]`: Generate list of phases with status indicators:
       - ✅ Complete: Phase with 100% completion
       - 🟡 In Progress: Phase with some tasks completed but not all
       - ⏳ Pending: Phase with 0% completion
       - Format: `- [STATUS] Phase N: [Name] ([completed]/[total] - [percentage]%)`
     - `[RECENT_ACTIVITY_LIST]`: List last 5-10 completed tasks (if any) with timestamps
   - Write to FEATURE_DIR/PROGRESS.md
   - If file exists, update it (preserve any manual notes if present)

6. **Generate STATUS.md** (quick summary):
   - Create a concise status file with:
     - Current phase name and progress
     - Overall progress percentage
     - Next steps (next incomplete task or phase)
     - Last update timestamp
   - Write to FEATURE_DIR/STATUS.md

7. **Display summary**:
   - Show progress summary in console:
     - Overall: X/Y tasks completed (Z%)
     - Current phase: [Phase Name] - X/Y tasks (Z%)
     - Next: [Next task or phase]
   - Display file paths to PROGRESS.md and STATUS.md

## Progress Calculation Rules

- **Task format detection**: Match lines starting with `- [ ]`, `- [X]`, or `- [x]` followed by task ID (T###)
- **Phase detection**: Match markdown headers `## Phase N:` or `## Phase N: [Name]`
- **Task assignment**: Assign tasks to the phase they appear under (until next phase header)
- **Completion status**: 
  - `- [ ]` = incomplete
  - `- [X]` or `- [x]` = complete
- **Percentage calculation**: Round to 1 decimal place (e.g., 27.3%)

## File Locations

- **PROGRESS.md**: FEATURE_DIR/PROGRESS.md
- **STATUS.md**: FEATURE_DIR/STATUS.md
- **Config**: REPO_ROOT/.specify/config.json (optional)

## Error Handling

- If tasks.md is missing: Report error and suggest running `/speckit.tasks` first
- If no tasks found: Report "No tasks found in tasks.md"
- If config.json is malformed: Use default settings and continue
- If template is missing: Use inline template structure

## Example Output

**PROGRESS.md**:
```markdown
# Progress Tracking: User Authentication

**Last Updated**: 2025-01-27T14:30:00Z
**Status**: 🟢 Active Development

## Overall Progress
- **Total Tasks**: 95
- **Completed**: 26
- **Remaining**: 69
- **Progress**: 27.4%

## Phase Status
- ✅ Phase 1: Setup (5/5 - 100.0%)
- ✅ Phase 2: Foundational (8/8 - 100.0%)
- 🟡 Phase 3: User Story 1 (13/16 - 81.3%)
- ⏳ Phase 4: User Story 2 (0/19 - 0.0%)
```

**STATUS.md**:
```markdown
# Implementation Status

**Current Phase**: Phase 3: User Story 1
**Overall Progress**: 27.4% (26/95 tasks)
**Phase Progress**: 81.3% (13/16 tasks)

**Next Steps**: Complete remaining 3 tasks in Phase 3

**Last Updated**: 2025-01-27T14:30:00Z
```

Note: This command can be run at any time to refresh progress tracking files, regardless of whether implementation is active.

