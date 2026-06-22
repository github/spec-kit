---
description: Wrap the core planning workflow with Phase 0 behavior projection and optional design artifacts.
strategy: wrap
---

## Change Scope Granularity

Apply the constitution's Change Scope Granularity principle.

During planning, lock the change scope to `M + U`: module/capability plus design object. Do not lock operation-level implementation details or concrete write paths.

## Design Artifact Policy

Core planning remains authoritative. Optional design artifacts carry structured details that do not belong in `plan.md`.

Generate design artifacts only when the feature requires internal object design or cross-boundary sequence constraints:

- `class-diagram.md`: internal implementation object structure.
- `contracts/sequences.md`: service-call, command, event, and integration sequencing.

For simple features, keep artifacts concise. `N/A` sections require a concrete rationale, for example "No service boundary exists for this static documentation change." Do not create large placeholder files.

Keep `plan.md` as summary/navigation. It must link generated design artifacts and must not embed complete class diagrams or complete sequence diagrams.

Store service sequences only at `contracts/sequences.md`, even when there are no other contract files. Do not create a root-level `sequences.md`.

Validation strategy is not a standalone planning artifact. Planning-time validation decisions belong in `research.md`; executable validation paths belong in `quickstart.md`; concrete test and verification tasks belong in `tasks.md` through the tasks command.

## Phase 0 Preflight

Before core research or design work, verify checklists/behavior-testability.md has passed: it must have `Gate Status: PASS` and `Blocking Items: none` or a `Blocking Items` section containing only `- none`.

If the checklist is missing, incomplete, has `Gate Status: BLOCKED`, or lists blocking items, stop with a report-only/no-write failure before planning artifacts are generated. Report an upstream gate failure with the missing checklist item or readiness gap. Do not create or update feature files, and must not create or update behavior artifacts. Return to `/speckit.checklist` or `/speckit.clarify` instead of repairing requirements inside planning.

Phase 0 preflight must not modify `spec.md`, ask clarification questions, create formal contracts, or bypass the checklist gate.

## Phase 0 Behavior Projection

After Phase 0 preflight passes and before core research or design work, project the accepted `spec.md` requirements into behavior drafts:

- `behavior/bdd.draft.feature`: readable BDD draft scenarios.
- `behavior/behavior-scenarios.draft.json`: structured draft scenario IDs, Given inputs, When actions, Then outcomes, and source.
- `behavior/uif.intent.json`: interaction intent extracted from accepted requirements.
- `behavior/data-fixtures.intent.json`: data setup intent required by draft scenarios.

Required case types from `checklists/behavior-testability.md` must project into `behavior/behavior-scenarios.draft.json`. Do not continue with only positive scenarios when Required case types exist. If a Required case type cannot be projected without inventing requirements, stop with a report-only/no-write failure and return to `/speckit.checklist` or `/speckit.clarify`.

Phase 0 behavior projection is a projection step, not a new requirement-discovery step:

- Do not discover new requirement problems.
- Do not ask clarification questions.
- Do not modify `spec.md`.
- Do not generate formal contracts.
- Do not decide test level, fixture strategy, external-system strategy, interface design, or validation commands.

Structured JSON draft artifacts must follow their matching `schemas/speckit.behavior.*.schema.json` contracts.

If Phase 0 cannot generate behavior drafts from a `spec.md` that passed checklist, stop with a report-only/no-write failure. Do not create or update partial behavior artifacts. The remedy is to return to `/speckit.checklist` or `/speckit.clarify`; do not invent missing requirements during planning.

## Additional Phase 1 Design Outputs

During Phase 1, after Phase 0 behavior projection and core research have resolved planning unknowns and while producing design/contracts, create or update these artifacts only when their trigger conditions are met:

1. `class-diagram.md`
   - Capture key classes, interfaces, abstract types, services, repositories, adapters, factories, strategies, controllers, and coordinators.
   - Explain each core type's responsibility and the relationships that constrain implementation: inheritance, composition, aggregation, dependency, and references.
   - Format must be Mermaid, PlantUML, or structured table; selected format must expose type responsibilities and relationships.
   - Do not define API request/response fields, domain business fields, test cases, task IDs, private helpers, or method-level implementation details.

2. `contracts/sequences.md`
   - Capture the observable flow of API requests, commands, events, callbacks, async workers, external systems, retries, compensation, rollback, and failure branches.
   - Include participants, service boundaries, main success paths, important alternate paths, and failure handling that affects implementation or testing.
   - Format must be Mermaid sequence diagram or structured text; selected format must expose participants, boundaries, success paths, and failure paths.
   - Do not define field schemas, internal class inheritance, test matrices, or user-facing run instructions.

When `plan.md` has a design artifact/navigation section, include links to:

- Internal object design: `./class-diagram.md`
- Service sequences: `./contracts/sequences.md`
- Behavior draft: `./behavior/bdd.draft.feature`
- BDD contracts: `./contracts/bdd/`
- Expected UIF contracts: `./contracts/uif/`
- Behavior contracts: `./contracts/behavior/`
- Data model: `./data-model.md`
- Interface contracts: `./contracts/`
- Validation path: `./quickstart.md`

When visual requirements are in scope, keep `plan.md` navigation linked to visual fidelity scope, screenshot refs, visual proof refs, and Design Requirement trace refs already accepted by `spec.md` and the readiness checklist.

## Visual Planning Responsibilities

When visual requirements are in scope, planning must keep the Visual Fidelity Evidence Matrix as the upstream readiness record and split visual carry-forward across the existing planning outputs:

- `research.md`: add Visual validation decisions for each relevant Visual Item ID. Record selected test level, fixture or asset strategy, viewport/state coverage strategy, visual regression or baseline proof strategy, screenshot refs, visual proof refs, Design Requirement trace refs, related quickstart validation path, and related UIF or behavior contract path. Do not copy the Visual Fidelity Evidence Matrix into `research.md`, do not create new visual requirements, do not call Figma or other provider tools, and do not rebuild provider evidence matrices.
- `contracts/uif/` and `contracts/behavior/`: formalize accepted visual interaction and state constraints only when they affect observable behavior. Expected UIF contracts may carry visual_item_refs, viewport_matrix_refs, state_matrix_refs, visual_proof_refs, and accepted_exception_refs. Behavior contracts may reference visual assertion IDs or blockers when a visual state cannot be formalized without inventing requirements. Interface contracts in `contracts/` may model only API or data fields needed to support UI states, assets, or feedback; they must not contain layout rules or screenshot proof decisions.
- `contracts/sequences.md`: add UI interaction sequence, visual state handoff points, responsive branch trigger refs, and visual proof references only when visual states affect cross-boundary order, async callbacks, retries, rollback, compensation, or error propagation. Keep visual style, tokens, layout breakpoints, screenshot matrices, and validation commands out of `contracts/sequences.md`.

## Behavior-First Planning Inputs

Use the Phase 0 behavior projection drafts as planning inputs:

- `behavior/bdd.draft.feature`
- `behavior/behavior-scenarios.draft.json`
- `behavior/uif.intent.json`
- `behavior/data-fixtures.intent.json`

Phase 1 outputs must cite applicable draft scenario IDs or record `N/A or blocker`.

During Phase 1, if behavior drafts exist and checklists/behavior-testability.md has passed, you must formalize them into formal behavior contracts:

- `contracts/bdd/`: acceptance-level BDD contracts.
- `contracts/uif/`: Expected UIF contracts.
- `contracts/behavior/`: scenario instance, fixture, and assertion contracts.

Required case types from `checklists/behavior-testability.md` must formalize into `contracts/behavior/scenario-instances.json`. Do not continue with only positive scenarios when Required case types exist. Map each Required Case ID to a Scenario ID or `case_coverage_blockers` entry. When a Required case type cannot be formalized, write `case_coverage_blockers` in `contracts/behavior/scenario-instances.json` and record `N/A or blocker` with the Case ID, missing planning input, and downstream contract path.

When formalizing BDD Draft into `contracts/bdd/*.feature`:

- Preserve scenario intent and business outcome from the draft.
- Convert ambiguous Given steps into formal fixture, actor, state, permission, or start-view conditions.
- Convert When steps into formal user events, request cases, or system triggers aligned with UIF/API contracts.
- Convert Then steps into formal feedback, response, business state, or assertion expectations.
- If a step cannot be formalized without inventing information, record `N/A or blocker` instead of guessing.
- Do not introduce independent traceability mechanisms for BDD formalization.

If behavior drafts exist but cannot be formalized, write `N/A or blocker` in the affected planning artifact with the source draft path, the missing planning input, and the downstream contract path that could not be produced. Do not silently skip behavior draft formalization.

BDD draft reasoning must feed the normal planning outputs:

- `research.md`: record the selected test level, fixture strategy, mock/external-system strategy, and error-branch validation decisions for each behavior scenario type that affects implementation.
- `data-model.md`: model formal behavior entities referenced by behavior contracts, including `BehaviorScenarioInstance`, `DataFixture`, `UIFPath`, `FeedbackView`, and `BehaviorAssertion`.
- `contracts/`: align interface contracts with BDD When steps, Expected UIF `api_call` steps, and behavior assertions.
- `quickstart.md`: include validation paths that exercise the formal BDD/UIF/behavior contracts.

Keep `plan.md` as summary/navigation for these formal behavior contracts. Product requirements stay in `spec.md`, domain details stay in `data-model.md`, interface schemas stay in `contracts/`, and validation run guidance stays in `quickstart.md`.

{CORE_TEMPLATE}

## Design Artifact Reporting

Before finishing, the final report must list generated artifacts and state whether each is populated or intentionally minimal:

- `class-diagram.md`: populated, intentionally minimal, or not applicable with reason.
- `contracts/sequences.md`: populated, intentionally minimal, or not applicable with reason.

Also report where validation decisions were recorded:

- `research.md`: selected test level, fixture strategy, mock/external-system strategy, and error-branch validation decisions required by behavior contracts.
- `quickstart.md`: executable validation paths for the planned behavior contracts.

Report unresolved design gaps separately from downstream tasks. Do not mark the planning run complete if a design artifact contains unresolved `NEEDS CLARIFICATION` items that block task generation.
