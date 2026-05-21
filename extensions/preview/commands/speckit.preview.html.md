---
description: Generate a self-contained interactive HTML prototype from Spec Kit artifacts.
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty). Treat it as prototype focus, audience, device, flow, fidelity, or style guidance.

## Goal

Generate or update a self-contained HTML prototype for the active Spec Kit feature:

- Output: `specs/<feature>/preview/index.html`
- Purpose: make product flow, information architecture, and interaction assumptions reviewable before implementation.
- Fidelity: interactive prototype only; this is not a production implementation.

## Positioning

Use this command after `/speckit.specify` and `/speckit.clarify` when a feature has user-facing flows that benefit from visual review. It may also run after `/speckit.plan` to reflect technical or platform constraints already captured in the plan.

Do not run this as a substitute for `/speckit.plan`, `/speckit.tasks`, or `/speckit.implement`. The prototype is an exploratory artifact for alignment, not source code for the application.

## Operating Boundaries

- Write only `specs/<feature>/preview/index.html`.
- Do not modify source code, tests, app assets, package manifests, build configuration, feature specs, plans, tasks, or memory files.
- Do not create additional files unless the user explicitly asks for separate assets.
- No external network dependencies: do not load fonts, icons, images, scripts, stylesheets, analytics, or APIs from the network.
- Use inline CSS and JavaScript. The HTML file must open directly in a browser without a build step.
- Do not use production framework code, generated application components, or repository source files.
- Do not invent business rules. If the artifacts do not specify a behavior, use a clearly labeled prototype assumption.
- Preserve an existing preview only when it contains user-authored decisions not contradicted by the current artifacts; otherwise update it to match the current feature.

## Context Loading

1. Verify the current directory is a Spec Kit project by checking for `.specify/`.
2. Identify the active feature:
   - Prefer `SPECIFY_FEATURE` when set.
   - Otherwise use the current Git branch name when it matches a directory under `specs/`.
   - Otherwise inspect `specs/` and choose the most recent feature directory only if there is a single clear candidate.
   - If the feature cannot be identified, stop and ask the user to set `SPECIFY_FEATURE` or run from the feature branch.
3. Read these files when present:
   - `specs/<feature>/spec.md` (required)
   - `specs/<feature>/plan.md`
   - `specs/<feature>/research.md`
   - `specs/<feature>/data-model.md`
   - `specs/<feature>/contracts/`
   - `specs/<feature>/quickstart.md`
4. Read `.specify/memory/constitution.md` if present for product, accessibility, and quality constraints.
5. If `spec.md` is missing, stop with an error explaining that `/speckit.specify` must run first.

## Prototype Requirements

The generated HTML must include:

- A realistic first screen for the feature, not a marketing landing page.
- At least one primary user flow that can be clicked through end to end.
- Meaningful state changes from user actions, such as selection, filtering, validation, navigation, save confirmation, or simulated data changes.
- empty, loading, error, and success states when relevant to the feature.
- responsive layout for mobile and desktop widths.
- keyboard reachable controls and visible focus states.
- Accessible labels or text for interactive controls.
- Sample data grounded in the feature spec. Mark any invented sample data as prototype-only.
- A visible "Prototype Assumptions" section or panel that lists inferred behaviors and unresolved questions.

For operational tools, dashboards, admin screens, and B2B workflows, prefer dense, scannable interfaces over marketing-style hero pages. For consumer or creative experiences, match the domain while keeping the feature workflow reviewable.

## HTML Construction Rules

- Produce valid HTML with inline `<style>` and `<script>` blocks.
- Use semantic elements where practical: `main`, `section`, `nav`, `button`, `form`, `label`, `table`, and lists.
- Keep visual assets as CSS shapes, inline SVG, emoji-free text, or data URIs only when needed. Do not fetch remote images.
- Keep JavaScript small and understandable. It should simulate interactions, not implement backend logic.
- Store all prototype state in memory or `localStorage` only when persistence helps review the flow.
- Make destructive actions reversible in the prototype unless the spec explicitly requires irreversible behavior.
- Avoid implying authentication, billing, compliance, security, or data retention behavior that is not present in the spec.

## Procedure

1. Summarize the feature goal, personas, primary scenarios, and constraints from the loaded artifacts.
2. Choose the prototype scope from `$ARGUMENTS`; if no focus is provided, cover the highest-priority user story and its main alternate state.
3. Define a small interaction model:
   - screens or panels
   - user actions
   - state transitions
   - prototype-only assumptions
4. Generate or update `specs/<feature>/preview/index.html`.
5. Self-review the HTML before reporting:
   - It opens without a build step.
   - It has no external network dependencies.
   - It includes inline CSS and JavaScript.
   - It covers the selected primary user flow.
   - It contains the required states that apply to the feature.
   - It does not modify or depend on production source code.
6. Report:
   - output path
   - user flows covered
   - important interactions
   - prototype assumptions
   - unresolved questions or missing spec details

## Quality Bar

- The prototype should help a stakeholder review behavior, flow, and layout decisions quickly.
- The artifact should be small enough for an agent to update safely in later iterations.
- The visual design should match the feature domain and audience without over-polishing speculative details.
- The command must leave the implementation workflow untouched; `/speckit.plan`, `/speckit.tasks`, and `/speckit.implement` remain authoritative for production work.

