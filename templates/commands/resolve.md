---
description: Execute the issue resolution plan by processing and executing all tasks defined in the issue's tasks.md
scripts:
  sh: scripts/bash/check-issue-prerequisites.sh --json --require-tasks --include-tasks
  ps: scripts/powershell/check-issue-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
---

The user input to you can be provided directly by the agent or as a command argument - you **MUST** consider it before proceeding with the prompt (if not empty).

User input:

$ARGUMENTS

1. Run `{SCRIPT}` from repo root and parse ISSUE_DIR and AVAILABLE_DOCS list. All paths must be absolute.

2. Load and analyze the issue resolution context:
   - **REQUIRED**: Read issue.md for the complete issue description and requirements
   - **REQUIRED**: Read tasks.md for the complete task list and execution plan
   - **REQUIRED**: Read plan.md for tech stack, architecture, and file structure
   - **IF EXISTS**: Read data-model.md for entities and relationships
   - **IF EXISTS**: Read contracts/ for API specifications and test requirements
   - **IF EXISTS**: Read research.md for technical decisions and constraints
   - **IF EXISTS**: Read quickstart.md for integration scenarios

3. Parse tasks.md structure and extract:
   - **Task phases**: Setup, Tests, Core, Integration, Polish
   - **Task dependencies**: Sequential vs parallel execution rules
   - **Task details**: ID, description, file paths, parallel markers [P]
   - **Execution flow**: Order and dependency requirements

4. Execute issue resolution following the task plan:
   - **Phase-by-phase execution**: Complete each phase before moving to the next
   - **Respect dependencies**: Run sequential tasks in order, parallel tasks [P] can run together  
   - **Follow TDD approach**: Execute test tasks before their corresponding implementation tasks
   - **File-based coordination**: Tasks affecting the same files must run sequentially
   - **Validation checkpoints**: Verify each phase completion before proceeding

5. Issue resolution execution rules:
   - **Setup first**: Initialize project structure, dependencies, configuration
   - **Tests before code**: If you need to write tests for contracts, entities, and integration scenarios
   - **Core development**: Implement models, services, CLI commands, endpoints
   - **Integration work**: Database connections, middleware, logging, external services
   - **Polish and validation**: Unit tests, performance optimization, documentation

6. Progress tracking and error handling:
   - Report progress after each completed task
   - Halt execution if any non-parallel task fails
   - For parallel tasks [P], continue with successful tasks, report failed ones
   - Provide clear error messages with context for debugging
   - Suggest next steps if resolution cannot proceed
   - **IMPORTANT** For completed tasks, make sure to mark the task off as [x] in the tasks file.

7. Completion validation:
   - Verify all required tasks are completed
   - Check that resolved issues match the original issue specification
   - Validate that tests pass and coverage meets requirements
   - Confirm the resolution follows the technical plan
   - Report final status with summary of completed work

Note: This command assumes a complete task breakdown exists in tasks.md for the issue. If tasks are incomplete or missing, suggest running `/plan` first to regenerate the task list for the issue.
