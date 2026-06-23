---
description: Wrap core specification with spec-only requirement ownership.
strategy: wrap
---

## Spec-Only Requirement Policy
This wrapper must not redefine core-owned User Input, Pre-Execution Checks, extension hooks, base path resolution, or core file handling.

Preset-added requirement output writes only `spec.md`.
Product requirements stay in `spec.md`: user stories, acceptance criteria, functional requirements, non-functional requirements, constraints, assumptions, and any clarification markers required by the core template.

Keep requirement text implementation-agnostic and scoped to product behavior. Non-functional requirements must be explicit product-level assumptions or constraints, including no-special-requirement or not-applicable statements when that is the confirmed requirement.

## Wrapper Input Additions
Treat product notes, PRDs, user prompts, design evidence, provider source packets, screenshots, visual proof, and source refs as input to the same feature description. If the core feature description is empty, follow the core command error path.

## Wrapper Preflight Additions
Before writing design-derived requirements, check whether provider evidence is ready. This preset consumes qualified provider evidence; it does not call Figma MCP and does not generate provider artifact instances.

For Figma-derived evidence, require a ready Figma Evidence Packet and Figma provider source readiness contract: raw metadata completeness, metadata index completeness proof, node inventory parity, and no blocker lint errors. If evidence is not ready, write explicit non-design requirements only and record Provider evidence readiness blockers as `[BLOCKED: PROVIDER_EVIDENCE]`; provider blockers must not become product `[NEEDS CLARIFICATION]` items.

## Wrapper Outline Additions
Design Requirement Input Policy: run specification as staged intake and merge work without changing this command's write scope:

### Stage 0: Product Requirement Intake
Product intake input: PRD, user prompt, product notes, and explicit product constraints. Product intake output: product-owned requirement facts in `spec.md`, including stories, functional requirements, non-functional requirements, assumptions, and product `[NEEDS CLARIFICATION]` markers.

### Stage 1: Design Requirement Intake
Design intake input: provider-neutral design evidence, provider source packets, screenshots, visual proof, and source refs. Design intake output: evidence-backed design facts recorded only in `spec.md`, including stable Visual Item ID trace refs, observed variant/state facts, and Client Asset Contract facts: source refs, asset source strategy, required variants, fallback policy, and blocker status.

If the design source is a Figma URL and a ready packet is supplied by a runtime agent or external Figma intake that has Figma MCP access:

- Require a ready Figma Evidence Packet before writing design-derived requirements.
- Use the Figma provider source readiness contract; the preset defines the required design intake and provider readiness artifact structure and ready gate.
- Treat the runtime agent or external Figma intake as the source of artifact instances; this command consumes qualified evidence, does not call Figma MCP, and does not generate the artifact instances.
- If the packet is not ready, do not write design-derived requirements from that evidence. Write only explicit non-design requirements and record Provider evidence readiness blockers as `[BLOCKED: PROVIDER_EVIDENCE]`.

Use `Observed from Figma` as design evidence. Treat `Inferred from Structure`, `Missing / Needs Clarification`, and `Out of Scope` as interpretation, unresolved requirements, and excluded evidence respectively.
Screenshots support visual facts only; screenshots must not create product semantics. Screenshot-implied business rules stay `[NEEDS CLARIFICATION]`.
Do not invent code props, code state names, component reuse decisions, self-drawing bans, or copy restrictions from Figma structure. Record component use, no-self-draw, and no-new-copy constraints only when product input or qualified provider evidence states them explicitly.

If Figma MCP access is unavailable, Continue to write only `spec.md` and record `[BLOCKED: PROVIDER_EVIDENCE]` for the missing Figma Evidence Packet, screenshots, or design facts.

### Stage 2: Requirement Merge
Merge input: product facts from Stage 0 plus qualified design facts from Stage 1. Merge output: confirmed baseline requirements, conflicts, assumptions, clarification markers, and provider blockers recorded in `spec.md`. Apply Design Requirement Promotion Rules: promote only evidence-backed visual, layout, state, interaction, responsive, accessibility, and acceptance facts with source refs; preserve Visual Item ID trace refs for visual requirements. Product semantics implied only by provider evidence stay `[NEEDS CLARIFICATION]`.

### Stage 3: Generate baseline spec.md
Baseline spec output: one implementation-agnostic `spec.md` contract containing confirmed product requirements, qualified design-derived requirements, source refs, `[NEEDS CLARIFICATION]`, and `[BLOCKED: PROVIDER_EVIDENCE]` items.

## Official Style Alignment
Focus on WHAT users need and WHY. Avoid HOW to implement. Limit [NEEDS CLARIFICATION] markers to the highest-impact unresolved product decisions; record low-impact gaps in Assumptions and provider readiness gaps as `[BLOCKED: PROVIDER_EVIDENCE]`.

## Specification Quality Validation
Validate that requirement text is stakeholder-readable, testable, implementation-agnostic, and explicit about assumptions, NFR applicability, visual evidence source refs, provider blockers, and unresolved product decisions.

{CORE_TEMPLATE}

## Completion Report
Before finishing, provide a stage-wise report and report the `spec.md` sections created or updated, confirmed requirements, provider blockers, and unresolved requirement ambiguities.

## Done When
- [ ] Stage 0-3 intake and merge decisions are reflected in `spec.md`.
- [ ] Product `[NEEDS CLARIFICATION]` markers are limited to high-impact unresolved decisions.
- [ ] Provider readiness blockers remain `[BLOCKED: PROVIDER_EVIDENCE]`.
- [ ] Completion reported with updated `spec.md` sections and remaining blockers.
