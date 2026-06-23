---
description: Wrap task generation with optional design artifact awareness.
strategy: wrap
---

## Change Scope Granularity

Preserve the planned `M + U` scope in task text when deriving implementation, validation, and integration tasks. Do not generate handoff fields or `allowed_write_paths`.

## Additional Design Inputs

If any listed file exists under FEATURE_DIR, task generation must consume it as an input:

- `class-diagram.md`: internal object structure, dependency direction, and design pattern participants.
- `contracts/sequences.md`: service, command, event, async, retry, rollback, and failure-path flows.
- `research.md`: selected test level, fixture strategy, mock/external-system strategy, and error-branch validation decisions.
- `quickstart.md`: executable validation paths and evidence collection guidance.
- `spec.md` visual acceptance requirements: visual fidelity requirements, screenshot refs, visual proof refs, and Design Requirement trace refs.
- `spec.md` Client Asset Contract: asset source strategy, required variants, fallback policy, and blocker status.
- `checklists/behavior-testability.md` Visual Fidelity Readiness: passed visual proof level, blockers, and accepted exceptions.
- `contracts/bdd/`: formal BDD acceptance contracts.
- `contracts/uif/`: Expected UIF interaction contracts.
- `contracts/behavior/`: formal scenario instance, fixture, and assertion contracts.
- `contracts/`: interface schemas and API/message contracts used by validation tasks.

Use these inputs to derive implementation, integration, orchestration, failure-handling, and validation tasks. For behavior contracts, derive test-first tasks in user-story order: fixture setup, BDD/E2E or contract test, implementation, and verification evidence. Keep task output in the existing checklist format and user-story organization.

Tasks owns validation and review task definition. `/speckit.implement` executes only tasks already present in `tasks.md` and records receipt evidence; it must not invent validation strategy, add lifecycle roles, change requirements, update contracts, or widen scope during execution.

For Client Asset Contract entries, derive asset preparation, binding, implementation, and validation tasks in dependency order. Missing required client visual assets become readiness blockers; do not generate handoff fields or `allowed_write_paths`.

Use Visual Fidelity Readiness as the only visual planning readiness source. Do not create a second readiness rule from Screenshot Coverage Matrix, Visual Item Matrix, Visual Restoration Trace, or provider evidence artifacts; if required visual evidence is missing, report a readiness blocker instead of deriving complete-looking UI tasks.

Missing Required case scenarios must become blockers, not silently skipped tasks. If `checklists/behavior-testability.md` marks a case type Required but the matching BDD or behavior contract is absent and no `N/A or blocker` exists, report the missing case instead of generating a complete-looking task list.

## Test Strategy Derivation

Do not create or require a standalone test strategy artifact. Instead, derive the test level, fixture/mock/sandbox/real-system strategy, and inline evidence requirement while generating `tasks.md`.

Use this level-selection rule for each scenario or validation path:

- `unit`: pure domain rules, data validation, state transitions, or behavior assertions that do not cross a process, network, database, browser, or external-system boundary.
- `contract`: API, message, schema, BDD request/response, or Expected UIF `api_call` behavior that can be verified at an interface boundary.
- `integration`: service orchestration, persistence, async events, retries, rollback, callbacks, external sandbox calls, or `contracts/sequences.md` failure branches.
- `e2e`: user-visible journeys that require frontend/CLI interaction plus backend behavior, multiple services, or final feedback verification.

Use this data and external-system strategy:

- Attach fixture IDs and setup strategies from `contracts/behavior/` when they exist.
- Use fixture intent only when it is recorded in `research.md` or formal `contracts/behavior/` blocker notes for a scenario documented as `N/A or blocker`.
- Use mock, sandbox, or real-system decisions from `research.md`.
- External-system validation must use mock or sandbox unless `research.md` and `quickstart.md` explicitly require a real-system validation path.
- Add a separate validation task for high-risk, non-functional, external-system, async, retry, rollback, permission, validation, state_conflict, negative, boundary, or error behavior.

Every generated test or validation task must include an inline evidence requirement. Evidence must name at least one relevant BDD scenario, behavior assertion, API contract, UIF path, quickstart validation path, visual proof ref, screenshot ref, or command output.

Generate explicit validation tasks for the applicable scope instead of relying on final code review to perform first-line validation:

- Contract validation tasks bind contract ref -> implementation surface -> validation command -> evidence. If the mapping cannot be derived from `contracts/`, `research.md`, `quickstart.md`, or task context, report a readiness blocker instead of generating an implementation task that can drift from the interface contract.
- Visual verification or UI acceptance tasks bind Visual Item ID -> Visual Fidelity Readiness row -> viewport/state coverage -> proof level -> screenshot refs or visual proof refs -> quickstart validation path -> evidence.
- Data-side-effect validation tasks bind affected entity or state transition -> expected write behavior -> rollback, compensation, retry, migration, backfill, or invariant assertion when applicable -> validation command or evidence path.
- Integration or e2e validation tasks bind user-visible journey or cross-boundary flow -> scenario/assertion refs -> external-system strategy -> quickstart validation path -> captured command output.

Example task shape:

```markdown
- [ ] T012 [US2] Add contract test for SCN-004 using fixture FX-002; level: contract; strategy: fixture factory + payment sandbox mock; evidence: BDD scenario SCN-004, AST-007, contracts/api/refunds.openapi.yaml
- [ ] T013 [US2] Run integration validation for payment sandbox callback path; level: integration; strategy: sandbox callback replay; evidence: quickstart validation path QV-003 and captured command output
- [ ] T014 [US2] Run contract validation for contracts/api/refunds.openapi.yaml#/paths/~1refunds/post against src/routes/refunds.ts; level: contract; evidence: quickstart validation path QV-API-002 and captured command output
- [ ] T015 [US2] Run visual verification for Visual Item ID VI-REFUND-001 / VIS-001 at desktop and mobile default/error states; level: e2e; evidence: screenshot refs, visual proof ref VP-004, quickstart validation path QV-VIS-001, and captured command output
```

Behavior task derivation must be explicit:

- For each BehaviorScenarioInstance, create a fixture task, BDD/E2E or contract test task, implementation task, and verification evidence task unless the scenario is documented as `N/A` with a planning blocker.
- For each non-positive BehaviorScenarioInstance, derive fixture, contract or BDD test, implementation, and verification evidence tasks. The task text must preserve the negative, boundary, permission, validation, state_conflict, or error behavior and name the expected error code, failure feedback, and state invariant, rollback, or compensation assertion when present.
- For each UIF user_event, create the frontend, CLI, or interaction task that emits or handles the event.
- For each UIF api_call, create the backend/API or contract task that provides the declared method and path.
- For each quickstart validation path, create a validation task that can collect evidence for the relevant scenario IDs and assertions.

UI implementation and acceptance tasks must be paired when a user story includes `contracts/uif/`, visual acceptance requirements, Visual Fidelity Readiness rows, or Client Asset Contract entries:

- Create a UI implementation task for the concrete component, view, CLI surface, or interaction path that implements the referenced UIF event, UIF api_call, visual item, state, or asset binding.
- Create a paired UI acceptance task that verifies the same UIF path, Visual Item ID, scenario ID, asset contract entry, or quickstart validation path before the story is complete.
- Each UI acceptance task must name the required state coverage from the accepted contracts or readiness matrix, such as default, hover, focus, active, disabled, loading, empty, and error states.
- Each UI acceptance task must name the required viewport coverage from `research.md`, Visual Fidelity Readiness, or `quickstart.md` when responsive visual behavior is in scope.
- Each UI acceptance task must include evidence refs: at least one relevant UIF path, BDD or behavior scenario, visual proof ref, screenshot ref, quickstart validation path, API contract, or captured command output.
- If a required visual proof ref, screenshot ref, viewport/state coverage rule, Client Asset Contract entry, asset variant, or fallback policy is missing, report a readiness blocker from Visual Fidelity Readiness instead of generating a complete-looking UI implementation or acceptance task.

For each applicable Visual Fidelity Readiness row, generate a paired visual verification or UI acceptance task unless the row is Not Applicable or blocked. Do not read Figma, re-extract provider evidence, rebuild Visual Item Matrix, or re-decide visual readiness in tasks.

When an implementation task depends on `contracts/`, include a paired contract validation task that names the contract ref, expected implementation surface, validation command or quickstart path, and evidence requirement. Do not instruct implementers to modify `spec.md`, `contracts/`, readiness checklists, or Visual Fidelity Readiness to make implementation pass; report a blocker if implementation requires requirement or contract changes.

When persistence, migrations, external writes, retries, rollback, or compensation are in scope, include a data-side-effect validation task before final code review. The task must name the affected entity, expected mutation behavior, invariant or rollback/compensation assertion, and evidence source.

## Final Code Review

When generating `tasks.md`, append the final phase after user-story tasks in the same checklist format. Add code review tasks with review scopes: boundary, interface_contract, visual, data_side_effect, behavior_contract, sequence_consistency, and asset_binding when applicable. These tasks check design, sequence, visual implementation, and contract consistency against `class-diagram.md`, `contracts/sequences.md`, `contracts/`, `contracts/uif/`, `research.md`, `quickstart.md`, `spec.md` visual acceptance requirements, `spec.md` Client Asset Contract entries, and `checklists/behavior-testability.md` Visual Fidelity Readiness, plus data side-effect review and real e2e environment readiness.

Code review task text must require review of the actual implementation diff for runtime database writes and other persistent data changes, especially field-level update/delete behavior, bulk writes, soft deletes, ORM whole-object saves, migrations/backfills, retries, rollback/compensation, and external-system writes. Do not generate field-level mutation allowlists or pre-implementation data-write gates in normal tasks.

Code review task text must require boundary review: changed paths stay within the implement handoff boundary, implementation matches the referenced contracts, validation evidence covers quickstart or contract paths, and no implementation task changed `spec.md`, `contracts/`, readiness checklists, or Visual Fidelity Readiness to make execution pass.

Code review task text must require visual consistency review when UI or visual acceptance was in scope. The review must reconcile implemented UI states and viewport behavior with Visual Fidelity Readiness, UIF paths, screenshot refs, visual proof refs, and Client Asset Contract bindings, variants, and fallback policy. Visual implementation drift must be recorded as review findings or repaired through `consistency_repairs` when the implementation repair path is authorized.

Code review task evidence must require a `speckit.implement.receipt.v1` review receipt with `task_type: code_review`, `review_conclusion.checked_sources`, `data_side_effect_review`, `review_conclusion`, `consistency_repairs`, and `deferred_validation_todos`; empty arrays or objects indicate no entries. The task text must require quickstart/contract validation command evidence and state that implementation drift from the plan, sequences, contracts, or data side-effect review is repaired during `/speckit.implement` only by changing authorized implementation, test, fixture, configuration, or receipt paths. If the repair would require changing `spec.md`, `contracts/`, `research.md`, `quickstart.md`, readiness checklists, or planning artifacts, record a blocker or todo instead of treating the repair as executable implementation work. Real e2e environment gaps are recorded as todos instead of treated as passing evidence.

{CORE_TEMPLATE}
