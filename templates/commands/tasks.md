---
description: Generate an actionable, dependency-ordered tasks.md for the feature based on available design artifacts.
scripts:
  sh: scripts/bash/check-task-prerequisites.sh --json
  ps: scripts/powershell/check-task-prerequisites.ps1 -Json
---

Given the context provided as an argument, do this:

1. Run `{SCRIPT}` from repo root and parse FEATURE_DIR and AVAILABLE_DOCS list. All paths must be absolute.
2. Load and analyze available design documents:
   - Always read plan.md for tech stack and libraries
   - IF EXISTS: Read data-model.md for entities
   - IF EXISTS: Read contracts/ for API endpoints
   - IF EXISTS: Read research.md for technical decisions
   - IF EXISTS: Read quickstart.md for test scenarios

   Note: Not all projects have all documents. For example:
   - CLI tools might not have contracts/
   - Simple libraries might not need data-model.md
   - Generate tasks based on what's available

3. Generate tasks following the template:
   - Use `/templates/tasks-template.md` as the base
   - **CRITICAL**: Ensure exactly 10-12 implementation tasks (excluding branch management)
   - **If >12 tasks needed**: Split into multiple files (tasks1.md, tasks2.md, etc.)
   - Replace example tasks with actual tasks based on:
     * **Setup tasks**: Project init, dependencies, linting (2-3h each)
     * **Test tasks [P]**: One per contract, one per integration scenario (2-4h each)
     * **Core tasks**: One per entity, service, CLI command, endpoint (3-6h each)
     * **Integration tasks**: DB connections, middleware, logging (4-6h each)
     * **Polish tasks [P]**: Unit tests, performance, docs (2-4h each)

4. Task generation rules:
   - **Task count validation**: Count all implementation tasks (exclude T000-T005)
   - **If count >12**: Split into logical groups (e.g., Core/Extensions, Frontend/Backend)
   - **If count <10**: Add more granular breakdown or additional polish tasks
   - Each contract file → contract test task marked [P] (2-3h)
   - Each entity in data-model → model creation task marked [P] (2-3h)
   - Each endpoint → implementation task (3-5h, not parallel if shared files)
   - Each user story → integration test marked [P] (3-4h)
   - Different files = can be parallel [P]
   - Same file = sequential (no [P])

5. Order tasks by dependencies:
   - Setup before everything
   - Tests before implementation (TDD)
   - Models before services
   - Services before endpoints
   - Core before integration
   - Everything before polish

6. Include parallel execution examples:
   - Group [P] tasks that can run together
   - Show actual Task agent commands

7. Create FEATURE_DIR/tasks.md (or tasks1.md, tasks2.md if split) with:
   - Correct feature name from implementation plan
   - Numbered tasks (T001, T002, etc.)
   - Clear file paths for each task
   - Time estimates (2-6h per task)
   - Dependency notes
   - Parallel execution guidance
   - **If split**: Clear dependencies between task files and logical grouping rationale

Context for task generation: {ARGS}

The tasks.md should be immediately executable - each task must be specific enough that an LLM can complete it without additional context.

**Task Splitting Guidelines**:
- If >12 tasks required, create tasks1.md (foundation), tasks2.md (extensions), etc.
- Each task file should have 10-12 tasks maximum
- Maintain clear dependencies: tasks1.md must complete before tasks2.md
- Split by logical boundaries (Core/UI, Backend/Frontend, Phase1/Phase2)
- Each task should estimate 2-6 hours of development work
