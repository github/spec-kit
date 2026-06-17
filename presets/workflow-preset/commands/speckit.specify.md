---
description: Wrap core specification with spec-only requirement ownership.
strategy: wrap
---

## Spec-Only Requirement Policy

During specification, produce or update `spec.md` only. This command writes only `spec.md`.

Product requirements stay in `spec.md`: user stories, acceptance criteria, functional requirements, non-functional requirements, constraints, assumptions, and any clarification markers required by the core template.

Keep requirement text implementation-agnostic and scoped to product behavior. Non-functional requirements should be explicit product-level assumptions or constraints, including no-special-requirement or not-applicable statements when that is the confirmed requirement.

## Figma URL Input Policy

If the raw request is a Figma URL and the runtime agent has Figma MCP access:

- Require a ready Figma Evidence Packet before writing Figma-derived requirements.
- Use the Figma intake contract: the preset defines the required Figma intake artifact structure and ready gate.
- Treat the runtime agent or external Figma intake as the source of artifact instances; this command consumes qualified evidence and does not generate the artifact instances.
- Apply the ready gate:
- `raw_metadata_complete: true`
- `node_inventory_coverage: 100%`
- `parity_passed: true`
- No blocker lint errors
- If the packet is not ready, do not write Figma-derived requirements from that evidence. Write only explicit non-Figma requirements and add `[NEEDS CLARIFICATION]` items for missing raw metadata, metadata index, node inventory parity, or blocker lint remediation.

Use `Observed from Figma` as design evidence. Treat `Inferred from Structure`,
`Missing / Needs Clarification`, and `Out of Scope` as interpretation,
unresolved requirements, and excluded evidence respectively. Mark business
semantics, permissions, validation, dynamic states, responsive behavior, error
handling, data semantics, and analytics as `[NEEDS CLARIFICATION]` unless packet
evidence explicitly confirms them.

If Figma MCP access is unavailable, Continue to write only `spec.md` and add a
`[NEEDS CLARIFICATION]` item requesting a filled Figma Evidence Packet,
screenshots, or design facts.

{CORE_TEMPLATE}

## Spec Reporting

Before finishing, report the `spec.md` sections created or updated and list unresolved requirement ambiguities separately from confirmed requirements.
