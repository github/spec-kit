---
description: Generate all 4+1 architecture views and the architecture synthesis from intended project context.
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

Generate or refresh the complete forward 4+1 architecture set:

- Scenario view: `.specify/memory/architecture-scenario-view.md`
- Logical view: `.specify/memory/architecture-logical-view.md`
- Process view: `.specify/memory/architecture-process-view.md`
- Development view: `.specify/memory/architecture-development-view.md`
- Physical view: `.specify/memory/architecture-physical-view.md`
- Synthesis: `.specify/memory/architecture.md`

This command is the full forward-generation workflow. It derives the `+1` scenario view first, then derives the four supporting views in dependency order, and refreshes the synthesis only from validated view content.

## Operating Boundaries

- Write only `SCENARIO_VIEW`, `LOGICAL_VIEW`, `PROCESS_VIEW`, `DEVELOPMENT_VIEW`, `PHYSICAL_VIEW`, and `ARCH_FILE`.
- Do not read, populate, or update `REPO_FACTS_FILE`.
- Read `.specify/memory/uc.md` only as optional scenario background.
- Do not modify `.specify/memory/uc.md`, `.specify/memory/constitution.md`, feature specs, plans, tasks, source code, tests, root `docs/`, deployment manifests, package files, infrastructure files, or runbooks.
- Stay at abstract architecture-design level across all views.
- If context is insufficient for any view, record a specific gap in that view instead of inventing architecture facts.

## Setup Bootstrap

`{SCRIPT}` may create missing architecture memory files from templates, including `REPO_FACTS_FILE`. Treat that as bootstrap scaffolding only. After setup, this command must populate only the five architecture views and `ARCH_FILE`.

If setup creates `REPO_FACTS_FILE`, leave it as-is. Do not read it as input and do not add facts to it from this generate command.

## Structured Contract

`ARCH_SCHEMA_FILE` is the authoritative working-model contract for architecture artifacts. Use it to shape JSON-compatible working models for every file you update before rendering Markdown with the corresponding templates. `ARCH_VALIDATOR_FILE` and `ARCH_VALIDATOR_PS_FILE` provide the executable readiness gate for rendered artifacts. After rendering candidate changes, run the readiness validator and use its `ready_gate` and blocker codes as the only synthesis refresh decision. The command owns evidence extraction, classification, merge policy when applicable, and write routing; schemas own working-model structure; validators own rendered-artifact readiness; templates own Markdown layout only.

For `DEVELOPMENT_VIEW`, the `Dependency Matrix` section is a required output section. Populate it from source-backed logical/process architecture relationships and stated constraints; when evidence is insufficient for a matrix relation, record the missing relation in `Development View Gaps` instead of omitting the section.

## Generation Order

Generate and validate views in this order:

1. `SCENARIO_VIEW` from user input, optional `.specify/memory/uc.md`, and existing memory context.
2. `LOGICAL_VIEW` from validated scenario architecture semantics.
3. `PROCESS_VIEW` from validated scenario paths and logical boundaries.
4. `DEVELOPMENT_VIEW` from validated logical/process architecture relationships.
5. `PHYSICAL_VIEW` from validated process/development architecture constraints.
6. `ARCH_FILE` from the five validated views, only after synthesis readiness passes.

Each later view may use earlier views generated in the same command after their working models pass the schema and quality gates. Do not use a placeholder or gap-only view as proof for downstream architecture conclusions.

## Synthesis Readiness

Parse all five view paths and validator paths from setup JSON: `SCENARIO_VIEW`, `LOGICAL_VIEW`, `PROCESS_VIEW`, `DEVELOPMENT_VIEW`, `PHYSICAL_VIEW`, `ARCH_VALIDATOR_FILE`, and `ARCH_VALIDATOR_PS_FILE`.

Synthesis readiness is validator-owned. Run `ARCH_VALIDATOR_FILE --json` (or `ARCH_VALIDATOR_PS_FILE -Json` in PowerShell-only environments) after rendering candidate view updates. Refresh `ARCH_FILE` only when the validator returns `ready_gate: PASS` with no blockers. If the validator returns `ready_gate: BLOCKED`, leave `ARCH_FILE` unchanged and report the blocker codes, affected artifacts, and affected sections.

## Outline

1. Run `{SCRIPT}` from repo root and parse JSON for `ARCH_FILE`, `ARCH_SCHEMA_FILE`, `ARCH_VALIDATOR_FILE`, `ARCH_VALIDATOR_PS_FILE`, `REPO_FACTS_FILE`, and all five view paths.
2. Load `ARCH_FILE`, all five view files, `ARCH_SCHEMA_FILE`, all six architecture templates, and `.specify/memory/uc.md` if present.
3. Generate the scenario working model from source-backed user, use-case, and memory context.
4. Generate logical, process, development, and physical working models in dependency order, using only validated upstream architecture conclusions and stated constraints.
5. Populate the required development `Dependency Matrix` section from validated logical/process relationships and stated constraints.
6. Classify every candidate conclusion as supported architecture content or a view-specific gap under the schema and quality gates.
7. Render the five schema-compliant view working models with their corresponding templates.
8. Run the readiness validator. If it returns `ready_gate: PASS`, render `ARCH_FILE` with `architecture-template.md`; otherwise leave synthesis untouched and report validator blocker codes.
9. Report updated paths and explicit gaps by view.

## Quality Gates

- BLOCKER `ARCH_UNSUPPORTED_CONCLUSION` if any generated view contains concrete implementation design, source paths, classes, functions, endpoints, database fields, deployment manifests, infrastructure configuration, scripts, runbooks, plans, tasks, or test strategy.
- BLOCKER `ARCH_SOURCE_MISSING` if a conclusion or dependency matrix entry lacks user input, optional use-case context, validated upstream architecture, existing memory context, or a stated constraint.
- BLOCKER `ARCH_DEPENDENCY_MATRIX_MISSING` if the development view omits the required `Dependency Matrix` section.
- BLOCKER `ARCH_SOURCE_MISSING` if a conclusion or dependency matrix entry lacks logical/process architecture or a stated constraint.
- BLOCKER `ARCH_UNSUPPORTED_CONCLUSION` if unsupported conclusions appear in conclusion tables; place them only in the corresponding view gaps.
- BLOCKER `ARCH_BOUNDARY_NONRESPONSIBILITY_MISSING` if a boundary has responsibilities but no explicit non-responsibility.
- Record gaps instead of inventing business facts, authority boundaries, runtime behavior, development structure, topology, or operational constraints.
