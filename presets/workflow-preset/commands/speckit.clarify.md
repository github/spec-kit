---
description: Wrap core clarification with spec-only ambiguity resolution.
strategy: wrap
---

## Spec-Only Clarification Policy

This wrapper must not redefine core-owned User Input, Pre-Execution Checks, extension hooks, base path resolution, or core file handling.

Use `spec.md` as the clarification source. Ask and record clarification only for requirement ambiguity that affects product behavior, constraints, non-functional requirement assumptions, visual/UI requirement coverage status, acceptance criteria, user roles, permissions, entity states, data semantics, exceptions, validation rules, or boundaries.

Do not read or update behavior draft artifacts. Do not use behavior drafts as clarification inputs, and do not open a separate behavior-question channel. Product requirements stay in `spec.md`; update `spec.md` only after user-provided answers make the requirement clear.

## Wrapper Input Additions

Treat `$ARGUMENTS` as prioritization context for the current clarification run. Do not ask the user to restate requirements already present in `spec.md`.

## Wrapper Preflight Additions

Load the active `spec.md` through the core command. Official hooks still apply: `hooks.before_clarify` runs before Outline, `hooks.after_clarify` runs before Completion Report, and mandatory hooks emit `EXECUTE_COMMAND`. If `spec.md` is missing, follow the core command error path and do not create a new spec here.

## Wrapper Outline Additions

## Design Requirement Clarification Strategy

When `spec.md` was created from external intake evidence or visual SSOT refs, prioritize clarification questions for evidence-derived gaps already written in `spec.md`. Scan `spec.md` first for `[NEEDS CLARIFICATION]`, visual/UI coverage status `Unknown`, and gaps about provider-unprovided states, responsive behavior, business rules, permissions, and error handling.

Do not call provider tools. Do not re-extract design facts, re-parse provider design links, parse HTML SSOT bundles, or turn clarification into an intake step. External intake owns source capture and provider readiness; `/speckit.specify` only projects confirmed evidence-backed requirements and trace refs into `spec.md`. `/speckit.clarify` only selects high-impact questions from existing `spec.md` gaps and records confirmed answers. Do not ask the user to fix provider extraction artifacts.

Ask at most 5 high-impact questions whose answers materially affect requirements, implementation planning, or validation readiness. Maximum of 5 total questions. Present EXACTLY ONE question at a time. Do NOT output them all at once. Never reveal future queued questions.

Format recommendations as `**Recommended:** Option [X] - <brief rationale>` when a discrete 2-5 option choice is available. Keep the rationale short and decision-focused. For short-answer gaps, use `Suggested` and constrain answers to `<=5 words`. Accept `yes`, `recommended`, or `suggested` as approval of the shown recommendation. Question selection order:

1. Visual/UI coverage status: Required, Not Applicable, Unknown, or `[BLOCKED: PROVIDER_EVIDENCE]`.
2. Required frames, states, and breakpoints for acceptance.
3. visual fidelity scope: pixel-perfect, design-system faithful, or functional equivalent.
4. missing UI states such as loading, empty, error, disabled, hover, and focus.
5. responsive behavior, scrolling, safe areas, and long-copy handling.
6. required component reuse constraints explicitly stated in `spec.md`.
7. data semantics for mock copy, API-backed copy, and interface-driven values.
8. Prototype-uncovered navigation, dialogs, recovery paths, and failure handling.
9. acceptance evidence, visual-difference tolerance, and exception approval flow.

After each accepted answer, write confirmed answers back into `spec.md` in the relevant Requirements, User Scenarios, Acceptance Criteria, Assumptions, Open Questions, or Visual & UI Specification, visual/responsive/state sections. Update affected visual/UI coverage status when the answer resolves an `Unknown` item. Ensure `## Clarifications`, `### Session YYYY-MM-DD`, and one `- Q: ... -> A: ...` bullet exist for the session. Save `spec.md` after each accepted answer. Do not create a separate provider-specific clarification document.

Do not generate visual restoration checklists. Clarification fills requirement gaps in `spec.md`; `/speckit.checklist` remains responsible for checking requirement text quality and readiness.

## Validation after each write

Run validation after EACH write plus final pass. Confirm the accepted answer appears once in `spec.md`, Total asked questions is at most 5, the targeted ambiguity is removed or replaced, no contradictory earlier statement remains, and heading structure is preserved.

Do not update checklist artifacts. After each `spec.md` write, report checklist impact as unresolved readiness context for `/speckit.checklist`.

{CORE_TEMPLATE}

## Completion Report

Before finishing, report answered questions, `spec.md` sections updated, and any unresolved requirement ambiguity that still blocks checklist readiness.

## Done When

- [ ] No more than 5 high-impact questions were asked.
- [ ] Each accepted answer was written back to `spec.md`.
- [ ] Any answered visual/UI coverage status was updated in `spec.md`.
- [ ] Validation after each write found no duplicate or contradictory clarification.
- [ ] Completion reported with sections touched and remaining blockers.
