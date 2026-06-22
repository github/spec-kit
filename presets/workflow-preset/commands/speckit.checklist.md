---
description: Wrap core checklist generation with BDD, NFR, and Visual Fidelity readiness gate.
strategy: wrap
---

## Checklist Purpose: "Unit Tests for English"

This wrapper must not redefine core-owned User Input, Pre-Execution Checks, extension hooks, base path resolution, or core file handling.

Checklists validate whether requirements are complete, clear, consistent, measurable, and ready for downstream planning. NOT for verification/testing: do not test implementation behavior, code execution, UI rendering, API responses, or whether the built system works.

CORE PRINCIPLE - Test the Requirements, Not the Implementation. Checklist questions must use requirement-quality forms such as "Are ... specified?", "Is ... quantified?", "Can ... be objectively verified?", or "Are ... requirements consistent?"

Use `$ARGUMENTS` as checklist intent. Generate dynamic clarifying questions with no pre-baked catalog only when the answer changes BDD, NFR, or Visual Fidelity checklist content. Use Q1/Q2/Q3 for initial questions and Q4/Q5 only for justified follow-up gaps.

For `checklists/behavior-testability.md`, create the file when absent; otherwise append or update without deleting existing checklist content. Before finishing, report the full path, item count, update mode, focus areas, depth level, actor/timing, must-have items, readiness status, and blockers.

## BDD Readiness Gate

Create or update `checklists/behavior-testability.md` as checklist artifacts only. This checklist is the plan-entry quality gate for BDD readiness and must evaluate requirements directly from `spec.md`; it must not depend on behavior drafts.

Include these sections:

- User Story Readiness
- Acceptance Criteria Quality
- Scenario Coverage
- Case Coverage Matrix
- Given Readiness
- When Readiness
- Then Readiness
- Visual Fidelity Readiness
- Visual Fidelity Evidence Matrix
- Non-Functional Requirement Readiness
- Gate Status
- Blocking Items

Check that each applicable user story has observable acceptance behavior, each acceptance criterion is verifiable, and primary, alternate, exception, boundary, permission, validation, and state_conflict paths are covered when applicable.

Build a Case Coverage Matrix with one row per story or capability case type. Use case status: Required|Not Applicable|Unknown. Cover positive, negative, boundary, permission, validation, and state_conflict case types. Each row must have a stable Case ID. Required rows must cite the source `spec.md` section. Scenario IDs and `case_coverage_blockers` are assigned during `/speckit.plan`. Not Applicable requires rationale. Unknown must appear in Blocking Items. Required case type without observable acceptance behavior blocks PASS.

Check Given readiness from `spec.md`: required roles, permissions, starting state, entity state, and data are explicit enough for later fixture setup.

Check When readiness from `spec.md`: each trigger is an executable user action, request case, or system trigger.

Check Then readiness from `spec.md`: each outcome maps to feedback, business state, error semantics, or assertion intent.

Check Visual Fidelity Readiness when `spec.md` contains design-derived requirements, a design source, provider evidence blockers, or provider-specific design evidence requests. Also apply it when `spec.md` contains product-side visual requirements such as pixel-perfect, brand-critical, responsive visual, or UI visual acceptance requirements.
Use the behavior-testability checklist template as the visual gate authority.
Require source traceability, provider readiness status, evidence refs, and blockers, and clear visual requirements for state, responsive, accessibility, component mapping, and accepted exception coverage.
Build a Visual Fidelity Evidence Matrix with one row per visual requirement or visual proof obligation. Record Screenshot evidence level, declared visual proof required, provider evidence refs or screenshot refs, and any Gate Status: BLOCKED item in Blocking Items.
The Visual Fidelity Evidence Matrix alone decides visual planning readiness, proof level sufficiency, screenshot sufficiency, accepted exception rules, Gate Status, and Blocking Items.
Use one Visual Fidelity Evidence Matrix as the single visual readiness record; do not duplicate visual evidence decisions outside the matrix and Blocking Items.
Read visual facts from `spec.md` and evidence refs; do not call Figma, re-extract Figma evidence, rebuild provider matrices, or create another visual readiness path.
Do not add historical visual rules or alternate visual decision paths.
Responsive visual requirements block PASS only when they are complex, multi-state, or declare L2 or L3 visual proof; missing viewport-specific evidence then sets Gate Status: BLOCKED and lists the item in Blocking Items.
Screenshots support visual facts but do not create product semantics.

Check Non-Functional Requirement Readiness from `spec.md`: applicable performance, security and privacy, reliability and recovery, accessibility, compliance and auditability, observability, compatibility, data lifecycle, and cost or operational constraints are explicitly declared in `spec.md` as `Required`, `Not Applicable`, or `Unknown`.

For each NFR dimension, require either verifiable product-level criteria, a `Not Applicable` rationale, or an `Unknown` marker that identifies what must be clarified. Do not require technical designs such as SLAs, RTO/RPO formulas, cache layers, queues, deployment topology, or infrastructure choices unless the product requirement already states them.

Treat these NFR readiness gaps as blocking items: Required but missing from `spec.md`; Required but not verifiable from product-level criteria; Unknown and affects downstream design. Do not block planning for NFR dimensions marked `Not Applicable` with a rationale or for dimensions with explicit no-special-requirement statements.

Set `Gate Status: PASS` only when every applicable readiness item is checked and `Blocking Items: none`. Otherwise set `Gate Status: BLOCKED` and list each unchecked readiness item that prevents behavior projection or downstream planning.

Unchecked readiness items that prevent behavior projection or downstream planning are blocking items. Do not proceed to `/speckit.plan`. Requirement ambiguity returns to `/speckit.clarify` or `/speckit.specify` to resolve missing requirements before planning. Provider evidence readiness blockers return to `/speckit.specify` or provider intake, not `/speckit.clarify`.

{CORE_TEMPLATE}

## Behavior Checklist Reporting

Before finishing, report the BDD, NFR, and Visual Fidelity readiness status and call out unchecked items that block planning.
