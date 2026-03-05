---
description: "Break down implementation plans into structured, dependency-aware tasks"
tools:
  - 'specify-mcp/tasks'
  - 'specify-mcp/task_progress'
---

# Generate Task Breakdown

Create structured, dependency-aware tasks from implementation plans.

## Purpose

Transform implementation plans into actionable tasks:
- Ordered task list with dependencies
- Effort estimates and priority
- Acceptance criteria per task
- Progress tracking integration

## Prerequisites

1. Implementation plan exists in `specs/{feature-id}/plan.md`
2. Specify MCP server running

## User Input

$ARGUMENTS

## Steps

### Step 1: Generate Task Breakdown

Create tasks from the plan:

Use MCP tool: `specify-mcp/tasks`

Parameters:
- `plan_path`: Path to implementation plan
- `project_path`: Project root path
- `include_estimates`: Include effort estimates (default: true)
- `granularity`: Task size - "fine" or "coarse" (default: "fine")

```json
{
  "plan_path": "specs/001-oauth-authentication/plan.md",
  "project_path": ".",
  "include_estimates": true,
  "granularity": "fine"
}
```

### Step 2: Review Generated Tasks

The tool generates `specs/{feature-id}/tasks.md` containing:

**Task Structure**:
- **Task ID**: Unique identifier (e.g., T001, T002)
- **Title**: Clear, actionable task name
- **Description**: Detailed task explanation
- **Dependencies**: Tasks that must complete first
- **Estimate**: Effort estimation (if enabled)
- **Acceptance Criteria**: Definition of done
- **Phase**: Implementation phase assignment

**Dependency Graph**:
- Visual representation of task dependencies
- Critical path identification
- Parallel work opportunities

### Step 3: Check Task Progress

Monitor task completion:

Use MCP tool: `specify-mcp/task_progress`

Parameters:
- `feature_path`: Path to feature directory
- `action`: "status" or "update"
- `task_id`: Task ID (for update action)
- `status`: New status (for update: "pending", "in_progress", "completed", "blocked")

```json
{
  "feature_path": "specs/001-oauth-authentication",
  "action": "status"
}
```

### Step 4: Track Progress

Update task status as work progresses:

```json
{
  "feature_path": "specs/001-oauth-authentication",
  "action": "update",
  "task_id": "T001",
  "status": "completed"
}
```

## Output Structure

```
specs/
└── 001-{feature-name}/
    ├── spec.md           # Specification
    ├── plan.md           # Implementation plan
    └── tasks.md          # Task breakdown
```

## Task Status Values

| Status | Description |
|--------|-------------|
| `pending` | Not started |
| `in_progress` | Currently being worked on |
| `completed` | Finished and verified |
| `blocked` | Cannot proceed (dependency issue) |

## Examples

### Generate Fine-Grained Tasks

```json
{
  "plan_path": "specs/001-oauth-authentication/plan.md",
  "project_path": ".",
  "granularity": "fine",
  "include_estimates": true
}
```

### Generate Coarse Tasks

```json
{
  "plan_path": "specs/002-notifications/plan.md",
  "project_path": ".",
  "granularity": "coarse"
}
```

### Update Task Status

```json
{
  "feature_path": "specs/001-oauth-authentication",
  "action": "update",
  "task_id": "T003",
  "status": "in_progress"
}
```

## Notes

- Start with coarse granularity, refine as needed
- Update task status regularly for accurate progress tracking
- Blocked tasks should include blocker description
- Use estimates as guidelines, adjust based on reality

---

*For more information: `specify extension info specify-mcp`*
