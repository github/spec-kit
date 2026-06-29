---
description: Run implement orchestration.
---
## Input
`$ARGUMENTS`; runtime hint: `agent-runtime=<spec-kit-integration-key>`.
## Mode
- Core mode: no handoff JSON path in `$ARGUMENTS`.
- Worker mode: `.json` handoff path in `$ARGUMENTS` or `Use handoff JSON <path>`.
- Forbidden: dispatch scripts, workflow runners, inline worker execution.
## Authority
- Core Agent: build `context-index.json` and `handoff-manifest.json`; dispatch, review receipts.
- Core Agent updates `tasks.md` during task commit and runs integration verification.
- Vertical Planner Agent: plan one `vertical_capability`, draft shard plans plus handoff/context digests, never execute.
- Worker Agent: execute exactly one handoff; never edit `tasks.md`, create handoffs, or dispatch workers.
## Core Agent
- Follow `tests/contracts/speckit-cross-agent-subagents.md`.
- Map planned `U` design objects to concrete source, test, fixture, configuration, and receipt paths.
- Use `isolated_subagent` only with isolated subagent/subsession execution; otherwise use `manual_fresh_worker_session`.
- If isolation is unavailable or unknown, write the manifest and handoffs, then stop with Worker-mode instructions.
- Consume planner outputs and worker receipts, not worker conversation history.
## Visual Implementation Boundary
- Execute only incomplete `tasks.md` visual items; preserve the `/speckit.tasks` visual task input filter.
- Visual Fidelity Readiness `Requirement Status` is `Required` or `Required` plus an accepted exception.
- Accepted exceptions cite the exception rule in task text, context digest, and receipt evidence.
- Do not create handoffs or worker instructions for visual rows with `Requirement Status` `Not Applicable`,
  `Unknown`, or `[BLOCKED: PROVIDER_EVIDENCE]`.
- Route `Unknown` visual rows back to `/speckit.clarify`;
  route `[BLOCKED: PROVIDER_EVIDENCE]` visual rows to the external intake extension.
- `/speckit.implement` must not discover visual requirements, repair Visual Fidelity Readiness evidence,
  or edit upstream artifacts to make visual work executable.
- Visual worker receipts must reference the relevant Visual Item ID, `Requirement Status`, and evidence refs.
## Vertical Planner Agent
- Read only `tasks.md`, `context-index.json`, and allowed planning artifacts.
- Preserve `tasks.md` order, lifecycle dependencies, capability boundaries, and Change Scope Granularity.
- Put unresolved shard, context, asset binding, path, visual status, evidence, asset, or fallback gaps
  into `context_gaps`.
- Emit drafts that validate against the handoff schema before Core assembly.
## Worker Agent
- Reject non-existent handoff paths.
- Reject handoffs not listed in `handoff-manifest.json`.
- Verify `contract_type` is `speckit.implement.handoff.v2`; load `context_digest_path`; stop on `context_gaps`.
- Execute only `task_ids`; read only `allowed_read_paths`; write only `allowed_write_paths`.
- Write `task_status_update.receipt_path` as `speckit.implement.receipt.v1`.
- For visual handoffs, validate assigned task text; use empty `completed_task_ids` when visual evidence is unavailable.
- Do not edit `tasks.md`.
## Contract References
- Runtime, shard, digest, path, asset binding, dispatch, Worker Prompt, receipt rules:
  `tests/contracts/speckit-cross-agent-subagents.md`.
- Schemas: `schemas/speckit.implement.manifest.v1.schema.json`,
  `schemas/speckit.implement.handoff.v2.schema.json`,
  `schemas/speckit.implement.receipt.v1.schema.json`.
- Cross-field validation: `validators/speckit_implement_contract.py`.
## Runtime Stops
- Stop on missing handoff files, unlisted handoffs, non-empty `context_gaps`, schema mismatch,
  writes outside `allowed_write_paths`, or planning artifact updates.
- Stop instead of inventing validation strategy, adding lifecycle roles, changing requirements,
  updating contracts, widening scope, or adding validation planning artifacts.
