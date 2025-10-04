---
description: Generate an actionable, dependency-ordered tasks.md for the feature based on available design artifacts.
scripts:
  sh: scripts/bash/check-prerequisites.sh --json
  ps: scripts/powershell/check-prerequisites.ps1 -Json
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

1. **Setup**: Run `{SCRIPT}` from repo root and parse FEATURE_DIR and AVAILABLE_DOCS list. All paths must be absolute.

2. **Load design documents**: Read from FEATURE_DIR:
   - **Required**: plan.md (tech stack, libraries, structure)
   - **Optional**: data-model.md (entities), contracts/ (API endpoints), research.md (decisions), quickstart.md (test scenarios)
   - Note: Not all projects have all documents. Generate tasks based on what's available.

3. **Execute task generation workflow** (follow the template structure):
   - Load plan.md and extract tech stack, libraries, project structure
   - If data-model.md exists: Extract entities → generate model tasks
   - If contracts/ exists: Each file → generate endpoint/API tasks
   - If research.md exists: Extract decisions → generate setup tasks
   - Generate tasks by category: Setup, Core Implementation, Integration, Polish
   - **Tests are OPTIONAL**: Only generate test tasks if explicitly requested in the feature spec or user asks for TDD approach
   - Apply task rules:
     * Different files = mark [P] for parallel
     * Same file = sequential (no [P])
     * If tests requested: Tests before implementation (TDD order)
   - Number tasks sequentially (T001, T002...)
   - Generate dependency graph
   - Create parallel execution examples
   - Validate task completeness (all entities have implementations, all endpoints covered)

4. **Generate tasks.md**: Use `.specify/templates/tasks-template.md` as structure, fill with:
   - Correct feature name from plan.md
   - Numbered tasks (T001, T002...) in dependency order
   - Clear file paths for each task
   - [P] markers for parallelizable tasks
   - Phase groupings based on what's needed (Setup, Core Implementation, Integration, Polish)
   - If tests requested: Include separate "Tests First (TDD)" phase before Core Implementation
   - Dependency notes

5. **Report**: Output path to generated tasks.md and summary of task counts by phase.
   - Parallel execution guidance

Context for task generation: {ARGS}

The tasks.md should be immediately executable - each task must be specific enough that an LLM can complete it without additional context.

## Task Generation Rules

**IMPORTANT**: Tests are optional. Only generate test tasks if the user explicitly requested testing or TDD approach in the feature specification.

1. **From Contracts**:
   - Each contract/endpoint → implementation task
   - If tests requested: Each contract → contract test task [P] before implementation
   
2. **From Data Model**:
   - Each entity → model creation task [P]
   - Relationships → service layer tasks
   
3. **From User Stories**:
   - Each story → implementation tasks
   - If tests requested: Each story → integration test [P]
   - If quickstart.md exists: Validation tasks

4. **Ordering**:
   - Without tests: Setup → Models → Services → Endpoints → Integration → Polish
   - With tests (TDD): Setup → Tests → Models → Services → Endpoints → Integration → Polish
   - Dependencies block parallel execution