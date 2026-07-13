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
`review-plan` gate uses this report in Standard mode; the combined
`review-compact-plan-tasks` gate uses it with native analyze in Compact mode.

## Steps

1. Locate the active feature directory from `.specify/feature.json`.
2. Read the work context, Permission Envelope,
   `spec.override.md` or `spec.md`, `plan.md`, `research.md`, `data-model.md`,
   `contracts/`, `ai-team-config.yml`, code graph and impact artifacts from
   `.specify/ai-team/work/<work_slug>/` when present.
3. Classify the work: new project / existing feature / bug-driven / refactor / migration.
4. For existing projects, assess code graph impact (owner module, contracts,
   callers/callees, reuse candidates, changed nodes, change radius).
   Confirm `plan.md` states allowed paths and numbered expected architecture
   deltas for cross-module changes, API/SPI changes, config or wire/data shape
   changes, and class add/delete. `None` is valid only with supporting evidence.
5. For new projects, assess build-from-zero readiness (skeleton, thin slice, module
   ownership, self-test strategy, dependency strategy, release owner when relevant).
6. Derive the implementation permission request from the plan: intended write
   paths, commands, network access, dependency changes, generated files, and
   approval categories. Flag broad or unspecified access for revision; do not
   grant access in this command.
7. Check privacy: no raw customer demand in public plans; feature plans link a coding
   issue, allowed handoff requirement, or public-safe summary.
8. Check compatibility: the plan defaults to forward-compatible,
   behavior-preserving change. If API/SPI or contract diffs, config defaults,
   wire/data shapes, examples, golden files, or snapshots indicate an
   incompatible behavior change, require owner decision, migration, and
   rollback details. A bug fix that restores the documented contract is not by
   itself an incompatible change.
9. Output the **Plan Check Report** in chat (structure below).
10. Update `.specify/ai-team/work/<work_slug>/work-context.yml` with:

```yaml
plan_check:
  status: pass | revise | blocked
  change_radius: local | module | cross-module | architecture | not-applicable
  work_type: new-project | existing-project-feature | bug-driven | refactor | migration
  summary: "<one-line conclusion>"
```

Also append a short **Plan Check** section to `context-pack.md` with status, change
radius, and required revisions (no separate check markdown file).

11. Update `work-context.yml` with the plan and plan-check status. Record the
    planned implementation access in `permission-envelope.yml` as requested,
    not approved, unless an accountable human has explicitly approved it.
12. Set `phase: planned`, `last_completed_command: speckit.ai-team.plan-check`, and
   `next_command: speckit.tasks` when status is `pass`, otherwise `speckit.plan`.

## Plan Check Report (chat output)

```markdown
## Plan Check Report

- **Feature**:
- **Task ID**:
- **Work type**:
- **Planning mode**: standard / compact
- **Plan status**: pass / revise / blocked
- **Change radius**: local / module / cross-module / architecture / not applicable
- **Work item boundary**:
- **Coding issue or handoff requirement URL**:

### Code Graph Impact

### Build-From-Zero Readiness

### Public/Private Boundary

### Architecture Decisions

### Expected Architecture Deltas And Allowed Paths

### Compatibility

### Planned Permission Boundary

- Intended write paths:
- Commands and network access:
- Required approvals:
- Enforcement mode and gaps:

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
- the plan omits allowed paths or required expected architecture deltas;
- an incompatible public contract or default-behavior change lacks owner
  decision, migration, or rollback details;
- implementation access is broad, unspecified, or inconsistent with the plan;
- the plan requires hard runtime confinement but only `policy-only`
  enforcement is available.

In Standard mode, wait for the human `review-plan` gate before task generation
when status is not pass. In Compact mode, continue only to generate draft tasks
for the combined review; do not begin implementation before
`review-compact-plan-tasks` approves both artifacts.
