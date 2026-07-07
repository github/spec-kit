---
description: "Produce an Evidence Board after implementation and record self-test, scope, and failure-evolution follow-ups."
---

# AI Team Evidence Board

Run this after `speckit.implement`, native `speckit.converge`, and
`speckit.ai-team.checks`, before PR submission, or after a failed
review/test/incident when evidence must be reconstructed.

## User Input

```text
$ARGUMENTS
```

## Goal

Make implementation evidence reviewable without asking humans to rediscover the
whole AI diff. This Evidence Board aggregates native SDD artifacts, converge
results, portable check output, code graph impact, and AI Team policy gates; it
does not replace `speckit.converge`.

## Steps

1. Locate the active feature directory from `.specify/feature.json` when
   available.
2. Read:
   - `.specify/ai-team/tasks/<task-id>/task-context.yml` and `context-pack.md` when
     present;
   - `spec.override.md` when present, otherwise `spec.md`;
   - `plan.md`, `tasks.md`;
   - AI Team handoffs and gates when present;
   - implementation diff;
   - native converge output when present;
   - test results and self-test notes;
   - quickstart validation results when present.
3. Produce an Evidence Board:
   - linked work item;
   - coding issue or handoff requirement URL for feature work;
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
   - whether `spec.override.md` was used and confirmed ignored by git.
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
6. Update the Task Context Package with evidence artifact path, skipped checks,
   current phase, and next command.

## Output Shape

```markdown
# AI Team Evidence Board

- **Feature**:
- **Task ID**:
- **Context Path**:
- **Repository role**:
- **Linked work item**:
- **Coding issue or handoff requirement URL**:
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
- feature work lacks a coding issue, handoff requirement, or approved task ID;
- changed nodes or impact radius cannot be stated;
- skipped checks have vague reasons;
- a failed review/test/incident has no follow-up owner.
