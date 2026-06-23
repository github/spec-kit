# Spec Kit Cross-Agent Subagents
## Purpose
Reduce implementation-stage context load and reasoning drift by turning broad `/speckit.implement` work into persisted, capability-scoped handoffs. Workers receive only task-local context, allowed paths, validation commands, and receipt obligations.
## Files and Schemas
- `handoffs/implement/<run-id>/handoff-manifest.json`, `planner-outputs/`, `context-index.json`
- `handoffs/implement/<run-id>/<shard>.json`, `<shard>.context.md`, `results/<shard>.json`
- `schemas/speckit.implement.manifest.v1.schema.json`, `schemas/speckit.implement.handoff.v2.schema.json`, `schemas/speckit.implement.receipt.v1.schema.json`
- Handoff records `planner_outputs` and `draft_source` fields.
## Authority
- Only Vertical Planner Agents may produce shard plans and digest drafts.
- Only Core Agent may write final `handoff-manifest.json` and commit `tasks.md`.
- Only Worker Agents may execute implementation handoffs.
## Lifecycle
`intake` -> `context_indexing` -> `vertical_planning` -> `manifest_assembly` -> `worker_dispatch` -> `worker_execution` -> `receipt_review` -> `code_review` -> `task_commit` -> `integration_verification` -> `closeout`
## Runtime Isolation Mapping
Use `agent-runtime=<spec-kit-integration-key>` as a prompt hint. The manifest records only `isolated_subagent` or `manual_fresh_worker_session`.
| Runtime key | Isolated execution | Planner dispatch | Worker dispatch |
| --- | --- | --- | --- |
| codex (Codex) | isolated subagent/subsession | one planner per `vertical_capability` | one worker per handoff |
| claude (Claude Code) | subagent | planner subagent | worker subagent |
| gemini (Gemini CLI) | `@subagent` | `@speckit_planner` | `@speckit_worker` |
| copilot (GitHub Copilot) | subagent/task agent | planner task agent | worker task agent |
| opencode | agent context | planner agent | worker agent |
| cursor-agent, devin, windsurf, kiro-cli, junie | runtime-managed isolated agent | planner role | worker role |
| generic | not assumed | write planner prompts only | manual fresh Worker-mode sessions |
## Dispatch Payloads
- Vertical Planner payload: planner prompt, one `vertical_capability`, `context-index.json`, allowed planning artifact paths.
- Worker payload: Worker Prompt, one handoff JSON path, no full `spec.md`, `plan.md`, `research.md`, `contracts/`, `quickstart.md`.
- Core consumes planner outputs and worker receipts, not worker conversation history.
## Core Agent
- read `tasks.md`
- write `context-index.json`
- dispatch Vertical Planner Agents
- collect planner drafts
- assemble final handoffs
- write `handoff-manifest.json`
- dispatch Worker Agent runs only for isolated execution
- review receipts
- commit `tasks.md`
- during task_commit, mark `[x]` only for receipt completed_task_ids that passed receipt review, required code review, and integration verification with no deferred_validation_todos
- run integration verification
- report closeout
## Vertical Planner Agent
- one `vertical_capability`
- produce shard plans, handoff drafts, context digest drafts
- derive `allowed_read_paths`, `allowed_write_paths`
- mark final review handoffs with `task_type: code_review`
- must not execute implementation, write final `handoff-manifest.json`, dispatch workers, edit `tasks.md`
## Worker Agent
- execute exactly one handoff
- Reject non-existent handoff paths
- Reject handoffs not listed in `handoff-manifest.json`
- Verify contract_type == speckit.implement.handoff.v2
- Load context_digest_path before editing
- Stop if context_gaps is not empty
- Execute only task_ids
- Read only allowed_read_paths
- Write only allowed_write_paths
- write receipt_path as speckit.implement.receipt.v1 with validation_evidence references to relevant BDD scenario, behavior assertion, API contract, or quickstart path
- use empty completed_task_ids when the handoff is blocked, validation is deferred, required evidence is missing, or code review status is not approved
- Code Review Receipts use task_type: code_review, review_conclusion.checked_sources, data_side_effect_review, consistency_repairs, deferred_validation_todos, and quickstart/contract validation command evidence
- review actual implementation diff data side effects, including runtime database writes and field-level update/delete behavior
- repair implementation drift against existing design, sequence, or contract constraints, or high-risk data side effects, only inside allowed_write_paths; upstream requirement, contract, checklist, or planning artifact gaps become blockers or todos instead of repair edits; real e2e gaps become todos
- must not edit tasks.md, create handoffs, dispatch workers
## Worker Prompt
```text
Worker Agent.
Handoff JSON: <path>
- Verify contract_type == speckit.implement.handoff.v2
- Load context_digest_path before editing
- Stop if context_gaps is not empty
- Execute only task_ids
- Read only allowed_read_paths
- Write only allowed_write_paths
- Do not edit tasks.md
- Do not dispatch workers
- Write receipt_path as speckit.implement.receipt.v1 with validation_evidence references to relevant BDD scenario, behavior assertion, API contract, or quickstart path
- Use empty completed_task_ids when the handoff is blocked, validation is deferred, required evidence is missing, or code review status is not approved
- For Code Review tasks, echo task_type: code_review; add review_conclusion.checked_sources and data_side_effect_review; review actual implementation diff runtime database writes and field-level update/delete behavior; include quickstart/contract validation command evidence; repair only authorized implementation drift; record upstream artifact gaps and real e2e todos
```
## Planner Prompt
```text
Vertical Planner Agent.
vertical_capability: <capability>
- Produce shard plans
- Produce handoff drafts
- Produce context digest drafts
- Derive allowed_read_paths
- Derive allowed_write_paths
- Do not execute implementation
- Do not write final handoff-manifest.json
- Do not dispatch workers
- Do not edit tasks.md
```
## Shard Rules
- one incomplete `tasks.md` checklist item maps to one candidate shard
- ignore completed `[x]` checklist items
- preserve `tasks.md` order
- infer `vertical_capability` from task section heading, task text, referenced paths
- group candidates only when lifecycle dependencies, vertical_capability, and allowed_write_paths match
- shard IDs use `S<2-digit-sequence>-<vertical_capability>-<2-digit-sequence>`
## Context Digest Rules
- include task text for assigned `task_ids`
- include document headings from `context-index.json`
- include only sections referenced by assigned task paths or vertical_capability
- include relevant `class-diagram.md`, `contracts/sequences.md`, `contracts/bdd/`, `contracts/uif/`, and `contracts/behavior/` constraints, plus research.md validation decisions and quickstart.md validation paths from `research.md` and `quickstart.md`
- include behavior contract constraints, visual fidelity requirements, screenshot refs, visual proof refs, Design Requirement trace refs, and Client Asset Contract entries
- asset binding maps required Client Asset Contract items to local asset paths or code asset mappings; missing required client visual assets, mappings, variants, or fallbacks become `context_gaps`
- record unresolved required context as `context_gaps`
## Path Rules
- derive `allowed_write_paths` from paths referenced by assigned task text, planned `U` design object, and specific source, test, fixture, configuration, or receipt paths
- include receipt path in `allowed_write_paths`
- derive `allowed_read_paths` from allowed write parents, validation files, context digest, and context index
- exclude `tasks.md` from `allowed_write_paths`
## Receipt Rejection
- mismatched `shard_id`
- `task_ids` outside handoff
- `completed_task_ids` outside handoff
- non-empty `completed_task_ids` with `deferred_validation_todos`
- non-empty `completed_task_ids` on Code Review Receipts whose `review_conclusion.status` is not approved
- empty `validation_evidence` or missing relevant BDD scenario, behavior assertion, API contract, or quickstart path reference
- receipt 路径不等于 handoff 中声明的 `task_status_update.receipt_path`
- Code Review Receipts missing `task_type: code_review`, `review_conclusion.checked_sources`, `data_side_effect_review`, quickstart/contract validation command evidence, in-scope `consistency_repairs`, or needed `deferred_validation_todos`
