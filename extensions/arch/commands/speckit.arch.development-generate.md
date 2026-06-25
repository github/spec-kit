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

The development view derives architecture-level components, package boundary intent, contract/artifact semantics, dependency rules, and the required dependency matrix from logical and process views.

## Operating Boundaries

- Write only `DEVELOPMENT_VIEW`; update `ARCH_FILE` only when the architecture readiness validator returns `ready_gate: PASS`.
- Do not read, populate, or update `REPO_FACTS_FILE`.
- Do not modify logical or process views, source code, specs, plans, tasks, docs, tests, package files, deployment files, or runbooks.
- Stay at architecture-level development structure, not concrete implementation design.
- If prerequisite views are insufficient, record development gaps instead of fabricating components, packages, or contracts.

## Setup Bootstrap

`{SCRIPT}` may create missing architecture memory files from templates, including non-target view placeholders and `REPO_FACTS_FILE`. Treat that as bootstrap scaffolding only. After setup, this command must populate only `DEVELOPMENT_VIEW`, and may refresh `ARCH_FILE` only under the synthesis readiness rule below.

If setup creates `REPO_FACTS_FILE`, leave it as-is. Do not read it as input and do not add facts to it from this generate command.

## Structured Contract

`ARCH_SCHEMA_FILE` is the authoritative working-model contract for architecture artifacts. Use it to shape JSON-compatible working models for every file you update before rendering Markdown with the corresponding templates. `ARCH_VALIDATOR_FILE` and `ARCH_VALIDATOR_PS_FILE` provide the executable readiness gate for rendered artifacts. After rendering candidate changes, run the readiness validator and use its `ready_gate` and blocker codes as the only synthesis refresh decision. The command owns evidence extraction, classification, merge policy when applicable, and write routing; schemas own working-model structure; validators own rendered-artifact readiness; templates own Markdown layout only.

For `DEVELOPMENT_VIEW`, the `Dependency Matrix` section is a required output section with section id `dependency-matrix`. Populate it from source-backed logical/process architecture relationships and stated constraints; when evidence is insufficient for a matrix relation, record the missing relation in `Development View Gaps` instead of omitting the section.

## Synthesis Readiness

Parse all five view paths and validator paths from setup JSON: `SCENARIO_VIEW`, `LOGICAL_VIEW`, `PROCESS_VIEW`, `DEVELOPMENT_VIEW`, `PHYSICAL_VIEW`, `ARCH_VALIDATOR_FILE`, and `ARCH_VALIDATOR_PS_FILE`.

Synthesis readiness is validator-owned. Run `ARCH_VALIDATOR_FILE --json` (or `ARCH_VALIDATOR_PS_FILE -Json` in PowerShell-only environments) after rendering candidate view updates. Refresh `ARCH_FILE` only when the validator returns `ready_gate: PASS` with no blockers. If the validator returns `ready_gate: BLOCKED`, leave `ARCH_FILE` unchanged and report the blocker codes, affected artifacts, and affected sections.

## Outline

1. Run `{SCRIPT}` from repo root and parse JSON for `ARCH_FILE`, `ARCH_SCHEMA_FILE`, `ARCH_VALIDATOR_FILE`, `ARCH_VALIDATOR_PS_FILE`, `REPO_FACTS_FILE`, and all five view paths.
2. Load `LOGICAL_VIEW`, `PROCESS_VIEW`, `DEVELOPMENT_VIEW`, `ARCH_SCHEMA_FILE`, `architecture-development-template.md`, and `architecture-template.md`.
3. Extract source-backed logical boundaries, process collaborations, contracts, and invariants.
4. Normalize component, package, contract, and dependency terminology.
5. Derive architecture-level development boundaries, dependency rules, and the required dependency matrix.
6. Classify each candidate as a supported development conclusion or a development gap under the schema and quality gates.
7. Render the schema-compliant development working model with `architecture-development-template.md`.
8. Run the readiness validator. If it returns `ready_gate: PASS`, refresh `ARCH_FILE`; otherwise leave synthesis untouched and report validator blocker codes.
9. Report updated paths and explicit development gaps.

## Quality Gates

- BLOCKER `ARCH_UNSUPPORTED_CONCLUSION` if the development view contains source file paths, concrete package trees, classes, functions, framework wiring, or implementation tasks.
- BLOCKER `ARCH_DEPENDENCY_MATRIX_MISSING` if the development view omits the required `Dependency Matrix` section.
- BLOCKER `ARCH_SOURCE_MISSING` if a conclusion or dependency matrix entry lacks logical/process architecture or a stated constraint.
- BLOCKER `ARCH_UNSUPPORTED_CONCLUSION` if unsupported target-view conclusions appear in conclusion tables; place them only in `Development View Gaps`.
- BLOCKER `ARCH_BOUNDARY_NONRESPONSIBILITY_MISSING` if a boundary has responsibilities but no explicit non-responsibility.
- Record gaps instead of inventing development structure.
