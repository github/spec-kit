## AI Team Checks (composite — after native bug test)

After completing native bug verification above, continue in this run with portable
checks for the bug fix:

1. Load `.specify/ai-team/tasks/<task-id>/task-context.yml` and bug artifacts under
   `.specify/bugs/<bug_slug>/` when present.
2. Confirm the fix links the coding issue or approved bug slug.
3. Run repository governance, build/self-test, and boundary checks for touched areas.
4. Record skipped checks with concrete reasons.

## AI Team Evidence Board (composite — same run as bug test)

After checks, produce the Evidence Board for the bug fix:

1. Read task context, bug assessment/fix/test reports, implementation diff, and test results.
2. Write `.specify/ai-team/evidence/<bug_slug>/evidence-board.md` (use `bug_slug` when no
   feature directory exists).
3. Include linked coding issue, changed nodes, tests run, skipped checks, and failure-evolution
   follow-ups when review or test failures exist.
4. Update the Task Context Package and hand off to `speckit.ai-team.pr` when ready.

Stop before claiming fix success when behavior changed without self-test evidence or the
coding issue anchor is missing.
