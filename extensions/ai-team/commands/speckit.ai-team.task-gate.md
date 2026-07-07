---
description: "Review generated tasks for phase isolation, self-test mapping, existing-project impact, and new-project build-plan completeness."
---

# AI Team Task Gate

Run this after `speckit.tasks` and the native `speckit.analyze`, before
`speckit.implement`.

## User Input

```text
$ARGUMENTS
```

## Goal

Confirm developer-owned tasks are ready for implementation without relying on
hidden context from product or architecture roles. This is an AI Team policy
overlay, not a replacement for Spec Kit's native analysis: use
`speckit.analyze` for spec/plan/task consistency, then use this gate for owner,
self-test, evidence, and impact-radius obligations.

## Steps

1. Locate the active feature directory from `.specify/feature.json`.
2. Read:
   - `.specify/ai-team/tasks/<task-id>/task-context.yml` and `context-pack.md` when
     present;
   - `spec.md`;
   - `plan.md`;
   - `tasks.md`;
   - native analyze report when present;
   - the coding issue or handoff requirement URL referenced by the feature;
   - AI Team handoff and plan gate files when present.
3. Verify tasks:
   - each task has an ID, phase, file path, and dependency position;
   - tasks are ordered by SDD phase and user story where applicable;
   - no task requires hidden product or architect chat context;
   - public interface changes have contract or compatibility tasks;
   - feature implementation tasks link the coding issue, allowed handoff
     requirement, or approved task ID;
   - self-test tasks exist for changed behavior;
   - evidence tasks exist before PR submission.
4. For new projects, ensure tasks create a runnable spine before breadth:
   - repository skeleton;
   - build command;
   - minimal executable path;
   - first self-test;
   - docs for how to run.
5. For existing projects, ensure tasks stay inside the plan gate's impact
   radius unless an owner-approved expansion task is present.
6. Write `.specify/ai-team/gates/<feature-slug>/task-gate.md`.
7. Update the Task Context Package with task gate status, task artifact path,
   current phase, and next command.

## Output Shape

```markdown
# AI Team Task Gate

- **Feature**:
- **Task ID**:
- **Context Path**:
- **Coding issue or handoff requirement URL**:
- **Task status**: pass / revise / blocked
- **Context isolation**: pass / fail
- **New-project strict build plan**: pass / not applicable / fail
- **Existing-project impact radius**: local / module / cross-module / architecture / not applicable

## Missing Tasks

## Self-Test Mapping

## Evidence Tasks

## Scope Risks

## Implementation Entry Conditions
```

## Stop Conditions

Stop before implementation when:

- tasks depend on hidden chat context;
- feature tasks use only a local file path instead of a coding issue, handoff
  requirement, or approved task ID;
- self-test or evidence tasks are missing for behavior changes;
- new-project tasks do not produce a runnable thin slice early;
- existing-project tasks exceed the approved impact radius.
