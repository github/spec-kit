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

- Write only `SCENARIO_VIEW`; update `ARCH_FILE` only when the architecture readiness validator returns `ready_gate: PASS`.
- Do not read, populate, or update `REPO_FACTS_FILE`.
- Read `.specify/memory/uc.md` only as optional scenario background.
- Do not modify `.specify/memory/uc.md`, `.specify/memory/constitution.md`, feature specs, plans, tasks, source code, tests, root `docs/`, deployment manifests, or runbooks.
- Stay at abstract architecture-design level.
- If context is insufficient, record a specific scenario gap instead of inventing actors, goals, business facts, or acceptance meaning.

## Setup Bootstrap

`{SCRIPT}` may create missing architecture memory files from templates, including non-target view placeholders and `REPO_FACTS_FILE`. Treat that as bootstrap scaffolding only. After setup, this command must populate only `SCENARIO_VIEW`, and may refresh `ARCH_FILE` only under the synthesis readiness rule below.

If setup creates `REPO_FACTS_FILE`, leave it as-is. Do not read it as input and do not add facts to it from this generate command.

## Structured Contract

`ARCH_SCHEMA_FILE` is the authoritative working-model contract for architecture artifacts. Use it to shape JSON-compatible working models for every file you update before rendering Markdown with the corresponding templates. `ARCH_VALIDATOR_FILE` and `ARCH_VALIDATOR_PS_FILE` provide the executable readiness gate for rendered artifacts. After rendering candidate changes, run the readiness validator and use its `ready_gate` and blocker codes as the only synthesis refresh decision. The command owns evidence extraction, classification, merge policy when applicable, and write routing; schemas own working-model structure; validators own rendered-artifact readiness; templates own Markdown layout only.

## Synthesis Readiness

Parse all five view paths and validator paths from setup JSON: `SCENARIO_VIEW`, `LOGICAL_VIEW`, `PROCESS_VIEW`, `DEVELOPMENT_VIEW`, `PHYSICAL_VIEW`, `ARCH_VALIDATOR_FILE`, and `ARCH_VALIDATOR_PS_FILE`.

Synthesis readiness is validator-owned. Run `ARCH_VALIDATOR_FILE --json` (or `ARCH_VALIDATOR_PS_FILE -Json` in PowerShell-only environments) after rendering candidate view updates. Refresh `ARCH_FILE` only when the validator returns `ready_gate: PASS` with no blockers. If the validator returns `ready_gate: BLOCKED`, leave `ARCH_FILE` unchanged and report the blocker codes, affected artifacts, and affected sections.

## Outline

1. Run `{SCRIPT}` from repo root and parse JSON for `ARCH_FILE`, `ARCH_SCHEMA_FILE`, `ARCH_VALIDATOR_FILE`, `ARCH_VALIDATOR_PS_FILE`, `REPO_FACTS_FILE`, and all five view paths.
2. Load `SCENARIO_VIEW`, `ARCH_FILE`, `ARCH_SCHEMA_FILE`, `architecture-scenario-template.md`, and `architecture-template.md`.
3. Load `.specify/memory/uc.md` if present as supporting context.
4. Extract source-backed actors, goals, triggers, paths, branches, and acceptance semantics.
5. Normalize scenario terminology and derive scenario-level boundaries.
6. Classify each candidate as a supported scenario conclusion or a scenario gap under the schema and quality gates.
7. Render the schema-compliant scenario working model with `architecture-scenario-template.md`.
8. Run the readiness validator. If it returns `ready_gate: PASS`, refresh `ARCH_FILE` using `architecture-template.md`; otherwise leave synthesis untouched and report validator blocker codes.
9. Report updated paths and explicit scenario gaps.

## Quality Gates

- BLOCKER `ARCH_UNSUPPORTED_CONCLUSION` if the scenario view contains implementation details, components, APIs, database tables, deployment scripts, or task plans.
- BLOCKER `ARCH_SOURCE_MISSING` if a conclusion or dependency matrix entry lacks stated scenario source, user input source, or existing memory source.
- BLOCKER `ARCH_UNSUPPORTED_CONCLUSION` if unsupported target-view conclusions appear in conclusion tables; place them only in `Scenario Gaps`.
- BLOCKER `ARCH_BOUNDARY_NONRESPONSIBILITY_MISSING` if a boundary has responsibilities but no explicit non-responsibility.
- Record gaps instead of inventing business facts.
