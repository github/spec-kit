---
description: View clarification history and decisions made for a feature specification
scripts:
  sh: scripts/bash/clarify-history.sh --json
  ps: scripts/powershell/clarify-history.ps1 -Json
---

## User Input

```text
$ARGUMENTS
```

You **MUST** parse feature name/number from `$ARGUMENTS` if provided, otherwise use current feature.

## Goal

Display all clarification sessions and their Q&A history for a feature specification, helping track decisions made over time and ensuring consistency.

## Execution Steps

### 1. Determine Target Feature

If `$ARGUMENTS` contains a feature name or number:
- Parse it (e.g., "001", "task-management", "001-task-management")
- Find matching feature directory

Otherwise:
- Detect current feature from git branch (same logic as other commands)

### 2. Run Clarify History Script

Execute `{SCRIPT}` which will:
- Locate the feature's spec.md
- Extract all `## Clarifications` sections
- Parse session dates and Q&A pairs
- Return structured JSON

Expected JSON output:
```json
{
  "feature": "001-task-management",
  "spec_file": "specs/001-task-management/spec.md",
  "total_sessions": 2,
  "total_questions": 7,
  "sessions": [
    {
      "date": "2025-11-05",
      "questions": 3,
      "qa_pairs": [
        {
          "question": "How should concurrent task updates be handled?",
          "answer": "Last-write-wins with conflict detection"
        },
        {
          "question": "What is the maximum task description length?",
          "answer": "5000 characters"
        }
      ]
    },
    {
      "date": "2025-11-07",
      "questions": 4,
      "qa_pairs": [...]
    }
  ],
  "topics": {
    "data_model": 3,
    "concurrency": 2,
    "validation": 2
  }
}
```

### 3. Display Clarification History

Present the history in an organized, scannable format:

```
Clarification History: 001-task-management
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Summary:
  Total Sessions: 2
  Total Questions: 7
  Spec File: specs/001-task-management/spec.md

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Session 1: 2025-11-05 (3 questions)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Q1: How should concurrent task updates be handled?
→  Last-write-wins with conflict detection

Q2: What is the maximum task description length?
→  5000 characters

Q3: Should tasks support rich text formatting?
→  Yes, Markdown only

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Session 2: 2025-11-07 (4 questions)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Q1: What authentication method for task API?
→  JWT Bearer tokens

Q2: Rate limiting for task creation?
→  100 tasks/hour per user

Q3: Support for task attachments?
→  Yes, max 10MB per file

Q4: Task deletion: soft or hard delete?
→  Soft delete with 30-day retention

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 Topics Covered:
  • Data Model: 3 questions
  • Concurrency: 2 questions
  • Validation: 2 questions

💡 Quick Ref:
  • Task length: 5000 chars
  • Attachments: max 10MB
  • Rate limit: 100/hour
  • Delete: soft, 30-day retention
  • Concurrent updates: last-write-wins
```

### 4. Cross-Reference with Spec

Optionally verify that all clarifications are still reflected in the spec:

```
Verification:
✓ All 7 clarifications found in spec.md
✓ No orphaned Q&A entries (all integrated)
```

If any clarifications are NOT reflected in the spec sections:
```
⚠️  Potential Issues:
  • Session 2025-11-07, Q2 (rate limiting): Not found in Non-Functional Requirements

  Recommendation: Re-run /speckit.clarify to re-integrate
```

### 5. Search Capability

If `$ARGUMENTS` contains keywords like "search" or "find":
```bash
/speckit.clarify-history search "authentication"
```

Filter and show only relevant Q&A:
```
Search Results: "authentication"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Session 2025-11-07:
Q1: What authentication method for task API?
→  JWT Bearer tokens

Found in: Non-Functional Requirements (line 145)
```

## Common Use Cases

### Review All Decisions
```bash
/speckit.clarify-history
# Shows complete history for current feature
```

### Check Specific Feature
```bash
/speckit.clarify-history 003-user-auth
# Shows history for feature 003
```

### Search for Decision
```bash
/speckit.clarify-history search "rate limit"
# Finds all Q&A about rate limiting
```

### Verify Integration
```bash
/speckit.clarify-history verify
# Checks that all clarifications are in spec
```

## Output Variations

### No Clarifications Yet
```
Clarification History: 001-task-management
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

No clarification sessions found.

The spec.md file does not contain a ## Clarifications section.

Recommendation: Run /speckit.clarify to identify ambiguities
```

### Single Session
```
Clarification History: 001-task-management
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Session 2025-11-07 (5 questions)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[Q&A list...]

All clarifications integrated into spec.
```

## Integration with Workflow

### Before Planning
```bash
# Review what was decided
/speckit.clarify-history

# Then proceed to planning
/speckit.plan
```

### During Implementation
```bash
# Quick check of a decision
/speckit.clarify-history search "validation"

# Reference the answer in code comments
```

### Cross-Feature Consistency
```bash
# Compare decisions across features
/speckit.clarify-history 001-tasks
/speckit.clarify-history 002-projects

# Ensure consistent patterns (e.g., all use JWT)
```

## Benefits

1. **Decision Tracking**: Never lose context on why something was decided
2. **Consistency**: Ensure similar questions get similar answers across features
3. **Onboarding**: New team members can see reasoning behind decisions
4. **Audit Trail**: Track when decisions were made and by whom
5. **Verification**: Catch cases where clarifications weren't integrated

## Context

{ARGS}
