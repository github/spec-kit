---
description: Reverse-generate all 4+1 architecture views and the architecture synthesis from observable repository facts.
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

Reverse-generate or refresh the complete 4+1 architecture set from observable repository evidence:

- Evidence layer: `.specify/memory/architecture-repo-facts.md`
- Scenario view: `.specify/memory/architecture-scenario-view.md`
- Logical view: `.specify/memory/architecture-logical-view.md`
- Process view: `.specify/memory/architecture-process-view.md`
- Development view: `.specify/memory/architecture-development-view.md`
- Physical view: `.specify/memory/architecture-physical-view.md`
- Synthesis: `.specify/memory/architecture.md`

This command is the full reverse-generation workflow. It records repository facts first, derives the `+1` scenario view and four supporting views from those facts, then refreshes synthesis only from validated view content.

## Operating Boundaries

- Write only `REPO_FACTS_FILE`, `SCENARIO_VIEW`, `LOGICAL_VIEW`, `PROCESS_VIEW`, `DEVELOPMENT_VIEW`, `PHYSICAL_VIEW`, and `ARCH_FILE`.
- Do not modify source code, README files, project documentation, package files, configuration, tests, deployment files, `.specify/memory/uc.md`, `.specify/memory/constitution.md`, feature specs, plans, tasks, root `docs/`, deployment manifests, infrastructure files, or runbooks.
- Stay at abstract architecture-design level across all views.
- If repository evidence is insufficient for any view, record a specific evidence gap and view gap instead of inventing architecture facts.

## Setup Bootstrap

`{SCRIPT}` may create missing architecture memory files from templates. Treat that as bootstrap scaffolding only. After setup, this command must populate only `REPO_FACTS_FILE`, the five architecture views, and `ARCH_FILE`.

## Evidence Sources

Inspect README/docs, CLI/API entry points, examples, tests, route declarations, package directories, module boundaries, imports, manifests, build scripts, configuration ownership, CI structure, deployment clues, and user-visible behavior descriptions. Prefer concise inventory over exhaustive source listing.

Repository-First Inputs: if `.specify/memory/repository-first/` exists, inspect its markdown artifacts before deriving the views. Dependency matrices are owned by the development view: summarize build manifest detection, first-party module edges, allowed/forbidden invocation rules, dependency matrix signals, and governance actions in `REPO_FACTS_FILE`, then project only architecture-level dependency constraints into the required development `Dependency Matrix` section and related development-view rules. A dependency matrix is evidence for development governance, not an independent architecture view or equal input to every 4+1 view. Repository-first content must not be copied verbatim into architecture views.

## Repo Facts Merge Rule

Treat `REPO_FACTS_FILE` as a cumulative evidence layer. Preserve existing non-placeholder facts unless the cited evidence no longer exists or is contradicted by stronger evidence. When replacing, removing, or downgrading an existing fact, record the reason in `Evidence Gaps` or a review trigger instead of silently dropping it.

## Repo Facts Evidence Rules

- Every non-placeholder fact must name an evidence source such as a file, directory, configuration, test, script, manifest, command output, or commit signal.
- Confidence values are `High`, `Medium`, or `Low`: `High` means multiple independent sources agree; `Medium` means one strong source is present; `Low` means naming, directory structure, isolated code, or Git history suggests a fact but lacks behavior evidence.
- Git history is an auxiliary signal for change axes and boundary risks. It cannot independently prove architecture conclusions.
- Repository-first outputs are fact inputs only when summarized into architecture constraints, dependency rules, governance signals, gaps, or review triggers; do not copy full dependency inventories into architecture views.
- Concrete classes, functions, fields, endpoints, database tables, and implementation data structures may appear only as evidence sources, not architecture conclusions.
- Architecture conclusions must trace to repo facts or stated external constraints. If a conclusion is supported only by user input, report blocker code `ARCH_USER_INPUT_ONLY` and place it in `Evidence Gaps` or the target view gaps instead of conclusion tables.

## Structured Contract

`ARCH_SCHEMA_FILE` is the authoritative working-model contract for architecture artifacts. Use it to shape JSON-compatible working models for every file you update before rendering Markdown with the corresponding templates. `ARCH_VALIDATOR_FILE` and `ARCH_VALIDATOR_PS_FILE` provide the executable readiness gate for rendered artifacts. After rendering candidate changes, run the readiness validator and use its `ready_gate` and blocker codes as the only synthesis refresh decision. The command owns evidence extraction, classification, merge policy when applicable, and write routing; schemas own working-model structure; validators own rendered-artifact readiness; templates own Markdown layout only.

For `DEVELOPMENT_VIEW`, the `Dependency Matrix` section is a required output section with section id `dependency-matrix`. Populate it from source-backed repository facts, repository-first dependency matrix signals, available logical/process architecture relationships generated in this command, and stated constraints; when evidence is insufficient for a matrix relation, record the missing relation in `Evidence Gaps` or `Development View Gaps` instead of omitting the section.

## Reverse Generation Order

Generate and validate artifacts in this order:

1. `REPO_FACTS_FILE` from observable repository evidence and optional repository-first evidence.
2. `SCENARIO_VIEW` from high- or medium-confidence facts about user-visible behavior, actors, goals, paths, and acceptance semantics.
3. `LOGICAL_VIEW` from repo facts plus validated scenario architecture semantics.
4. `PROCESS_VIEW` from repo facts plus validated scenario paths and logical boundaries.
5. `DEVELOPMENT_VIEW` from repo facts plus validated logical/process architecture relationships, including the required `Dependency Matrix` section.
6. `PHYSICAL_VIEW` from repo facts plus validated process/development architecture constraints.
7. `ARCH_FILE` from the five validated views, only after synthesis readiness passes.

Each later view may use earlier views generated in the same command after their working models pass the schema and quality gates. Do not use a placeholder or gap-only view as proof for downstream architecture conclusions.

## Synthesis Readiness

Parse all five view paths and validator paths from setup JSON: `SCENARIO_VIEW`, `LOGICAL_VIEW`, `PROCESS_VIEW`, `DEVELOPMENT_VIEW`, `PHYSICAL_VIEW`, `ARCH_VALIDATOR_FILE`, and `ARCH_VALIDATOR_PS_FILE`.

Synthesis readiness is validator-owned. Run `ARCH_VALIDATOR_FILE --json` (or `ARCH_VALIDATOR_PS_FILE -Json` in PowerShell-only environments) after rendering candidate view updates. Refresh `ARCH_FILE` only when the validator returns `ready_gate: PASS` with no blockers. If the validator returns `ready_gate: BLOCKED`, leave `ARCH_FILE` unchanged and report the blocker codes, affected artifacts, and affected sections.

## Outline

1. Run `{SCRIPT}` from repo root and parse JSON for `ARCH_FILE`, `ARCH_SCHEMA_FILE`, `ARCH_VALIDATOR_FILE`, `ARCH_VALIDATOR_PS_FILE`, `REPO_FACTS_FILE`, and all five view paths.
2. Load `REPO_FACTS_FILE`, `ARCH_FILE`, all five view files, `ARCH_SCHEMA_FILE`, all seven architecture templates, and optional `.specify/memory/repository-first/` markdown artifacts.
3. Refresh repo facts across scenario, logical, process, development, and physical evidence focuses; classify unsupported observations as evidence gaps.
4. Generate scenario, logical, process, development, and physical working models in reverse-generation order, using only eligible repo facts, validated upstream architecture conclusions, and stated constraints.
5. Populate the required development `Dependency Matrix` section and summarize repository-first dependency matrices only as development-view architecture constraints, dependency rules, gaps, or review triggers.
6. Apply the repo facts merge rule before writing `REPO_FACTS_FILE`.
7. Classify every candidate conclusion as supported architecture content or a view-specific gap under the schema and quality gates.
8. Render the repo facts file and five schema-compliant view working models with their corresponding templates.
9. Run the readiness validator. If it returns `ready_gate: PASS`, render `ARCH_FILE` with `architecture-template.md`; otherwise leave synthesis untouched and report validator blocker codes.
10. Report updated paths and explicit unresolved gaps by evidence focus and view.

## Quality Gates

- BLOCKER `ARCH_SOURCE_MISSING` if a conclusion or dependency matrix entry lacks a repo fact source or stated external constraint source.
- BLOCKER `ARCH_SOURCE_MISSING` if the repo facts file contains generic claims without file paths, directories, configuration, tests, commands, or commit signals.
- BLOCKER `ARCH_UNSUPPORTED_CONCLUSION` if any generated view promotes concrete source paths, package trees, classes, functions, fields, endpoints, database structure, framework wiring, deployment manifests, infrastructure configuration, scripts, runbooks, plans, tasks, or test strategy into architecture conclusions.
- BLOCKER `ARCH_DEPENDENCY_MATRIX_MISSING` if the development view omits the required `Dependency Matrix` section.
- BLOCKER `ARCH_SOURCE_MISSING` if a conclusion or dependency matrix entry lacks a repo fact, generated `LOGICAL_VIEW` or `PROCESS_VIEW` source, repository-first dependency matrix signal, or stated constraint.
- BLOCKER `ARCH_REPO_FIRST_MATRIX_MISUSED` if repository-first dependency matrices are copied into architecture views, treated as an independent architecture view, or used as direct non-development evidence.
- BLOCKER `ARCH_GIT_HISTORY_ONLY` if Git history is used alone as an architecture conclusion.
- BLOCKER `ARCH_UNSUPPORTED_CONCLUSION` if unsupported conclusions appear in conclusion tables; place them only in `Evidence Gaps` or the corresponding view gaps.
- Record gaps instead of inventing actors, business meaning, authority boundaries, runtime behavior, development structure, topology, or operational constraints.
