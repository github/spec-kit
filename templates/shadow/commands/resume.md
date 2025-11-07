---
description: Resume work on feature from previous session
---

# Resume Work Session

Resume work on a feature from a previous session with full context restoration.

## When to Use

- Starting a new work session
- Switching between features
- Returning after interruption
- Picking up someone else's work

## What This Does

1. **Loads Context**
   - Reads relevant specifications
   - Reviews implementation plan
   - Checks task status
   - Recalls previous decisions

2. **Provides Summary**
   - What was completed
   - What's in progress
   - What's remaining
   - Known blockers

3. **Suggests Next Steps**
   - Next task to tackle
   - Tests to write
   - Reviews to address
   - Documentation to update

## Usage

Specify the feature to resume:
```
Resume work on: <feature-name>
```

## Output

- Context summary
- Progress report
- Next recommended actions
- Relevant file locations

## Information Shown

### Completed
- ✅ Finished tasks
- ✅ Merged pull requests
- ✅ Closed issues

### In Progress
- 🔄 Current tasks
- 🔄 Open pull requests
- 🔄 Active branches

### Remaining
- ⏳ Pending tasks
- ⏳ Open issues
- ⏳ Future phases

## Best Practices

- Use at start of each session
- Update task status before ending session
- Document blockers and decisions
- Keep specifications current
- Note questions for team

## Quick Resume

For a quick context refresh:
1. Read `.memory/last-session.md`
2. Check `.tasks/<feature>-tasks.md`
3. Review git status and recent commits
4. Pick up where you left off
