---
description: "Resume an interrupted session by detecting feature state and suggesting the next command"
---

## User Input

```text
$ARGUMENTS
```

## Outline

Resume an interrupted SDD session by scanning the project for active features, detecting their completion state, and generating a prompt to continue work.

### Step 1: Find the project root

Locate the `.specify/` directory to identify the project root. If not found, error: "No spec-kit project found. Run `specify init` first."

### Step 2: Discover features

Scan the `specs/` directory for feature directories (numbered directories like `001-auth`, `002-dashboard`).

For each feature directory, detect state by checking for these files:
- `spec.md` - specification exists and is non-empty
- `plan.md` - implementation plan exists and is non-empty
- `tasks.md` - task breakdown exists
- `checklists/` - quality checklists exist

### Step 3: Parse task completion

If `tasks.md` exists, parse checkbox items:
- `- [x]` or `- [X]` = completed
- `- [ ]` = remaining

Count total tasks, completed tasks, and extract remaining task descriptions.

### Step 4: Determine phase for each feature

| Condition | Phase | Next Command |
|-----------|-------|-------------|
| No `spec.md` or empty | `specify` | `/speckit.specify` |
| `spec.md` exists, no `plan.md` | `plan` | `/speckit.plan` |
| `plan.md` exists, no `tasks.md` | `tasks` | `/speckit.tasks` |
| `tasks.md` exists, some incomplete | `implement` | `/speckit.implement` |
| All tasks complete | `complete` | Review and finalize |

### Step 5: Handle arguments

If `$ARGUMENTS` specifies a feature name or number (e.g., `001-auth` or `auth`), filter to that feature only.

### Step 6: Generate resume prompt

For each active (non-complete) feature, output:

```
Feature: {name}
Status: {spec ✓/✗} {plan ✓/✗} {tasks ✓/✗}
Phase: {phase}
Progress: {completed}/{total} tasks complete

Next step: Run `/{next_command}`
```

If tasks remain, list the first 3 remaining tasks:

```
Remaining tasks:
  1. {task description}
  2. {task description}
  3. {task description}
```

If all features are complete:

```
All features are complete. Review and finalize the project.
```

### Step 7: Report

Output the resume prompt. If `--copy` was passed as an argument, mention that the prompt can be copied to clipboard.
