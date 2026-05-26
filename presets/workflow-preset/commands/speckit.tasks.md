---
description: Wrap task generation with optional design artifact awareness.
strategy: wrap
---

## Additional Design Inputs

When present, treat these files as optional design documents under FEATURE_DIR:

- `class-diagram.md`: internal object structure, dependency direction, and design pattern participants.
- `contracts/sequences.md`: service, command, event, async, retry, rollback, and failure-path flows.
- `test-plan.md`: validation objectives, test levels, data strategy, traceability, and scenario matrix.
- `contracts/bdd/`: formal BDD acceptance contracts.
- `contracts/uif/`: Expected UIF interaction contracts.
- `contracts/behavior/`: formal scenario instance, fixture, and assertion contracts.

Use these inputs to derive implementation, integration, orchestration, failure-handling, and validation tasks. For behavior contracts, derive test-first tasks in user-story order: fixture setup, BDD/E2E or contract test, implementation, and verification evidence. Keep task output in the existing checklist format and user-story organization.

Behavior task derivation must be explicit:

- For each BehaviorScenarioInstance, create a fixture task, BDD/E2E or contract test task, implementation task, and verification evidence task unless the scenario is documented as `N/A` with a planning blocker.
- For each UIF user_event, create the frontend, CLI, or interaction task that emits or handles the event.
- For each UIF api_call, create the backend/API or contract task that provides the declared method and path.
- For each quickstart validation path, create a validation task that can collect evidence for the relevant scenario IDs and assertions.

{CORE_TEMPLATE}
