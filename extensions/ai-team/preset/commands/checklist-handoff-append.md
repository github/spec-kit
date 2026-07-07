## AI Team Effective Spec (preset: ai-team-handoff-spec)

When loading feature context for checklist generation:

1. **Preferred**: `EFFECTIVE_SPEC` from `speckit.ai-team.handoff-spec.resolve` hook JSON
2. **Fallback**: `$FEATURE_DIR/spec.override.md` when present
3. **Else**: `$FEATURE_DIR/spec.md`

Never commit `spec.override.md`.

## AI Team Plan Gate (composite — same run as checklist)

After completing the native requirements-quality checklist above, continue in this
run with the AI Team plan gate.

Confirm the architect-owned plan is safe to turn into developer tasks:

1. Locate the active feature directory from `.specify/feature.json`.
2. Read task context, effective spec, `plan.md`, native checklist output, `research.md`,
   `data-model.md`, `contracts/`, `ai-team-config.yml`, and code graph output when
   the work touches an existing project.
3. Classify the work: new project / existing feature / bug-driven / refactor / migration.
4. For existing projects, record code graph impact (owner module, contracts, callers/callees,
   reuse candidates, changed nodes, change radius).
5. For new projects, require build-from-zero readiness (skeleton, thin slice, module
   ownership, self-test strategy, dependency strategy, release owner when relevant).
6. Check privacy: no raw customer demand in public plans; feature plans link a coding
   issue, allowed handoff requirement, or public-safe summary; `spec.override.md` stays
   gitignored when it holds internal handoff context.
7. Write `.specify/ai-team/gates/<feature-slug>/plan-gate.md` using this shape:

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

8. Update the Task Context Package with plan gate status and next command (`speckit.tasks`
   when pass).

Stop before task generation when a public plan would expose private demand, existing-project
impact lacks code graph evidence, a new project has no runnable thin-slice plan, or public
interfaces lack owner review.
