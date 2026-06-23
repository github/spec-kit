---
description: Run agent-native implement orchestration or execute one worker handoff.
---
## Input
```text
$ARGUMENTS
```
Optional runtime hint: `agent-runtime=<spec-kit-integration-key>`.
## Mode
- Core mode: no handoff JSON path in `$ARGUMENTS`.
- Worker mode: `.json` handoff path in `$ARGUMENTS` or `Use handoff JSON <path>`.
- Forbidden: external dispatch scripts, workflow runners, inline worker execution.
## Authority
- Core Agent is the orchestrator: build `context-index.json`, assemble `handoff-manifest.json`,
  dispatch isolated runs, review receipts, update `tasks.md` only during task commit,
  and run integration verification.
- Vertical Planner Agent is the capability planner: plan exactly one `vertical_capability`,
  produce shard plans plus handoff/context digest drafts, and never execute implementation
  or write the final manifest.
- Worker Agent is the handoff executor: execute exactly one handoff and never edit `tasks.md`,
  create handoffs, or dispatch workers.
## Core Agent
- Follow the lifecycle and runtime isolation contract in `tests/contracts/speckit-cross-agent-subagents.md`.
- Map planned `U` design objects to concrete source, test, fixture, configuration,
  and receipt paths before worker execution.
- Use `isolated_subagent` only when the runtime provides isolated subagent/subsession execution.
- Otherwise use manifest `execution_mode: manual_fresh_worker_session`.
- If isolation is unavailable or unknown, write the manifest and handoffs, then stop with Worker-mode instructions.
- Consume planner outputs and worker receipts, not worker conversation history.
## Vertical Planner Agent
- Read only `tasks.md`, `context-index.json`, and allowed planning artifacts.
- Preserve `tasks.md` order, lifecycle dependencies, capability boundaries, and Change Scope Granularity.
- Put unresolved shard, context, asset binding, or path ambiguity into `context_gaps`.
- Emit drafts that validate against the handoff schema before Core assembly.
## Worker Agent
- Reject non-existent handoff paths.
- Reject handoffs not listed in `handoff-manifest.json`.
- Verify `contract_type` is `speckit.implement.handoff.v2`.
- Load `context_digest_path` before editing.
- Stop before editing when `context_gaps` is not empty.
- Execute only `task_ids`.
- Read only `allowed_read_paths`.
- Write only `allowed_write_paths`.
- Write `task_status_update.receipt_path` as `speckit.implement.receipt.v1`.
- Do not edit `tasks.md`.
## Contract References
- Runtime, shard, context digest, path, asset binding, dispatch, Worker Prompt,
  and review receipt rules: `tests/contracts/speckit-cross-agent-subagents.md`.
- Manifest schema: `schemas/speckit.implement.manifest.v1.schema.json`.
- Handoff schema: `schemas/speckit.implement.handoff.v2.schema.json`.
- Receipt schema: `schemas/speckit.implement.receipt.v1.schema.json`.
- Cross-field validation: `validators/speckit_implement_contract.py`.
## Runtime Stops
- Stop on missing handoff files, unlisted handoffs, non-empty `context_gaps`, schema mismatch,
  write paths outside `allowed_write_paths`, or attempts to update planning artifacts from Worker mode.
- Stop instead of inventing validation strategy, adding lifecycle roles, changing requirements,
  updating contracts, widening scope, or adding standalone validation planning artifacts.
