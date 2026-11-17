---
description: Complete coding tasks without writing or running tests, with durable progress and bounded retries.
handoffs:
  - label: Deploy Product
    agent: speckit.deployment
    prompt: Deploy the completed coding outputs to compatible authorized targets.
scripts:
  sh: scripts/bash/workflow.sh context impcode --json
  ps: scripts/powershell/workflow.ps1 context impcode --json
  py: scripts/python/workflow_context.py impcode --json
---

## User Input

```text
$ARGUMENTS
```

## Contract

The project constitution is `.specify/memory/constitution.md` (CONSTITUTION in helper output).

Execute programming tasks from tasks-code.md. Own only their application source
paths and code-progress.json through the helper. Read constitution, spec, architecture,
environment, plan/contracts, analysis and existing task/progress/source files.
Do not edit specification/design, task definitions, completion criteria, dependencies,
test files, deployment files or unrelated working code. Never add tasks here.

**No tests:** do not run unit, integration, end-to-end, native or cloud tests. Do not
write, create or edit test files, fixtures or test configuration. Do not deploy,
connect to real servers to run applications, install remote dependencies, change
cloud/OS resources or start/stop services. No acceptance/deployment/testing prerequisites
may be added to coding completion. Test success is never a CODE_COMPLETE criterion.

Build, compile, type-check and lint are **off by default**. They may run only when
the user explicitly allows the specific local check and its inspected invocation
cannot execute tests, application startup, install hooks or deployment. Do not infer
permission from a task named "validate". Static reading/diff inspection and the
progress helper are allowed. No hidden test execution through hooks or package scripts.

## Resume and execute

1. Run `{SCRIPT}` and load its required paths. Invoke the returned PYTHON executable
   with PROGRESS_HELPER and `status` using an argument array. Do not recreate or reset
   existing state. Missing/stale state routes to __SPECKIT_COMMAND_TASKSCODE__ and
   `sync`; do not fabricate a new progress file or redo every task.
2. Inspect analysis findings and source paths relevant to the next ready tasks.
   Preserve working code and user edits. Important contradictions or missing essential
   design block affected tasks and are reported to the owning command; continue all
   independent tasks. Unchecked reviewer checklists or future tests are not coding gates.
3. Choose from `ready`, respecting actual dependencies and shared-file serialization.
   Resume interrupted work first; retry a blocked task only when a concrete correction exists.
   Use `start --task T001` before editing. An IN_PROGRESS task resumes the same attempt;
   inspect partial changes before continuing. Do not restart merely because the session
   changed. NEEDS_REVIEW means inspect existing code against current contracts, not erase it.
4. Implement the complete task using the approved technologies and interfaces. At the
   beginning of **every code file written or modified**, add/update a language-valid
   comment naming Component, logical Deployment assets and Task IDs, for example:

   ```text
   # Component: API; Deployment assets: APP01; Tasks: T001, T004
   ```

   Preserve mandatory shebang, encoding declarations, license notices and language
   directives; put metadata at the earliest legal comment position. Shared files list
   all applicable components/assets/tasks. Use logical assets, never invented physical
   hostnames or secrets. Non-code formats that forbid comments (JSON, lockfiles, binary
   assets) keep ownership in tasks-code.md/progress; never corrupt their syntax to insert
   a header. Generated code needs generator-supported headers; record a genuine blocker
   if the required code-file header cannot be emitted safely.
5. Inspect the written code and integration against done_when and contract requirements.
   No TODO stubs, NotImplementedError, constant fake results, omitted error handling or
   temporary placeholders count as complete. If changing a file shared with completed
   tasks, inspect and preserve their required behavior before recording completion.
6. Record success using `complete --task T001 --note "coding outputs and integration"`.
   CODE_COMPLETE means code was written and connected according to the plan; it does
   **not** mean correct behavior, tested, deployed or accepted. The helper records output
   hashes and evidence, and never edits task definitions or executes application tools.
7. On a failed attempt, use `block --task T001 --note "actual obstacle and changed files"`.
   At most three starts/attempts per unchanged task/design are allowed. Retry only when
   a concrete correction is available; never spin. After the bound, leave the obstacle
   recorded and continue independent work. Do not repeatedly retry in-progress work
   without recording failed attempts. A process interruption alone is not a failed attempt.
8. Continue until all tasks are CODE_COMPLETE or every remaining task has a genuine
   recorded obstacle/dependency. Do not stop after an arbitrary task count. Checkpoint
   each task and before context/session limits; a new session resumes from this ledger.
9. Give a concise count of completed/blocked/remaining tasks, changed files and obstacles.
   State that tests were not run. Recommend __SPECKIT_COMMAND_DEPLOYMENT__ or
   __SPECKIT_COMMAND_TEST__ for local tests; never wait for them to declare coding complete.

## Extension boundary

Read `.specify/extensions.yml` if present. Skip `enabled: false` hooks. Offer
`optional: true` hooks without automatically executing them; invoke mandatory hooks
only within this stage's boundaries and wait for their result. Nonempty conditions
belong to HookExecutor, not ad hoc expression evaluation. Use the integration's native
command spelling when invoking a logical `speckit.*` name. Report malformed hook
configuration and any mandatory hook that cannot safely run; never claim it succeeded.

Inspect before_impcode/after_impcode hooks and inherited tool hooks before invoking
tools. Skip/report anything that writes/runs tests, deploys or exceeds owned files.
Never alias before_implement/after_implement to this command. If mandatory workspace
instructions require forbidden work, report the conflict instead of silently violating
either contract or claiming completion.
