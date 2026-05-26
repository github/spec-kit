# Workflow Preset

This Spec Kit community preset combines behavior-first specification, design-aware planning, and agent-native handoff orchestration.

It keeps `/speckit.specify`, `/speckit.clarify`, `/speckit.checklist`, `/speckit.plan`, `/speckit.tasks`, and `/speckit.analyze` compatible with the core workflow while adding behavior drafts, behavior testability checks, optional design artifacts for internal object design, service sequencing, and test strategy. It replaces `/speckit.implement` with a Core Agent, Vertical Planner Agent, and Worker Agent orchestration contract that writes handoffs to disk.

## Goal

`workflow-preset` turns a Spec Kit feature from a single broad implementation prompt into a staged workflow with stable design context and explicit worker boundaries.

The preset has two goals:

- Make behavior testability explicit early by drafting BDD, UIF intent, fixture intent, and behavior questions during requirement work.
- Preserve richer planning intent so downstream tasks and implementation do not lose object design, service-flow, or validation decisions.
- Execute implementation through agent-native handoff orchestration so each worker receives explicit task IDs, lifecycle stage, vertical capability, context, read/write paths, validation commands, and receipt requirements.

## Problem Addressed

Large Spec Kit features can overload the implementation phase. A single `/speckit.implement` run may need to keep product requirements, technical decisions, domain details, interface contracts, object design, service flows, test strategy, task ordering, and current code changes in one prompt. As the context grows, the agent is more likely to drift from earlier design decisions, blur task boundaries, read unrelated documents, update the wrong files, or mark tasks complete without enough validation evidence.

`workflow-preset` reduces that failure mode in three complementary ways:

- Requirement enhancement keeps draft behavior, interaction intent, fixture intent, and behavior questions beside `spec.md`.
- Plan enhancement gives object design, service sequencing, and validation intent stable homes before tasks are generated.
- Implement handoff orchestration slices work by lifecycle and vertical capability, then gives each Worker Agent a compact digest, scoped paths, validation commands, and a receipt contract instead of the full planning corpus.

The intent is not to add ceremony to simple features. The intent is to preserve reasoning quality when the feature is large enough that a single implementation context becomes a source of drift.

## Capabilities

Requirement capabilities:

- Wraps `/speckit.specify` to produce requirement-phase behavior drafts when useful.
- Writes `behavior/bdd.draft.feature`, `behavior/behavior-scenarios.draft.json`, `behavior/uif.intent.json`, `behavior/data-fixtures.intent.json`, and `behavior/open-questions.json`.
- Applies BDD draft quality rules for scenario type coverage and Given/When/Then mapping.
- Wraps `/speckit.clarify` so Given/When/Then ambiguity can drive requirement questions.
- Wraps `/speckit.checklist` to add `checklists/behavior-testability.md`.
- Keeps BDD Draft and UIF Intent separate from formal planning contracts.

Planning capabilities:

- Wraps `/speckit.plan` to produce optional/contextual design artifacts when useful.
- Consumes behavior drafts and must formalize them into `contracts/bdd/`, `contracts/uif/`, and `contracts/behavior/` when no blocking behavior questions exist.
- Records `N/A or blocker` when behavior drafts cannot be formalized.
- Keeps `plan.md` focused on technical decisions and navigation.
- Adds plan-template navigation to the core plan output.
- Stores internal object design in `class-diagram.md`.
- Stores service, command, event, async, retry, rollback, and failure-path flows in `contracts/sequences.md`.
- Stores validation strategy and scenario planning in `test-plan.md`.
- Keeps product requirements in `spec.md`, domain facts in `data-model.md`, interface schemas in `contracts/`, and executable validation guidance in `quickstart.md`.

Task generation capabilities:

- Wraps `/speckit.tasks` so task generation can consume the design artifacts.
- Uses formal BDD, UIF, and behavior contracts to derive test-first fixture, acceptance test, implementation, and verification tasks.
- Uses design artifacts to derive implementation, integration, orchestration, failure-handling, and validation tasks.
- Preserves the existing checklist format and user-story organization.

Analysis capabilities:

- Wraps `/speckit.analyze` to check vertical consistency from `spec.md` through BDD/UIF intent, formal contracts, and `tasks.md`.
- Checks that user stories, Given/When/Then steps, UIF API calls, behavior contracts, tasks, and quickstart validation paths remain traceable.
- Treats UIF as a requirement behavior projection, formalized during planning as Expected UIF contracts.

Implementation capabilities:

- Replaces `/speckit.implement` with an agent-native handoff orchestration command.
- Uses Core Agent mode to own lifecycle state, create the context index, assemble the final manifest, dispatch Worker Agent runs, review receipts, update `tasks.md`, and run integration verification.
- Uses Vertical Planner Agent mode to plan one `vertical_capability`, produce shard plans, create handoff drafts, create context digest drafts, and derive allowed paths.
- Uses Worker Agent mode to execute exactly one `speckit.implement.handoff.v2` handoff.
- Writes `handoff-manifest.json`, one handoff JSON, one context digest, a context index, and one worker receipt per shard.
- Defines deterministic shard, context digest, and allowed path derivation rules.
- Keeps manifest, handoff, and receipt JSON contracts in standalone schema files.
- Requires behavior-linked `validation_evidence` in worker receipts when behavior contracts are in handoff context.
- Assigns every handoff a lifecycle stage and vertical capability such as `domain-model`, `api-contract`, `persistence`, `service-flow`, `ui`, `test-validation`, `documentation`, `integration`, or `cleanup`.
- Supports direct single-shard execution with `Use handoff JSON <path>`.
- Blocks worker execution when generated context has unresolved `context_gaps`.
- Commits completed task statuses from `speckit.implement.receipt.v1` receipts so the Core Agent is the only `tasks.md` writer.

Context-load controls:

- `context-index.json` records the available planning and implementation context without requiring every worker to read every source document.
- Context digests include only assigned task text, relevant headings, referenced sections, and applicable `class-diagram.md`, `contracts/sequences.md`, or `test-plan.md` constraints.
- `context_gaps` are explicit blockers. A Worker Agent stops instead of guessing or expanding into full `spec.md`, `plan.md`, `contracts/`, `class-diagram.md`, or `test-plan.md`.
- `allowed_read_paths` and `allowed_write_paths` make each handoff auditable and prevent broad implementation runs from silently crossing capability boundaries.
- Worker receipts separate execution evidence from task status commits, so the Core Agent can review validation evidence before updating `tasks.md`.

## Workflow

1. `/speckit.specify` keeps the core requirements output and adds behavior drafts when they help clarify acceptance behavior.
2. `/speckit.clarify` and `/speckit.checklist` use those drafts to surface ambiguity and testability gaps.
3. `/speckit.plan` keeps the core planning outputs, formalizes behavior drafts into contracts, and adds design artifacts when they help implementation.
4. `/speckit.tasks` reads the core plan outputs plus behavior and design artifacts, then produces executable tasks.
5. `/speckit.analyze` checks vertical consistency across requirements, behavior drafts, contracts, and tasks.
6. `/speckit.implement` enters Core Agent mode when no handoff path is provided.
7. The Core Agent writes `context-index.json` and dispatches one Vertical Planner Agent per active vertical capability.
8. Vertical Planner Agents produce shard plans, handoff drafts, context digest drafts, and allowed path derivations.
9. The Core Agent assembles final handoffs and writes `handoff-manifest.json`.
10. Worker Agents run only from persisted handoff JSON files and write receipts.
11. The Core Agent reviews receipts, updates `tasks.md`, runs integration verification, and reports closeout status.

## Non-Goals

- It does not make every feature produce large diagrams or test matrices.
- It does not move product requirements out of `spec.md`.
- It does not move API or message schemas out of `contracts/`.
- It does not replace `data-model.md`, `research.md`, or `quickstart.md`.
- It does not infer UIF from built code; UIF remains a requirement and planning contract.
- It does not provide a Python orchestration script, workflow shell runner, or integration adapter layer.
- It does not allow Worker Agents to freely expand context by reading full planning documents when the digest is insufficient.

## Install

Release install:

```bash
specify preset add workflow-preset --from https://github.com/bigsmartben/spec-kit-workflow-preset/archive/refs/tags/v1.1.0.zip
```

Local development install:

```bash
specify preset add --dev /path/to/workflow-preset
```

## Usage

Run the behavior-first workflow:

```text
/speckit.specify
/speckit.clarify
/speckit.checklist
/speckit.plan
/speckit.tasks
/speckit.analyze
```

Then run agent-native orchestrated implementation:

```text
/speckit.implement
```

Run a single worker handoff directly:

```text
/speckit.implement Use handoff JSON specs/001-demo/handoffs/implement/<run-id>/S01-service-flow-01.json
```

## Files Written

The core planning workflow still owns its normal artifacts:

- `specs/<feature>/plan.md`
- `specs/<feature>/research.md`
- `specs/<feature>/data-model.md`
- `specs/<feature>/contracts/`
- `specs/<feature>/quickstart.md`
- `specs/<feature>/tasks.md`

This preset adds requirement-phase behavior artifacts:

- `specs/<feature>/behavior/bdd.draft.feature`
- `specs/<feature>/behavior/behavior-scenarios.draft.json`
- `specs/<feature>/behavior/uif.intent.json`
- `specs/<feature>/behavior/data-fixtures.intent.json`
- `specs/<feature>/behavior/open-questions.json`
- `specs/<feature>/checklists/behavior-testability.md`

This preset adds planning-phase formal behavior contracts:

- `specs/<feature>/contracts/bdd/`
- `specs/<feature>/contracts/uif/`
- `specs/<feature>/contracts/behavior/`

This preset adds optional/contextual planning artifacts:

- `specs/<feature>/class-diagram.md`
- `specs/<feature>/contracts/sequences.md`
- `specs/<feature>/test-plan.md`

Agent-native handoff orchestration writes implementation artifacts:

- `specs/<feature>/handoffs/implement/<run-id>/handoff-manifest.json`
- `specs/<feature>/handoffs/implement/<run-id>/planner-outputs/`
- `specs/<feature>/handoffs/implement/<run-id>/*.json`
- `specs/<feature>/handoffs/implement/<run-id>/*.context.md`
- `specs/<feature>/handoffs/implement/<run-id>/context-index.json`
- `specs/<feature>/handoffs/implement/<run-id>/results/*.json`

Contract files packaged by the preset:

- `schemas/speckit.behavior.scenarios.draft.v1.schema.json`
- `schemas/speckit.behavior.uif.intent.v1.schema.json`
- `schemas/speckit.behavior.data-fixtures.intent.v1.schema.json`
- `schemas/speckit.behavior.open-questions.v1.schema.json`
- `schemas/speckit.behavior.uif.expected.v1.schema.json`
- `schemas/speckit.behavior.scenario-instances.v1.schema.json`
- `schemas/speckit.behavior.data-fixtures.v1.schema.json`
- `schemas/speckit.behavior.assertions.v1.schema.json`
- `schemas/speckit.implement.manifest.v1.schema.json`
- `schemas/speckit.implement.handoff.v2.schema.json`
- `schemas/speckit.implement.receipt.v1.schema.json`

Development-only contract helpers:

- `validators/speckit_implement_contract.py`

## Artifact Roles

`behavior/bdd.draft.feature` captures requirement-phase behavior in readable Given/When/Then form. `behavior/behavior-scenarios.draft.json`, `behavior/uif.intent.json`, and `behavior/data-fixtures.intent.json` make the same draft behavior machine-readable enough for clarification, checklist, and planning.

`contracts/bdd/`, `contracts/uif/`, and `contracts/behavior/` contain planning-phase formal behavior contracts. They are generated from the requirement drafts after planning has resolved fixture strategy, data model, interface contracts, and validation paths, unless planning records `N/A or blocker` for unresolved behavior questions.

`class-diagram.md` captures internal implementation object structure: classes, interfaces, abstract types, composition, dependencies, references, and design pattern participants. It is the object design map that helps implementation preserve boundaries between services, adapters, repositories, strategies, factories, controllers, coordinators, and extension points.

`contracts/sequences.md` captures service-call, command, event, external-system, retry, rollback, compensation, async, and failure-path sequencing. It is the flow design map that helps implementation preserve call order, service boundaries, async behavior, idempotency, compensation, and error propagation. Sequences always live at this path, even when there are no other contract files.

`test-plan.md` captures validation intent: test objectives, in/out of scope, test levels, data strategy, requirement traceability, and scenario matrix. It is the validation design map that helps `/speckit.tasks` and Worker Agents produce tests and evidence aligned with planned risk, not just nearby code changes.

The handoff context digest includes these design artifacts when present, so Worker Agents can preserve object boundaries, service flows, and validation intent without reading full planning documents by default.

See `speckit-cross-agent-subagents.md` for the cross-platform subagent mapping, worker prompt, parallel dispatch rules, and minimal handoff/receipt contract.

## Agent Topology

The Core Agent is the lifecycle orchestrator. It owns context indexing, manifest assembly, worker dispatch, receipt review, task status commit, integration verification, and closeout. It does not directly produce shard plans or context digest drafts.

Vertical Planner Agent runs are planners. A Vertical Planner Agent handles one `vertical_capability`, produces shard plans, handoff drafts, context digest drafts, and allowed path derivations, and does not execute implementation, write the final manifest, dispatch workers, or edit `tasks.md`.

Worker Agent runs are executors. A Worker Agent handles one persisted handoff, writes only `allowed_write_paths`, does not edit `tasks.md`, does not dispatch additional workers, and writes a `speckit.implement.receipt.v1` receipt.

Worker mode rejects handoff paths that do not exist or are not listed in `handoff-manifest.json`.

Only Vertical Planner Agents may produce shard plans and digest drafts.

Only Core Agent may write final `handoff-manifest.json` and commit `tasks.md`.

Only Worker Agents may execute implementation handoffs.

## Lifecycle

Core Agent mode proceeds through these stages:

- `intake`
- `context_indexing`
- `vertical_planning`
- `manifest_assembly`
- `worker_dispatch`
- `worker_execution`
- `receipt_review`
- `task_commit`
- `integration_verification`
- `closeout`

Every worker handoff records its `lifecycle_stage`, `vertical_capability`, `agent_topology`, `capability_boundary`, `planner_outputs`, and `draft_source`.

## Vertical Capability

Worker handoffs should stay inside one vertical capability:

- `domain-model`
- `api-contract`
- `persistence`
- `service-flow`
- `ui`
- `cli`
- `test-validation`
- `documentation`
- `integration`
- `cleanup`

When a task spans capabilities, the Core Agent should split it into dependent handoffs instead of assigning broad cross-cutting work to one Worker Agent.

## Safety Boundaries

Planning artifacts are optional/contextual. Simple features may produce concise files or `N/A` sections with concrete reasons. The command should avoid large placeholder artifacts and should not move product requirements out of `spec.md`, interface schemas out of `contracts/`, or quick validation instructions out of `quickstart.md`.

Vertical Planner Agents may read only the planning artifacts required to produce their capability-local shard plan and digest drafts. Worker Agents should treat the final handoff JSON and its digest as the primary context. They should not read full `spec.md`, `plan.md`, `contracts/`, `class-diagram.md`, or `test-plan.md` by default. If the digest contains `context_gaps`, the Worker Agent must stop instead of expanding context on its own.

Completed `[x]` tasks are not scheduled into new implementation handoffs.

## Development

Runtime requirements:

- Spec Kit CLI `>=0.8.10.dev0`
- An agent environment capable of running `/speckit.implement` in Core Agent, Vertical Planner Agent, and Worker Agent modes

Development and release tooling:

- Python 3.10 or newer
- PyYAML and jsonschema for contract tests
- Git
- GitHub CLI `gh` for repository and release publishing

Install development test dependencies:

```bash
python3 -m pip install -r requirements-dev.txt
```

Run the contract tests:

```bash
python3 -m unittest tests/test_preset_contract.py
```

Validate local installation:

```bash
specify preset add --dev /path/to/workflow-preset
specify preset info workflow-preset
specify preset remove workflow-preset
```

After tagging a release, validate archive installation:

```bash
specify preset add workflow-preset --from https://github.com/bigsmartben/spec-kit-workflow-preset/archive/refs/tags/v1.1.0.zip
```

## Source Rationale

See `2026-05-15-plan-design-artifacts-proposal.md` for the design artifact proposal that this preset incorporates.
