---
description: "Review the architecture plan gate for code graph impact, public plan safety, and build-from-zero readiness."
---

# AI Team Plan Gate

Run this after `speckit.plan` and before `speckit.tasks`.

## User Input

```text
$ARGUMENTS
```

## Goal

Confirm the architect-owned plan is safe to turn into developer tasks.

## Steps

1. Locate the active feature directory from `.specify/feature.json`.
2. Read:
   - `spec.md`;
   - `plan.md`;
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
   - raw customer demand remains in enhancement repository;
   - public plan contains only implementation-appropriate context.
7. Write `.specify/ai-team/gates/<feature-slug>/plan-gate.md`.

## Output Shape

```markdown
# AI Team Plan Gate

- **Feature**:
- **Work type**: new project / existing project feature / bug-driven / refactor / migration
- **Plan status**: pass / revise / blocked
- **Enhancement repo boundary**:
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
