---
description: Wrap core checklist generation with behavior testability checks.
strategy: wrap
---

## Behavior Testability Checklist

When behavior drafts exist, create or update `checklists/behavior-testability.md` as checklist artifacts only.

Include these sections:

- Scenario Coverage
- Given Quality
- When Quality
- Then Quality
- Fixture Readiness
- Gaps

Check that each applicable user story has at least one scenario, each important business rule has positive or negative coverage, each Given maps to fixture intent, each When maps to an executable action or request case, and each Then maps to visible feedback, state, error code, or assertion.

{CORE_TEMPLATE}

## Behavior Checklist Reporting

Before finishing, report the behavior testability checklist status and call out unchecked items that block planning.
