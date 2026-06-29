---
description: Wrap core specification with spec-only requirement ownership.
strategy: wrap
---

## Spec-Only Requirement Policy
This wrapper must not redefine core-owned User Input, Pre-Execution Checks, extension hooks, base path resolution, or core file handling.

Preset-added requirement output writes only `spec.md`.
Product requirements stay in `spec.md`: user stories, acceptance criteria, functional requirements, non-functional requirements, visual and UI requirements, constraints, assumptions, and any clarification markers required by the core template.

Keep requirement text implementation-agnostic and scoped to product behavior. Non-functional requirements must be explicit product-level assumptions or constraints, including no-special-requirement or not-applicable statements when that is the confirmed requirement.

## Wrapper Input Additions
Treat product notes, PRDs, user prompts, confirmed external intake facts, visual SSOT refs, evidence refs, screenshots, and visual proof refs as input to the same feature description. If the core feature description is empty, follow the core command error path.

Treat confirmed Visual Asset Registry refs as external source artifact inputs only. They describe visual media inventory such as icons, images, illustrations, fonts, motion, video, textures, source refs, variants, license status, fallback policy, and blocker status.

## Wrapper Preflight Additions
Before writing evidence-derived requirements, consume only confirmed external intake facts or explicit user-provided requirement text. This preset does not perform intake, call provider tools, parse HTML bundles, decide provider source readiness, or generate provider artifact instances.

If external intake or visual SSOT evidence is missing or blocked, write explicit non-evidence requirements only and record source readiness blockers as `[BLOCKED: PROVIDER_EVIDENCE]`; provider blockers must not become product `[NEEDS CLARIFICATION]` items.

## Wrapper Outline Additions
Specification Projection Policy: write one implementation-agnostic `spec.md` from confirmed product facts, explicit product constraints, and source-backed external intake facts.

When visual or UI requirements apply, write a `Visual & UI Specification` section inside `spec.md` for observable visual and UI requirements only. When no visual or UI surface applies, record a Not Applicable rationale in `spec.md`.

Every identified visual or UI requirement must be recorded with status `Required`, `Not Applicable`, `Unknown`, or `[BLOCKED: PROVIDER_EVIDENCE]`; do not silently omit low-evidence visual or UI requirements.

For visual requirements, preserve visual SSOT refs, evidence refs, state and viewport refs, visual proof refs, and Client Asset Contract facts: source refs, asset source strategy, required variants, fallback policy, and blocker status.

Promote only source-backed visual, layout, state, interaction, responsive, accessibility, and acceptance facts with source refs. Product semantics implied only by provider evidence stay `[NEEDS CLARIFICATION]`.

Treat Component State Matrix content as Visual & UI Specification requirements, not visual assets. Record observable states, visual feedback, and interaction outcomes; do not turn them into framework component names or implementation contracts.

Do not invent code props, code state names, component reuse decisions, self-drawing bans, copy restrictions, DOM structure, CSS selectors, component props, generated code organization, asset binding, or packaging strategy from external visual evidence.

When visual SSOT refs are blocked or unavailable, keep explicit visual or UI requirement coverage in `spec.md`, mark evidence-derived coverage as `[BLOCKED: PROVIDER_EVIDENCE]`, and do not invent missing visual facts.

## Official Style Alignment
Focus on WHAT users need and WHY. Avoid HOW to implement. Limit [NEEDS CLARIFICATION] markers to the highest-impact unresolved product decisions; record low-impact gaps in Assumptions and provider readiness gaps as `[BLOCKED: PROVIDER_EVIDENCE]`.

## Specification Quality Validation
Validate that requirement text is stakeholder-readable, testable, implementation-agnostic, and explicit about assumptions, NFR applicability, visual evidence source refs, provider blockers, and unresolved product decisions.

{CORE_TEMPLATE}

## Completion Report
Before finishing, report the `spec.md` sections created or updated, confirmed requirements, visual SSOT refs preserved, provider blockers, and unresolved requirement ambiguities.

## Done When
- [ ] Confirmed requirement facts, visual SSOT refs, and applicable Client Asset Contract facts are reflected in `spec.md`.
- [ ] Functional, non-functional, and visual/UI requirement coverage is present or explicitly marked Not Applicable, Unknown, or `[BLOCKED: PROVIDER_EVIDENCE]`.
- [ ] Product `[NEEDS CLARIFICATION]` markers are limited to high-impact unresolved decisions.
- [ ] Provider readiness blockers remain `[BLOCKED: PROVIDER_EVIDENCE]`.
- [ ] Completion reported with updated `spec.md` sections and remaining blockers.
