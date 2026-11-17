---
description: Design system components, technologies and communication without selecting deployment infrastructure.
handoffs:
  - label: Design Runtime Environment
    agent: speckit.environment
    prompt: Recommend the runtime environment for this architecture.
scripts:
  sh: scripts/bash/workflow.sh context architecture --json
  ps: scripts/powershell/workflow.ps1 context architecture --json
  py: scripts/python/workflow_context.py architecture --json
---

## User Input

```text
$ARGUMENTS
```

## Contract

The project constitution is `.specify/memory/constitution.md` (CONSTITUTION in helper output).

Own only `.specify/memory/architecture.md`. Read constitution, current spec, existing
architecture/environment and affected prior feature designs as needed. This is the
architecture of the whole product, not an isolated redesign for every feature.
Do not edit requirements, infrastructure, plans, tasks, application code or tests.
Do not select particular operating systems, servers, cloud assets or hardware
resources. Do not implement, install, deploy, start services or run tests.

## Procedure

1. Run `{SCRIPT}` once. Parse absolute artifact paths and TEMPLATE_CONTENT. Read
   existing architecture before writing. Missing required inputs are a real blocker.
2. Derive component responsibilities from approved requirements and constitution.
   Retain stable component IDs. Reuse existing components and standard solutions
   where suitable; justify additional queues, caches, services or abstraction layers.
3. Investigate compatible languages, frameworks, databases, versions, protocols and
   standard libraries. Cite sources and distinguish verified constraints from assumptions.
4. Describe interfaces, trust boundaries, communication direction, formats, errors,
   retries, durability and required co-location/separation. Capability requirements
   such as GUI access constrain later placement but do not select an OS here.
5. Write the architecture using the template, with exactly one JSON component
   inventory. Preserve prior decisions outside the requested change; record reasons,
   alternatives and impact of changed decisions and list downstream artifacts for review.
6. Review requirement coverage, compatibility, unnecessary complexity and constitution
   alignment. Resolve routine choices without repeated approval questions. Report
   material missing product constraints instead of inventing features.
7. Report path/revision, changed decisions and next command __SPECKIT_COMMAND_ENVIRONMENT__.

## Extension boundary

Read `.specify/extensions.yml` if present. Skip `enabled: false` hooks. Offer
`optional: true` hooks without automatically executing them; invoke mandatory hooks
only within this stage's boundaries and wait for their result. Nonempty conditions
belong to HookExecutor, not ad hoc expression evaluation. Use the integration's native
command spelling when invoking a logical `speckit.*` name. Report malformed hook
configuration and any mandatory hook that cannot safely run; never claim it succeeded.

Inspect configured before_architecture/after_architecture hooks before executing
them. A hook must obey this command's file and execution boundaries. Offer out-of-scope
hooks as separate follow-up work; never let a hook silently expand this run. Invalid
hook configuration must be reported, not treated as successful hook execution.
