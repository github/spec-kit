# Behavior Testability Checklist

## User Story Readiness
- [ ] Each applicable user story has observable acceptance behavior.
- [ ] Each story identifies the actor or system responsible for the behavior.
- [ ] Each story has enough context to distinguish primary, alternate, and exception behavior when applicable.

## Acceptance Criteria Quality
- [ ] Acceptance criteria are observable and verifiable from `spec.md`.
- [ ] Acceptance criteria avoid implementation-only wording.
- [ ] Business rules include precise success, rejection, validation, permission, boundary, and state_conflict outcomes when applicable.

## Scenario Coverage
- [ ] Primary success behavior is covered.
- [ ] Alternate and exception behavior is covered when applicable.
- [ ] Boundary, permission, validation, and state_conflict behavior is covered when applicable.

## Case Coverage Matrix
For each user story or capability, record one row per story or capability case type. Status: Required|Not Applicable|Unknown.

| Case ID | Story/Capability | Case Type | Status | Source `spec.md` section | Blocking Item ID | Rationale |
| --- | --- | --- | --- | --- | --- | --- |
| CASE-PERMISSION-001 | Example | permission | Required | `spec.md#...` |  | reason |
| CASE-BOUNDARY-001 | Example | boundary | Not Applicable | `spec.md#...` |  | reason |
| CASE-VALIDATION-001 | Example | validation | Unknown | `spec.md#...` | BI-... | missing rule |

- [ ] Required case type must cite the source `spec.md` section.
- [ ] Each row must have a stable Case ID.
- [ ] Scenario IDs and `case_coverage_blockers` are assigned during `/speckit.plan`.
- [ ] Not Applicable requires rationale.
- [ ] Unknown must appear in Blocking Items.

## Given Readiness
- [ ] Required roles and permissions are explicit.
- [ ] Required starting state, entity state, and data are explicit enough for later fixture setup.
- [ ] Required data does not depend on production-only records.

## When Readiness
- [ ] Each trigger is an executable user action, request case, or system trigger.
- [ ] Required inputs, selections, uploads, and submitted values are explicit.

## Then Readiness
- [ ] Each outcome maps to user feedback, business state, error semantics, or assertion intent.
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
- [ ] Apply this section when `spec.md` contains design-derived requirements, a design source, provider evidence blockers, or provider-specific design evidence requests. Also apply it when `spec.md` contains product-side visual requirements such as pixel-perfect, brand-critical, responsive visual, or UI visual acceptance requirements.
- [ ] Design-derived requirements identify the design source, provider source refs, and required fidelity.
- [ ] Design-derived requirements record provider readiness status, evidence refs, and blockers when provider evidence is required.
- [ ] Visual Fidelity Evidence Matrix rows cite source `spec.md` sections, evidence refs, required screenshot level, blocking item IDs, and accepted exception rules.
- [ ] Visual Fidelity Evidence Matrix is the only artifact that decides visual planning readiness, proof level sufficiency, screenshot sufficiency, accepted exception rules, Gate Status, and Blocking Items.
- [ ] Visual Fidelity Evidence Matrix reads visual facts from `spec.md` and evidence refs; it does not call Figma, re-extract provider evidence, rebuild provider matrices, or create another visual readiness path.
- [ ] Use one Visual Fidelity Evidence Matrix as the single visual readiness record; do not duplicate visual evidence decisions outside the matrix and Blocking Items.
- [ ] Do not add historical visual rules or alternate visual decision paths.

## Visual Fidelity Evidence Matrix

| Visual Item ID | Source `spec.md` section | Fidelity Scope | Screenshot Level | Evidence Refs | Visual Proof Required | Blocking Item ID | Exception Rule |
| --- | --- | --- | --- | --- | --- | --- | --- |
| VIS-001 | `spec.md#...` | functional-equivalent|design-system-faithful|pixel-perfect|brand-critical|responsive-visual | L0|L1|L2|L3 | provider/screenshot refs or none | yes|no | BI-... or none | EX-... or none |

- [ ] Screenshot evidence level is declared when screenshots are required: L0|L1|L2|L3.
- [ ] visual proof refs point to provider evidence or screenshot sources.
- [ ] declared visual proof required is recorded when `spec.md` makes screenshot-backed visual proof mandatory.
- [ ] Ordinary UI visual requirements may use L1 Key Screenshots; `spec.md` visual proof requirements require L1 or higher.
- [ ] L2 State + Viewport Matrix covers key page, state, and viewport combinations for complex UI, responsive, or multi-state requirements.
- [ ] L3 Visual Baseline is present for high-fidelity visual matching, pixel-perfect requirements, brand-critical pages, design systems, or visual regression.
- [ ] Missing screenshot evidence sets Gate Status: BLOCKED and lists the item in Blocking Items when visual proof is required.
- [ ] High-fidelity requirements without L3 screenshot evidence set Gate Status: BLOCKED and lists the item in Blocking Items.
- [ ] Pixel-perfect requirements without L3 screenshot evidence set Gate Status: BLOCKED and lists the item in Blocking Items.
- [ ] Responsive visual requirements block PASS only when they are complex, multi-state, or declare L2 or L3 visual proof; missing viewport-specific evidence then sets Gate Status: BLOCKED and lists the item in Blocking Items.
- [ ] Complex UI or multi-state requirements without L2 or L3 screenshot evidence set Gate Status: BLOCKED and lists the item in Blocking Items.
- [ ] Layout, spacing, typography, colors, effects, assets, and clipping requirements are explicit.
- [ ] Required client visual assets have source refs, asset source strategy, required variants, fallback policy, and blocker status.
- [ ] Required component mappings and variant coverage are explicit or marked as blocking clarification items.
- [ ] Default, hover, focus, active, disabled, loading, empty, and error states are explicit or marked as missing.
- [ ] Required breakpoints, reflow rules, scrolling, minimum widths, safe areas, and responsive behavior is explicit.
- [ ] Copy, icons, images, fonts, numeric formats, and placeholder content are explicit.
- [ ] Keyboard, focus, semantics, contrast, ARIA, form error behavior, and accessibility requirements are explicit.
- [ ] Accepted visual differences are defined as traceable exception rules.

## Gate Status
Gate Status: PASS|BLOCKED
Blocking Items:
- none
