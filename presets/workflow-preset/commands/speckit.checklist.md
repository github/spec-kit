---
description: Wrap core checklist generation with BDD readiness gate.
strategy: wrap
---

## BDD Readiness Gate

Create or update `checklists/behavior-testability.md` as checklist artifacts only. This checklist is the plan-entry quality gate for BDD readiness and must evaluate requirements directly from `spec.md`; it must not depend on behavior drafts.

Include these sections:

- User Story Readiness
- Acceptance Criteria Quality
- Scenario Coverage
- Given Readiness
- When Readiness
- Then Readiness
- Gate Status
- Blocking Items

Check that each applicable user story has observable acceptance behavior, each acceptance criterion is verifiable, and primary, alternate, exception, boundary, permission, validation, and state-conflict paths are covered when applicable.

Check Given readiness from `spec.md`: required roles, permissions, starting state, entity state, and data are explicit enough for later fixture setup.

Check When readiness from `spec.md`: each trigger is an executable user action, request case, or system trigger.

Check Then readiness from `spec.md`: each outcome can become feedback, business state, error semantics, or assertion intent.

Set `Gate Status: PASS` only when every applicable readiness item is checked and `Blocking Items: none`. Otherwise set `Gate Status: BLOCKED` and list each unchecked readiness item that prevents behavior projection.

Unchecked readiness items that prevent behavior projection are blocking items. Do not proceed to `/speckit.plan`; Return to `/speckit.clarify` or `/speckit.specify` to resolve missing requirements before planning.

{CORE_TEMPLATE}

## Behavior Checklist Reporting

Before finishing, report the BDD readiness status and call out unchecked items that block planning.
