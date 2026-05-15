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

Generate or update the project-level 4+1 architecture artifacts:

- Main synthesis: `.specify/memory/architecture.md`
- Scenario view: `.specify/memory/architecture-scenario-view.md`
- Logical view: `.specify/memory/architecture-logical-view.md`
- Process view: `.specify/memory/architecture-process-view.md`
- Development view: `.specify/memory/architecture-development-view.md`
- Physical view: `.specify/memory/architecture-physical-view.md`

The scenario view is the entry point. It produces the UC semantics for this architecture pass: actors, goals, use cases, scenario paths, branches, and acceptance meaning. The other four views are derived from the scenario view.

## Operating Boundaries

- Write only the six architecture artifacts listed above.
- Do not require `.specify/memory/uc.md`. If it exists, read it only as supporting reference, not as a hard prerequisite or sole source of truth.
- Do not modify `.specify/memory/uc.md`, `.specify/memory/constitution.md`, feature specs, plans, tasks, source code, tests, or root `docs/`.
- Stay at abstract architecture-design level.
- Do not write concrete classes, files, functions, endpoints, DTO fields, database tables, framework selections, library choices, UI component details, deployment manifests, task breakdowns, test strategy, validation anchors, code notes, deployment scripts, or runbooks.
- If evidence is insufficient, record a specific gap in the affected view instead of inventing business facts, components, interfaces, modules, deployment units, or numeric metrics.

## Outline

1. **Setup**: Run `{SCRIPT}` from repo root and parse JSON for `ARCH_FILE`, `ARCH_DIR`, `SCENARIO_VIEW`, `LOGICAL_VIEW`, `PROCESS_VIEW`, `DEVELOPMENT_VIEW`, and `PHYSICAL_VIEW`.

2. **Load context**:
   - Read all six architecture artifacts created by setup.
   - Read `.specify/memory/uc.md` if present as optional scenario background.
   - Read the five view templates under `.specify/templates/`.

3. **Execute architecture workflow**:
   - Phase 0: Fill `SCENARIO_VIEW`.
   - Phase 1: Fill `LOGICAL_VIEW` from `SCENARIO_VIEW`.
   - Phase 2: Fill `PROCESS_VIEW` from `SCENARIO_VIEW` and `LOGICAL_VIEW`.
   - Phase 3: Fill `DEVELOPMENT_VIEW` from `LOGICAL_VIEW` and `PROCESS_VIEW`.
   - Phase 4: Fill `PHYSICAL_VIEW` from `PROCESS_VIEW` and `DEVELOPMENT_VIEW`.
   - Phase 5: Update `ARCH_FILE` as a synthesis and index over the five views.

4. **Stop and report**: Report the six updated paths and any explicit unresolved architecture gaps.

## Phases

### Phase 0: Scenario View

**Output**: `.specify/memory/architecture-scenario-view.md`

Create or update the UC-producing scenario view:

- Actors and external participants
- Use cases and goals
- Preconditions and scope boundaries
- Main scenario paths
- Alternative and failure branches
- Acceptance semantics
- Open scenario questions

This phase is authoritative for scenario semantics inside the architecture workflow. Do not defer UC creation to a separate command.

### Phase 1: Logical View

**Input**: `.specify/memory/architecture-scenario-view.md`
**Output**: `.specify/memory/architecture-logical-view.md`

Derive:

- System capability boundaries
- Domain objects and relationships
- Object ownership and fact sources
- State lifecycle and invariants
- Governance or decision boundaries that are architectural, not organizational process notes

Do not write class models, DTOs, database tables, field lists, method names, endpoint names, or implementation data structures.

### Phase 2: Process View

**Input**: `.specify/memory/architecture-scenario-view.md`, `.specify/memory/architecture-logical-view.md`
**Output**: `.specify/memory/architecture-process-view.md`

Derive:

- Main runtime links
- Handoffs and approvals
- Receipts and user participation points
- State advancement across scenario paths
- Failure, degradation, compensation, and closure

Do not write call stacks, queue names, retry counts, thread/process details, endpoint sequences, or implementation orchestration code.

### Phase 3: Development View

**Input**: `.specify/memory/architecture-logical-view.md`, `.specify/memory/architecture-process-view.md`
**Output**: `.specify/memory/architecture-development-view.md`

Derive:

- Architecture-level components or capability packages
- Package boundary intent
- Contract and artifact semantics
- Dependency direction and forbidden crossings
- Component responsibility, collaborators, and input/output boundary

Do not write source file paths, classes, functions, module-by-module implementation tasks, or framework-specific wiring.

### Phase 4: Physical View

**Input**: `.specify/memory/architecture-process-view.md`, `.specify/memory/architecture-development-view.md`
**Output**: `.specify/memory/architecture-physical-view.md`

Derive:

- Deployment and hosting boundaries
- External system collaboration
- Fact-source placement
- Observability and operational boundaries
- Release or runtime ownership constraints

Do not write Kubernetes YAML, cloud resource manifests, machine sizes, concrete service SKUs, deployment scripts, or runbooks.

### Phase 5: Architecture Synthesis

**Input**: all five view files
**Output**: `architecture.md`

Update the main synthesis file:

- View index with links to all five view files
- Architecture axis and central design forces
- Cross-view mapping table
- Key boundaries and constraints
- Open risks and architecture review triggers

Do not copy every detail from the view files. Summarize the architecture conclusions that connect multiple views.

## Quality Bar

- Scenario view must contain enough UC semantics for the other four views to derive from it.
- Every non-placeholder conclusion must be traceable to a scenario, object, runtime link, component boundary, deployment boundary, or stated constraint.
- Use stable names consistently across all five views and the synthesis file.
- Keep uncertainty specific: record what is unknown, which view it affects, and which architecture conclusion cannot yet be made.
- Remove generic statements such as "scalable", "secure", "observable", or "modular" unless they name owner, affected view, scope, and architecture consequence.
