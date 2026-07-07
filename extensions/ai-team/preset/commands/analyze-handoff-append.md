## AI Team Effective Spec (preset: ai-team-handoff-spec)

For cross-artifact analysis, set SPEC to the effective spec path:

1. **Preferred**: `EFFECTIVE_SPEC` from hook JSON
2. **Fallback**: `$FEATURE_DIR/spec.override.md` if present
3. **Else**: `$FEATURE_DIR/spec.md`

Analyze requirement content from the effective spec, not the URL pointer alone.

Never commit `spec.override.md`.

## AI Team Task Gate (composite — same run as analyze)

After completing the native cross-artifact analysis above, continue in this run with
the AI Team task gate.

Confirm developer-owned tasks are ready for implementation:

1. Locate the active feature directory from `.specify/feature.json`.
2. Read task context, effective spec, `plan.md`, `tasks.md`, native analyze report, work
   item URL, and AI Team handoff/plan gate files when present.
3. Verify tasks have IDs, phases, paths, and dependencies; avoid hidden product/architect
   chat context; include contract, self-test, and evidence tasks where required.
4. For new projects, ensure tasks build a runnable spine before breadth.
5. For existing projects, stay inside the plan gate impact radius unless an approved
   expansion task exists.
6. Write `.specify/ai-team/gates/<feature-slug>/task-gate.md` using this shape:

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

7. Update the Task Context Package with task gate status and next command (`speckit.implement`
   when pass).

Stop before implementation when tasks depend on hidden context, self-test/evidence tasks
are missing, or scope exceeds the approved impact radius.
