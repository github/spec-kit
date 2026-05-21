---
description: Wrap task generation with optional design artifact awareness.
strategy: wrap
---

## Additional Design Inputs

When present, treat these files as optional design documents under FEATURE_DIR:

- `class-diagram.md`: internal object structure, dependency direction, and design pattern participants.
- `contracts/sequences.md`: service, command, event, async, retry, rollback, and failure-path flows.
- `test-plan.md`: validation objectives, test levels, data strategy, traceability, and scenario matrix.

Use these inputs to derive implementation, integration, orchestration, failure-handling, and validation tasks. Keep task output in the existing checklist format and user-story organization.

{CORE_TEMPLATE}
