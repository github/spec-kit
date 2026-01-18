# Data Model: Ralph Loop Implementation Support

**Feature**: 001-ralph-loop-implement  
**Date**: 2026-01-18

## Entities

### 1. Ralph Session

A single execution of the `specify ralph` command from start to termination.

| Attribute | Type | Description |
|-----------|------|-------------|
| feature_branch | string | Feature branch name (e.g., `001-ralph-loop-implement`) |
| start_time | datetime | When the session started |
| end_time | datetime | When the session ended (null if running) |
| status | enum | `running`, `completed`, `interrupted`, `failed` |
| max_iterations | int | Configured iteration limit (default: 10) |
| iterations_run | int | Number of iterations executed |
| tasks_completed | int | Number of tasks marked complete during session |
| tasks_remaining | int | Number of incomplete tasks at session end |

**Storage**: Not persisted as structured data. Reconstructable from progress.txt and tasks.md state.

### 2. Iteration

One invocation of the agent CLI within a session.

| Attribute | Type | Description |
|-----------|------|-------------|
| number | int | Iteration number (1-indexed) |
| task_attempted | string | Task ID attempted (e.g., `T001`) |
| start_time | datetime | When iteration started |
| end_time | datetime | When iteration ended |
| outcome | enum | `success`, `failure`, `skipped` |
| files_changed | list[string] | Files modified during iteration |
| learnings | string | Agent-reported discoveries (optional) |

**Storage**: Appended to `progress.txt` as markdown sections.

### 3. Progress Log

Append-only file tracking all iterations across sessions.

| Attribute | Type | Description |
|-----------|------|-------------|
| file_path | path | `specs/{feature}/progress.txt` |
| header | string | Feature name and initial timestamp |
| entries | list[Iteration] | Markdown-formatted iteration records |
| codebase_patterns | string | Extracted patterns section (optional) |

**Storage**: Markdown file in specs directory.

### 4. Task Tracking

Implicit tracking via tasks.md checkbox state.

| Attribute | Type | Description |
|-----------|------|-------------|
| task_id | string | Task identifier (e.g., `T001`, `T002`) |
| description | string | Task description text |
| is_complete | bool | `[x]` = true, `[ ]` = false |
| phase | string | Phase the task belongs to |

**Storage**: Parsed from existing `tasks.md` markdown. No separate tracking file needed.

### 5. Prompt Template

Static template combined with dynamic context for each iteration.

| Attribute | Type | Description |
|-----------|------|-------------|
| template_path | path | `templates/ralph-prompt.md` |
| placeholders | dict | Variables replaced at runtime |

**Placeholders**:
- `{FEATURE_NAME}` - Feature branch name
- `{SPEC_PATH}` - Path to spec.md
- `{TASKS_PATH}` - Path to tasks.md  
- `{PROGRESS_PATH}` - Path to progress.txt
- `{CURRENT_TASK}` - Next incomplete task details
- `{ITERATION_NUMBER}` - Current iteration count

## File Formats

### progress.txt

```markdown
# Ralph Progress Log

Feature: {FEATURE_NAME}
Started: {TIMESTAMP}

## Codebase Patterns

[Patterns discovered during implementation - updated by agent]

---

## Iteration 1 - {TIMESTAMP}
**Task**: {TASK_ID} {TASK_DESCRIPTION}
**Status**: ✅ Completed | ❌ Failed | ⏭️ Skipped
**Files Changed**: 
- {file1}
- {file2}
**Learnings**:
- {learning1}
- {learning2}
---

## Iteration 2 - {TIMESTAMP}
...
```

### tasks.md (existing format, parsed)

```markdown
## Phase 1: Setup

- [ ] T001 Create project structure
- [x] T002 Initialize dependencies
- [ ] T003 Configure linting

## Phase 2: Implementation

- [ ] T004 Implement core logic
...
```

### ralph-prompt.md (new template)

See [contracts/prompt-template.md](contracts/prompt-template.md) for full template.

## State Transitions

### Session Status

```
[start] ──► running ──► completed (all tasks done OR COMPLETE signal)
              │
              ├──► interrupted (Ctrl+C)
              │
              └──► failed (max iterations reached with tasks remaining)
```

### Task Status (implicit in tasks.md)

```
[ ] incomplete ──► [x] complete (agent updates checkbox)
```

### Iteration Outcome

```
[start] ──► success (task checkbox changed to [x])
              │
              ├──► failure (task checkbox unchanged, agent error/timeout)
              │
              └──► skipped (same task failed 3+ times consecutively)
```

## Relationships

```
Ralph Session
    │
    ├── 1:N ──► Iteration
    │              │
    │              └── 1:1 ──► Task (attempted)
    │
    ├── 1:1 ──► Progress Log (writes to)
    │
    └── 1:1 ──► tasks.md (reads from / agent writes to)
```

## Validation Rules

1. **Session cannot start** if:
   - `tasks.md` does not exist or is empty
   - No incomplete tasks remain
   - `gh copilot` is not installed/authenticated

2. **Iteration is marked success** when:
   - At least one `[ ]` changed to `[x]` in tasks.md
   - Agent did not output error signals

3. **Session completes** when:
   - Agent outputs `<promise>COMPLETE</promise>`, OR
   - No incomplete tasks remain in tasks.md, OR
   - Max iterations reached (exits with non-zero if tasks remain)

4. **Task is skipped** when:
   - Same task failed 3 consecutive iterations
   - Logged as skipped, loop continues to next task
