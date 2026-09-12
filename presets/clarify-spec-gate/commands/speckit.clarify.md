---
description: Identify underspecified areas in the current feature spec, keeping spec-taxonomy items in this stage.
strategy: wrap
---

## Spec-vs-plan stage gate

This preset tightens deferral. Apply it while you scan the spec (the taxonomy lives in the core command below).

For every unchecked checklist item and every Partial/Missing taxonomy category, classify before considering deferral:

1. Match the item against the spec-oriented taxonomy in the core command.
2. A hit on any taxonomy category is a question candidate for this stage. Do not defer NFRs, acceptance/DoD testability, edge cases, UX empty states, domain constraints, or external-dependency failure modes.
3. Defer to planning only when the item is specifically about implementation method, tech-stack comparison, or task breakdown.
4. Mixed items (spec decision plus plan detail): split them and handle the spec part now.

If more than 60% of unresolved items would be marked Defer, pause, report the ratio, and re-check each against the taxonomy before continuing.

Do not use a vague "better deferred to planning" catch-all.

{CORE_TEMPLATE}

## Spec-taxonomy MUST-NOT

MUST NOT defer spec-taxonomy items to Plan. Concurrent-user volume, NFR quantification, acceptance-criteria testability, empty-state UX, and external-dependency failure modes are spec questions. How you implement pagination can wait. Whether the API paginates cannot.
