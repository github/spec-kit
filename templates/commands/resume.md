---
description: Resume interrupted implementation from last checkpoint
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Goal

Resume an interrupted `/speckit.implement` session from the last saved checkpoint, continuing where you left off without redoing completed work.

## Prerequisites

This command requires that:
1. A previous `/speckit.implement` was started
2. Implementation was interrupted (not completed)
3. A checkpoint file exists (`.speckit-progress.json`)

## Execution Steps

### 1. Check for Checkpoint File

Look for `.speckit-progress.json` in the current feature directory:

```bash
specs/###-feature-name/.speckit-progress.json
```

If not found, inform the user:
```
No checkpoint file found.

This could mean:
  • No implementation was started yet (run /speckit.implement)
  • Implementation completed successfully (checkpoint was cleaned up)
  • Checkpoint file was deleted

To start fresh implementation, use /speckit.implement
```

### 2. Load Checkpoint Data

Read the checkpoint file structure:
```json
{
  "feature": "001-task-management",
  "started_at": "2025-11-07T14:30:00Z",
  "last_checkpoint": "2025-11-07T15:45:00Z",
  "total_tasks": 42,
  "completed_tasks": 23,
  "current_task": 24,
  "failed_tasks": [],
  "state": {
    "last_successful_task": "Task 23: Create API endpoint for task updates",
    "last_file_modified": "src/api/tasks.py",
    "tests_passing": true,
    "build_status": "success"
  }
}
```

### 3. Display Resume Information

Show the user what will resume:

```
Resume Implementation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Feature: 001-task-management
Progress: 23 of 42 tasks completed (55%)

Last checkpoint: 2025-11-07 15:45:00
Last successful: Task 23 - Create API endpoint for task updates

Status:
  ✓ Tests passing
  ✓ Build successful
  ✓ No failed tasks

Resuming from: Task 24 of 42

Ready to continue? The implementation will resume from where it left off.
```

### 4. Resume Implementation

Continue with the implementation workflow from the current_task:

1. Read `tasks.md` to get remaining tasks
2. Start from task number `current_task` (24 in example)
3. Execute each task sequentially
4. Update checkpoint after each task
5. Continue until all tasks complete

### 5. Checkpoint Updates

After each task completion, update `.speckit-progress.json`:

```json
{
  "feature": "001-task-management",
  "last_checkpoint": "2025-11-07T15:50:00Z",
  "completed_tasks": 24,
  "current_task": 25,
  "state": {
    "last_successful_task": "Task 24: Add validation to task update endpoint",
    "last_file_modified": "src/api/tasks.py",
    "tests_passing": true
  }
}
```

### 6. Completion

When all tasks complete:
1. Remove checkpoint file
2. Display completion summary
3. Recommend next steps

```
Implementation Complete!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Feature: 001-task-management
Total tasks: 42
Duration: 2h 15m

All tasks completed successfully ✓

Next steps:
  • Run tests: npm test
  • Validate: /speckit.validate
  • Document: /speckit.document
```

## Checkpoint Strategy

### When Checkpoints Are Created

Checkpoints are saved:
- After each task completion
- After successful test runs
- Before potentially destructive operations
- Every 10 minutes during long-running tasks

### What Gets Checkpointed

```json
{
  "feature": "string",
  "started_at": "ISO8601 timestamp",
  "last_checkpoint": "ISO8601 timestamp",
  "total_tasks": number,
  "completed_tasks": number,
  "current_task": number,
  "failed_tasks": [
    {"task": number, "error": "string", "timestamp": "ISO8601"}
  ],
  "state": {
    "last_successful_task": "string",
    "last_file_modified": "string",
    "tests_passing": boolean,
    "build_status": "success|failure|unknown",
    "notes": ["string"]
  }
}
```

### Checkpoint Location

- File: `specs/###-feature-name/.speckit-progress.json`
- Git-ignored (not committed)
- Automatically cleaned up on successful completion
- Preserved on failure for debugging

## Error Handling

### Checkpoint File Corrupted

```
⚠️ Checkpoint file appears corrupted

Options:
  1. Delete checkpoint and start fresh: /speckit.implement
  2. Manually inspect: cat specs/###-feature/.speckit-progress.json
  3. Contact support if issue persists
```

### Previous Failure Detected

If checkpoint shows failed tasks:

```
⚠️ Previous implementation had failures

Failed tasks:
  • Task 15: Database migration failed
    Error: Column 'status' already exists
    Time: 2025-11-07 14:30:00

Options:
  1. Resume and retry failed tasks
  2. Skip failed tasks (may cause issues)
  3. Start fresh: Delete checkpoint and run /speckit.implement

Recommended: Resume and retry (fixes may have been applied)
```

### Spec/Plan Changed Since Checkpoint

```
⚠️ Specification changed since checkpoint

Last checkpoint: 2025-11-07 14:00
Spec modified: 2025-11-07 16:00

Changes detected in:
  • spec.md (2 requirements added)
  • tasks.md (5 new tasks)

Options:
  1. Continue with original tasks (complete existing work)
  2. Regenerate tasks: /speckit.tasks (starts fresh)
  3. Manual review recommended

Proceeding with option 1 (complete existing work first)
```

## Best Practices

### Save Checkpoint Frequently

The implement command should checkpoint after:
- Every completed task
- Every 10-15 minutes
- Before long-running operations
- After successful test runs

### Handle Interruptions Gracefully

Common interruption scenarios:
- User cancels (Ctrl+C)
- Network errors
- Build failures
- Test failures
- System crashes

All should preserve checkpoint for resume.

### Clean Up on Success

When implementation completes successfully:
```bash
rm specs/###-feature/.speckit-progress.json
```

Keep checkpoints only for incomplete/failed implementations.

## Integration with Other Commands

### Before Resume

```bash
# Check what will resume
cat specs/001-feature/.speckit-progress.json

# Check current project state
/speckit.validate

# Check token budget
/speckit.budget
```

### After Resume

```bash
# Validate completed implementation
/speckit.validate

# Generate documentation
/speckit.document

# Run full tests
npm test
```

## Example Workflows

### Scenario 1: Quick Interruption

```bash
# Start implementation
/speckit.implement

# [System crash or Ctrl+C at task 15/42]

# Later: Resume
/speckit.resume
# Continues from task 15
```

### Scenario 2: Failed Task

```bash
/speckit.implement
# Task 20 fails: API endpoint returns 500

# Fix the issue in code
# Edit src/api/users.py

# Resume
/speckit.resume
# Retries task 20, continues if successful
```

### Scenario 3: Overnight Break

```bash
# Friday 5pm: Start large implementation
/speckit.implement
# Complete tasks 1-25 of 60

# [Go home for weekend]

# Monday 9am: Resume
/speckit.resume
# Continues from task 26
```

## Limitations

### Current Version

- Manual resume (must run command)
- Single checkpoint per feature
- No task-level rollback
- No automatic conflict resolution

### Future Enhancements

- Auto-resume on restart
- Multiple checkpoint versions
- Task-level undo/redo
- Smart conflict resolution
- Progress visualization

## Output Example

### Successful Resume

```
Resuming Implementation: 001-task-management
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Checkpoint loaded:
  Started: 2 hours ago
  Progress: 23/42 tasks (55%)
  Status: All tests passing ✓

Resuming from task 24...

✓ Task 24: Add validation to task update endpoint
✓ Task 25: Create task deletion endpoint
✓ Task 26: Add cascade delete for tasks
...

[Implementation continues]
```

### No Checkpoint Found

```
No checkpoint found
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

No incomplete implementation to resume.

Options:
  • Start new implementation: /speckit.implement
  • Check feature status: /speckit.validate
  • View tasks: cat specs/###-feature/tasks.md
```

## Context

{ARGS}

## Important Note

This command template is ready for use. The actual checkpoint creation
needs to be implemented in the `/speckit.implement` command workflow.

To enable full resume functionality:
1. Modify implement command to create checkpoints
2. Save .speckit-progress.json after each task
3. Handle interruption signals (SIGINT, SIGTERM)
4. Clean up checkpoint on successful completion
