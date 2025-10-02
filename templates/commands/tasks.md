---
description: Generate an actionable, dependency-ordered tasks.md for the feature based on available design artifacts.
scripts:
  sh: scripts/bash/check-prerequisites.sh --json
  ps: scripts/powershell/check-prerequisites.ps1 -Json
---

The user input to you can be provided directly by the agent or as a command argument - you **MUST** consider it before proceeding with the prompt (if not empty).

User input:

$ARGUMENTS

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
   - Replace example tasks with actual tasks based on:
     * **Setup tasks**: Project init, dependencies, linting
     * **Test tasks [P]**: One per contract, one per integration scenario
     * **Core tasks**: One per entity, service, CLI command, endpoint
     * **Integration tasks**: DB connections, middleware, logging
     * **Polish tasks [P]**: Unit tests, performance, docs

4. Task generation rules:
   - Each contract file → contract test task marked [P]
   - Each entity in data-model → model creation task marked [P]
   - Each endpoint → implementation task (not parallel if shared files)
   - Each user story → integration test marked [P]
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

7. Create FEATURE_DIR/tasks.md with:
   - Correct feature name from implementation plan
   - Numbered tasks (T001, T002, etc.)
   - Clear file paths for each task
   - Dependency notes
   - Parallel execution guidance

8. Update the Pull Request description:
   - Append the tasks.md content to the existing PR description
   - Format tasks with checkboxes for each task phase:
     * Setup: `- [ ] T001: Task description`
     * Tests: `- [ ] T002: Task description [P]`
     * Core: `- [ ] T003: Task description`
     * Integration: `- [ ] T004: Task description`
     * Polish: `- [ ] T005: Task description [P]`
   - Keep the existing PR content (summary, plan.md content, issue link)
   - Add a section header before tasks: `## Implementation Tasks`

   **GitHub Integration**: If GitHub tools or integrations are available (such as GitHub MCP Server), use them to update the PR description automatically. If not available, provide this fallback command:
   ```bash
   # Get current PR description and append tasks
   gh pr view <PR-number> --json body --jq .body > temp_body.md
   cat tasks.md >> temp_body.md
   gh pr edit <PR-number> --body-file temp_body.md
   rm temp_body.md
   ```

9. Report completion with task count, file path, and PR update status.

Context for task generation: {ARGS}

The tasks.md should be immediately executable - each task must be specific enough that an LLM can complete it without additional context.
