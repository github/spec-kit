---
description: Wrap the core planning workflow with Phase 0 behavior projection and optional design artifacts.
strategy: wrap
---

## Design Artifact Policy

This preset preserves the core planning workflow and adds optional/contextual design artifacts for features that need more structure than `plan.md` should carry.

Generate the two design artifacts only when useful for the feature:

- `class-diagram.md`: internal implementation object structure.
- `contracts/sequences.md`: service-call, command, event, and integration sequencing.

For simple features, keep these artifacts concise. It is acceptable to create a short artifact with `N/A` sections when the reason is concrete, for example "No service boundary exists for this static documentation change." Do not create large placeholder files.

Keep `plan.md` as summary/navigation. It should point to detailed design artifacts when they exist, but it must not embed complete class diagrams or complete sequence diagrams.

Store service sequences only at `contracts/sequences.md`, even when there are no other contract files. Do not create a root-level `sequences.md`.

Validation strategy is not a standalone planning artifact. Planning-time validation decisions belong in `research.md`; executable validation paths belong in `quickstart.md`; concrete test and verification tasks belong in `tasks.md` through the tasks command.

## Phase 0 Preflight

Before core research or design work, verify checklists/behavior-testability.md has passed: it must have `Gate Status: PASS` and `Blocking Items: none`.

If the checklist is missing, incomplete, has `Gate Status: BLOCKED`, or lists blocking items, stop with a report-only/no-write failure before planning artifacts are generated. Report an upstream gate failure with the missing checklist item or readiness gap. Do not create or update feature files, and must not create or update behavior artifacts. Return to `/speckit.checklist` or `/speckit.clarify` instead of repairing requirements inside planning.

Phase 0 preflight must not modify `spec.md`, ask clarification questions, create formal contracts, or bypass the checklist gate.

## Phase 0 Behavior Projection

After Phase 0 preflight passes and before core research or design work, project the accepted `spec.md` requirements into behavior drafts:

- `behavior/bdd.draft.feature`: readable BDD draft scenarios.
- `behavior/behavior-scenarios.draft.json`: structured draft scenario IDs, Given inputs, When actions, Then outcomes, and source.
- `behavior/uif.intent.json`: interaction intent extracted from accepted requirements.
- `behavior/data-fixtures.intent.json`: data setup intent required by draft scenarios.

Phase 0 behavior projection is a projection step, not a new requirement-discovery step:

- Do not discover new requirement problems.
- Do not ask clarification questions.
- Do not modify `spec.md`.
- Do not generate formal contracts.
- Do not decide test level, fixture strategy, external-system strategy, interface design, or validation commands.

Structured JSON draft artifacts must follow their matching `schemas/speckit.behavior.*.schema.json` contracts.

If Phase 0 cannot generate behavior drafts from a `spec.md` that passed checklist, stop with a report-only/no-write failure. Do not create or update partial behavior artifacts. The remedy is to return to `/speckit.checklist` or `/speckit.clarify`; do not invent missing requirements during planning.

## Additional Phase 1 Design Outputs

During Phase 1, after Phase 0 behavior projection and core research have resolved planning unknowns and while producing design/contracts, create or update these artifacts when relevant:

1. `class-diagram.md`
   - Capture key classes, interfaces, abstract types, services, repositories, adapters, factories, strategies, controllers, and coordinators.
   - Explain each core type's responsibility and the relationships that constrain implementation: inheritance, composition, aggregation, dependency, and references.
   - Use Mermaid class diagrams by default when diagrams help, but text tables or PlantUML are acceptable if they better fit the project.
   - Do not define API request/response fields, domain business fields, test cases, task IDs, private helpers, or method-level implementation details.

2. `contracts/sequences.md`
   - Capture the observable flow of API requests, commands, events, callbacks, async workers, external systems, retries, compensation, rollback, and failure branches.
   - Include participants, service boundaries, main success paths, important alternate paths, and failure handling that affects implementation or testing.
   - Use Mermaid sequence diagrams by default when diagrams help, but structured text is acceptable for simple flows.
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

## Behavior-First Planning Inputs

Use the Phase 0 behavior projection drafts as planning inputs:

- `behavior/bdd.draft.feature`
- `behavior/behavior-scenarios.draft.json`
- `behavior/uif.intent.json`
- `behavior/data-fixtures.intent.json`

Use these drafts to guide research decisions, fixture strategy, data-model entities, interface contracts, and quickstart validation paths.

During Phase 1, if behavior drafts exist and checklists/behavior-testability.md has passed, you must formalize them into formal behavior contracts:

- `contracts/bdd/`: acceptance-level BDD contracts.
- `contracts/uif/`: Expected UIF contracts.
- `contracts/behavior/`: scenario instance, fixture, and assertion contracts.

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
- `data-model.md`: model formal behavior entities when relevant, including `BehaviorScenarioInstance`, `DataFixture`, `UIFPath`, `FeedbackView`, and `BehaviorAssertion`.
- `contracts/`: align interface contracts with BDD When steps, Expected UIF `api_call` steps, and behavior assertions.
- `quickstart.md`: include validation paths that exercise the formal BDD/UIF/behavior contracts.

Keep `plan.md` as summary/navigation for these formal behavior contracts. Product requirements stay in `spec.md`, domain details stay in `data-model.md`, interface schemas stay in `contracts/`, and validation run guidance stays in `quickstart.md`.

{CORE_TEMPLATE}

## Design Artifact Reporting

Before finishing, the final report must list generated artifacts and state whether each is populated or intentionally minimal:

- `class-diagram.md`: populated, intentionally minimal, or not applicable with reason.
- `contracts/sequences.md`: populated, intentionally minimal, or not applicable with reason.

Also report where validation decisions were recorded:

- `research.md`: selected test level, fixture strategy, mock/external-system strategy, and error-branch validation decisions when relevant.
- `quickstart.md`: executable validation paths for the planned behavior when relevant.

Report unresolved design gaps separately from downstream tasks. Do not mark the planning run complete if a design artifact contains unresolved `NEEDS CLARIFICATION` items that block task generation.
