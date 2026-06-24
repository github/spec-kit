---
description: Generate the 4+1 development view from logical and process architecture views.
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

Generate or refresh the development view:

- Target view: `.specify/memory/architecture-development-view.md`
- Primary inputs: `.specify/memory/architecture-logical-view.md`, `.specify/memory/architecture-process-view.md`
- Optional synthesis refresh: `.specify/memory/architecture.md`

The development view derives architecture-level components, package boundary intent, contract/artifact semantics, and dependency rules from logical and process views.

## Operating Boundaries

- Write only `DEVELOPMENT_VIEW`; update `ARCH_FILE` only if the five architecture views are already coherent enough to refresh synthesis without inventing content.
- Do not read, populate, or update `REPO_FACTS_FILE`.
- Do not modify logical or process views, source code, specs, plans, tasks, docs, tests, package files, deployment files, or runbooks.
- Stay at architecture-level development structure, not concrete implementation design.
- If prerequisite views are insufficient, record development gaps instead of fabricating components, packages, or contracts.

## Setup Bootstrap

`{SCRIPT}` may create missing architecture memory files from templates, including non-target view placeholders and `REPO_FACTS_FILE`. Treat that as bootstrap scaffolding only. After setup, this command must populate only `DEVELOPMENT_VIEW`, and may refresh `ARCH_FILE` only under the synthesis readiness rule below.

If setup creates `REPO_FACTS_FILE`, leave it as-is. Do not read it as input and do not add facts to it from this generate command.

## Structured Contract

`ARCH_SCHEMA_FILE` is the authoritative structural contract for architecture artifacts. Build a JSON-compatible working model for every file you update, validate required sections, traceability records, gaps, and `High` / `Medium` / `Low` confidence values against the schema, then render Markdown with the corresponding template. The command owns extraction, classification, validation, and write policy; templates own Markdown layout only.

## Synthesis Readiness

Parse all five view paths from setup JSON: `SCENARIO_VIEW`, `LOGICAL_VIEW`, `PROCESS_VIEW`, `DEVELOPMENT_VIEW`, and `PHYSICAL_VIEW`.

A view is ready for synthesis only when it exists, no longer contains `NEEDS ARCH UPDATE`, and contains at least one source-backed non-gap architecture conclusion in its required sections. Unsupported or unknown items must be recorded in that view's gaps and do not make the view ready. Refresh `ARCH_FILE` only when all five views are ready and cross-view terminology is coherent. Otherwise leave `ARCH_FILE` unchanged and report the missing or not-ready views.

## Outline

1. Run `{SCRIPT}` from repo root and parse JSON for `ARCH_FILE`, `ARCH_SCHEMA_FILE`, `REPO_FACTS_FILE`, and all five view paths.
2. Load `LOGICAL_VIEW`, `PROCESS_VIEW`, `DEVELOPMENT_VIEW`, `ARCH_SCHEMA_FILE`, `architecture-development-template.md`, and `architecture-template.md`.
3. Extract source-backed logical boundaries, process collaborations, contracts, and invariants.
4. Normalize component, package, contract, and dependency terminology.
5. Derive architecture-level development boundaries and dependency rules.
6. Classify each candidate as a supported development conclusion or a development gap under the schema and quality gates.
7. Render the schema-compliant development working model with `architecture-development-template.md`.
8. Apply the synthesis readiness rule. If all five view files are ready, refresh `ARCH_FILE`; otherwise leave synthesis untouched and report the missing or not-ready views.
9. Report updated paths and explicit development gaps.

## Quality Gates

- ERROR if the development view contains source file paths, concrete package trees, classes, functions, framework wiring, or implementation tasks.
- ERROR if a target-view conclusion is not grounded in logical/process architecture or a stated constraint.
- Unsupported target-view conclusions MUST appear only in `Development View Gaps`, not in conclusion tables.
- ERROR if a boundary has responsibilities but no explicit non-responsibility.
- Record gaps instead of inventing development structure.
