---
description: Run three-layer agent-native handoff orchestration or execute one worker handoff.
---
## Input
```text
$ARGUMENTS
```
Optional runtime hint: `agent-runtime=<spec-kit-integration-key>`.
## Mode
- Core mode: no handoff JSON path in `$ARGUMENTS`
- Worker mode: `.json` handoff path in `$ARGUMENTS` or `Use handoff JSON <path>`
- Forbidden: external dispatch scripts, workflow runners
## Authority
- Only Vertical Planner Agents may produce shard plans and digest drafts.
- Only Core Agent may write final `handoff-manifest.json` and commit `tasks.md`.
- Only Worker Agents may execute implementation handoffs.
## Change Scope Granularity
Map planned `U` design objects to concrete source, test, fixture, configuration, and receipt paths before worker execution. If the mapping is ambiguous, record `context_gaps`; do not widen to repository scope or broad module scope.
## Isolation Policy
- Manifest `execution_mode`: `isolated_subagent` or `manual_fresh_worker_session`.
- Use `isolated_subagent` only for runtimes with isolated subagent/subsession execution.
- Use `manual_fresh_worker_session` when runtime isolation is unavailable or unknown.
- Core mode must not execute Worker handoffs inline in the same conversation context.
- If isolated dispatch is unavailable or unknown, Core mode writes the manifest and handoffs, then stops with Worker-mode instructions.
- Worker runs receive only the Worker prompt and one handoff JSON path.
- Core consumes planner outputs and worker receipts, not worker conversation history.
## Core Agent
- lifecycle owner
- create `context-index.json`
- dispatch one Vertical Planner Agent per `vertical_capability`
- collect shard plans, handoff drafts, context digest drafts
- assemble final handoffs under `handoffs/implement/<run-id>`
- write final `handoff-manifest.json`
- dispatch Worker Agent runs from final manifest only for `isolated_subagent`
- review receipts
- commit `tasks.md` only during `task_commit`
- run `integration_verification`, closeout
- must not produce shard plans or digest drafts
## Vertical Planner Agent
- vertical planner only
- exactly one `vertical_capability`
- read `tasks.md`, `context-index.json`, allowed planning artifacts
- produce shard plans, handoff drafts, context digest drafts
- derive `allowed_read_paths`, `allowed_write_paths`
- record `planner_outputs`, `draft_source`
- mark final review shards with `task_type: code_review`
- must not execute implementation, write final `handoff-manifest.json`, dispatch workers, update `tasks.md`
## Worker Agent
- single handoff only
- execute exactly one handoff JSON
- Worker mode must reject non-existent handoff paths
- Worker mode must reject handoffs not listed in `handoff-manifest.json`
- verify `contract_type` is `speckit.implement.handoff.v2`
- load `context_digest_path` before editing
- stop before editing when `context_gaps` is not empty
- execute only `task_ids`
- read only `allowed_read_paths`
- write only `allowed_write_paths`
- write `task_status_update.receipt_path` as `speckit.implement.receipt.v1`
- validation_evidence must reference the relevant BDD scenario, behavior assertion, API contract, or quickstart path when the handoff context includes behavior contracts
- Code review tasks must echo `task_type: code_review`, write `review_conclusion.checked_sources`, `data_side_effect_review`, `consistency_repairs`, and `deferred_validation_todos` when applicable
- For data side-effect review, inspect the actual implementation diff for runtime database writes and field-level update/delete behavior, bulk writes, soft deletes, ORM whole-object saves, migrations/backfills, retries, rollback/compensation, and external-system writes
- repair design, sequence, or contract drift and high-risk data side effects only inside `allowed_write_paths`; real e2e cannot run becomes a todo
- Do not edit `tasks.md`, create handoffs, dispatch workers
## Lifecycle
`intake` -> `context_indexing` -> `vertical_planning` -> `manifest_assembly` -> `worker_dispatch` -> `worker_execution` -> `receipt_review` -> `code_review` -> `task_commit` -> `integration_verification` -> `closeout`
## Vertical Capabilities
`domain-model`, `api-contract`, `persistence`, `service-flow`, `ui`, `cli`, `test-validation`, `documentation`, `integration`, `cleanup`
## Shard Rules
- one incomplete `tasks.md` checklist item maps to one candidate shard
- ignore completed `[x]` checklist items
- preserve `tasks.md` order
- infer `vertical_capability` from section heading, task text, referenced paths
- group candidates only when lifecycle dependencies, vertical_capability, and allowed_write_paths match
- shard IDs use `S<2-digit-sequence>-<vertical_capability>-<2-digit-sequence>`
- record explicit dependencies for shards that consume another shard's allowed_write_paths
## Context Digest Rules
- include task text for assigned `task_ids`
- include document headings from `context-index.json`
- include only sections referenced by assigned task paths or vertical_capability
- include relevant `class-diagram.md` and `contracts/sequences.md` constraints
- include relevant `research.md` validation decisions and include relevant `quickstart.md` validation paths
- include relevant `contracts/bdd/`, `contracts/uif/`, and `contracts/behavior/` behavior contract constraints
- omit unrelated full `spec.md`, `plan.md`, `research.md`, `contracts/`, `class-diagram.md`, and `quickstart.md`; record unresolved required context as `context_gaps`
## Path Rules
- derive `allowed_write_paths` from paths referenced by assigned task text
- include receipt path in `allowed_write_paths`
- derive `allowed_read_paths` from allowed write parents, validation files, context digest, and context index
- include `tasks.md` in `allowed_read_paths`
- add planning artifacts only when digest references their sections
- exclude `tasks.md` from `allowed_write_paths`
## Files
- root: `specs/<feature>/handoffs/implement/<run-id>/`
- `handoff-manifest.json`
- `context-index.json`
- `planner-outputs/`
- `<shard-id>.json`
- `<shard-id>.context.md`
- `results/<shard-id>.json`
## Schemas
- manifest: `schemas/speckit.implement.manifest.v1.schema.json`
- handoff: `schemas/speckit.implement.handoff.v2.schema.json`
- receipt: `schemas/speckit.implement.receipt.v1.schema.json`
## Receipt Rejection
- mismatched `shard_id`
- mismatched `task_type`
- `task_ids` outside handoff
- `completed_task_ids` outside handoff
- empty `validation_evidence`
- behavior-contract task receipt missing evidence references to the relevant BDD scenario, behavior assertion, API contract, or quickstart path
- receipt path does not equal `task_status_update.receipt_path`
## Code Review Receipts
- require `task_type: code_review` and `review_conclusion.checked_sources` from `allowed_read_paths` or `context_digest_path`
- require `data_side_effect_review.reviewed_diff_paths`, `runtime_data_writes_found`, and `mutation_findings` for data side-effect review of the actual implementation diff
- `data_side_effect_review.reviewed_diff_paths` must come from `allowed_read_paths` or `context_digest_path`
- require quickstart/contract validation command evidence when `validation_commands` are declared
- approved receipts must not contain unresolved critical/high findings
- approved receipts must not contain unresolved critical/high data side-effect findings
- approved receipts are invalid when real e2e cannot run
- `consistency_repairs` changed paths must stay inside `allowed_write_paths`
- `deferred_validation_todos` lists missing environment, quickstart path, and commands when real e2e cannot run
## Dispatch Rules
- no `context_gaps`
- satisfied lifecycle dependencies
- no shared sequencing requirement
- no overlapping `allowed_write_paths` or `capability_boundary.owns`
