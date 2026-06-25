# Changelog

## Unreleased

- Added constitution governance coverage for the fixed R/M/U/O mapping and Architecture SSOT boundary, with preset manifest, documentation, contract tests, and install smoke checks aligned to the constitution template.
- Fixed the preset artifact integration workflow to update both bundled and community catalog metadata before opening the `bigsmartben/spec-kit` fork PR.

## 1.3.10

- Tightened implement handoff, manifest, and receipt shard IDs to the `S00-capability-00` format.
- Added validator checks that shard ID capabilities match declared vertical capabilities.
- Moved detailed `/speckit.implement` subagent lifecycle, shard, context digest, path, receipt, and review rules into the cross-agent contract reference.
- Clarified `/speckit.tasks`, `/speckit.specify`, and `/speckit.clarify` wrapper boundaries.

## 1.3.9

- Hardened implement receipt completion gates so deferred validation or unapproved code review cannot mark `tasks.md` items complete.
- Added Final Code Review visual consistency checks for implemented UI states, viewport behavior, visual proof evidence, and Client Asset Contract bindings.
- Clarified that `/speckit.tasks` defines validation, visual verification, contract validation, data-side-effect validation, integration/e2e validation, and scope-aware code review tasks, while `/speckit.implement` only executes those tasks and records receipt evidence without inventing validation strategy or widening scope.
- Added Visual Item Matrix and Visual Restoration Trace fields so Figma/provider evidence can carry stable UI/UX restoration refs into `spec.md` and Visual Fidelity readiness.
- Added a normalized Visual Item Matrix JSON schema and validator checks for deterministic UI/UX restoration intake.
- Added validator coverage that rejects full provider Visual Item Matrix copies inside Design Requirement Intake Visual Restoration Trace rows.
- Clarified that provider evidence artifacts may record screenshot/proof refs and provider blockers, while only the checklist Visual Fidelity Evidence Matrix decides visual planning readiness, proof sufficiency, Gate Status, Blocking Items, and accepted exception rules.
- Clarified implementation repair boundaries so workers repair only authorized implementation drift and record upstream artifact gaps as blockers or todos.

## 1.3.8

- Aligned code review receipt validation with the receipt schema for data side-effect review required fields.
- Rejected empty Case Coverage Matrix inputs in the behavior case coverage validator.
- Restored source-only workflow contract checks to skip when tests run from a packaged preset without `.github/workflows`.

## 1.3.7

- Generalized Figma-derived requirement handling into provider-neutral Design Requirement Intake and Requirement Merge templates while keeping Figma MCP execution outside the preset.
- Added a row-per-case Case Coverage Matrix to make positive, negative, boundary, permission, validation, and state_conflict applicability explicit before planning.
- Hardened failure behavior scenarios so permission, validation, state_conflict, and other error paths require structured request cases, error responses, failure feedback, and assertions before tasks are generated.
- Hardened UI task generation so UI implementation and acceptance tasks are paired with explicit state coverage, viewport coverage, visual proof refs, screenshot refs, and readiness blockers for missing visual or asset evidence.

## 1.3.6

- Added a Figma Evidence Packet input template and Figma intake contract for Figma-derived specifications without adding Figma MCP execution to the preset.
- Hardened Figma intake readiness with raw metadata completeness, metadata index proof, node inventory parity, and blocker lint gates before writing Figma-derived requirements.

## 1.3.4

- Added NFR readiness to `/speckit.checklist` so `spec.md` must explicitly declare applicable non-functional requirements, mark them not applicable, or block planning for unknown assumptions.
- Added Final Code Review task generation and structured code review receipts for implementation consistency repairs, post-implementation data side-effect review, and deferred real e2e validation todos.
- Isolated release install smoke checks to a GitHub runner venv and runner temp paths instead of relying on local environment behavior.

## 1.3.1

- Added GitHub Actions boundaries for preset contract tests, release artifact verification, project-scoped install smoke checks, and fail-fast fork integration dispatch.
- Added Change Scope Granularity governance through `/speckit.constitution`, the constitution template, and stage-local plan/tasks/analyze/implement references.

## 1.3.0

- Hardened implementation handoff isolation with runtime-neutral execution modes, subagent/subsession dispatch policy, and validator checks for empty tasks, context gaps, overlapping write ownership, and must-not-touch conflicts.
- Moved behavior draft generation from `/speckit.specify` to `/speckit.plan` Phase 0 and made `/speckit.checklist` the BDD readiness gate before planning.
- Clarified BDD readiness gate status and Phase 0 report-only/no-write failure handling.
- Removed `behavior/open-questions.json`; unresolved behavior gaps now return to `spec.md` through checklist and clarification instead of a separate behavior artifact.

## 1.2.0

- Removed the standalone test strategy artifact from the current contract; `/speckit.tasks` now derives test level, fixture/mock/sandbox strategy, and validation evidence requirements from behavior contracts, interface contracts, `research.md`, and `quickstart.md`.

## 1.1.0

- Tightened `/speckit.plan` BDD Draft formalization rules to improve reasoning stability without adding a traceability system.
- Hardened behavior contract quality gates for BDD Given/When/Then, scenario fixtures, assertions, Expected UIF steps, formalization blockers, and behavior-linked validation evidence.
- Added `/speckit.analyze` ownership for behavior-first vertical consistency across requirements, behavior drafts, contracts, and tasks.
- Added behavior-first requirement drafts, clarification/checklist wrappers, formal behavior contract templates, JSON schemas, and validator coverage.
- Expanded project documentation for the planning artifact capabilities and implementation-stage context-load controls that reduce reasoning drift.

## 1.0.3

- Aligned manifest tags with the community preset publishing guide.
- Updated release install examples for the `v1.0.3` archive.

## 1.0.2

- Prepared the preset for community catalog submission.
- Added deterministic validator coverage for dispatch order completeness, dependency ordering, and unlisted handoff or receipt rejection.
- Kept implementation orchestration agent-native with no packaged CLI, workflow dispatch, or integration adapter scripts.

## 1.0.1

- Updated preset and orchestrated workflow version metadata for the 1.0.1 release.
- Updated release install examples to use the `v1.0.1` archive.
- Reworked implementation orchestration as agent-native handoff orchestration.
- Removed Python dispatch tooling from the preset contract while preserving persisted handoff, digest, receipt, Core Agent, and Worker Agent semantics.
- Added lifecycle and vertical capability requirements to implementation handoffs.
- Decoupled manifest, handoff, and receipt contracts into standalone schema files.
- Removed preset-packaged handoff tooling; Core and Worker modes use persisted JSON contracts directly.
- Added Vertical Planner Agent topology so shard plans, digest drafts, and allowed path derivation are separated from Core lifecycle ownership and Worker execution.
- Added schema and cross-field contract tests for manifest, handoff, receipt, and planner/worker authority boundaries.

## 1.0.0

- Merged the plan design artifacts preset and orchestrated implement preset into `workflow-preset`.
- Kept `/speckit.plan`, `/speckit.tasks`, and `plan-template` as design-aware wrappers.
- Replaced `/speckit.implement` with orchestrated handoff shard dispatch.
- Added workflow and scripts for scoped implementation handoff generation, dispatch, and post-dispatch scope verification.
- Included `class-diagram.md`, `contracts/sequences.md`, and `test-plan.md` in implementation shard context digests.
- Added the subagent profile matrix for setup, test, implementation, integration, validation, and cleanup shards.
- Added fresh process and fresh context isolation metadata to implementation handoffs.
- Reduced unmatched `spec.md` and `plan.md` digest content to outlines plus blocking clarification context.
- Allowed directory-scoped handoffs to create, update, or delete descendant files while preserving scope verification.
- Declared packaged scripts and the orchestrated workflow as preset support files.
