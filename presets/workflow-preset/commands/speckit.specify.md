---
description: Wrap core specification with requirement-phase behavior drafts.
strategy: wrap
---

## Behavior Draft Policy

During specification, keep product requirements in `spec.md` and add requirement-phase behavior drafts when the feature has user-visible behavior, state-dependent rules, or acceptance scenarios.

Create or update these draft artifacts under the feature directory:

- `behavior/bdd.draft.feature`: readable BDD draft scenarios.
- `behavior/behavior-scenarios.draft.json`: structured draft scenario IDs, Given inputs, When actions, Then outcomes, and source.
- `behavior/uif.intent.json`: interaction intent extracted from user behavior and requirements.
- `behavior/data-fixtures.intent.json`: data setup intent required by draft scenarios.
- `behavior/open-questions.json`: unresolved requirement questions found while drafting behavior.

These files are requirement-phase behavior drafts. Keep them concise and traceable to `spec.md`; leave technology binding, formal API/UIF/behavior contracts, and validation commands for planning artifacts.

BDD draft quality rules:

- Scenario type coverage: include positive, negative, boundary, permission, validation, and state_conflict scenarios when those behaviors are present or implied by the requirements.
- Given/When/Then mapping: every drafted scenario must keep each step mappable to a later planning artifact.
- Given maps to fixture, actor, starting view, or state.
- When maps to user event, request intent, or system trigger.
- Then maps to feedback, business state, error, or assertion intent.
- If a scenario type is not applicable or cannot be drafted from current requirements, record the reason in `behavior/open-questions.json` or the final behavior draft report.

Structured JSON draft artifacts must follow their matching `schemas/speckit.behavior.*.schema.json` contracts.

{CORE_TEMPLATE}

## Behavior Draft Reporting

Before finishing, report which behavior drafts were created or updated and list unresolved questions separately from confirmed requirements.
