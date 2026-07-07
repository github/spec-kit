---
description: "Assess whether the architecture plan is ready for task generation (chat report only)."
---

# AI Team Plan Check

Review the plan after `speckit.plan`. Output a chat report only — do **not** write
`plan-check.md`, checklist files, or modify `spec.md`, `spec.override.md`, or `plan.md`.

## User Input

```text
$ARGUMENTS
```

## Handoff spec

When loading requirement content, prefer `$FEATURE_DIR/spec.override.md` if it exists;
do not use a handoff URL in `spec.md` as the requirement body.

## Goal

Confirm the architect-owned plan is safe to turn into developer tasks. The human
`review-plan` workflow gate uses this report to approve, revise, or reject.

## Steps

1. Locate the active feature directory from `.specify/feature.json`.
2. Read work context, `spec.override.md` or `spec.md`, `plan.md`, `research.md`,
   `data-model.md`, `contracts/`, `ai-team-config.yml`, code graph and impact
   artifacts from `.specify/ai-team/work/<work_slug>/work-context.yml` when present.
3. Classify the work: new project / existing feature / bug-driven / refactor / migration.
4. For existing projects, assess code graph impact (owner module, contracts,
   callers/callees, reuse candidates, changed nodes, change radius).
5. For new projects, assess build-from-zero readiness (skeleton, thin slice, module
   ownership, self-test strategy, dependency strategy, release owner when relevant).
6. Check privacy: no raw customer demand in public plans; feature plans link a coding
   issue, allowed handoff requirement, or public-safe summary.
7. Output the **Plan Check Report** in chat (structure below).
8. Update `.specify/ai-team/work/<work_slug>/work-context.yml` with:

```yaml
plan_check:
  status: pass | revise | blocked
  change_radius: local | module | cross-module | architecture | not-applicable
  work_type: new-project | existing-project-feature | bug-driven | refactor | migration
  summary: "<one-line conclusion>"
```

Also append a short **Plan Check** section to `context-pack.md` with status, change
radius, and required revisions (no separate check markdown file).

9. Set `phase: planned`, `last_completed_command: speckit.ai-team.plan-check`, and
   `next_command: speckit.tasks` when status is `pass`, otherwise `speckit.plan`.

## Plan Check Report (chat output)

```markdown
## Plan Check Report

- **Feature**:
- **Task ID**:
- **Work type**:
- **Plan status**: pass / revise / blocked
- **Change radius**: local / module / cross-module / architecture / not applicable
- **Work item boundary**:
- **Coding issue or handoff requirement URL**:

### Code Graph Impact

### Build-From-Zero Readiness

### Public/Private Boundary

### Architecture Decisions

### Required Plan Revisions

### Recommended Next Step

Run `speckit.plan` to revise, or proceed to `speckit.tasks` when pass and the human
review-plan gate approves.
```

## Stop Conditions

Recommend **blocked** or **revise** (do not claim pass) when:

- a public plan would expose private demand;
- existing-project impact lacks code graph evidence;
- a new project has no runnable thin-slice plan;
- public interfaces lack owner review.

Wait for the human `review-plan` gate before task generation when status is not pass.
