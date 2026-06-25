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

You **MUST** consider the user input before proceeding (if not empty). In reverse workflows, user input may scope evidence collection or state explicit external constraints, but user input alone must not prove a reverse-generated architecture conclusion.

## Goal

Reverse-generate or refresh the development view from observable repository evidence:

- Evidence layer: `.specify/memory/architecture-repo-facts.md`
- Target view: `.specify/memory/architecture-development-view.md`
- Supporting inputs: logical and process views if available under Supporting View Availability
- Optional synthesis refresh: `.specify/memory/architecture.md`

The development view must include a `Dependency Matrix` section as a required output of this command.

## Operating Boundaries

- Write only `REPO_FACTS_FILE` and `DEVELOPMENT_VIEW`; update `ARCH_FILE` only when the architecture readiness validator returns `ready_gate: PASS`.
- Do not modify logical/process views, source code, README files, docs, package files, configuration, tests, deployment files, specs, plans, tasks, or runbooks.
- Stay at architecture-level development structure, not implementation design.
- If repository evidence is insufficient, record a specific evidence gap and development gap instead of inventing components, packages, contracts, or dependency rules.

## Setup Bootstrap

`{SCRIPT}` may create missing architecture memory files from templates, including non-target view placeholders. Treat that as bootstrap scaffolding only. After setup, this command must populate only `REPO_FACTS_FILE` and `DEVELOPMENT_VIEW`, and may refresh `ARCH_FILE` only under the synthesis readiness rule below.

## Evidence Sources

Inspect package directories, module boundaries, imports, manifests, build scripts, configuration ownership, test grouping, examples, and CI structure.

Repository-First Inputs: if `.specify/memory/repository-first/` exists, inspect its markdown artifacts before deriving the view. Treat dependency matrices as development-owned dependency governance evidence, not as an independent architecture view. Summarize build manifest detection, first-party module edges, allowed/forbidden invocation rules, dependency matrix signals, and governance actions in `REPO_FACTS_FILE`, then project only architecture-level constraints into the required `Dependency Matrix` section and related `DEVELOPMENT_VIEW` dependency rules. Other views may consume only derived development-view constraints, never the matrix itself. Repository-first content must not be copied verbatim into architecture views.

## Supporting View Availability

`LOGICAL_VIEW` and `PROCESS_VIEW` are available only when the readiness validator reports no blockers for those views such as missing artifact, placeholder marker, required-section, or traceability failures. Placeholder content and view gaps may identify missing context but must not support new development conclusions.

## Repo Facts Merge Rule

Treat `REPO_FACTS_FILE` as a cumulative evidence layer. Preserve existing non-placeholder facts from sections outside this command's evidence focus unless the cited evidence no longer exists or is contradicted by stronger evidence. When replacing, removing, or downgrading an existing fact, record the reason in `Evidence Gaps` or a review trigger instead of silently dropping it.

## Repo Facts Evidence Rules

- Every non-placeholder fact must name an evidence source such as a file, directory, configuration, test, script, manifest, command output, or commit signal.
- Confidence values are `High`, `Medium`, or `Low`: `High` means multiple independent sources agree; `Medium` means one strong source is present; `Low` means naming, directory structure, isolated code, or Git history suggests a fact but lacks behavior evidence.
- Git history is an auxiliary signal for change axes and boundary risks. It cannot independently prove architecture conclusions.
- Repository-first outputs are fact inputs for development governance. Summarize only architecture constraints, dependency rules, governance signals, gaps, or review triggers; do not copy full dependency inventories into architecture views.
- Concrete classes, functions, fields, endpoints, database tables, and implementation data structures may appear only as evidence sources, not architecture conclusions.
- Architecture conclusions must trace to repo facts, available supporting-view conclusions, or stated external constraints. If a conclusion is supported only by user input, report blocker code `ARCH_USER_INPUT_ONLY` and place it in `Evidence Gaps` or the target view gaps instead of conclusion tables.

## Structured Contract

`ARCH_SCHEMA_FILE` is the authoritative working-model contract for architecture artifacts. Use it to shape JSON-compatible working models for every file you update before rendering Markdown with the corresponding templates. `ARCH_VALIDATOR_FILE` and `ARCH_VALIDATOR_PS_FILE` provide the executable readiness gate for rendered artifacts. After rendering candidate changes, run the readiness validator and use its `ready_gate` and blocker codes as the only synthesis refresh decision. The command owns evidence extraction, classification, merge policy when applicable, and write routing; schemas own working-model structure; validators own rendered-artifact readiness; templates own Markdown layout only.

For `DEVELOPMENT_VIEW`, the `Dependency Matrix` section is a required output section with section id `dependency-matrix`. Populate it from source-backed repository facts, repository-first dependency matrix signals, available logical/process architecture relationships, and stated constraints; when evidence is insufficient for a matrix relation, record the missing relation in `Evidence Gaps` or `Development View Gaps` instead of omitting the section.

## Synthesis Readiness

Parse all five view paths and validator paths from setup JSON: `SCENARIO_VIEW`, `LOGICAL_VIEW`, `PROCESS_VIEW`, `DEVELOPMENT_VIEW`, `PHYSICAL_VIEW`, `ARCH_VALIDATOR_FILE`, and `ARCH_VALIDATOR_PS_FILE`.

Synthesis readiness is validator-owned. Run `ARCH_VALIDATOR_FILE --json` (or `ARCH_VALIDATOR_PS_FILE -Json` in PowerShell-only environments) after rendering candidate view updates. Refresh `ARCH_FILE` only when the validator returns `ready_gate: PASS` with no blockers. If the validator returns `ready_gate: BLOCKED`, leave `ARCH_FILE` unchanged and report the blocker codes, affected artifacts, and affected sections.

## Outline

1. Run `{SCRIPT}` from repo root and parse JSON for `ARCH_FILE`, `ARCH_SCHEMA_FILE`, `ARCH_VALIDATOR_FILE`, `ARCH_VALIDATOR_PS_FILE`, `REPO_FACTS_FILE`, and all five view paths.
2. Load `REPO_FACTS_FILE`, `LOGICAL_VIEW`, `PROCESS_VIEW`, `DEVELOPMENT_VIEW`, `ARCH_SCHEMA_FILE`, `architecture-repo-facts-template.md`, `architecture-development-template.md`, and `architecture-template.md`.
3. Refresh repo facts for this command's evidence focus and classify unsupported observations as evidence gaps.
4. Populate a schema-compliant development working model from eligible repo facts plus `LOGICAL_VIEW` and `PROCESS_VIEW` when they satisfy Supporting View Availability.
5. Populate the required `Dependency Matrix` section and summarize repository-first dependency matrices only as development-view architecture constraints, dependency rules, gaps, or review triggers.
6. Apply the repo facts merge rule before writing `REPO_FACTS_FILE`.
7. Run the readiness validator. If it returns `ready_gate: PASS`, refresh `ARCH_FILE`; otherwise leave synthesis untouched and report validator blocker codes.
8. Report updated paths and explicit unresolved gaps.

## Quality Gates

- BLOCKER `ARCH_UNSUPPORTED_CONCLUSION` if the development view promotes concrete source paths, package trees, classes, functions, framework wiring, or implementation tasks into architecture conclusions.
- BLOCKER `ARCH_DEPENDENCY_MATRIX_MISSING` if the development view omits the required `Dependency Matrix` section.
- BLOCKER `ARCH_SOURCE_MISSING` if a conclusion or dependency matrix entry lacks a repo fact, available `LOGICAL_VIEW` or `PROCESS_VIEW` source, or stated constraint.
- BLOCKER `ARCH_REPO_FIRST_MATRIX_MISUSED` if repository-first dependency matrices are copied into architecture views, treated as an independent architecture view, or used as direct non-development evidence.
- BLOCKER `ARCH_UNSUPPORTED_CONCLUSION` if unsupported target-view conclusions appear in conclusion tables; place them only in `Evidence Gaps` or `Development View Gaps`.
- BLOCKER `ARCH_GIT_HISTORY_ONLY` if Git history is used alone as a development conclusion.
- BLOCKER `ARCH_SOURCE_MISSING` if development ownership or dependency governance cannot be supported by repository evidence; record the unsupported item in evidence gaps and target-view gaps.
