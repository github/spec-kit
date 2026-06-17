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

## Non-Functional Requirement Readiness
- [ ] Performance - Status: Required|Not Applicable|Unknown; requirement or rationale is explicitly declared in `spec.md`.
- [ ] Security and Privacy - Status: Required|Not Applicable|Unknown; requirement or rationale is explicitly declared in `spec.md`.
- [ ] Reliability and Recovery - Status: Required|Not Applicable|Unknown; requirement or rationale is explicitly declared in `spec.md`.
- [ ] Accessibility - Status: Required|Not Applicable|Unknown; requirement or rationale is explicitly declared in `spec.md`.
- [ ] Compliance and Auditability - Status: Required|Not Applicable|Unknown; requirement or rationale is explicitly declared in `spec.md`.
- [ ] Observability - Status: Required|Not Applicable|Unknown; requirement or rationale is explicitly declared in `spec.md`.
- [ ] Compatibility - Status: Required|Not Applicable|Unknown; requirement or rationale is explicitly declared in `spec.md`.
- [ ] Data Lifecycle - Status: Required|Not Applicable|Unknown; requirement or rationale is explicitly declared in `spec.md`.
- [ ] Cost and Operational Constraints - Status: Required|Not Applicable|Unknown; requirement or rationale is explicitly declared in `spec.md`.
- [ ] Required NFR entries have verifiable product-level criteria without prescribing architecture.
- [ ] Unknown NFR entries that affect downstream design are listed as blocking items.

## Visual Fidelity Readiness
- [ ] Figma-derived requirements identify the source Figma URL, frame or node IDs, and required fidelity.
- [ ] Figma intake ready gate evidence in `spec.md` shows raw metadata completeness, metadata index completeness proof, node inventory parity, and no blocker lint errors.
- [ ] Layout, spacing, typography, colors, effects, assets, and clipping requirements are explicit.
- [ ] Required component mappings and variant coverage are explicit or marked as blocking clarification items.
- [ ] Default, hover, focus, active, disabled, loading, empty, and error states are explicit or marked as missing.
- [ ] Required breakpoints, reflow rules, scrolling, minimum widths, safe areas, and responsive behavior is explicit.
- [ ] Copy, icons, images, fonts, numeric formats, and placeholder content are explicit.
- [ ] Keyboard, focus, semantics, contrast, ARIA, form error behavior, and accessibility requirements are explicit.
- [ ] Visual differences that may be accepted are defined as traceable exception rules.

## Gate Status
Gate Status: PASS|BLOCKED
Blocking Items:
- none
