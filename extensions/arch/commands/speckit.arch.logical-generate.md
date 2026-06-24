---
description: Generate the 4+1 logical view from scenario architecture semantics.
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

Generate or refresh the logical view:

- Target view: `.specify/memory/architecture-logical-view.md`
- Primary input: `.specify/memory/architecture-scenario-view.md`
- Optional synthesis refresh: `.specify/memory/architecture.md`

The logical view derives capability boundaries, domain objects, states, relationships, and invariants from scenario semantics.

## Operating Boundaries

- Write only `LOGICAL_VIEW`; update `ARCH_FILE` only if the five architecture views are already coherent enough to refresh synthesis without inventing content.
- Do not read, populate, or update `REPO_FACTS_FILE`.
- Do not modify scenario view, source code, specs, plans, tasks, docs, tests, deployment files, or runbooks.
- Stay at abstract logical architecture level.
- If the scenario view is placeholder, stale, or insufficient, record logical gaps instead of fabricating capabilities or domain objects.

## Setup Bootstrap

`{SCRIPT}` may create missing architecture memory files from templates, including non-target view placeholders and `REPO_FACTS_FILE`. Treat that as bootstrap scaffolding only. After setup, this command must populate only `LOGICAL_VIEW`, and may refresh `ARCH_FILE` only under the synthesis readiness rule below.

If setup creates `REPO_FACTS_FILE`, leave it as-is. Do not read it as input and do not add facts to it from this generate command.

## Structured Contract

`ARCH_SCHEMA_FILE` is the authoritative structural contract for architecture artifacts. Build a JSON-compatible working model for every file you update, validate required sections, traceability records, gaps, and `High` / `Medium` / `Low` confidence values against the schema, then render Markdown with the corresponding template. The command owns extraction, classification, validation, and write policy; templates own Markdown layout only.

## Synthesis Readiness

Parse all five view paths from setup JSON: `SCENARIO_VIEW`, `LOGICAL_VIEW`, `PROCESS_VIEW`, `DEVELOPMENT_VIEW`, and `PHYSICAL_VIEW`.

A view is ready for synthesis only when it exists, no longer contains `NEEDS ARCH UPDATE`, and contains at least one source-backed non-gap architecture conclusion in its required sections. Unsupported or unknown items must be recorded in that view's gaps and do not make the view ready. Refresh `ARCH_FILE` only when all five views are ready and cross-view terminology is coherent. Otherwise leave `ARCH_FILE` unchanged and report the missing or not-ready views.

## Outline

1. Run `{SCRIPT}` from repo root and parse JSON for `ARCH_FILE`, `ARCH_SCHEMA_FILE`, `REPO_FACTS_FILE`, and all five view paths.
2. Load `SCENARIO_VIEW`, `LOGICAL_VIEW`, `ARCH_FILE`, `ARCH_SCHEMA_FILE`, `architecture-logical-template.md`, and `architecture-template.md`.
3. Extract source-backed scenario conclusions and scenario terminology.
4. Normalize capability, object, state, and boundary names.
5. Derive logical authority boundaries, domain relationships, and lifecycle constraints.
6. Classify each candidate as a supported logical conclusion or a logical gap under the schema and quality gates.
7. Render the schema-compliant logical working model with `architecture-logical-template.md`.
8. Apply the synthesis readiness rule. If all five view files are ready, refresh `ARCH_FILE`; otherwise leave synthesis untouched and report the missing or not-ready views.
9. Report updated paths and explicit logical gaps.

## Quality Gates

- ERROR if the logical view introduces classes, DTOs, database tables, fields, endpoints, schemas, or implementation data structures.
- ERROR if a target-view conclusion is not grounded in a scenario, boundary, lifecycle constraint, or stated user constraint.
- Unsupported target-view conclusions MUST appear only in `Logical Gaps`, not in conclusion tables.
- ERROR if a boundary has responsibilities but no explicit non-responsibility.
- Record gaps instead of inventing authority, lifecycle, or object facts.
