---
description: Generate a low-fidelity evidence-backed static HTML wireflow preview from Spec Kit artifacts.
---

## User Input

```text
$ARGUMENTS
```

You **MUST** evaluate the user input before proceeding. Treat it as preview focus, audience, device, flow, or review criteria.

If `$ARGUMENTS` requests a page, role, device, state, interaction, or business rule that is not supported by the loaded artifacts, do not invent it. Mark it as `输入未说明`, or use `推理补齐` only for the minimal traceable inference required to preserve preview coherence.

## Goal

Generate or update `specs/<feature>/preview/wireflow-low.html`.

Low-fidelity HTML is a static browser-renderable artifact for early product-scope validation. It presents the core path, branch points, missing scope, and review questions in HTML without adding interaction fidelity.

## Command Responsibilities

- Resolve the active feature and load source artifacts.
- Apply evidence policy and fidelity-specific extraction rules.
- Load the output template from `.specify/extensions/preview/templates/preview/low.html`; when running from this extension repository, use `templates/preview/low.html`.
- Populate template slots with evidence-backed content only.
- Write only `specs/<feature>/preview/wireflow-low.html`. Create `specs/<feature>/preview/` if it is missing; do not create any other files or directories.

Do not redefine template sections, table columns, CSS shell, or output structure in this command. The template is the source of truth for HTML shape and required tables.

## Boundaries

- Do not modify source code, tests, app assets, package manifests, build configuration, feature specs, plans, tasks, or memory files.
- Do not create Markdown, Figma files, images, screenshots, or production UI.
- Do not invent pages, fields, business rules, roles, states, or visual details. Mark unsupported items as `输入未说明`; mark only minimal traceable inferences as `推理补齐`.
- HTML output must remain static, self-contained, and network-free. Use embedded CSS only; do not use external fonts, icons, images, scripts, analytics, APIs, or JavaScript interaction.
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
6. If `specs/<feature>/preview/wireflow-low.html` already exists, read it before writing. Preserve user-authored review notes, decisions, and unresolved questions when they remain consistent with current source artifacts; label changed items as `UPDATED` and superseded items as `SUPERSEDED`.

## Evidence Policy

Use these coverage labels exactly: `已覆盖`, `部分覆盖`, `未覆盖`, `输入未说明`, `推理补齐`.

Every requirement, node, branch, state, and terminal outcome included in the preview must include a coverage label and provenance. Provenance must be either a source anchor or a `推理补齐` explanation.

Coverage evidence must identify the source with a precise anchor: file path, heading, section id, line number, table row, or short quoted source excerpt. Use `输入未说明` when no source supports the requested item. Use `推理补齐` only when a minimal inference connects two supported facts; include the reasoning bridge and keep it non-authoritative.

## Low-Fidelity Extraction Policy

Extract only:

- Core actor, trigger, goal, and terminal outcome.
- Primary path and major branch points.
- Abstract page or state nodes when screens are unnamed.
- Major alternate, error, empty, permission, cancellation, and retry paths only when source evidence supports them.
- Coverage conclusions for major user stories, acceptance criteria, and missing scope.

Exclude precise layout, colors, component styling, animation, JavaScript interaction, and pixel-level details.

## Procedure

1. Summarize the feature goal, actors, primary scenarios, and constraints from loaded artifacts.
2. Select the preview focus from `$ARGUMENTS`; if absent, cover the highest-priority user story.
3. Extract evidence-backed actors, tasks, steps, decisions, states, and terminal outcomes.
4. Fill the low-fidelity HTML template slots for metadata, evidence summary, wireflow, node inventory, branches, coverage, preserved review records, and unresolved review questions.
5. Escape user-provided content and source excerpts before inserting them into HTML.
6. Write `specs/<feature>/preview/wireflow-low.html`, preserving existing review content as described above.
7. Report output path, fidelity, input sources, flows covered, inferred assumptions, unsupported items, and unresolved review questions.
