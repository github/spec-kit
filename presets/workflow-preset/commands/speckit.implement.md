---
description: Run three-layer agent-native handoff orchestration or execute one worker handoff.
---

## Input

```text
$ARGUMENTS
```

## Mode

- Core mode: no handoff JSON path in `$ARGUMENTS`
- Worker mode: `.json` handoff path in `$ARGUMENTS` or `Use handoff JSON <path>`
- Forbidden: external dispatch scripts, workflow runners

## Authority

- Only Vertical Planner Agents may produce shard plans and digest drafts.
- Only Core Agent may write final `handoff-manifest.json` and commit `tasks.md`.
- Only Worker Agents may execute implementation handoffs.

## Core Agent

- lifecycle owner
- create `context-index.json`
- dispatch one Vertical Planner Agent per `vertical_capability`
- collect shard plans, handoff drafts, context digest drafts
- assemble final handoffs under `handoffs/implement/<run-id>`
- write final `handoff-manifest.json`
- dispatch Worker Agent runs from final manifest
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
- Do not edit `tasks.md`, create handoffs, dispatch workers

## Lifecycle

`intake` -> `context_indexing` -> `vertical_planning` -> `manifest_assembly` -> `worker_dispatch` -> `worker_execution` -> `receipt_review` -> `task_commit` -> `integration_verification` -> `closeout`

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
- include relevant `class-diagram.md`, `contracts/sequences.md`, `test-plan.md` constraints
- include relevant `contracts/bdd/`, `contracts/uif/`, and `contracts/behavior/` behavior contract constraints
- omit unrelated full `spec.md`, `plan.md`, `contracts/`, `class-diagram.md`, `test-plan.md`
- record unresolved required context as `context_gaps`

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
- `task_ids` outside handoff
- `completed_task_ids` outside handoff
- empty `validation_evidence`
- behavior-contract task receipt missing evidence references to the relevant BDD scenario, behavior assertion, API contract, or quickstart path
- receipt path does not equal `task_status_update.receipt_path`

## Dispatch Rules

- no `context_gaps`
- satisfied lifecycle dependencies
- no shared sequencing requirement
- no overlapping `allowed_write_paths` or `capability_boundary.owns`
