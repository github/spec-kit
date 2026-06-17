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
- Visual Fidelity Readiness
- Non-Functional Requirement Readiness
- Gate Status
- Blocking Items

Check that each applicable user story has observable acceptance behavior, each acceptance criterion is verifiable, and primary, alternate, exception, boundary, permission, validation, and state-conflict paths are covered when applicable.

Check Given readiness from `spec.md`: required roles, permissions, starting state, entity state, and data are explicit enough for later fixture setup.

Check When readiness from `spec.md`: each trigger is an executable user action, request case, or system trigger.

Check Then readiness from `spec.md`: each outcome can become feedback, business state, error semantics, or assertion intent.

Check Visual Fidelity Readiness when `spec.md` contains Figma-derived requirements.
Require source traceability, ready gate evidence, and clear visual requirements for
state, responsive, accessibility, component mapping, and accepted exception
coverage. Missing raw metadata completeness, metadata index completeness proof,
node inventory parity, or blocker lint errors are blocking items for
Figma-derived requirements.

Check Non-Functional Requirement Readiness from `spec.md`: applicable performance, security and privacy, reliability and recovery, accessibility, compliance and auditability, observability, compatibility, data lifecycle, and cost or operational constraints are explicitly declared in `spec.md` as `Required`, `Not Applicable`, or `Unknown`.

For each NFR dimension, require either verifiable product-level criteria, a `Not Applicable` rationale, or an `Unknown` marker that identifies what must be clarified. Do not require technical designs such as SLAs, RTO/RPO formulas, cache layers, queues, deployment topology, or infrastructure choices unless the product requirement already states them.

Treat these NFR readiness gaps as blocking items: Required but missing from `spec.md`; Required but not verifiable from product-level criteria; Unknown and affects downstream design. Do not block planning for NFR dimensions marked `Not Applicable` with a rationale or for dimensions with explicit no-special-requirement statements.

Set `Gate Status: PASS` only when every applicable readiness item is checked and `Blocking Items: none`. Otherwise set `Gate Status: BLOCKED` and list each unchecked readiness item that prevents behavior projection or downstream planning.

Unchecked readiness items that prevent behavior projection or downstream planning are blocking items. Do not proceed to `/speckit.plan`; Return to `/speckit.clarify` or `/speckit.specify` to resolve missing requirements before planning.

{CORE_TEMPLATE}

## Behavior Checklist Reporting

Before finishing, report the BDD readiness status and call out unchecked items that block planning.
