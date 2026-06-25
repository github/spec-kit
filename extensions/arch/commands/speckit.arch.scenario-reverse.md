---
description: Reverse-generate the 4+1 scenario view from observable repository facts.
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

Reverse-generate or refresh the scenario view from observable repository evidence:

- Evidence layer: `.specify/memory/architecture-repo-facts.md`
- Target view: `.specify/memory/architecture-scenario-view.md`
- Optional synthesis refresh: `.specify/memory/architecture.md`

## Operating Boundaries

- Write only `REPO_FACTS_FILE` and `SCENARIO_VIEW`; update `ARCH_FILE` only when the architecture readiness validator returns `ready_gate: PASS`.
- Do not modify source code, README files, project documentation, package files, configuration, tests, deployment files, `.specify/memory/uc.md`, `.specify/memory/constitution.md`, feature specs, plans, tasks, root `docs/`, deployment manifests, or runbooks.
- Stay at abstract architecture-design level.
- If repository evidence is insufficient, record a specific evidence gap and scenario gap instead of inventing actors, use cases, business meaning, or acceptance semantics.

## Setup Bootstrap

`{SCRIPT}` may create missing architecture memory files from templates, including non-target view placeholders. Treat that as bootstrap scaffolding only. After setup, this command must populate only `REPO_FACTS_FILE` and `SCENARIO_VIEW`, and may refresh `ARCH_FILE` only under the synthesis readiness rule below.

## Evidence Sources

Inspect README/docs, CLI/API entry points, examples, tests, route declarations, configuration, package manifests, and user-visible behavior descriptions. Infer target-view conclusions only from user-visible behavior, explicit documentation, or stated external constraints. Prefer concise inventory over exhaustive source listing.

Repository-First Inputs: if `.specify/memory/repository-first/` exists, inspect only non-matrix markdown evidence that affects scenario meaning, such as user-visible entry points, examples, or stated invocation constraints, and summarize those signals in `REPO_FACTS_FILE`. Dependency matrices are owned by the development view; this command must not consume dependency matrices directly or treat them as a separate architecture view. Repository-first content must not be copied verbatim into architecture views.

## Repo Facts Merge Rule

Treat `REPO_FACTS_FILE` as a cumulative evidence layer. Preserve existing non-placeholder facts from sections outside this command's evidence focus unless the cited evidence no longer exists or is contradicted by stronger evidence. When replacing, removing, or downgrading an existing fact, record the reason in `Evidence Gaps` or a review trigger instead of silently dropping it.

## Repo Facts Evidence Rules

- Every non-placeholder fact must name an evidence source such as a file, directory, configuration, test, script, manifest, command output, or commit signal.
- Confidence values are `High`, `Medium`, or `Low`: `High` means multiple independent sources agree; `Medium` means one strong source is present; `Low` means naming, directory structure, isolated code, or Git history suggests a fact but lacks behavior evidence.
- Git history is an auxiliary signal for change axes and boundary risks. It cannot independently prove architecture conclusions.
- Repository-first outputs are fact inputs only when they match this command's scenario evidence focus. Do not consume repository-first dependency matrices directly; use development-view dependency conclusions only after `DEVELOPMENT_VIEW` is synthesis-ready and relevant to scenario meaning.
- Concrete classes, functions, fields, endpoints, database tables, and implementation data structures may appear only as evidence sources, not architecture conclusions.
- Architecture conclusions must trace to repo facts or stated external constraints. If a conclusion is supported only by user input, report blocker code `ARCH_USER_INPUT_ONLY` and place it in `Evidence Gaps` or the target view gaps instead of conclusion tables.

## Structured Contract

`ARCH_SCHEMA_FILE` is the authoritative working-model contract for architecture artifacts. Use it to shape JSON-compatible working models for every file you update before rendering Markdown with the corresponding templates. `ARCH_VALIDATOR_FILE` and `ARCH_VALIDATOR_PS_FILE` provide the executable readiness gate for rendered artifacts. After rendering candidate changes, run the readiness validator and use its `ready_gate` and blocker codes as the only synthesis refresh decision. The command owns evidence extraction, classification, merge policy when applicable, and write routing; schemas own working-model structure; validators own rendered-artifact readiness; templates own Markdown layout only.

## Synthesis Readiness

Parse all five view paths and validator paths from setup JSON: `SCENARIO_VIEW`, `LOGICAL_VIEW`, `PROCESS_VIEW`, `DEVELOPMENT_VIEW`, `PHYSICAL_VIEW`, `ARCH_VALIDATOR_FILE`, and `ARCH_VALIDATOR_PS_FILE`.

Synthesis readiness is validator-owned. Run `ARCH_VALIDATOR_FILE --json` (or `ARCH_VALIDATOR_PS_FILE -Json` in PowerShell-only environments) after rendering candidate view updates. Refresh `ARCH_FILE` only when the validator returns `ready_gate: PASS` with no blockers. If the validator returns `ready_gate: BLOCKED`, leave `ARCH_FILE` unchanged and report the blocker codes, affected artifacts, and affected sections.

## Outline

1. Run `{SCRIPT}` from repo root and parse JSON for `ARCH_FILE`, `ARCH_SCHEMA_FILE`, `ARCH_VALIDATOR_FILE`, `ARCH_VALIDATOR_PS_FILE`, `REPO_FACTS_FILE`, and all five view paths.
2. Load `REPO_FACTS_FILE`, `SCENARIO_VIEW`, `ARCH_SCHEMA_FILE`, `architecture-repo-facts-template.md`, `architecture-scenario-template.md`, and `architecture-template.md`.
3. Refresh repo facts for this command's evidence focus and classify unsupported observations as evidence gaps.
4. Populate a schema-compliant scenario working model from high- or medium-confidence facts.
5. Put low-confidence or missing business meaning in evidence gaps and scenario gaps.
6. Apply the repo facts merge rule before writing `REPO_FACTS_FILE`.
7. Run the readiness validator. If it returns `ready_gate: PASS`, refresh `ARCH_FILE`; otherwise leave synthesis untouched and report validator blocker codes.
8. Report updated paths and explicit unresolved gaps.

## Quality Gates

- BLOCKER `ARCH_SOURCE_MISSING` if a conclusion or dependency matrix entry lacks a repo fact source or stated external constraint source.
- BLOCKER `ARCH_SOURCE_MISSING` if the repo facts file contains generic claims without file paths, directories, configuration, tests, commands, or commit signals.
- BLOCKER `ARCH_REPO_FIRST_MATRIX_MISUSED` if repository-first dependency matrices are copied into architecture views, treated as an independent architecture view, or used as direct non-development evidence.
- BLOCKER `ARCH_UNSUPPORTED_CONCLUSION` if unsupported target-view conclusions appear in conclusion tables; place them only in `Evidence Gaps` or `Scenario Gaps`.
- BLOCKER `ARCH_GIT_HISTORY_ONLY` if Git history is used alone as a scenario conclusion.
- BLOCKER `ARCH_SOURCE_MISSING` if actors, goals, or business meaning cannot be supported by repository evidence; record the unsupported item in evidence gaps and target-view gaps.
