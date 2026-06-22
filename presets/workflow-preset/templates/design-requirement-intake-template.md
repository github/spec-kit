# Design Requirement Intake

Purpose: normalize provider-neutral design requirements before Requirement Merge writes `spec.md`.

## Design Sources

- Source type:
- Source URL or path:
- Provider Evidence:
- Capture timestamp:
- Required fidelity:

## Page Inventory

- Page or screen:
- Purpose:
- Source refs:

## Page Hierarchy

- Navigation structure:
- Parent / child relationships:
- Modal, drawer, or overlay relationships:

## User Paths

- Entry point:
- Interaction path:
- Destination or outcome:
- Missing path evidence:

## Component Inventory

- Component:
- Required variants:
- Source refs:
- Existing code constraint, only if explicitly provided:

## Component States

- Default:
- Hover / focus / active:
- Disabled:
- Loading:
- Empty:
- Error:
- Success:

## Interaction Rules

- User action:
- System response:
- Validation or guard:
- Feedback:

## Visual Tokens

- Typography:
- Color:
- Spacing:
- Radius:
- Effects:
- Assets:

## Layout Rules

- Grid or alignment:
- Sizing:
- Scroll behavior:
- Clipping:
- Safe areas:

## Responsive Rules

- Breakpoints:
- Reflow behavior:
- Minimum and maximum widths:
- Long-copy handling:

## Motion Rules

- Transition:
- Duration:
- Easing:
- Reduced-motion requirement:

## State Coverage

- Covered states:
- Missing states:
- Items marked `[NEEDS CLARIFICATION]`:

## Visual Acceptance Requirements

- Required fidelity:
- Visual difference tolerance:
- Accepted exceptions:
- Accessibility requirements:

## Visual Restoration Trace

Use one row per accepted Visual Item ID from provider evidence. Each row records the minimum facts needed to preserve UI/UX intent without re-reading provider tools.
Do not copy the full provider Visual Item Matrix. Record only requirement-level facts promoted toward `spec.md`, supporting evidence refs, and unresolved provider or requirement gaps. Visual Restoration Trace must not decide visual planning readiness, proof sufficiency, accepted exception rules, checklist Gate Status, or checklist Blocking Items.

- Visual Item ID:
- Provider source refs:
- Requirement ID:
- UI surface:
- Fidelity scope: functional-equivalent|design-system-faithful|pixel-perfect|brand-critical|responsive-visual
- Layout constraints:
- Typography constraints:
- Color/token constraints:
- Effect constraints:
- Asset bindings:
- Requirement-level component role:
- Variant/state coverage:
- Component use constraint: visual-reference-only|must-reuse-existing|figma-export-required|unspecified
- Constraint source refs:
- Copy/content constraint: no-new-copy|figma-copy-required|product-copy-required|unspecified
- Drawing/asset constraint: no-self-draw|figma-export-required|existing-asset-required|unspecified
- Required states:
- Required viewport coverage:
- Screenshot refs:
- Visual proof refs:
- Allowed deviations:
- Blocking item:

## Client Asset Contract

- Asset ID:
- Required resource type:
- Source refs:
- Asset source strategy:
- Required variants:
- Fallback policy:
- Blocker status:

## Screenshot Traceability

Design Requirement Intake remains provider-neutral.

Screenshot-derived visual facts must include screenshot refs; screenshots must not create product semantics.
Keep screenshot files in provider evidence or `sources/`;
record only requirement-level references here.
Screenshot Traceability records supported facts and unsupported assumptions only. It must not create an independent visual readiness decision.

- Requirement ID:
- Screenshot refs:
- Visual proof refs:
- Supported visual facts:
- Unsupported assumptions:
- Confidence:

## Traceability

- Requirement ID:
- Visual Item ID:
- Source refs:
- Confidence:
- Provider notes:
