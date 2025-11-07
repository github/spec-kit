# Git Hooks for Spec-Kit

This directory contains Git hooks that enhance the spec-kit workflow by automating validation and quality checks.

## Available Hooks

### pre-commit

Validates specification files before allowing a commit.

**What it checks:**
- `spec.md`: Minimum size (500 bytes), required sections, TODO/TBD placeholders
- `plan.md`: Minimum size (300 bytes), Technology Stack section
- `tasks.md`: Minimum size (200 bytes), minimum 5 tasks

**Behavior:**
- **Errors** (critical issues): Block the commit
- **Warnings** (minor issues): Allow commit but show warnings

## Installation

### Option 1: Symbolic Link (Recommended)

```bash
# From repository root
ln -s ../../hooks/pre-commit .git/hooks/pre-commit
```

Benefits:
- Automatic updates when hook changes
- Easy to maintain

### Option 2: Copy

```bash
# From repository root
cp hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

Benefits:
- Works if symlinks not supported
- Can customize per-project

## Usage

Once installed, the hook runs automatically before every commit:

```bash
git commit -m "Update spec"
```

Output:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Spec-Kit Pre-Commit Validation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Checking 001-task-management...
  ✓ spec.md valid
  ✓ plan.md valid
  ⚠️  tasks.md has only 3 tasks (minimum 5 recommended)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  1 warning(s) found

Warnings do not block commits, but should be addressed.
Proceeding with commit...
```

### Bypassing the Hook

If you need to commit despite validation errors:

```bash
git commit --no-verify -m "WIP: incomplete spec"
```

**Warning:** Only bypass when absolutely necessary. The hook catches issues that would cause problems later in the workflow.

## Validation Levels

### Critical (Blocks Commit)
- Missing `spec.md` file
- `spec.md` too short (< 500 bytes)
- Missing "## User Scenarios" section in spec.md

### Warning (Allows Commit)
- Missing "## Functional Requirements" section
- TODO/TBD placeholders present
- `plan.md` or `tasks.md` too short
- Fewer than 5 tasks in tasks.md

## Customization

You can customize the validation rules by editing the hook file:

```bash
# Edit the hook
vim .git/hooks/pre-commit

# Key variables to adjust:
SPEC_MIN_SIZE=500      # Minimum bytes for spec.md
PLAN_MIN_SIZE=300      # Minimum bytes for plan.md
TASKS_MIN_SIZE=200     # Minimum bytes for tasks.md
MIN_TASKS=5            # Minimum number of tasks
```

## Troubleshooting

### Hook not running
```bash
# Check if hook is executable
ls -l .git/hooks/pre-commit

# If not, make it executable
chmod +x .git/hooks/pre-commit
```

### Hook running but failing
```bash
# Test the hook manually
.git/hooks/pre-commit

# Check which files would be validated
git diff --cached --name-only | grep "^specs/"
```

### Disable hook temporarily
```bash
# Rename the hook
mv .git/hooks/pre-commit .git/hooks/pre-commit.disabled

# To re-enable
mv .git/hooks/pre-commit.disabled .git/hooks/pre-commit
```

## Integration with Workflow

The pre-commit hook fits into the spec-kit workflow at these points:

1. After `/speckit.specify` - Validates spec.md before committing
2. After `/speckit.plan` - Validates plan.md completeness
3. After `/speckit.tasks` - Ensures sufficient task breakdown
4. Continuous validation - Catches regressions when updating specs

## Benefits

- **Catch issues early**: Identify incomplete specs before they cause implementation problems
- **Consistency**: Enforce minimum quality standards across all features
- **Automation**: No need to remember to run `/speckit.validate` manually
- **Fast feedback**: Validation runs in <1 second for typical specs
- **Flexibility**: Warnings don't block workflow, only critical errors

## Future Enhancements

Planned improvements:
- `post-merge` hook: Auto-generate AI docs after merging feature branches
- `prepare-commit-msg` hook: Auto-populate commit messages from spec changes
- Configuration file: `.speckit-hooks.json` for per-project customization
