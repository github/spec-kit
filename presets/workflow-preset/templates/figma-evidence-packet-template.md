# Figma Evidence Packet

Purpose: normalize Figma design evidence before Design Requirement Intake and
`/speckit.specify`. Readiness gate: `templates/figma-intake-contract.md`.

## Figma Source

- File URL:
- Page / Frame / Node IDs:
- Design version / timestamp:
- Target platform:
- Required fidelity:

## Extraction Context

- Runtime agent:
- Figma MCP availability:
- Screenshots captured:
- Variables / styles captured:
- Component metadata captured:

## Screenshot Evidence

Screenshot evidence must declare L0-L3 coverage and coverage gaps. Screenshots are visual proof, not the primary Design Requirement Intake carrier.
Constraint: screenshot-derived visual facts require screenshot refs and must not replace Design Requirement Intake.
Screenshot evidence and the Screenshot Coverage Matrix record coverage facts and gaps only. They must not decide visual planning readiness, proof sufficiency, accepted exception rules, checklist Gate Status, or checklist Blocking Items.

- Screenshot level: L0|L1|L2|L3
- L0: no screenshot evidence
- L1: static screenshot reference
- L2: viewport or state screenshot coverage
- L3: visual diff baseline or approved visual proof
- L3 applies to high-fidelity, pixel-perfect, brand-critical, design-system, or visual regression work

## Screenshot Coverage Matrix

- Requirement ID:
- Screenshot level:
- Screenshot refs:
- Frame / node refs:
- Viewport:
- State:
- Capture timestamp:
- Design version:
- Redaction required:
- Baseline usage:
- Missing coverage:
- Blocking item:
- Visual baseline usage: none|manual review|visual diff

## Figma Intake Readiness

Figma Intake Readiness is provider source readiness only. It proves raw Figma metadata and inventory completeness before evidence can be consumed; it is separate from Visual Fidelity planning readiness, which is decided only by the checklist Visual Fidelity Evidence Matrix.

- figma-metadata.part-*.xml:
- figma-metadata.index.yaml:
- figma-node-inventory.yaml:
- raw metadata completeness:
- metadata index completeness proof:
- node inventory parity:
- blocker lint errors:
- ready gate: PASS|BLOCKED

## Evidence Record Format

Record schema for observed, inferred, missing, and out-of-scope facts.

- Fact ID:
- Evidence type: Observed|Inferred|Missing|Out of Scope
- Source refs: file/page/frame/node/component/screenshot
- Raw Figma value:
- Normalized requirement:
- Confidence:
- Spec target:

## Observed from Figma

- Layout hierarchy:
- Spacing / sizing / grid:
- Typography:
- Colors / tokens:
- Effects:
- Assets:
- Components / variants:
- Prototype links:

## Inferred from Structure

- Likely navigation:
- Likely grouping:
- Likely content priority:
- Confidence notes:

## Missing / Needs Clarification

- Business semantics:
- Dynamic states:
- Responsive behavior:
- Permissions:
- Validation:
- Error handling:
- Data source:
- Analytics / tracking:
- Items marked `[NEEDS CLARIFICATION]`:

## Out of Scope

- Figma content not included in this extraction:
- Runtime behavior not represented by the selected frames:
- Explicit exclusions:

## Visual Facts for Spec

- Layout and spacing:
- Typography and color:
- Assets and content:
- States observed or missing:
- Responsive evidence:
- Accessibility evidence:
- Accepted exceptions:

## Visual Item Matrix

Use one row per restorable UI surface, component, state, or visual proof obligation.
Visual Item IDs must be stable enough to carry into Design Requirement Intake, `spec.md`, and the Visual Fidelity Evidence Matrix.
The Visual Item Matrix records provider-normalized visual facts, observed state and viewport evidence, proof refs, and provider evidence blockers. It must not decide visual planning readiness, proof level sufficiency, accepted exception rules, checklist Gate Status, or checklist Blocking Items.

- Visual Item ID:
- Figma frame/node refs:
- Requirement target:
- UI surface:
- Required fidelity: functional-equivalent|design-system-faithful|pixel-perfect|brand-critical|responsive-visual
- Layout facts:
- Typography facts:
- Color/token facts:
- Effect facts:
- Asset refs:
- Variant/state evidence:
- Component requirement role:
- Component use constraint: visual-reference-only|must-reuse-existing|figma-export-required|unspecified
- Constraint source refs:
- Copy/content constraint: no-new-copy|figma-copy-required|product-copy-required|unspecified
- Drawing/asset constraint: no-self-draw|figma-export-required|existing-asset-required|unspecified
- Required states:
- Required viewport coverage:
- Screenshot refs:
- Visual proof level: L0|L1|L2|L3
- Allowed deviations:
- Blockers:
- Spec requirement target:

## Client Asset Inventory

- Asset ID:
- Asset role:
- Resource type: image|icon|video|lottie|svg|font
- Figma node/component ref:
- Asset source strategy: figma_export_required|code_asset|existing_repo_asset|remote_runtime_asset
- Export/use contract:
- Required variants:
- Fallback policy:
- Blocker status:

## Component Mapping

- Figma component -> requirement-level component role:
- Variant -> observed state or semantic role:
- Existing code component constraint, only if explicitly provided:
- Visual-reference-only components:
- Must-reuse-existing components:
- No self-draw / no new copy constraints:
- Missing mappings or constraints:

## Spec Handoff Notes

- Supported requirement sections:
- Clarification items that must remain unresolved:
- Source refs required in `spec.md`:

## Open Questions

- [NEEDS CLARIFICATION]
