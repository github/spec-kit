---
description: Bind logical assets to compatible destinations, prepare and deploy outputs, and record resumable operational evidence.
handoffs:
  - label: Test Product
    agent: speckit.test
    prompt: Run unit, integration and end-to-end tests and record defects.
scripts:
  sh: scripts/bash/workflow.sh context deployment --json
  ps: scripts/powershell/workflow.ps1 context deployment --json
  py: scripts/python/workflow_context.py deployment --json
---

## User Input

```text
$ARGUMENTS
```

## Contract

The project constitution is `.specify/memory/constitution.md` (CONSTITUTION in helper output).

Read constitution, spec, architecture, environment, plan, coding tasks/progress and
existing deployment record. Own FEATURE_DIR/deployment.md, required deployment
manifests/scripts (for example deploy/), and authorized target-environment changes.
Do not change application source, requirements, architecture, environment recommendations,
coding task definitions/progress or test files. Product defects go to taskscode/impcode.

## Procedure

1. Run `{SCRIPT}`; use PYTHON and PROGRESS_HELPER `status`. Scope deployment to components
   whose required coding tasks/dependencies are CODE_COMPLETE at the recorded revision.
   An explicit partial deployment must identify omitted components and limitations.
2. Read the existing deployment record and inspect actual destination state before
   resuming; never assume a prior side effect did not happen because a session ended.
   Record a release/commit/artifact digest and protect existing data and running services.
3. Bind environment logical asset IDs to actual available destinations using supplied
   access information. Inspect OS/version, CPU architecture, runtime, resources, storage,
   network reachability and co-location constraints. Do not substitute incompatible
   hosts or redesign the environment. If access/targets are missing, record the concrete
   requirement and stop dependent actions; no invented endpoints or deployment success.
4. Prepare a concrete execution plan in deployment.md: destination mapping, installation,
   build/acquisition, transfer, configuration, migrations, service startup, health checks
   and rollback. Reuse authorization already supplied. New purchases, destructive data
   changes or infrastructure outside the authorized target require explicit authorization;
   seek it only after the proposed actions and consequences are reviewable.
5. Within authorized scope, prepare targets, install required runtimes/dependencies,
   build/package code if needed, obtain/transfer verified outputs, configure secrets by
   reference, run reviewed migrations and launch the product. Inspect package lifecycle
   scripts so testing is not silently bundled into installation/build. Do not persist
   credentials in code, reports or command logs. Capture safe exact commands/results.
6. Save step state before and after operations. On resume, observe the resource/service
   and reconcile pending/running operations; do not blindly repeat provisioning or data
   migrations. Stop affected work on failures, preserve evidence and use the documented
   rollback when safe and authorized. Independent destinations may continue.
7. Check process health and endpoint accessibility as operational smoke checks. These
   are not unit/integration/end-to-end suites or acceptance. Suites belong to test.
8. Record actual destinations, deployed revision, installed versions, endpoints, health,
   unresolved operations and rollback state. Claim deployed only from observed evidence.
   Hand off to __SPECKIT_COMMAND_TEST__. Environment design itself never depends on this run.

## Extension boundary

Read `.specify/extensions.yml` if present. Skip `enabled: false` hooks. Offer
`optional: true` hooks without automatically executing them; invoke mandatory hooks
only within this stage's boundaries and wait for their result. Nonempty conditions
belong to HookExecutor, not ad hoc expression evaluation. Use the integration's native
command spelling when invoking a logical `speckit.*` name. Report malformed hook
configuration and any mandatory hook that cannot safely run; never claim it succeeded.

Inspect before_deployment/after_deployment hooks, their targets and effects. They must
stay within the authorized deployment and cannot silently modify source or run test
suites. Preserve the same operation log and recovery boundaries for hook actions.
