## Handoff spec

When loading requirement content, prefer `$FEATURE_DIR/spec.override.md` if it exists; do not use a handoff URL in `spec.md` as the requirement body.

If `spec.md` is a remote handoff pointer and `spec.override.md` is missing, stop and re-run `speckit.plan` or `speckit.ai-team.handoff-spec-sync` before continuing.

{CORE_TEMPLATE}

## Checks

After native converge completes (Phase 1), continue in this run with portable checks (Phase 2). Phase 1 rules still apply: append-only to `tasks.md`; do not modify `spec.md`, `spec.override.md`, or `plan.md`.

| Level | When | Evidence |
|---|---|---|
| repository governance | every PR | no private requirement leakage, no local AI scratch files |
| project build | source or tests changed | project build command from docs or profile |
| developer self-test | behavior changed | affected unit/self-tests and self-test map |
| contract or boundary | SPI/API, config, schema, cross-module behavior | code graph impact and contract tests when available |
| release scoped | release notes, deployment, dependency/security impact | release verification or explicit deferral |

1. Identify repository role and load work context when present.
2. Confirm feature work links the correct coding issue or allowed handoff requirement.
3. Compare changed files with `plan.md#change-scope`; any unplanned path is a
   deviation and blocks success until recorded and reviewed.
4. When architecture impact was required, generate the post-change Code Graph
   or source-structure evidence and compare it with every `ARCH-*` expectation.
5. Detect public contract or default-behavior changes from API/SPI, config,
   wire/data shapes, examples, golden files, and snapshots. Require an owner
   decision only when the result is incompatible or behavior-changing.
6. Run governance, build/self-test, and boundary checks for touched areas.
7. Record skipped checks with concrete reasons and update the Work Context Package.

## Evidence board

After checks (or when checks are skipped with documented reasons), produce the evidence board in this run:

1. Read work context, `spec.override.md` or `spec.md`, plan/tasks, handoffs, gates, implementation diff, native converge output, and test results.
2. Write `.specify/ai-team/work/<work_slug>/evidence/evidence-board.md`:

```markdown
# Evidence Board

- **Feature**:
- **Task ID**:
- **Context Path**:
- **Repository role**:
- **Linked work item**:
- **Primary coding issue or handoff requirement URL**:
- **Also resolves coding issues**:
- **Implementation status**:

## Scope and Impact

## Code Graph / Source Structure Evidence

## Planned vs As-Built Architecture

| Plan delta | Expected | Actual | Result / deviation |
|---|---|---|---|

## Work Item Verification

| Work item | Symptom or behavior | Test/evidence | Result |
|---|---|---|---|

## Self-Test Evidence

## Commands and Results

## Uncovered Paths

## Security, Dependency, and Compatibility Impact

## Rollback or Recovery

## Human Review Points

## Skipped Checks

## Failure Evolution Follow-Up
```

3. Update the Work Context Package with evidence path and next command (`speckit.ai-team.pr` when ready).

Stop before claiming implementation success when behavior changed without
self-test evidence, a linked work item lacks its own verification mapping,
actual paths exceed the planned scope, required architecture comparison is
missing, or skipped checks have vague reasons.
