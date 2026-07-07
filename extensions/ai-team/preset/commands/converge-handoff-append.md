## AI Team Effective Spec (preset: ai-team-handoff-spec)

For converge, read the effective spec as the requirement source:

1. **Preferred**: `EFFECTIVE_SPEC` from hook JSON
2. **Fallback**: `$FEATURE_DIR/spec.override.md` if present
3. **Else**: `$FEATURE_DIR/spec.md`

Do not modify `spec.md`, `spec.override.md`, or `plan.md` during converge.

Never commit `spec.override.md`.

## AI Team Checks (composite — after native converge)

After native converge completes, continue in this run with portable checks:

| Level | When | Evidence |
|---|---|---|
| repository governance | every PR | no private requirement leakage, no local AI scratch files |
| project build | source or tests changed | project build command from docs or profile |
| developer self-test | behavior changed | affected unit/self-tests and self-test map |
| contract or boundary | SPI/API, config, schema, cross-module behavior | code graph impact and contract tests when available |
| release scoped | release notes, deployment, dependency/security impact | release verification or explicit deferral |

1. Identify repository role and load task context when present.
2. Confirm feature work links the correct coding issue or allowed handoff requirement.
3. Run governance, build/self-test, and boundary checks for touched areas.
4. Record skipped checks with concrete reasons and update the Task Context Package.

## AI Team Evidence Board (composite — same run as converge)

After checks (or when checks are skipped with documented reasons), produce the Evidence
Board in this run:

1. Read task context, effective spec, plan/tasks, handoffs, gates, implementation diff,
   native converge output, and test results.
2. Write `.specify/ai-team/evidence/<feature-slug>/evidence-board.md` using this shape:

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

3. Update the Task Context Package with evidence path and next command (`speckit.ai-team.pr`
   when ready).

Stop before claiming implementation success when behavior changed without self-test evidence,
feature work lacks a work item anchor, or skipped checks have vague reasons.
