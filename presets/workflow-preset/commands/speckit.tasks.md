---
description: Wrap task generation with optional design artifact awareness.
strategy: wrap
---

## Change Scope Granularity

Preserve the planned `M + U` scope in task text when deriving implementation, validation, and integration tasks. Do not generate handoff fields or `allowed_write_paths`.

## Additional Design Inputs

When present, treat these files as optional task-generation inputs under FEATURE_DIR:

- `class-diagram.md`: internal object structure, dependency direction, and design pattern participants.
- `contracts/sequences.md`: service, command, event, async, retry, rollback, and failure-path flows.
- `research.md`: selected test level, fixture strategy, mock/external-system strategy, and error-branch validation decisions.
- `quickstart.md`: executable validation paths and evidence collection guidance.
- `contracts/bdd/`: formal BDD acceptance contracts.
- `contracts/uif/`: Expected UIF interaction contracts.
- `contracts/behavior/`: formal scenario instance, fixture, and assertion contracts.
- `contracts/`: interface schemas and API/message contracts used by validation tasks.

Use these inputs to derive implementation, integration, orchestration, failure-handling, and validation tasks. For behavior contracts, derive test-first tasks in user-story order: fixture setup, BDD/E2E or contract test, implementation, and verification evidence. Keep task output in the existing checklist format and user-story organization.

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
- Prefer mock or sandbox for external systems unless `research.md` and `quickstart.md` explicitly require a real-system validation path.
- Add a separate validation task for high-risk, non-functional, external-system, async, retry, rollback, permission, validation, state-conflict, or security-relevant behavior.

Every generated test or validation task must include an inline evidence requirement. Evidence should name the relevant BDD scenario, behavior assertion, API contract, UIF path, quickstart validation path, or command output.

Example task shape:

```markdown
- [ ] T012 [US2] Add contract test for SCN-004 using fixture FX-002; level: contract; strategy: fixture factory + payment sandbox mock; evidence: BDD scenario SCN-004, AST-007, contracts/api/refunds.openapi.yaml
- [ ] T013 [US2] Run integration validation for payment sandbox callback path; level: integration; strategy: sandbox callback replay; evidence: quickstart validation path QV-003 and captured command output
```

Behavior task derivation must be explicit:

- For each BehaviorScenarioInstance, create a fixture task, BDD/E2E or contract test task, implementation task, and verification evidence task unless the scenario is documented as `N/A` with a planning blocker.
- For each UIF user_event, create the frontend, CLI, or interaction task that emits or handles the event.
- For each UIF api_call, create the backend/API or contract task that provides the declared method and path.
- For each quickstart validation path, create a validation task that can collect evidence for the relevant scenario IDs and assertions.

## Final Code Review

When generating `tasks.md`, append the final phase after user-story tasks in the same checklist format. Add code review tasks that check design, sequence, and contract consistency against `class-diagram.md`, `contracts/sequences.md`, `contracts/`, `research.md`, and `quickstart.md`, plus real e2e environment readiness.

Code review task evidence must require a `speckit.implement.receipt.v1` review receipt with `task_type: code_review`, `review_conclusion.checked_sources`, plus `review_conclusion` and, when applicable, `consistency_repairs` and `deferred_validation_todos`. The task text must require quickstart/contract validation command evidence and state that implementation drift from the plan, sequences, or contracts is repaired during `/speckit.implement` when the repair path is authorized; real e2e environment gaps are recorded as todos instead of treated as passing evidence.

{CORE_TEMPLATE}
