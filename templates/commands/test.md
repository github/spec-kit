---
description: Author and run unit, integration and end-to-end tests, record reproducible bugs and route coding fixes.
scripts:
  sh: scripts/bash/workflow.sh context test --json
  ps: scripts/powershell/workflow.ps1 context test --json
  py: scripts/python/workflow_context.py test --json
---

## User Input

```text
$ARGUMENTS
```

## Contract

The project constitution is `.specify/memory/constitution.md` (CONSTITUTION in helper output).

Read constitution, spec, architecture, environment, plan/contracts, coding tasks,
progress, application code and deployment record when relevant. Own test source,
fixtures and test-only configuration/dependencies, FEATURE_DIR/test-report.md,
FEATURE_DIR/bugs.md and scoped test evidence. Preserve application dependencies
when a manifest also holds test dependencies. Do not modify production source,
task definitions, code-progress.json, architecture, environment or deployment.
Test fixtures may change explicitly authorized disposable runtime data through the
product interface. That does not authorize editing deployment manifests, staged
application code, service configuration or the deployment record.

## Procedure

1. Run `{SCRIPT}`. Read coding status using PYTHON and PROGRESS_HELPER `status`.
   Identify the exact code revision/output digest and intended scope. Local unit and
   isolated integration tests do not require deployment; target-dependent end-to-end
   tests use the actual deployment record and compatible available test environment.
   Compare the observed deployed release/artifact identity with the intended coding
   revision before crediting target-dependent results. A stale deployment is BLOCKED
   for the new revision; results against an older release must be labeled separately.
   Incomplete code may be tested explicitly, but report that scope accurately.
2. Own test planning here: map requirements/contracts to unit, integration and end-to-end
   cases, including positive, negative, boundary, error, security and recovery behavior
   appropriate to the product. Preserve existing tests; add missing meaningful coverage.
   Do not weaken tests just to obtain a pass. Fixtures/mocks belong here, not impcode.
3. Prepare isolated test dependencies/data. Inspect commands and target before execution.
   Never run destructive tests on production or expose real credentials/data without
   explicit authorization. Missing infrastructure is BLOCKED, not a product failure
   and not permission to provision/deploy from this command.
4. Write/update tests and run unit, integration and end-to-end suites appropriate to
   scope. Use real commands and capture exit codes, counts, logs, target and revision.
   Explain not-applicable suites; unavailable/failed/skipped is never passed. Do not
   claim tests were executed from reading code or reusing stale evidence.
5. Record test-report.md incrementally, keeping previous relevant runs. In bugs.md use
   stable BUG-### IDs with severity, requirement/contract, reproduction, expected/actual,
   affected components/files, evidence and status. Deduplicate existing open findings.
6. Fix test defects only when evidence shows the test contradicts the approved contract;
   record that reasoning. Production defects require __SPECKIT_COMMAND_TASKSCODE__ to
   create coding repair tasks and __SPECKIT_COMMAND_IMPCODE__ to implement them. Then
   rerun local tests here. When the fix changes a deployed artifact, route its refresh
   through __SPECKIT_COMMAND_DEPLOYMENT__ before target-dependent retesting; do not
   redeploy from this command or credit tests of the previous release to the fix.
   Do not alter coding history or retroactively treat CODE_COMPLETE
   as a test pass. Architecture/environment defects go to their owning commands.
7. Summarize passed/failed/blocked coverage, defects and next actions. Close a bug only
   with a relevant passing reproduction at the changed code revision. Product acceptance
   is separate from coding completion and must not be fabricated by a test report.

## Extension boundary

Read `.specify/extensions.yml` if present. Skip `enabled: false` hooks. Offer
`optional: true` hooks without automatically executing them; invoke mandatory hooks
only within this stage's boundaries and wait for their result. Nonempty conditions
belong to HookExecutor, not ad hoc expression evaluation. Use the integration's native
command spelling when invoking a logical `speckit.*` name. Report malformed hook
configuration and any mandatory hook that cannot safely run; never claim it succeeded.

Inspect before_test/after_test hooks. Only testing and reporting effects within the
selected scope are allowed; no hidden production fixes, deployment or task rewriting.
