---
description: "Review the architecture plan gate for code graph impact, public plan safety, and build-from-zero readiness."
---

# AI Team Plan Gate

Run this after `speckit.plan` and the native `speckit.checklist`, before
`speckit.tasks`.

## User Input

```text
$ARGUMENTS
```

## Goal

Confirm the architect-owned plan is safe to turn into developer tasks. This is
an AI Team policy overlay, not a replacement for Spec Kit's native checklist:
use `speckit.checklist` for requirements completeness and clarity, then use
this gate for code graph impact, privacy boundary, owner review, and
build-from-zero readiness.

## Steps

1. Locate the active feature directory from `.specify/feature.json`.
2. Read:
   - `.specify/ai-team/tasks/<task-id>/task-context.yml` and `context-pack.md` when
     present;
   - `spec.md`;
   - `plan.md`;
   - native checklist output when present;
   - `research.md` when present;
   - `data-model.md` and `contracts/` when present;
   - `.specify/extensions/ai-team/ai-team-config.yml` when present;
   - project architecture docs and code graph output when the work touches an
     existing project.
3. Classify the work:
   - new project from zero to one;
   - feature in existing project;
   - bug-driven plan;
   - refactor or migration.
4. For existing projects, record code graph impact:
   - owner module;
   - adjacent modules;
   - public contracts touched;
   - callers/callees;
   - reuse candidates;
   - changed nodes;
   - change radius.
5. For new projects, require a strict build plan:
   - project skeleton;
   - runnable thin slice;
   - module ownership;
   - self-test strategy;
   - dependency strategy;
   - release and operations owner when relevant.
6. Check privacy:
   - raw customer demand remains in enhancement-internal;
   - feature plans reference a coding issue, allowed handoff requirement, or
     public-safe summary;
   - public plan contains only implementation-appropriate context.
7. Write `.specify/ai-team/gates/<feature-slug>/plan-gate.md`.
8. Update the Task Context Package with plan gate status, code graph artifact,
   current phase, and next command.

## Output Shape

```markdown
# AI Team Plan Gate

- **Feature**:
- **Task ID**:
- **Context Path**:
- **Work type**: new project / existing project feature / bug-driven / refactor / migration
- **Plan status**: pass / revise / blocked
- **Work item boundary**:
- **Coding issue or handoff requirement URL**:
- **Enhancement-internal leakage check**:
- **Coding repo boundary**:

## Code Graph Impact

## Build-From-Zero Readiness

## Public/Private Boundary

## Architecture Decisions

## Required Plan Revisions

## Next Phase Conditions
```

## Stop Conditions

Stop before task generation when:

- a public plan would expose private customer demand;
- existing project impact lacks code graph or equivalent source structure
  evidence;
- a new project has no runnable thin-slice plan;
- public interfaces or cross-module semantics lack owner or architecture review.
