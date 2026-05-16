---
description: Execute the 4+1 architecture workflow and generate architecture view artifacts.
scripts:
  sh: scripts/bash/setup-arch.sh --json
  ps: scripts/powershell/setup-arch.ps1 -Json
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Goal

Generate or update the project-level architecture SSOT as 4+1 architecture artifacts:

- Main synthesis: `.specify/memory/architecture.md`
- Scenario view: `.specify/memory/architecture-scenario-view.md`
- Logical view: `.specify/memory/architecture-logical-view.md`
- Process view: `.specify/memory/architecture-process-view.md`
- Development view: `.specify/memory/architecture-development-view.md`
- Physical view: `.specify/memory/architecture-physical-view.md`

The scenario view is the entry point. It produces the UC semantics for this architecture pass: actors, goals, use cases, scenario paths, branches, and acceptance meaning. The other four views are derived from the scenario view.

The six artifacts are the authoritative architecture design source for later iterations. They serve two purposes: produce high-quality 4+1 architecture reasoning in this command, and constrain later `plan` reasoning to stay inside the architecture SSOT.

## Operating Boundaries

- Write only the six architecture artifacts listed above.
- Do not require `.specify/memory/uc.md`. If it exists, read it only as supporting reference, not as a hard prerequisite or sole source of truth.
- Do not modify `.specify/memory/uc.md`, `.specify/memory/constitution.md`, feature specs, plans, tasks, source code, tests, or root `docs/`.
- Stay at abstract architecture-design level.
- Do not write concrete classes, files, functions, endpoints, DTO fields, database tables, framework selections, library choices, UI component details, deployment manifests, task breakdowns, test strategy, validation anchors, code notes, deployment scripts, or runbooks.
- If evidence is insufficient, record a specific gap in the affected view instead of inventing business facts, components, interfaces, modules, deployment units, or numeric metrics.

## Architecture Layers

### Architecture Reasoning Layer

Reason only in the 4+1 views. Use each view template as the source of truth for that view's reasoning contract and artifact structure. Produce architecture design inference, not tracking, audit, or implementation planning. Maintain a cross-view architecture model that normalizes architecture meaning for synthesis and later `plan` reasoning while preserving each view's distinct concept type. Every conclusion must still be grounded in a scenario, object, state, collaboration, boundary, deployment constraint, or stated external constraint. Do not translate, rename, or equate concepts across views through notation-specific terms.

### Representation Layer

Markdown tables are the default artifact structure. Optional diagrams are renderings, not reasoning inputs.

- Add optional diagrams only after the relevant view's reasoning is complete.
- Render only facts already present in that view.
- Do not introduce concepts, boundaries, relationships, deployment units, or cross-view concept alignments.
- C4, UML, Mermaid, and PlantUML are notation choices only; they must not change 4+1 view responsibilities.

## Outline

1. **Setup**: Run `{SCRIPT}` from repo root and parse JSON for `ARCH_FILE`, `ARCH_DIR`, `SCENARIO_VIEW`, `LOGICAL_VIEW`, `PROCESS_VIEW`, `DEVELOPMENT_VIEW`, and `PHYSICAL_VIEW`.

2. **Load context**:
   - Read all six architecture artifacts created by setup.
   - Read `.specify/memory/uc.md` if present as optional scenario background.
   - Read the six architecture templates under `.specify/templates/`.

3. **Execute architecture workflow**:
   - Phase -1: Establish architecture framing before writing any view.
   - Phase 0: Fill `SCENARIO_VIEW` using its template.
   - Phase 1: Fill `LOGICAL_VIEW` using its template and `SCENARIO_VIEW`.
   - Phase 2: Fill `PROCESS_VIEW` using its template, `SCENARIO_VIEW`, and `LOGICAL_VIEW`.
   - Phase 3: Fill `DEVELOPMENT_VIEW` using its template, `LOGICAL_VIEW`, and `PROCESS_VIEW`.
   - Phase 4: Fill `PHYSICAL_VIEW` using its template, `PROCESS_VIEW`, and `DEVELOPMENT_VIEW`.
   - Phase 5: Update `ARCH_FILE` using its synthesis template and the five completed views.

4. **Stop and report**: Report the six updated paths and any explicit unresolved architecture gaps.

## Phases

### Phase -1: Architecture Framing

**Output**: Working framing used to constrain all five views and the synthesis. Do not create an additional file.

Before filling any view, identify the architecture judgment this pass must preserve:

- View dimensions: scenario, logical, process, development, and physical
- Architecture intent: what this architecture pass is trying to make stable or explicit
- Core tensions: the main design forces in conflict, and the current tradeoff direction
- Stable boundaries: responsibilities or authority lines that should remain stable across iterations
- Change axes: business, workflow, operational, or integration areas expected to vary and therefore needing isolation
- Responsibility collision risks: responsibilities that agents or teams are likely to merge incorrectly
- Invariants: architecture rules later iterations must not violate
- Non-goals / anti-patterns: concerns this architecture pass does not solve, plus designs that would drift from the intent
- Implementation details to exclude: concrete classes, files, APIs, data schemas, frameworks, infrastructure manifests, or task plans that must stay out of the architecture layer

Use this framing as the decision filter for every later phase. If a view cannot support a framing claim with scenario, boundary, lifecycle, collaboration, component, deployment, or stated-constraint evidence, record a specific gap instead of inventing facts.
Defer any optional diagram or notation-specific rendering until the affected view's 4+1 reasoning is complete.

### Phase 0: Scenario View

**Output**: `.specify/memory/architecture-scenario-view.md`

Create or update the UC-producing scenario view by following the scenario view template. This phase is authoritative for scenario semantics inside the architecture workflow. Do not defer UC creation to a separate command.

### Phase 1: Logical View

**Input**: `.specify/memory/architecture-scenario-view.md`
**Output**: `.specify/memory/architecture-logical-view.md`

Derive the logical view from the scenario view by following the logical view template.

### Phase 2: Process View

**Input**: `.specify/memory/architecture-scenario-view.md`, `.specify/memory/architecture-logical-view.md`
**Output**: `.specify/memory/architecture-process-view.md`

Derive the process view from the scenario and logical views by following the process view template.

### Phase 3: Development View

**Input**: `.specify/memory/architecture-logical-view.md`, `.specify/memory/architecture-process-view.md`
**Output**: `.specify/memory/architecture-development-view.md`

Derive the development view from the logical and process views by following the development view template.

### Phase 4: Physical View

**Input**: `.specify/memory/architecture-process-view.md`, `.specify/memory/architecture-development-view.md`
**Output**: `.specify/memory/architecture-physical-view.md`

Derive the physical view from the process and development views by following the physical view template.

### Phase 5: Architecture Synthesis

**Input**: all five view files
**Output**: `architecture.md`

Update the main synthesis file by following the synthesis template. Do not copy every detail from the view files. Summarize the architecture conclusions that connect multiple views.

## Architecture Gates

- ERROR if any view contains implementation details prohibited by the Operating Boundaries.
- ERROR if a boundary has responsibilities but no explicit non-responsibility or forbidden crossing.
- ERROR if a major architecture decision lacks consequence, tradeoff, or affected view.
- ERROR if an invariant is not tied to a scenario, state, boundary, collaboration, deployment constraint, or stated external constraint.
- ERROR if default tables or optional diagrams introduce concepts, relationships, or deployment units not justified by the framing or source views.
- ERROR if notation-specific output changes 4+1 view responsibilities or introduces architecture conclusions.
- ERROR if the cross-view architecture model erases the distinct meaning of a view-specific concept.
- ERROR if the workflow maps Use Case, Domain Object, Component, Container, or Deployment Unit as equivalent concepts across views.
- Record a specific gap instead of inventing business facts, authority boundaries, lifecycle rules, components, interfaces, deployment units, or numeric metrics.

## Quality Bar

- Scenario view must contain enough UC semantics for the other four views to derive from it.
- Every non-placeholder conclusion must be grounded in a scenario, object, runtime link, component boundary, deployment boundary, or stated constraint.
- Use stable names consistently across all five views and the synthesis file.
- Keep uncertainty specific: record what is unknown, which view it affects, and which architecture conclusion cannot yet be made.
- Remove generic statements such as "scalable", "secure", "observable", or "modular" unless they name owner, affected view, scope, and architecture consequence.
