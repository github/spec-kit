---
description: Analyze requirements, architecture, environment, implementation design and coding dependencies; write only its report.
scripts:
  sh: scripts/bash/workflow.sh context analyze --json
  ps: scripts/powershell/workflow.ps1 context analyze --json
  py: scripts/python/workflow_context.py analyze --json
---

## User Input

```text
$ARGUMENTS
```

## Contract

The project constitution is `.specify/memory/constitution.md` (CONSTITUTION in helper output).

**Read-only with respect to input documents.** Own only FEATURE_DIR/analysis.md.
Do not fix source inputs, change checkboxes, update the feature pointer or progress,
run application code/tests, or deploy. Never automatically remediate findings in this run.

## Procedure

1. Run `{SCRIPT}` for paths and report template. If required inputs are missing,
   report the actual missing files; do not invent them. The helper performs no writes.
2. Read constitution, spec, architecture, environment, plan, tasks-code.md and referenced
   research/model/contracts. Read existing analysis only to preserve finding IDs.
3. Invoke PYTHON with PROGRESS_HELPER `validate`; include validation errors as findings
   rather than editing inputs. Check semantic issues that the helper cannot decide:
   requirement coverage, invented features, unnecessary complexity, protocol/API drift,
   OS/runtime incompatibility, sizing assumptions, asset placement, incomplete contracts,
   duplicate/oversized tasks, dependency cycles, unnecessary coupling and missing code.
4. Trace requirements through components, assets, design and coding tasks. Verify every
   task has a target and code-output criterion. Flag testing/deployment work or gates in
   taskscode, and test plans inside plan. Business outcomes do not become coding tasks.
5. Constitution conflicts are CRITICAL; contradictions, missing required implementation
   and incompatible placement are HIGH; ambiguity/coverage gaps are severity-rated by
   impact. Do not dilute the constitution. Route conflicting TDD/process rules to an
   explicit constitution amendment, without changing them here.
6. Write analysis.md with stable IDs, severity, precise file/section, evidence/reason and
   recommended owner/action. Include coverage and dependency summary. Cap detail at 50
   findings plus an overflow summary; preserve unresolved finding IDs on repeat runs.
7. Report the result and next actions. A clean document review does not prove correct
   code, working infrastructure or passing tests. Critical design issues require the
   owning command to resolve them before affected coding can proceed.

## Extension boundary

Read `.specify/extensions.yml` if present. Skip `enabled: false` hooks. Offer
`optional: true` hooks without automatically executing them; invoke mandatory hooks
only within this stage's boundaries and wait for their result. Nonempty conditions
belong to HookExecutor, not ad hoc expression evaluation. Use the integration's native
command spelling when invoking a logical `speckit.*` name. Report malformed hook
configuration and any mandatory hook that cannot safely run; never claim it succeeded.

Do not run hooks that mutate inputs, state, Git or remote systems. Only read-only
before_analyze/after_analyze hooks can run in this command; report other hooks as
separate follow-up actions. The report remains the sole writable output.
