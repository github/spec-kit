---
description: Analyze errors with specification context to provide relevant debugging guidance
scripts:
  sh: scripts/bash/error-analysis.sh --json
  ps: scripts/powershell/error-analysis.ps1 -Json
---

## User Input

```text
$ARGUMENTS
```

You **MUST** parse the error message or error type from `$ARGUMENTS`.

## Goal

When errors occur during development, provide enriched context by cross-referencing the error with specifications, requirements, and implementation plans. This helps identify which requirement might be violated or what specification detail was missed.

## Execution Steps

### 1. Parse Error Information

Extract from `$ARGUMENTS`:
- Error message or error output
- File where error occurred (if available)
- Error type (test failure, build error, runtime error, etc.)

Examples:
```bash
/speckit.error-context "TypeError: Cannot read property 'status' of undefined"
/speckit.error-context "Test failed: should update task status"
/speckit.error-context --file src/api/tasks.py --line 145
```

### 2. Run Error Analysis Script

Execute `{SCRIPT}` with the error details:

```bash
# Example: scripts/bash/error-analysis.sh --json "error message"
```

Expected JSON output:
```json
{
  "error": "TypeError: Cannot read property 'status' of undefined",
  "related_specs": [
    {
      "feature": "001-task-management",
      "requirement": "REQ-005: Task status transitions",
      "relevance": 85
    }
  ],
  "related_files": [
    {
      "file": "src/models/task.py",
      "line": 67,
      "context": "Status property definition"
    }
  ],
  "possible_causes": [
    "Task object not initialized before accessing status",
    "Async operation not awaited",
    "Null/undefined task returned from database"
  ],
  "suggestions": [
    "Check task initialization in specs/001-task-management/spec.md REQ-005",
    "Verify null handling in plan.md data validation section",
    "Review similar pattern in src/models/project.py:45"
  ]
}
```

### 3. Display Error Analysis

Present enriched context in clear format:

```
Error Analysis
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔴 Error: TypeError: Cannot read property 'status' of undefined

📍 Location: src/api/tasks.py:145

📋 Related Requirements:

  1. Spec 001-task-management, REQ-005 (relevance: 85%)
     "Task status transitions must be validated"
     File: specs/001-task-management/spec.md:78

  2. Spec 001-task-management, REQ-003 (relevance: 72%)
     "Tasks must have a default status upon creation"
     File: specs/001-task-management/spec.md:52

🔍 Possible Causes:

  • Task object not initialized before accessing status
  • Async operation not awaited (task fetch)
  • Null/undefined task returned from database query

💡 Suggestions:

  1. Check null handling in spec requirement REQ-005
     → specs/001-task-management/spec.md:78
     → "Tasks must exist before status updates"

  2. Review data validation in plan
     → specs/001-task-management/plan.md:145
     → "Input validation: task ID must be valid"

  3. Similar pattern handled correctly here:
     → src/models/project.py:45
     → Check for null before accessing properties

🎯 Quick Fix Checklist:

  ☐ Verify task exists before accessing properties
  ☐ Add null/undefined check
  ☐ Ensure async/await is used correctly
  ☐ Check database query returns expected format
```

### 4. Cross-Reference Specifications

For each error, search specifications for:

#### A. Related Requirements
- Keywords from error message
- File/function names mentioned
- Entity types involved (e.g., "task", "status")

Match against:
- Spec functional requirements
- Non-functional requirements
- Edge cases
- Success criteria

#### B. Related Plans
- Implementation details for affected area
- Data models and schemas
- API contracts
- Validation rules

#### C. Related Tasks
- Tasks that implemented this feature
- File paths mentioned in tasks
- Dependencies between tasks

### 5. Identify Patterns

Common error patterns to recognize:

#### Type Errors
```
"TypeError", "AttributeError", "NullReferenceException"
→ Check: Data model specs, null handling requirements
→ Look for: Validation rules, optional fields
```

#### Test Failures
```
"Test failed:", "Assertion error", "Expected X but got Y"
→ Check: Success criteria, acceptance tests in spec
→ Look for: User story scenarios, edge cases
```

#### Build Errors
```
"SyntaxError", "ImportError", "Module not found"
→ Check: Technology stack in plan
→ Look for: Dependencies, project structure
```

#### Runtime Errors
```
"500 Internal Server Error", "Database error", "Connection refused"
→ Check: Non-functional requirements (reliability, error handling)
→ Look for: Integration points, external dependencies
```

### 6. Provide Contextual Guidance

Based on error type and spec context:

**For Missing Requirements:**
```
⚠️ This error may indicate missing specification

The error suggests behavior not covered in requirements:
  • Error: "User role 'moderator' not recognized"
  • Spec 002-user-auth has roles: admin, user, guest
  • Missing: moderator role

Recommendation:
  1. Update spec.md to include moderator role
  2. Regenerate tasks with /speckit.tasks
  3. Implement the missing requirement
```

**For Violated Requirements:**
```
🚫 This error indicates requirement violation

Requirement says:
  REQ-008: "Email must be validated before account creation"
  → specs/002-user-auth/spec.md:95

But implementation:
  src/api/auth.py:67 - Creates account without email validation

Fix: Add email validation check before account creation
```

**For Implementation Deviation:**
```
⚙️ Implementation differs from plan

Plan specifies:
  "Use PostgreSQL JSONB for task metadata"
  → specs/001-task-management/plan.md:120

Error suggests:
  "JSON parsing error" - Using TEXT column instead

Fix: Align implementation with plan, or update plan if intentional
```

## Search Strategy

### 1. Keyword Extraction
From error message, extract:
- Entity names (User, Task, Project)
- Property names (status, email, role)
- Operation names (create, update, delete)
- Error types (null, undefined, invalid)

### 2. Search Scope
Search in order of relevance:
1. **Current feature specs** (highest priority)
2. **Related feature specs** (shared entities)
3. **Plans** (implementation details)
4. **Tasks** (actual work done)
5. **AI docs** (gotchas and edge cases)

### 3. Relevance Scoring
```
Score = keyword_matches × 40 +
        file_proximity × 30 +
        requirement_type × 20 +
        recency × 10

keyword_matches: Error terms found in requirement
file_proximity: Error file matches spec file reference
requirement_type: Functional > Non-functional > Edge case
recency: Recently modified specs score higher
```

## Common Use Cases

### During Implementation
```bash
# Test fails
npm test
# Error: "Expected status 'in-progress' but got 'pending'"

/speckit.error-context "Expected status 'in-progress' but got 'pending'"
# Returns: Status transition requirements from spec
```

### During Debugging
```bash
# Runtime error in logs
# TypeError: Cannot read property 'user' of null

/speckit.error-context "Cannot read property 'user' of null" --file src/middleware/auth.ts

# Returns:
# - User authentication requirements
# - Null handling specifications
# - Similar patterns in codebase
```

### After Build Failure
```bash
# Build error
# ModuleNotFoundError: No module named 'pandas'

/speckit.error-context "No module named 'pandas'"
# Returns:
# - Technology stack from plan.md
# - Dependencies list
# - Installation instructions
```

## Integration with Workflow

### 1. Automatic Error Enrichment
When `/speckit.implement` encounters errors:
```bash
# Implementation fails at task 15
# Error: "Database constraint violation"

# Automatically run:
/speckit.error-context "Database constraint violation" --task 15

# Show enriched error with spec context
# Continue or abort based on error severity
```

### 2. Pre-Fix Analysis
Before fixing an error:
```bash
# Understand the error first
/speckit.error-context "error message"

# Read suggested spec sections
cat specs/001-feature/spec.md # lines 78-95

# Then fix with full context
```

### 3. Post-Fix Verification
After fixing an error:
```bash
# Fix the code
# Re-run tests
npm test

# If still failing:
/speckit.error-context "new error message"
# Get updated context
```

## Output Examples

### Simple Error
```
Error Analysis
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔴 Error: Module 'axios' not found

📋 Related Plan:
  specs/001-api-integration/plan.md:45
  "Use axios for HTTP requests"

💡 Quick Fix:
  npm install axios

✓ This is a simple dependency issue
```

### Complex Error with Spec Context
```
Error Analysis
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔴 Error: Validation failed - Email format invalid

📍 Location: src/api/users.py:123

📋 Related Requirements (3 found):

  1. REQ-012: Email Validation (relevance: 95%)
     "Email must match pattern: [a-z0-9]+@[a-z]+\.[a-z]+"
     → specs/002-user-auth/spec.md:145

  2. REQ-013: Error Messages (relevance: 68%)
     "Validation errors must be user-friendly"
     → specs/002-user-auth/spec.md:156

🔍 Spec says:
  Pattern: [a-z0-9]+@[a-z]+\.[a-z]+
  Your implementation: [a-zA-Z0-9]+@.+

🚫 Mismatch detected!
  Spec allows: lowercase only
  Code allows: mixed case

💡 Resolution Options:

  Option 1: Fix code to match spec
    → Use spec pattern exactly
    → Update validation in src/api/users.py:123

  Option 2: Update spec (if requirements changed)
    → Run /speckit.specify to update requirements
    → Regenerate tasks with /speckit.tasks

Recommendation: Option 1 (align code with spec)
```

### No Context Found
```
Error Analysis
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔴 Error: ECONNREFUSED connection to localhost:5432

📋 Related Context: None found in specifications

💡 This appears to be an infrastructure issue:
  • PostgreSQL server not running
  • Wrong port configured
  • Connection string incorrect

Check:
  1. Is PostgreSQL running? (pg_ctl status)
  2. Check plan.md for connection config
  3. Verify DATABASE_URL environment variable

This is not a specification issue.
```

## Limitations

### Current Version
- Keyword-based matching (not semantic understanding)
- Limited to text-based errors
- No learning from past errors
- Requires specifications to exist

### Future Enhancements
- ML-based error classification
- Historical error patterns
- Automatic fix suggestions
- Integration with git blame
- Stack trace analysis

## Context

{ARGS}
