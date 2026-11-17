---
description: Generate and reconcile coding-only tasks with component targets and explicit dependencies.
handoffs:
  - label: Analyze Consistency
    agent: speckit.analyze
    prompt: Analyze all design inputs and coding tasks before coding.
scripts:
  sh: scripts/bash/workflow.sh context taskscode --json
  ps: scripts/powershell/workflow.ps1 context taskscode --json
  py: scripts/python/workflow_context.py taskscode --json
---

## User Input

```text
$ARGUMENTS
```

## Contract

The project constitution is `.specify/memory/constitution.md` (CONSTITUTION in helper output).

Read constitution, spec, architecture, environment, plan and relevant design artifacts,
existing tasks-code.md/code-progress.json and bugs.md if present. Own tasks-code.md;
only the progress helper may reconcile code-progress.json. No source changes, tests,
test generation, testing tasks, deployment tasks, installations or non-programming
tasks. Do not alter upstream requirements/design or independently choose technologies
and runtime locations.

## Procedure

1. Run `{SCRIPT}`. Read existing task definitions and progress before generation.
2. Convert every coding requirement into small, concrete source creation/integration
   tasks. Use TEMPLATE_CONTENT's single JSON inventory and required fields. Application
   configuration and migration source are coding; executing migrations, Docker/host
   setup, firewall changes, deployment scripts and testing belong to later commands.
3. Each task names requirement IDs, coding category, architecture component, environment
   asset IDs, exact source paths, dependency IDs and coding-output completion criteria.
   Quote the constraint verbatim in the task description for every relevant data-model
   field (max length, nullable/required, enum values and validation rules), using title
   or done_when. Include contract references. No tests/deployment/acceptance gates.
4. Dependencies express actual technical prerequisites. Prefer contract-based integration;
   frontend need not await all backend features. Do not order solely by server or impose
   broad phase barriers. Avoid duplicate outputs, unjustified coupling and oversized tasks.
5. Preserve IDs and unchanged definitions on regeneration. Never reuse retired IDs
   (consult progress history). Record removed/revised tasks and reasons. For bugs, add
   specific coding repair tasks linked to BUG IDs; impcode does not invent repairs.
   Do not silently reclassify testing/deployment tasks as coding when migrating tasks.md.
6. Invoke the JSON result's PYTHON executable with PROGRESS_HELPER and `validate`.
   Correct structural errors, then invoke `sync`. These helpers perform document/state
   checks only; no application code or tests run. Sync preserves unchanged progress and
   history; revised tasks/design inputs require review without deleting existing code.
7. Report task count, categories, dependency opportunities, retained progress and real
   blockers. Recommend __SPECKIT_COMMAND_ANALYZE__ then __SPECKIT_COMMAND_IMPCODE__.

## Extension boundary

Read `.specify/extensions.yml` if present. Skip `enabled: false` hooks. Offer
`optional: true` hooks without automatically executing them; invoke mandatory hooks
only within this stage's boundaries and wait for their result. Nonempty conditions
belong to HookExecutor, not ad hoc expression evaluation. Use the integration's native
command spelling when invoking a logical `speckit.*` name. Report malformed hook
configuration and any mandatory hook that cannot safely run; never claim it succeeded.

Inspect before_taskscode/after_taskscode hooks. Execute only scope-compatible hooks.
Never invoke legacy tasks/implement hooks as aliases: their contracts include testing.
Report incompatible hooks and malformed configuration.
