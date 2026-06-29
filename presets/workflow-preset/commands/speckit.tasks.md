---
description: Wrap task generation with optional design artifact awareness.
strategy: wrap
---

## Derivation Boundary

Preserve the planned `M + U` scope in task text when deriving implementation, validation, and integration tasks. Do not generate execution metadata or write-path fields.

## Planning Input Taxonomy

If any listed file exists under FEATURE_DIR, task generation must consume it as an input:

- `class-diagram.md`: internal object structure, dependency direction, and design pattern participants.
- `contracts/sequences.md`: service, command, event, async, retry, rollback, and failure-path flows.
- `research.md`: selected validation level, fixture strategy, external-system execution mode, and error-branch validation decisions.
- `quickstart.md`: executable validation paths and evidence collection guidance.
- `spec.md` visual acceptance requirements: visual fidelity requirements, screenshot refs, visual proof refs, visual SSOT refs, and external evidence refs.
- `spec.md` Client Asset Contract: asset source strategy, required variants, fallback policy, and blocker status.
- `checklists/behavior-testability.md` Visual Fidelity Readiness: `Requirement Status`, passed visual proof level, blockers, and accepted exceptions.
- `contracts/bdd/`: formal BDD acceptance contracts.
- `contracts/uif/`: Expected UIF interaction contracts.
- `contracts/behavior/`: formal scenario instance, fixture, and assertion contracts.
- `contracts/`: interface schemas and API/message contracts used by validation tasks.

Use these inputs to derive implementation, integration, orchestration, failure-handling, and validation tasks. For behavior contracts, derive test-first task chains in user-story order: fixture setup, BDD/E2E or contract test, implementation, and verification evidence. Keep task output in the existing checklist format and user-story organization.

`/speckit.tasks` owns implementation, validation, and review task definition in `tasks.md`. Task derivation must not invent validation strategy, add lifecycle roles, change requirements, update contracts, or widen scope.

For Client Asset Contract entries, derive asset preparation, binding, implementation, and validation tasks in dependency order. Missing required client visual assets are readiness blockers.

Use Visual Fidelity Readiness as the only visual planning readiness source. Do not create a second readiness rule from screenshot coverage, external intake artifacts, HTML SSOT bundles, or provider evidence artifacts; if required visual evidence is missing, report a readiness blocker instead of deriving complete-looking UI tasks.

Use each Visual Fidelity Readiness row's `Requirement Status` as the visual task input filter. Generate visual tasks only for rows with status `Required` or `Required` plus an accepted exception; tasks for accepted exceptions must cite the exception rule. Do not generate implementation, validation, verification, evidence, asset binding, UI acceptance, or review tasks for `Not Applicable`, `Unknown`, or `[BLOCKED: PROVIDER_EVIDENCE]` rows. Route `Unknown` rows back to `/speckit.clarify`; route `[BLOCKED: PROVIDER_EVIDENCE]` rows to the external intake extension. `/speckit.tasks` must not discover visual requirements or repair evidence; it only decomposes visual specifications that already passed the readiness gate.

Missing Required case coverage is a coverage blocker, not silently skipped work. If `checklists/behavior-testability.md` marks a case type Required but the matching BDD or behavior contract is absent and no `Not Applicable` rationale or `case_coverage_blockers` entry exists, report the missing case instead of generating a complete-looking task list.

## Validation Task Derivation

Do not create or require a standalone test strategy artifact. Instead, derive the validation level, fixture strategy, external-system execution mode, and inline evidence requirement while generating `tasks.md`.

Use this validation level taxonomy for each scenario or validation path:

- `unit`: pure domain rules, data validation, state transitions, or behavior assertions that do not cross a process, network, database, browser, or external-system boundary.
- `contract`: API, message, schema, BDD request/response, or Expected UIF contract step with type `api_call` that can be verified at an interface boundary.
- `integration`: service orchestration, persistence, async events, retries, rollback, callbacks, external sandbox calls, or `contracts/sequences.md` failure branches.
- `e2e`: user-visible journeys that require frontend/CLI interaction plus backend behavior, multiple services, or final feedback verification.

Use this fixture strategy and external-system execution mode taxonomy:

- Attach fixture IDs and setup strategies from `contracts/behavior/` when they exist.
- Use fixture intent only when it is recorded in `research.md` or formal `contracts/behavior/` blocker notes for a scenario documented as `Not Applicable` or blocked by `case_coverage_blockers`.
- Use mock, sandbox, or real-system decisions from `research.md`.
- External-system validation must use mock or sandbox unless `research.md` and `quickstart.md` explicitly require a real-system validation path.
- Add a separate validation task for high-risk, non-functional, external-system, async, retry, rollback, permission, validation, state_conflict, negative, boundary, or error behavior.

Evidence binding: every generated test or validation task must name at least one relevant BDD scenario, behavior assertion, API contract, UIF path, quickstart validation path, visual proof ref, screenshot ref, or command output.

Generate explicit validation tasks from this validation task taxonomy instead of relying on final code review for primary validation responsibility:

- `contract_validation`: contract ref, implementation surface, validation command, and evidence; report a blocker when mapping is unavailable.
- `visual_verification` or `ui_acceptance`: Visual Item ID, Visual Fidelity Readiness row, viewport/state coverage, proof level, screenshot refs or visual proof refs, quickstart validation path, and evidence.
- `data_side_effect_validation`: affected entity or state transition, expected write behavior, rollback/compensation/retry/migration/backfill or invariant assertion when applicable, and validation evidence.
- `integration_e2e_validation`: user-visible journey or cross-boundary flow, scenario/assertion refs, external-system strategy, quickstart validation path, and captured command output.

Task shape: checklist item plus story tag, validation level, strategy when applicable, and evidence refs.

Behavior traceability must be explicit:

- For each BehaviorScenarioInstance, create a fixture task, BDD/E2E or contract test task, implementation task, and verification evidence task unless the scenario is documented as `Not Applicable` or blocked by `case_coverage_blockers`.
- For each BehaviorScenarioInstance with type `negative`, `boundary`, `permission`, `validation`, or `state_conflict`, derive fixture, contract or BDD test, implementation, and verification evidence tasks. For failure outcomes, name the expected error code, failure feedback, and state invariant, rollback, or compensation assertion when present.
- For each Expected UIF contract step with type `user_event`, create the frontend, CLI, or interaction task that emits or handles the event.
- For each Expected UIF contract step with type `api_call`, create the backend/API or contract task that provides the declared method and path.
- For each quickstart validation path, create a validation task that can collect evidence for the relevant scenario IDs and assertions.

Use only this visual task taxonomy when a user story includes `contracts/uif/`, visual acceptance requirements, Visual Fidelity Readiness rows, or Client Asset Contract entries:

- Maintain story-local task granularity: `visual_setup` -> `visual_validation` -> `visual_implementation` -> `visual_evidence` -> `final_visual_review`. Do not create a separate visual lifecycle phase.
- `visual_setup`: prepare visual fixtures, viewport configuration, screenshot baseline paths, client resource setup, asset variants, fallback policy mapping, and other visual validation prerequisites.
- `visual_validation`: create or configure the validation path before implementation, including visual regression tests, UI acceptance checks, screenshot comparison, state or viewport coverage validation, and accessibility check entrypoints.
- `visual_implementation`: implement the visual or UI behavior, including page or component states, interaction feedback, responsive layout, asset binding, empty/error/loading/disabled/hover/focus states, and fallback behavior.
- `visual_evidence`: collect delivery evidence, including screenshot refs, visual proof refs, command output, visual diff results, and quickstart validation evidence.
- `ui_acceptance`: verify a user-facing UIF path or BDD scenario, including user action, feedback, page state, and visible result.
- `visual_verification`: verify visual-spec fidelity by Visual Item ID, `Requirement Status`, viewport/state coverage, proof level, screenshot refs, and visual proof refs.
- `asset_binding`: when a Client Asset Contract applies, bind source assets, variants, license or authorization refs, fallback policy, code paths, and missing-asset blockers.
- `final_visual_review`: require final review of implemented UI states, viewport behavior, Visual Fidelity Readiness rows, UIF paths, screenshot refs, visual proof refs, and Client Asset Contract bindings without changing `spec.md`, contracts, readiness checklists, or planning artifacts.
- `visual_setup`, `visual_validation`, `visual_implementation`, `visual_evidence`, `ui_acceptance`, `visual_verification`, `asset_binding`, and `final_visual_review` are the only visual task types.
- Visual tasks must name concrete source, test, fixture, configuration, or asset paths when derivable; otherwise report a readiness blocker instead of generating an ambiguous visual task.
- UI acceptance tasks must verify the same UIF path, Visual Item ID, scenario ID, asset contract entry, or quickstart validation path as the implementation task, including required state and viewport coverage when responsive visual behavior is in scope.
- UI acceptance evidence must reference at least one relevant UIF path, BDD or behavior scenario, visual proof ref, screenshot ref, quickstart validation path, API contract, or captured command output.
- Missing visual proof refs, screenshot refs, viewport/state coverage, Client Asset Contract entries, asset variants, or fallback policy are Visual Fidelity Readiness blockers.

For each applicable Visual Fidelity Readiness row with `Requirement Status` `Required` or `Required` plus an accepted exception, generate paired `visual_validation` and `visual_evidence` work; use `ui_acceptance` or `visual_verification` as concrete validation or evidence task types when they best match the UIF path, BDD scenario, or visual item. Do not generate visual tasks for rows with `Requirement Status` `Not Applicable`, `Unknown`, or `[BLOCKED: PROVIDER_EVIDENCE]`.

When an implementation task depends on `contracts/`, include a paired contract validation task that names the contract ref, expected implementation surface, validation command or quickstart path, and evidence requirement. Do not instruct implementers to modify `spec.md`, `contracts/`, readiness checklists, or Visual Fidelity Readiness to make implementation pass; report a blocker if implementation requires requirement or contract changes.

When persistence, migrations, external writes, retries, rollback, or compensation are in scope, include a data-side-effect validation task before final code review. The task must name the affected entity, expected mutation behavior, invariant or rollback/compensation assertion, and evidence source.

## Final Code Review

When generating `tasks.md`, append the final phase after user-story tasks in the same checklist format. Use this final review scope taxonomy when applicable: `boundary`, `interface_contract`, `visual`, `data_side_effect`, `behavior_contract`, `sequence_consistency`, and `asset_binding`. Checked sources include `class-diagram.md`, `contracts/sequences.md`, `contracts/`, `contracts/uif/`, `research.md`, `quickstart.md`, `spec.md` visual acceptance requirements, `spec.md` Client Asset Contract entries, and `checklists/behavior-testability.md` Visual Fidelity Readiness, plus data side-effect review and real-system e2e environment readiness.

Code review task text must require review of runtime database writes and other persistent data changes, including field-level update/delete behavior, bulk writes, soft deletes, ORM whole-object saves, migrations/backfills, retries, rollback/compensation, and external-system writes. Do not generate field-level mutation allowlists or pre-implementation data-write gates in normal tasks.

Code review task text must require boundary review: task scope stays within planned `M + U`, implementation matches the referenced contracts, validation evidence covers quickstart or contract paths, and no implementation task changed `spec.md`, `contracts/`, readiness checklists, or Visual Fidelity Readiness to make execution pass.

Code review task text must require visual consistency review when UI or visual acceptance was in scope. The review must reconcile implemented UI states and viewport behavior with Visual Fidelity Readiness, UIF paths, screenshot refs, visual proof refs, and Client Asset Contract bindings, variants, and fallback policy.

Review evidence binding: final review tasks must name concrete review scope, source artifacts, implementation surfaces, and evidence refs. If review scope exposes drift from the plan, sequences, contracts, or data-side-effect expectations, express it as review evidence, bounded repair permission, or a blocker. If resolving the drift would require changing `spec.md`, `contracts/`, `research.md`, `quickstart.md`, readiness checklists, or planning artifacts, record a blocker instead of treating the change as implementation work. Real-system e2e environment gaps must remain visible as evidence gaps instead of treated as passing evidence.

{CORE_TEMPLATE}
