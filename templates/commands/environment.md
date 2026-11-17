---
description: Recommend OS, runtime, logical assets and minimum/recommended infrastructure from product needs.
handoffs:
  - label: Plan Implementation
    agent: speckit.plan
    prompt: Design implementation using the specification, architecture and environment.
scripts:
  sh: scripts/bash/workflow.sh context environment --json
  ps: scripts/powershell/workflow.ps1 context environment --json
  py: scripts/python/workflow_context.py environment --json
---

## User Input

```text
$ARGUMENTS
```

## Contract

The project constitution is `.specify/memory/constitution.md` (CONSTITUTION in helper output).

Own only `.specify/memory/environment.md`. Read constitution, spec and architecture,
existing environment and relevant affected feature plans. Recommend infrastructure
from product requirements, not current server inventory. No source code, tests,
implementation tasks, actual deployment, software installation, provisioning,
cloud purchases, remote configuration or service start/stop/restart.
Do not change requirements, components, languages, frameworks or protocols.

## Procedure

1. Run `{SCRIPT}` and load its inputs/template. Preserve the existing design unless
   changing it is in scope; document impact before replacing approved recommendations.
2. Derive workload, concurrency, latency, storage growth, availability and retention
   assumptions. Distinguish estimates from measurements. Do not run experiments.
3. Assign every architecture component to stable logical asset IDs. Specify asset
   counts/replicas, exact OS/version, runtime/version, minimum and recommended resource
   quantities with units, disk/storage class, networking/cloud topology and backup.
   Include client/desktop/edge components as well as services. Managed services state
   provider-managed OS and real quota dimensions instead of fictional host resources.
4. Verify compatibility from documentation: GUI/platform dependencies, instruction
   set, runtimes, database support, protocol reachability, co-location/separation and
   summed demand on shared assets. Never put a Windows-GUI-dependent component on
   Linux. Record unresolved constraints rather than changing architecture to fit inventory.
5. Write one JSON asset inventory using TEMPLATE_CONTENT plus the sizing rationale,
   topology, resource totals, supported operating limits and change impact. Actual
   hostnames, IPs, credentials and available assets are bound during deployment.
6. Run the context helper for `plan` to check the inventory structurally; this only
   reads documents and does not run the application. Completion depends on a coherent
   recommendation, never on starting servers, access credentials or tests.
7. Report path/revision, assumptions and next command __SPECKIT_COMMAND_PLAN__.

## Extension boundary

Read `.specify/extensions.yml` if present. Skip `enabled: false` hooks. Offer
`optional: true` hooks without automatically executing them; invoke mandatory hooks
only within this stage's boundaries and wait for their result. Nonempty conditions
belong to HookExecutor, not ad hoc expression evaluation. Use the integration's native
command spelling when invoking a logical `speckit.*` name. Report malformed hook
configuration and any mandatory hook that cannot safely run; never claim it succeeded.

Inspect before_environment/after_environment hooks. Execute only hooks compatible
with the read/design-only scope; defer all operational hooks to deployment. Report
invalid configuration and skipped incompatible hooks explicitly.
