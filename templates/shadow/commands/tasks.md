---
description: Generate actionable task breakdown from plan
---

# Generate Task Breakdown

Create detailed, actionable tasks from the implementation plan.

## Process

1. **Review plan** - Understand all phases and tasks
2. **Use the template** - Base tasks on `templates/tasks-template.md`
3. **Break down tasks** - Create granular, actionable items
4. **Set priorities** - Identify critical vs. optional tasks
5. **Map dependencies** - Show what blocks what

## Task Structure

Each task must include:
- Unique task ID
- Clear description
- Priority level
- Effort estimate
- Dependencies
- Acceptance criteria

## Output

Save the tasks to:
```
.tasks/<feature-name>-tasks.md
```

## Categories

Organize tasks by:
- Backend implementation
- Frontend implementation
- Database changes
- Testing
- Documentation
- Deployment

## Best Practices

- Tasks should be completable in 1-2 days
- Include setup and cleanup tasks
- Add testing tasks for each component
- Document integration points
