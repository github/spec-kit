---
description: "Produce an Evidence Board after implementation and record self-test, scope, and failure-evolution follow-ups."
---

# AI Team Evidence Board

Run this after `speckit.implement`, before PR submission, or after a failed
review/test/incident when evidence must be reconstructed.

## User Input

```text
$ARGUMENTS
```

## Goal

Make implementation evidence reviewable without asking humans to rediscover the
whole AI diff.

## Steps

1. Locate the active feature directory from `.specify/feature.json` when
   available.
2. Read:
   - `spec.md`, `plan.md`, `tasks.md`;
   - AI Team handoffs and gates when present;
   - implementation diff;
   - test results and self-test notes;
   - quickstart validation results when present.
3. Produce an Evidence Board:
   - linked work item;
   - published requirement URL for feature work;
   - repo role;
   - changed nodes;
   - impact radius;
   - reused components;
   - tests run;
   - uncovered paths;
   - dependency/security impact;
   - rollback or recovery note;
   - human review points;
   - skipped checks and reasons.
4. If review comments, failed tests, incidents, or repeated AI mistakes exist,
   add a Failure Evolution section:
   - context missing;
   - graph missing;
   - skill missing;
   - hook missing;
   - gate missing;
   - evidence missing;
   - human decision missing.
5. Write `.specify/ai-team/evidence/<feature-slug>/evidence-board.md`.

## Output Shape

```markdown
# AI Team Evidence Board

- **Feature**:
- **Repository role**:
- **Linked work item**:
- **Published requirement URL**:
- **Implementation status**:

## Scope and Impact

## Code Graph / Source Structure Evidence

## Self-Test Evidence

## Commands and Results

## Uncovered Paths

## Security, Dependency, and Compatibility Impact

## Rollback or Recovery

## Human Review Points

## Skipped Checks

## Failure Evolution Follow-Up
```

## Stop Conditions

Stop before claiming implementation success when:

- behavior changed but no self-test or validation evidence exists;
- feature work lacks a published requirement URL;
- changed nodes or impact radius cannot be stated;
- skipped checks have vague reasons;
- a failed review/test/incident has no follow-up owner.
