---
ready_gate: BLOCKED
blockers: []
source_ref_count: 0
extracted_item_count: 0
generated_at:
---

# Visual Design Evidence Packet

Purpose: summarize provider-neutral visual design evidence for downstream Spec Kit workflows, while preserving enough traceability for downstream workflows to define their own visual verification criteria against the original design source.

This packet is a human-readable readiness summary. Machine-readable visual facts are recorded in `visual-requirements.yaml` and validated by `templates/schemas/visual-requirements.schema.json`. This packet does not define downstream workflow schemas, downstream-owned item IDs, code component names, product semantics, or implementation ownership.

## Design Source

- Source type: image|pdf|markdown|figma
- Source path or URL:
- Source files / pages / frames / nodes:
- Design version / timestamp:
- Target platform:
- Required fidelity: low|medium|high
- Capture method:

## Source Integrity

- design-source-manifest.yaml:
- source files preserved:
- source checksums verified:
- page/frame/image coverage:
- source_integrity_complete:

## Fidelity Profile

- Fidelity level applied:
- Low-fidelity requirements captured:
- Medium-fidelity requirements captured:
- High-fidelity requirements captured:
- Accepted fidelity gaps:
- fidelity_rules_applied:

## Extraction Context

- Runtime agent:
- Input tooling availability:
- Figma MCP availability:
- Image/OCR availability:
- PDF render/text extraction availability:
- Markdown asset parsing availability:
- Screenshots or rendered pages captured:
- Variables / styles / tokens captured:
- Component metadata captured:

## Intake Readiness

- design-source-manifest.yaml:
- visual-requirements.yaml:
- visual-evidence-packet.md:
- figma-metadata.part-*.xml:
- figma-metadata.index.yaml:
- figma-node-inventory.yaml:
- source integrity completeness:
- visual requirements completeness:
- source refs completeness:
- fidelity rules completeness:
- visual parity plan completeness:
- Figma metadata completeness:
- Figma inventory parity:
- blocker lint errors:
- readiness front matter synchronized: yes|no

## Machine-Readable Artifacts

- design-source-manifest.yaml:
- visual-requirements.yaml:
- figma-metadata.index.yaml:
- figma-node-inventory.yaml:
- schema validation result:
- readiness validator result:

## Observed Visual Fact Summary

- Layout hierarchy:
- Spacing / sizing / grid:
- Typography:
- Colors / tokens:
- Effects:
- Assets:
- Components / variants:
- States:
- Prototype or interaction links:
- Responsive evidence:
- Accessibility evidence:

## Derived Assumptions

- Inferred navigation:
- Inferred grouping:
- Inferred content priority:
- Inferred responsive behavior:
- Required marker: `evidence_type: inferred`
- Required clarification or acceptance gap:
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

## Engineering Input Summary

- Requirement categories represented:
- Source refs represented:
- Acceptance checks represented:
- Required fidelity:
- Blocker status:

## Traceability Summary

- Source evidence refs represented:
- Requirement categories represented:
- Comparison methods represented:
- Accepted exceptions:

## Intake Parity Plan

- Original design refs:
- Comparison method: visual_diff|measurement|token_match|asset_match|manual_review
- Thresholds:
- Blocking difference categories:
- Accepted exception policy:
- Intake readiness front matter synchronized: yes|no

## Source Asset Summary

- Asset ID:
- Asset role:
- Resource type: image|icon|video|lottie|svg|font
- Source ref:
- Source export requirement:
- Required variants:
- Blocker status:

## Source Component Summary

- Source component or pattern:
- Variant coverage:
- Missing mappings:

## Consumer Handoff Notes

- Supported requirement sections:
- Clarification items that must remain unresolved:
- Source refs required in downstream artifacts:

## Open Questions

- [NEEDS CLARIFICATION]
