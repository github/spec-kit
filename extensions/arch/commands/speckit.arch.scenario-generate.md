---
description: Generate the 4+1 scenario view from intended product and use-case context.
scripts:
  sh: .specify/extensions/arch/scripts/bash/setup-arch.sh --json
  ps: .specify/extensions/arch/scripts/powershell/setup-arch.ps1 -Json
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Goal

Generate or refresh the scenario view:

- Target view: `.specify/memory/architecture-scenario-view.md`
- Optional synthesis refresh: `.specify/memory/architecture.md`

This is the `+1` view in 4+1 architecture. It produces actor, goal, use-case, path, branch, and acceptance semantics for the other architecture views.

## Operating Boundaries

- Write only `SCENARIO_VIEW`; update `ARCH_FILE` only if the five architecture views are already coherent enough to refresh synthesis without inventing content.
- Do not read, populate, or update `REPO_FACTS_FILE`.
- Read `.specify/memory/uc.md` only as optional scenario background.
- Do not modify `.specify/memory/uc.md`, `.specify/memory/constitution.md`, feature specs, plans, tasks, source code, tests, root `docs/`, deployment manifests, or runbooks.
- Stay at abstract architecture-design level.
- If context is insufficient, record a specific scenario gap instead of inventing actors, goals, business facts, or acceptance meaning.

## Setup Bootstrap

`{SCRIPT}` may create missing architecture memory files from templates, including non-target view placeholders and `REPO_FACTS_FILE`. Treat that as bootstrap scaffolding only. After setup, this command must populate only `SCENARIO_VIEW`, and may refresh `ARCH_FILE` only under the synthesis readiness rule below.

If setup creates `REPO_FACTS_FILE`, leave it as-is. Do not read it as input and do not add facts to it from this generate command.

## Structured Contract

`ARCH_SCHEMA_FILE` is the authoritative structural contract for architecture artifacts. Build a JSON-compatible working model for every file you update, validate required sections, traceability records, gaps, and `High` / `Medium` / `Low` confidence values against the schema, then render Markdown with the corresponding template. The command owns extraction, classification, validation, and write policy; templates own Markdown layout only.

## Synthesis Readiness

Parse all five view paths from setup JSON: `SCENARIO_VIEW`, `LOGICAL_VIEW`, `PROCESS_VIEW`, `DEVELOPMENT_VIEW`, and `PHYSICAL_VIEW`.

A view is ready for synthesis only when it exists, no longer contains `NEEDS ARCH UPDATE`, and contains at least one source-backed non-gap architecture conclusion in its required sections. Unsupported or unknown items must be recorded in that view's gaps and do not make the view ready. Refresh `ARCH_FILE` only when all five views are ready and cross-view terminology is coherent. Otherwise leave `ARCH_FILE` unchanged and report the missing or not-ready views.

## Outline

1. Run `{SCRIPT}` from repo root and parse JSON for `ARCH_FILE`, `ARCH_SCHEMA_FILE`, `REPO_FACTS_FILE`, and all five view paths.
2. Load `SCENARIO_VIEW`, `ARCH_FILE`, `ARCH_SCHEMA_FILE`, `architecture-scenario-template.md`, and `architecture-template.md`.
3. Load `.specify/memory/uc.md` if present as supporting context.
4. Extract source-backed actors, goals, triggers, paths, branches, and acceptance semantics.
5. Normalize scenario terminology and derive scenario-level boundaries.
6. Classify each candidate as a supported scenario conclusion or a scenario gap under the schema and quality gates.
7. Render the schema-compliant scenario working model with `architecture-scenario-template.md`.
8. Apply the synthesis readiness rule. If all five view files are ready, refresh `ARCH_FILE` using `architecture-template.md`; otherwise leave synthesis untouched and report the missing or not-ready views.
9. Report updated paths and explicit scenario gaps.

## Quality Gates

- ERROR if the scenario view contains implementation details, components, APIs, database tables, deployment scripts, or task plans.
- ERROR if a target-view conclusion has no stated scenario source, user input source, or existing memory source.
- Unsupported target-view conclusions MUST appear only in `Scenario Gaps`, not in conclusion tables.
- ERROR if a boundary has responsibilities but no explicit non-responsibility.
- Record gaps instead of inventing business facts.
