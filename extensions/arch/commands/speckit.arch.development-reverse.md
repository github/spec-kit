---
description: Reverse-generate the 4+1 development view from observable repository facts.
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

Reverse-generate or refresh the development view from observable repository evidence:

- Evidence layer: `.specify/memory/architecture-repo-facts.md`
- Target view: `.specify/memory/architecture-development-view.md`
- Supporting inputs: logical and process views if available under Supporting View Availability
- Optional synthesis refresh: `.specify/memory/architecture.md`

## Operating Boundaries

- Write only `REPO_FACTS_FILE` and `DEVELOPMENT_VIEW`; update `ARCH_FILE` only if the five architecture views are already coherent enough to refresh synthesis without inventing content.
- Do not modify logical/process views, source code, README files, docs, package files, configuration, tests, deployment files, specs, plans, tasks, or runbooks.
- Stay at architecture-level development structure, not implementation design.
- If repository evidence is insufficient, record a specific evidence gap and development gap instead of inventing components, packages, contracts, or dependency rules.

## Setup Bootstrap

`{SCRIPT}` may create missing architecture memory files from templates, including non-target view placeholders. Treat that as bootstrap scaffolding only. After setup, this command must populate only `REPO_FACTS_FILE` and `DEVELOPMENT_VIEW`, and may refresh `ARCH_FILE` only under the synthesis readiness rule below.

## Evidence Sources

Inspect package directories, module boundaries, imports, manifests, build scripts, configuration ownership, test grouping, examples, and CI structure.

Repository-First Inputs: if `.specify/memory/repository-first/` exists, inspect its markdown artifacts before deriving the view. Summarize build manifest detection, first-party module edges, allowed/forbidden invocation rules, dependency matrix signals, and governance actions in `REPO_FACTS_FILE`. Repository-first content must not be copied verbatim into architecture views.

## Supporting View Availability

`LOGICAL_VIEW` and `PROCESS_VIEW` are available only when each file exists, does not contain `NEEDS ARCH UPDATE`, and contains at least one source-backed non-gap architecture conclusion. Placeholder content and view gaps may identify missing context but must not support new development conclusions.

## Repo Facts Merge Rule

Treat `REPO_FACTS_FILE` as a cumulative evidence layer. Preserve existing non-placeholder facts from sections outside this command's evidence focus unless the cited evidence no longer exists or is contradicted by stronger evidence. When replacing, removing, or downgrading an existing fact, record the reason in `Evidence Gaps` or a review trigger instead of silently dropping it.

## Repo Facts Evidence Rules

- Every non-placeholder fact must name an evidence source such as a file, directory, configuration, test, script, manifest, command output, or commit signal.
- Confidence values are `High`, `Medium`, or `Low`: `High` means multiple independent sources agree; `Medium` means one strong source is present; `Low` means naming, directory structure, isolated code, or Git history suggests a fact but lacks behavior evidence.
- Git history is an auxiliary signal for change axes and boundary risks. It cannot independently prove architecture conclusions.
- Repository-first outputs are fact inputs. Summarize only architecture constraints, governance signals, gaps, or review triggers; do not copy full dependency inventories into architecture views.
- Concrete classes, functions, fields, endpoints, database tables, and implementation data structures may appear only as evidence sources, not architecture conclusions.
- Architecture conclusions must trace to repo facts, available supporting-view conclusions, user input, or stated external constraints. Unsupported items MUST appear only in `Evidence Gaps` or the target view gaps.

## Structured Contract

`ARCH_SCHEMA_FILE` is the authoritative structural contract for architecture artifacts. Build JSON-compatible working models for `REPO_FACTS_FILE` and the target view, validate sections, traceability records, gaps, and `High` / `Medium` / `Low` confidence values against the schema, then render Markdown with the corresponding templates. The command owns evidence collection, classification, merge policy, validation, and write policy; templates own Markdown layout only.

## Synthesis Readiness

Parse all five view paths from setup JSON: `SCENARIO_VIEW`, `LOGICAL_VIEW`, `PROCESS_VIEW`, `DEVELOPMENT_VIEW`, and `PHYSICAL_VIEW`.

A view is ready for synthesis only when it exists, no longer contains `NEEDS ARCH UPDATE`, and contains at least one source-backed non-gap architecture conclusion in its required sections. Unsupported or unknown items must be recorded in that view's gaps and do not make the view ready. Refresh `ARCH_FILE` only when all five views are ready and cross-view terminology is coherent. Otherwise leave `ARCH_FILE` unchanged and report the missing or not-ready views.

## Outline

1. Run `{SCRIPT}` from repo root and parse JSON for `ARCH_FILE`, `ARCH_SCHEMA_FILE`, `REPO_FACTS_FILE`, and all five view paths.
2. Load `REPO_FACTS_FILE`, `LOGICAL_VIEW`, `PROCESS_VIEW`, `DEVELOPMENT_VIEW`, `ARCH_SCHEMA_FILE`, `architecture-repo-facts-template.md`, `architecture-development-template.md`, and `architecture-template.md`.
3. Refresh repo facts for this command's evidence focus and classify unsupported observations as evidence gaps.
4. Populate a schema-compliant development working model from eligible repo facts plus `LOGICAL_VIEW` and `PROCESS_VIEW` when they satisfy Supporting View Availability.
5. Summarize repository-first dependency matrices only as architecture constraints, dependency rules, gaps, or review triggers.
6. Apply the repo facts merge rule before writing `REPO_FACTS_FILE`.
7. Apply the synthesis readiness rule. If all five view files are ready, refresh `ARCH_FILE`; otherwise leave synthesis untouched and report the missing or not-ready views.
8. Report updated paths and explicit unresolved gaps.

## Quality Gates

- ERROR if the development view promotes concrete source paths, package trees, classes, functions, framework wiring, or implementation tasks into architecture conclusions.
- ERROR if repository-first dependency matrices are copied wholesale into a 4+1 view instead of summarized as architecture constraints.
- ERROR if a target-view conclusion lacks a repo fact, available `LOGICAL_VIEW` or `PROCESS_VIEW` source, or stated constraint.
- Unsupported target-view conclusions MUST appear only in `Evidence Gaps` or `Development View Gaps`, not in conclusion tables.
- ERROR if Git history is used alone as a development conclusion.
- GAP if development ownership or dependency governance cannot be supported by repository evidence.
