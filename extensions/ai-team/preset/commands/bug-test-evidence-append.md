## Checks

After native bug verification above, continue in this run:

1. Load `.specify/ai-team/work/<work_slug>/work-context.yml` and bug artifacts under `.specify/bugs/<bug_slug>/` when present.
2. Confirm the fix links the coding issue or approved bug slug.
3. Run repository governance, build/self-test, and boundary checks for touched areas.
4. Record skipped checks with concrete reasons.

## Evidence board

After checks, produce the evidence board for the bug fix:

1. Read work context, bug assessment/fix/test reports, implementation diff, and test results.
2. Write `.specify/ai-team/work/<work_slug>/evidence/evidence-board.md` (use `work_slug` when no feature directory exists).
3. Include linked coding issue, changed nodes, tests run, skipped checks, and failure-evolution follow-ups when review or test failures exist.
4. Update the Work Context Package and hand off to `speckit.ai-team.pr` when ready.

Stop before claiming fix success when behavior changed without self-test evidence or the coding issue anchor is missing.
