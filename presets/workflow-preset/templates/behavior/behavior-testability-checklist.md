# Behavior Testability Checklist

## User Story Readiness
- [ ] Each applicable user story has observable acceptance behavior.
- [ ] Each story identifies the actor or system responsible for the behavior.
- [ ] Each story has enough context to distinguish primary, alternate, and exception behavior when applicable.

## Acceptance Criteria Quality
- [ ] Acceptance criteria are observable and verifiable from `spec.md`.
- [ ] Acceptance criteria avoid implementation-only wording.
- [ ] Business rules include precise success, rejection, validation, permission, boundary, and state-conflict outcomes when applicable.

## Scenario Coverage
- [ ] Primary success behavior is covered.
- [ ] Alternate and exception behavior is covered when applicable.
- [ ] Boundary, permission, validation, and state-conflict behavior is covered when applicable.

## Given Readiness
- [ ] Required roles and permissions are explicit.
- [ ] Required starting state, entity state, and data are explicit enough for later fixture setup.
- [ ] Required data does not depend on production-only records.

## When Readiness
- [ ] Each trigger is an executable user action, request case, or system trigger.
- [ ] Required inputs, selections, uploads, and submitted values are explicit.

## Then Readiness
- [ ] Each outcome can become user feedback, business state, error semantics, or assertion intent.
- [ ] Failure outcomes include precise feedback or error semantics.

## Gate Status
Gate Status: PASS|BLOCKED
Blocking Items:
- none
