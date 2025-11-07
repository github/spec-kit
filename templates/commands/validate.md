---
description: Validate specifications, plans, and tasks for completeness and consistency
scripts:
  sh: scripts/bash/validate-spec.sh --json
  ps: scripts/powershell/validate-spec.ps1 -Json
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Goal

Provide quick, lightweight validation of SpecKit artifacts before major operations. Catch issues early in the workflow to save time and tokens.

## Validation Modes

Parse `$ARGUMENTS` to determine validation mode:

- **No arguments** or `--current`: Validate current feature only
- `--spec`: Validate only spec.md
- `--plan`: Validate only plan.md
- `--tasks`: Validate only tasks.md
- `--all`: Validate all features in project
- `--constitution`: Validate constitution.md exists and is complete

## Execution Steps

### 1. Run Validation Script

Execute `{SCRIPT}` with appropriate arguments based on user input.

The script will return JSON with validation results:

```json
{
  "feature": "001-feature-name",
  "validations": {
    "spec": {"exists": true, "complete": true, "issues": []},
    "plan": {"exists": true, "complete": true, "issues": ["Missing test strategy"]},
    "tasks": {"exists": true, "complete": true, "issues": []},
    "constitution": {"exists": true, "complete": true}
  },
  "status": "warning",
  "summary": "2 of 3 artifacts validated successfully"
}
```

### 2. Display Results

Present validation results in clear format:

**For single feature:**
```
Validation: 001-feature-name
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ spec.md: Complete
⚠ plan.md: Issues found
  • Missing test strategy
✓ tasks.md: Complete

Status: ⚠️ Warning
Ready for next step: Yes (with improvements needed)
```

**For all features:**
```
Project Validation Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total features: 5

✓ 001-task-management: Complete
✓ 002-user-auth: Complete
⚠ 003-project-tags: Missing AI docs
✓ 004-notifications: Complete
✗ 005-file-uploads: Spec incomplete

Constitution: ✓ Present

Overall: 3 complete, 1 warning, 1 error
Recommendation: Fix 005-file-uploads before proceeding
```

### 3. Validation Checks

The script performs these lightweight checks:

**spec.md:**
- File exists
- Has required sections (User Scenarios, Functional Requirements)
- No TODO/TBD placeholders in critical sections
- Minimum length (>500 characters)

**plan.md:**
- File exists
- Has technology stack defined
- Has project structure
- References spec.md

**tasks.md:**
- File exists
- Has task list
- Tasks reference file paths
- Minimum number of tasks (>5)

**constitution.md:**
- File exists
- Has principles defined
- Minimum length (>300 characters)

### 4. Provide Recommendations

Based on validation results, suggest next actions:

**All validations pass:**
```
✓ All validations passed
Ready to proceed with: [next workflow step]
```

**Warnings found:**
```
⚠️ Warnings found - review recommended
Issues can be addressed now or later
Safe to proceed if issues are acceptable
```

**Errors found:**
```
✗ Errors found - must fix before proceeding
Run these commands to fix:
  • /speckit.specify (to complete spec)
  • /speckit.plan (to add missing plan sections)
```

## Common Use Cases

### Before Planning
```bash
/speckit.validate --spec
# Ensures spec is ready before creating plan
```

### Before Implementation
```bash
/speckit.validate --tasks
# Ensures tasks are complete before implementing
```

### Project Health Check
```bash
/speckit.validate --all
# Quick check of entire project status
```

### Pre-commit Check
```bash
/speckit.validate
# Validate current feature before committing
```

## Output Examples

### Healthy Feature
```
Validation: 002-user-auth
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ spec.md: Complete (1,245 lines)
✓ plan.md: Complete (856 lines)
✓ tasks.md: Complete (42 tasks)

Status: ✓ Excellent
Ready for implementation: Yes
```

### Feature with Issues
```
Validation: 005-file-uploads
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✗ spec.md: Incomplete
  • Contains TODO placeholders
  • Missing Success Criteria section
✓ plan.md: Complete
✗ tasks.md: Not found

Status: ✗ Errors found
Recommendation: Complete spec and generate tasks
  Run: /speckit.clarify
  Then: /speckit.tasks
```

## Validation Rules

### Critical (Must Fix)
- Missing required files (spec.md)
- Empty or stub files
- Spec has no functional requirements

### Warning (Should Fix)
- Missing optional files (ai-doc.md)
- TODO/TBD placeholders
- Very short content (<500 chars for spec)
- Missing recommended sections

### Info (Optional)
- Suggestions for improvement
- Best practice recommendations

## Context

{ARGS}
