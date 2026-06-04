# Changelog

## Unreleased

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
