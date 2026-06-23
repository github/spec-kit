---
description: Generate a high-fidelity evidence-backed Markdown interaction preview from Spec Kit artifacts.
---

## User Input

```text
$ARGUMENTS
```

You **MUST** evaluate the user input before proceeding. Treat it as preview focus, audience, device, flow, interaction, or review criteria.

If `$ARGUMENTS` requests a page, role, device, state, interaction, validation rule, permission, or business rule that is not supported by the loaded artifacts, do not invent it. Mark it as `输入未说明`, or use `推理补齐` only for the minimal traceable inference required to preserve preview coherence.

## Goal

Generate or update `specs/<feature>/preview/wireflow-high.md`.

High-fidelity Markdown is a final product validation artifact for implementation handoff validation. It documents evidence-backed interaction feedback, state transitions, validation, permissions, and edge cases without emitting production implementation code.

## Command Responsibilities

- Resolve the active feature and load source artifacts.
- Apply evidence policy and fidelity-specific extraction rules.
- Load the output template from `.specify/extensions/preview/templates/preview/high.md`; when running from this extension repository, use `templates/preview/high.md`.
- Populate template slots with evidence-backed content only.
- Write only `specs/<feature>/preview/wireflow-high.md`. Create `specs/<feature>/preview/` if it is missing; do not create any other files or directories.

Do not redefine template sections, table columns, or output structure in this command. The template is the source of truth for Markdown shape and required tables.

## Boundaries

- Do not modify source code, tests, app assets, package manifests, build configuration, feature specs, plans, tasks, or memory files.
- Do not create HTML, Figma files, images, screenshots, or production UI.
- Do not invent business rules, roles, fields, states, copy, data rules, or interactions. Mark unsupported items as `输入未说明`; mark only minimal traceable inferences as `推理补齐`.
- If the template file cannot be read, stop with an error explaining that the preview extension template is missing.

## Context Loading

1. Verify the current directory is a Spec Kit project by checking for `.specify/`.
2. Identify the active feature:
   - Prefer `SPECIFY_FEATURE` when set.
   - Otherwise use the current Git branch name when it exactly matches a directory under `specs/`.
   - Otherwise inspect `specs/` and use it only when there is exactly one unambiguous candidate directory.
   - Do not choose by most recent timestamp when multiple feature directories exist.
   - If the feature cannot be identified, stop and ask the user to set `SPECIFY_FEATURE` or run from the feature branch.
3. Read these files when present:
   - `specs/<feature>/spec.md` (required)
   - `specs/<feature>/plan.md`
   - `specs/<feature>/research.md`
   - `specs/<feature>/data-model.md`
   - `specs/<feature>/contracts/`
   - `specs/<feature>/quickstart.md`
4. Read `.specify/memory/constitution.md` if present.
5. If `spec.md` is missing, stop with an error explaining that `/speckit.specify` must run first.
6. If `specs/<feature>/preview/wireflow-high.md` already exists, read it before writing. Preserve user-authored review notes, decisions, and unresolved questions when they remain consistent with current source artifacts; label changed items as `UPDATED` and superseded items as `SUPERSEDED`.

## Evidence Policy

Use these coverage labels exactly: `已覆盖`, `部分覆盖`, `未覆盖`, `输入未说明`, `推理补齐`.

Every requirement, page, node, field, interaction, state, branch, permission, validation rule, and system response included in the preview must include a coverage label and provenance. Provenance must be either a source anchor or a `推理补齐` explanation.

Coverage evidence must identify the source with a precise anchor: file path, heading, section id, line number, table row, or short quoted source excerpt. Use `输入未说明` when no source supports the requested item. Use `推理补齐` only when a minimal inference connects two supported facts; include the reasoning bridge and keep it non-authoritative.

## High-Fidelity Extraction Policy

Extract only:

- Artifact-defined data conditions, roles, permissions, validation rules, and user-visible feedback.
- Interaction matrix content: event, target, precondition, feedback, state change, error handling, coverage, and evidence.
- State matrix content for hover, focus, click, loading, success, failure, disabled, empty, validation, timeout, retry, cancellation, and permission-denied states where relevant.
- Toast, inline error, confirmation dialog, retry, cancellation, timeout, and loading feedback rules when supported by evidence.
- Motion or timing notes only when artifacts state them or when explicitly marked as `推理补齐`.
- Coverage evidence mapped from requirements to preview nodes, interactions, states, or review questions.

Do not claim that Markdown is a clickable prototype or production-ready.

## Procedure

1. Summarize the feature goal, personas, primary scenarios, and constraints from loaded artifacts.
2. Select the preview focus from `$ARGUMENTS`; if absent, cover the highest-priority user story and primary alternate flow state.
3. Extract evidence-backed pages, tasks, fields, controls, roles, permissions, data conditions, states, decisions, and system responses.
4. Fill the high-fidelity Markdown template slots for metadata, evidence summary, wireflow, node inventory, interaction matrix, state matrix, branches, coverage, preserved review records, and unresolved review questions.
5. Write `specs/<feature>/preview/wireflow-high.md`, preserving existing review content as described above.
6. Report output path, fidelity, input sources, flows covered, covered interactions, inferred assumptions, unsupported items, and unresolved review questions.
