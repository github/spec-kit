---
description: Wrap core clarification with spec-only ambiguity resolution.
strategy: wrap
---

## Spec-Only Clarification Policy

Use `spec.md` as the clarification source. Ask and record clarification only for requirement ambiguity that affects product behavior, constraints, non-functional requirement assumptions, acceptance criteria, user roles, permissions, entity states, data semantics, exceptions, validation rules, or boundaries.

Do not read or update behavior draft artifacts. Do not use behavior drafts as clarification inputs, and do not open a separate behavior-question channel. Product requirements stay in `spec.md`; update `spec.md` only after user-provided answers make the requirement clear.

## Figma-Derived Clarification Strategy

When `spec.md` was created from a Figma Evidence Packet, prioritize clarification questions for Figma-derived gaps already written in `spec.md`. Scan `spec.md` first for `Missing / Needs clarification`, `[NEEDS CLARIFICATION]`, `Inferred from structure`, and gaps about Figma-unprovided states, responsive behavior, business rules, permissions, and error handling.

Do not call Figma MCP. Do not re-extract design facts, re-parse Figma links, or turn clarification into a Figma extraction step. `/speckit.specify` owns writing Figma evidence into `spec.md`; `/speckit.clarify` only selects high-impact questions from existing `spec.md` gaps and records confirmed answers.

Ask at most 5 high-impact questions whose answers materially affect requirements, implementation planning, or validation readiness. Prefer questions in this order:

1. Required frames, states, and breakpoints for acceptance.
2. visual fidelity scope: pixel-perfect, design-system faithful, or functional equivalent.
3. missing UI states such as loading, empty, error, disabled, hover, and focus.
4. responsive behavior, scrolling, safe areas, and long-copy handling.
5. component mapping from Figma components to existing code components.
6. data semantics for mock copy, API-backed copy, and interface-driven values.
7. Prototype-uncovered navigation, dialogs, recovery paths, and failure handling.
8. acceptance evidence, visual-difference tolerance, and exception approval flow.

After the user answers, write confirmed answers back into `spec.md` in the relevant Requirements, User Scenarios, Acceptance Criteria, Assumptions, Open Questions, or visual/responsive/state sections. Do not create a separate Figma clarification document.

Do not generate visual restoration checklists. Clarification fills requirement gaps in `spec.md`; `/speckit.checklist` remains responsible for checking requirement text quality and readiness.

{CORE_TEMPLATE}

## Clarification Reporting

Before finishing, report answered questions, `spec.md` sections updated, and any unresolved requirement ambiguity that still blocks checklist readiness.
