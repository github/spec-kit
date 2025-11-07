---
description: Cross-artifact consistency and alignment analysis
---

# Cross-Artifact Analysis

Analyze consistency and alignment across specifications, plans, and tasks.

## When to Run

Run this command **after** `/tasks` and **before** `/implement` to ensure all artifacts are aligned.

## What This Analyzes

### Spec ↔ Plan Alignment
- All spec requirements addressed in plan
- Plan tasks map to spec requirements
- No orphaned tasks or requirements

### Plan ↔ Tasks Alignment
- All plan phases have corresponding tasks
- Task dependencies match plan phases
- Effort estimates are consistent

### Cross-Cutting Concerns
- Security requirements addressed
- Performance requirements covered
- Testing strategy is complete
- Documentation tasks included

## What You Get

- **Gaps Report** - Missing requirements or tasks
- **Conflicts** - Contradictions between artifacts
- **Recommendations** - Suggested improvements
- **Readiness Score** - Overall implementation readiness

## Common Issues Found

- Requirements missing from plan
- Tasks without acceptance criteria
- Inconsistent naming across artifacts
- Missing error handling tasks
- Incomplete test coverage plan
- Documentation gaps

## After Analysis

1. Review identified gaps
2. Update affected artifacts
3. Re-run analysis to verify fixes
4. Proceed with implementation

## Best Practices

- Run before starting implementation
- Re-run after significant changes
- Address high-priority issues first
- Keep artifacts in sync during development
