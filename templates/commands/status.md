---
description: Display project status, feature progress, and recommended next actions across the spec-driven development workflow.
scripts:
  sh: scripts/bash/get-project-status.sh --json
  ps: scripts/powershell/Get-ProjectStatus.ps1 -Json
---

## User Input

```text
$ARGUMENTS
```

## Goal

Provide a clear, at-a-glance view of project status and workflow progress. This command is **READ-ONLY** and helps users understand where they are in the spec-driven development workflow and what to do next.

This command answers: "Where am I and what should I do next?"

(For artifact quality and consistency analysis, use `/speckit.analyze` instead.)

## Input Parsing

Parse user input for:

1. **Feature identifier** (optional, positional):
   - Feature name: `002-dashboard`
   - Feature number prefix: `002`
   - Feature path: `specs/002-dashboard`

2. **Flags**:
   - `--all`: Show features overview only, no detail section
   - `--verbose`: Include task breakdown and artifact summaries
   - `--json`: Output machine-readable JSON instead of formatted text
   - `--feature <name>`: Explicit feature selection (alternative to positional)

**Precedence**: Explicit feature > positional argument > current branch > `--all` required

## Execution Steps

### 1. Initialize Context

Run `{SCRIPT}` from repo root to get REPO_ROOT and BRANCH. Determine:

- **REPO_ROOT**: Project root directory
- **SPECS_DIR**: `{REPO_ROOT}/.specify/specs` (fall back to `{REPO_ROOT}/specs` if not found)
- **MEMORY_DIR**: `{REPO_ROOT}/.specify/memory` (fall back to `{REPO_ROOT}/memory`)
- **CURRENT_BRANCH**: Current git branch (or fallback per script logic)
- **HAS_GIT**: Whether project is a git repository

### 2. Load Constitution Status

Check for constitution file at `{MEMORY_DIR}/constitution.md`:

- If exists: Extract version from file (look for `## Version` section or `version:` in frontmatter)
- Format: `✓ Defined (v1.2.0)` or `✓ Defined` if no version found
- If missing: `○ Not defined`

### 3. Scan All Features

Scan `{SPECS_DIR}` for feature directories (matching pattern `NNN-*` where NNN is 3 digits):

For each feature directory, detect stage by checking file existence:

| Stage | Condition | Display |
|-------|-----------|---------|
| Specify | `spec.md` exists | ✓ |
| Specify | `spec.md` missing | ○ |
| Plan | `plan.md` exists | ✓ |
| Plan | `plan.md` missing, spec exists | ○ |
| Plan | `plan.md` missing, no spec | - |
| Tasks | `tasks.md` exists | ✓ |
| Tasks | `tasks.md` missing, plan exists | ○ |
| Tasks | `tasks.md` missing, no plan | - |
| Implement | Parse `tasks.md` for completion | See below |

**Implementation stage logic** (when `tasks.md` exists):

- Count total tasks: Lines matching `- [ ]` or `- [x]` or `- [X]`
- Count completed: Lines matching `- [x]` or `- [X]`
- If 0 completed: `○ Ready`
- If all completed: `✓ Complete`
- If partial: `● {completed}/{total} ({percent}%)`

### 4. Determine Target Feature

Based on input parsing:

1. If `--all` flag: Skip detail section, show overview only
2. If feature specified (positional or `--feature`): Use that feature
3. If on feature branch (matches `NNN-*` pattern): Use current branch feature
4. If on non-feature branch (e.g., `main`):
   - Add note: `ℹ Not on a feature branch`
   - Show overview only (no detail section)

### 5. Build Feature Detail (if target feature selected)

For the target feature, gather:

**Artifacts status**:

| Artifact | Path | Check |
|----------|------|-------|
| spec.md | `{FEATURE_DIR}/spec.md` | File exists |
| plan.md | `{FEATURE_DIR}/plan.md` | File exists |
| tasks.md | `{FEATURE_DIR}/tasks.md` | File exists |
| research.md | `{FEATURE_DIR}/research.md` | File exists |
| data-model.md | `{FEATURE_DIR}/data-model.md` | File exists |
| quickstart.md | `{FEATURE_DIR}/quickstart.md` | File exists |
| contracts/ | `{FEATURE_DIR}/contracts/` | Directory exists and non-empty |
| checklists/ | `{FEATURE_DIR}/checklists/` | Directory exists and non-empty |

Display: `✓` exists, `○` ready to create (prerequisite exists), `-` not applicable yet

**Checklists status** (if `checklists/` exists):

For each `.md` file in checklists/:
- Count total items: `- [ ]` or `- [x]` or `- [X]`
- Count completed: `- [x]` or `- [X]`
- Format: `✓ {name} {completed}/{total}` or `● {name} {completed}/{total}`

**Task progress** (if `--verbose` and `tasks.md` exists):

Parse tasks.md for phase sections (headers containing "Phase"):
- Extract phase name and task counts
- Show: `✓` complete, `●` in progress, `○` not started, `-` blocked

### 6. Determine Next Action

Based on target feature state, recommend next command:

| Current State | Next Action | Message |
|---------------|-------------|---------|
| No spec.md | `/speckit.specify` | Create feature specification |
| spec.md, no plan.md | `/speckit.plan` | Create implementation plan |
| plan.md, no tasks.md | `/speckit.tasks` | Generate implementation tasks |
| tasks.md, 0% complete | `/speckit.implement` | Begin implementation |
| tasks.md, partial | `/speckit.implement` | Continue implementation |
| tasks.md, 100% complete | (none) | Ready for review/merge |

Optional recommendations based on context:
- If spec.md exists but no clarifications: Mention `/speckit.clarify` as optional
- If tasks.md exists but not analyzed: Mention `/speckit.analyze` as optional

### 7. Generate Output

**Human-readable format** (default):

```
Spec-Driven Development Status

Project: {project_name}
Branch: {current_branch}
Constitution: {constitution_status}

Features
+-----------------+---------+------+-------+------------------+
| Feature         | Specify | Plan | Tasks | Implement        |
+-----------------+---------+------+-------+------------------+
| 001-onboarding  |    ✓    |  ✓   |   ✓   | ✓ Complete       |
| 002-dashboard   |    ✓    |  ✓   |   ✓   | ● 12/18 (67%)    |
| 003-user-auth < |    ✓    |  ✓   |   ○   | -                |
+-----------------+---------+------+-------+------------------+

Legend: ✓ complete  ● in progress  ○ ready  - not started

{FEATURE_DETAIL_SECTION if target feature selected}

{EMPTY_STATE_MESSAGE if no features exist}
```

**Feature detail section**:

```
003-user-auth

Artifacts:
  ✓ spec.md        ✓ plan.md        ○ tasks.md
  ✓ research.md    ✓ data-model.md  - quickstart.md
  ✓ contracts/     - checklists/

Checklists: None defined

Next: /speckit.tasks
  Generate implementation tasks from your plan
```

**Verbose additions** (when `--verbose`):

```
Task Progress:
  Phase 1 - Setup:        ✓ 4/4 complete
  Phase 2 - Foundation:   ✓ 3/3 complete
  Phase 3 - US1 Login:    ● 5/8 in progress
  Phase 4 - US2 Register: ○ 0/6 not started
  Phase 5 - Polish:       - 0/3 blocked

Checklists:
  ✓ security.md    6/6
  ● ux.md          8/12
```

**Empty state** (no features in specs/):

```
Spec-Driven Development Status

Project: {project_name}
Branch: {current_branch}
Constitution: {constitution_status}

Features
+---------+---------+------+-------+-----------+
| Feature | Specify | Plan | Tasks | Implement |
+---------+---------+------+-------+-----------+
| (none)  |         |      |       |           |
+---------+---------+------+-------+-----------+

No features defined yet.
Run /speckit.specify to create your first feature.
```

**JSON format** (when `--json`):

```json
{
  "project": "my-project",
  "branch": "003-user-auth",
  "is_feature_branch": true,
  "constitution": {
    "exists": true,
    "version": "1.2.0"
  },
  "features": [
    {
      "name": "001-onboarding",
      "path": "/path/to/specs/001-onboarding",
      "stages": {
        "specify": "complete",
        "plan": "complete",
        "tasks": "complete",
        "implement": "complete"
      },
      "tasks": {
        "total": 24,
        "completed": 24,
        "percent": 100
      }
    },
    {
      "name": "003-user-auth",
      "path": "/path/to/specs/003-user-auth",
      "is_current": true,
      "stages": {
        "specify": "complete",
        "plan": "complete",
        "tasks": "ready",
        "implement": "not_started"
      },
      "tasks": null
    }
  ],
  "current_feature": {
    "name": "003-user-auth",
    "artifacts": {
      "spec.md": true,
      "plan.md": true,
      "tasks.md": false,
      "research.md": true,
      "data-model.md": true,
      "quickstart.md": false,
      "contracts/": true,
      "checklists/": false
    },
    "checklists": [],
    "next_action": {
      "command": "/speckit.tasks",
      "message": "Generate implementation tasks from your plan"
    }
  }
}
```

## Operating Principles

### Read-Only Operation

- **NEVER** modify any files
- **NEVER** create any files
- This command is purely informational

### Context Efficiency

- Scan only what's needed (file existence checks, not full content reads)
- Parse tasks.md minimally (line matching, not full semantic analysis)
- Keep output concise and actionable

### Graceful Handling

- Missing directories: Report as empty state
- Missing files: Report as not yet created
- Parse errors: Skip and continue, note in output if critical
- Non-git repos: Function normally, note git status as unavailable

### User Experience

- Always show the features overview for project context
- Clearly indicate current/active feature with `<` marker
- Make next action obvious and specific
- Support both quick checks (`/speckit.status`) and deep dives (`--verbose`)
