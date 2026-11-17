---
description: Design feature implementation from specification, architecture and environment without coding or test planning.
handoffs:
  - label: Generate Coding Tasks
    agent: speckit.taskscode
    prompt: Break this implementation design into coding-only tasks.
scripts:
  sh: scripts/bash/workflow.sh context plan --json
  ps: scripts/powershell/workflow.ps1 context plan --json
  py: scripts/python/workflow_context.py plan --json
---

## User Input

```text
$ARGUMENTS
```

## Contract

The project constitution is `.specify/memory/constitution.md` (CONSTITUTION in helper output).

Read constitution, spec, shared architecture/environment and existing feature design.
Own `FEATURE_DIR/plan.md` and only necessary `research.md`, `data-model.md`, `contracts/`.
No source code, complete function logic, tests, test plans, test tasks, validation
experiments, quickstart test/run guides, deployment operations or task generation.
Do not change product requirements, architecture technologies or environment assets.

## Procedure

1. Run `{SCRIPT}` and read all required inputs before writing; use TEMPLATE_CONTENT
   for a new plan. Merge updates into existing design; do not reset approved artifacts.
2. Map requirements to components and logical deployment targets. Inherit technologies,
   protocols, OS and resource constraints. A conflict goes to the owning command,
   not an invented workaround or reduced requirement.
3. Investigate existing standard solutions and compatible libraries before selecting
   implementation dependencies. Justify complexity. Make routine engineering choices
   within approved bounds without asking for approval of each minor choice.
4. Specify source structure, module boundaries, schemas, migrations, state transitions,
   validation/error handling, concurrency, security and important communication behavior.
   Define APIs with request/response types, errors, authentication and versioning.
   Do not leave essential design choices for coding or write complete function bodies.
5. Define technical dependencies and contracts that allow independent components to
   proceed. No requirement that coding await deployment, experiments, successful
   future tests or final acceptance. Acceptance criteria in the spec remain unchanged.
6. Write compact design artifacts, each with a distinct purpose. No testing section
   or testing workflow. Record input revisions, changed decisions and downstream impact.
7. Check completeness and constitution alignment by reading the artifacts. Report
   output paths and recommend __SPECKIT_COMMAND_TASKSCODE__.

## Extension boundary

Read `.specify/extensions.yml` if present. Skip `enabled: false` hooks. Offer
`optional: true` hooks without automatically executing them; invoke mandatory hooks
only within this stage's boundaries and wait for their result. Nonempty conditions
belong to HookExecutor, not ad hoc expression evaluation. Use the integration's native
command spelling when invoking a logical `speckit.*` name. Report malformed hook
configuration and any mandatory hook that cannot safely run; never claim it succeeded.

Inspect before_plan/after_plan hooks. Run only hooks respecting this command's
owned files and no-execution scope. Offer agent-context updates or commits separately;
do not silently run tests, edit source or change infrastructure via a hook.
