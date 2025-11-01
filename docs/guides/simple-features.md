# Quick Mode: Simple Features (<200 LOC)

For small bug fixes, configuration changes, and quick tweaks.

## When to Use This Guide

- Estimated <200 lines of code
- Clear requirements (no ambiguity)
- Low risk (isolated changes)
- Examples: bug fixes, UI tweaks, config updates

## The 3-Step Process

### Step 1: Create Minimal Spec (2 minutes)

```
/specify [Your feature description]

Example:
/specify Fix login timeout from 30 to 60 minutes. Update the timeout constant
in config and add a note to security docs about the rationale.
```

The AI generates a focused spec with:
- What needs to change
- Why it matters
- Acceptance criteria

### Step 2: Create Task List (2 minutes)

```
/tasks
```

The AI breaks down the work into concrete tasks.

### Step 3: Implement (5-10 minutes)

```
implement specs/[feature-id]/plan.md
```

Done! Simple as that.

## Total Time: ~10 minutes

Compare to traditional approach:
- Traditional: "Make this change" → Git commit (30 min with context-switching)
- Spec Kit quick mode: `/specify` → `/tasks` → `/implement` (10 min with clarity)

## Example: Adding a Feature Flag

```
/specify Add a feature flag for dark mode. Default to light mode.
Users should be able to toggle in settings. Persist preference in localStorage.
```

AI generates spec → You review it (2 min) → `/tasks` → Implement

The spec becomes your documentation and implementation guide in one.

## Tips

- Be specific about what and why
- Don't overthink it—this is for simple changes
- If it's getting complex, switch to [Complex Features](./complex-features.md)
- Use `/smart-commit` for good commit messages

## When to Escalate

If you find yourself:
- Writing multiple long feature specs
- Needing architectural decisions
- Facing scope uncertainty

→ Switch to [Standard Features](./standard-features.md) or [Complex Features](./complex-features.md)
