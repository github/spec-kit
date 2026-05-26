# Behavior Testability Checklist

## Scenario Coverage
- [ ] Each applicable user story has at least one BDD scenario.
- [ ] Each important success path has positive scenario coverage.
- [ ] Each important business restriction has negative scenario coverage.
- [ ] Each important boundary, permission, validation, or state-conflict rule is covered when applicable.

## Given Quality
- [ ] Each Given maps to fixture intent, user role, permission, entity state, or starting view.
- [ ] Entity states are precise enough for test setup.
- [ ] Fixtures do not require production data.

## When Quality
- [ ] Each When is executable as a user event, request case, or system trigger.
- [ ] Inputs, selections, uploads, and submit actions include required parameters.

## Then Quality
- [ ] Each Then has visible feedback, business state, error code, or assertion target.
- [ ] Failure scenarios include precise feedback or error semantics.

## Fixture Readiness
- [ ] Each scenario can be set up from declared fixture intent.

## Gaps
- [ ] Open behavior questions are recorded in `behavior/open-questions.json`.
