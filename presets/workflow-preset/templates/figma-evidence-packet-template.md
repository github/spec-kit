# Figma Evidence Packet

Use this packet to normalize design evidence before `/speckit.specify` writes
Figma-derived requirements. Raw intake readiness is governed by
`templates/figma-intake-contract.md`.

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

## Figma Intake Readiness

- figma-metadata.part-*.xml:
- figma-metadata.index.yaml:
- figma-node-inventory.yaml:
- raw metadata completeness:
- metadata index completeness proof:
- node inventory parity:
- blocker lint errors:
- ready gate: PASS|BLOCKED

## Evidence Record Format

Use this record for extracted facts in observed, inferred, missing, and
out-of-scope sections.

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

## Component Mapping

- Figma component -> code component:
- Variant coverage:
- Missing mappings:

## Spec Handoff Notes

- Requirement sections this evidence can support:
- Clarification items that must remain unresolved:
- Source refs required in `spec.md`:

## Open Questions

- [NEEDS CLARIFICATION]
