---
description: Wrap core clarification with behavior-driven ambiguity checks.
strategy: wrap
---

## Behavior Clarification Policy

Use `spec.md` and these behavior drafts, when present, as clarification inputs:

- `behavior/bdd.draft.feature`
- `behavior/behavior-scenarios.draft.json`
- `behavior/uif.intent.json`
- `behavior/data-fixtures.intent.json`
- `behavior/open-questions.json`

Review BDD draft steps for ambiguity:

- Given: user role, permissions, starting view, fixture data, and entity states are explicit.
- When: each action is executable by a user, system, or request case.
- Then: each expected outcome has user-visible feedback, business state, error code, or assertion target.
- Coverage: important success, rejection, validation, permission, boundary, and state-conflict behavior is covered when applicable.

Write unresolved gaps to `behavior/open-questions.json`. Update `spec.md` and behavior drafts only after user-provided answers make the requirement clear.

{CORE_TEMPLATE}

## Behavior Clarification Reporting

Before finishing, report answered questions, newly opened questions, and any behavior drafts updated from user-provided answers.
