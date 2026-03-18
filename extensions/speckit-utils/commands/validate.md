---
description: "Verify spec-to-task traceability and check that completed tasks produced expected files"
---

## User Input

```text
$ARGUMENTS
```

## Outline

Deterministically verify that the implementation matches the specification by checking task completion, file existence, and requirement traceability.

### Step 1: Select feature

If `$ARGUMENTS` specifies a feature name or number, use that. Otherwise, find the most recently modified feature in `specs/`.

If no features exist, error: "No features found in specs/. Run `/speckit.specify` first."

### Step 2: Parse tasks

Read `tasks.md` from the feature directory. Parse each checkbox line:
- Extract task text (after `- [x]` or `- [ ]`)
- Mark as completed or remaining
- Extract keywords: file paths (`auth/login.py`), snake_case names (`user_auth`), CamelCase names (`UserAuth`), dotted names (`config.yaml`)

If no `tasks.md` exists, error: "No tasks.md found. Run `/speckit.tasks` first."

### Step 3: Verify completed task artifacts

For each completed task that references file paths:
1. Search the project directory for the referenced file
2. If found: PASS
3. If not found: WARN ("task says 'Create auth/login.py' but file not found")

Skip verification for:
- Incomplete tasks (not yet implemented)
- Tasks with no file path references (e.g., "Set up CI pipeline")

### Step 4: Parse spec requirements

Read `spec.md` from the feature directory. Extract items from the "Functional Requirements" section (bulleted list items under that heading).

If no requirements section found, skip to Step 6.

### Step 5: Trace requirements to tasks

For each requirement, search task descriptions for matching keywords:
- Tokenize the requirement into significant words (skip stop words)
- Check each task's text for overlap (2+ matching keywords = traced)

Report:
- Requirement with matching tasks: PASS ("traced to Task N")
- Requirement with no matching tasks: WARN ("no task found for this requirement")

### Step 6: Report

Output a validation report:

```
Validation Report: 001-auth
============================

Task Completion: 3/5 (60%)
  [x] Task 1: Create auth/login.py      -> auth/login.py FOUND
  [x] Task 2: Add password hashing      -> (no file reference)
  [x] Task 3: Write auth tests          -> tests/test_auth.py FOUND
  [ ] Task 4: Add rate limiting         -> (not yet implemented)
  [ ] Task 5: Update API docs           -> (not yet implemented)

Requirement Traceability: 3/3
  "Users can log in with email"          -> Task 1 (PASS)
  "Passwords are stored securely"        -> Task 2 (PASS)
  "Users can reset password via email"   -> (no matching task - WARN)

Summary: 2 PASS, 1 WARN, 0 FAIL
```

If `$ARGUMENTS` includes `--strict`, treat any WARN as FAIL and report a non-zero exit status.
