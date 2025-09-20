---
description: Generate an actionable, dependency-ordered tasks.md for the feature based on available design artifacts.
scripts:
  sh: scripts/bash/check-task-prerequisites.sh --json
  ps: scripts/powershell/check-task-prerequisites.ps1 -Json
---

Given the context provided as an argument, do this:

1. Load Spec Kit configuration:
   - Check for `/.specify.yaml` at the host project root; if it exists, load that file
   - Otherwise load `/config-default.yaml`
   - Extract the root `spec-kit` entry and store it as `SPEC_KIT_CONFIG`
   - Output the resulting `SPEC_KIT_CONFIG` for operator visibility

2. Run `{SCRIPT}` from repo root and parse FEATURE_DIR and AVAILABLE_DOCS list. All future file paths must be absolute.

3. If defined, read documents from `SPEC_KIT_CONFIG.tasks.documents`:
   - For each item, resolve `path` to an absolute path from the repo root
   - Read the file and consider its `context` to guide task generation decisions
   - If a file is missing, note it and continue

4. Load and analyze available design documents:
   - Always read plan.md for tech stack and libraries
   - IF EXISTS: Read data-model.md for entities
   - IF EXISTS: Read contracts/ for API endpoints
   - IF EXISTS: Read research.md for technical decisions
   - IF EXISTS: Read quickstart.md for test scenarios

   Note: Not all projects have all documents. For example:
   - CLI tools might not have contracts/
   - Simple libraries might not need data-model.md
   - Generate tasks based on what's available

5. Generate tasks following the template:
   - Use `/templates/tasks-template.md` as the base
   - Replace example tasks with actual tasks based on:
     * **Setup tasks**: Project init, dependencies, linting
     * **Test tasks [P]**: One per contract, one per integration scenario
     * **Core tasks**: One per entity, service, CLI command, endpoint
     * **Integration tasks**: DB connections, middleware, logging
     * **Polish tasks [P]**: Unit tests, performance, docs

6. Task generation rules:
   - Each contract file → contract test task marked [P]
   - Each entity in data-model → model creation task marked [P]
   - Each endpoint → implementation task (not parallel if shared files)
   - Each user story → integration test marked [P]
   - Different files = can be parallel [P]
   - Same file = sequential (no [P])

7. Order tasks by dependencies:
   - Setup before everything
   - Tests before implementation (TDD)
   - Models before services
   - Services before endpoints
   - Core before integration
   - Everything before polish

8. Include parallel execution examples:
   - Group [P] tasks that can run together
   - Show actual Task agent commands

9. Create FEATURE_DIR/tasks.md with:
   - Correct feature name from implementation plan
   - Numbered tasks (T001, T002, etc.)
   - Clear file paths for each task
   - Dependency notes
   - Parallel execution guidance

Context for task generation: {ARGS}

The tasks.md should be immediately executable - each task must be specific enough that an LLM can complete it without additional context.

Use absolute paths with the repository root for all file operations to avoid path issues.
