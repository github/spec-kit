---
description: Execute the implementation plan by processing and executing all tasks defined in tasks.md
---

# Implement

The user input can be provided directly by the agent or as a command argument - you **MUST** consider it before proceeding with the prompt (if not empty).

User input:

$ARGUMENTS

1. Run `.specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks` from repo root and parse FEATURE_DIR and AVAILABLE_DOCS list. All paths must be absolute.

2. Load and analyze the implementation context:
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

4. Execute implementation following the task plan:
   - **Phase-by-phase execution**: Complete each phase before moving to the next
   - **Respect dependencies**: Run sequential tasks in order, parallel tasks [P] can run together
   - **Follow TDD approach**: Execute test tasks before their corresponding implementation tasks
   - **File-based coordination**: Tasks affecting the same files must run sequentially
   - **Validation checkpoints**: Verify each phase completion before proceeding

5. Implementation execution rules:
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
   - Suggest next steps if implementation cannot proceed
   - **IMPORTANT** For completed tasks, make sure to mark the task off as [X] in the tasks file.

7. Completion validation:
   - Verify all required tasks are completed
   - Check that implemented features match the original specification
   - Validate that tests pass and coverage meets requirements
   - Confirm the implementation follows the technical plan
   - Report final status with summary of completed work

8. Create or update Pull Request:
   - **Target branch**: The PR must be against the default branch
   - **PR status**: The PR must not be draft, it should be ready for review
   - **Determine PR type and icon** based on the changes:

     | Type of change | Icon | Label |
     |-|-|-|
     | Docs | 📖 | Docs |
     | Fix | 🪲 | Fix, Patch |
     | Security fix | ⚠️ | Fix |
     | Patch | 🩹 | Patch |
     | Feature | 🚀 | Minor |
     | Breaking change | 🌟 | Major |

   - **PR title format**: `<Icon> [Type of change]: <Short description>`
   - **PR description structure**:
     * Start with a summary paragraph describing the key outcome and changes for user
     * DO NOT add a title before the leading paragraph
     * At the end of the PR paragraph, add a "- Fixes #<issue-number>" line to link the PR to the issue
     * Follow with additional details answering Why, How, and What
     * Avoid superfluous headers or sections
     * We do not need details, we need to add what changes for the user of the code
   - **Apply appropriate label(s)** based on the type of change
   - **Link the PR** to the associated issue

9. Update issue labels:
   - Remove 'plan' label from the linked issue
   - Add 'implement' label to the linked issue

10. Update the constitution:
    - Read the [Constitution](../../.specify/memory/constitution.md) file.
    - Read the [constitution prompt](./constitution.prompt.md) for guidance on how to update the constitution.
    - Update the constitution file with details on what has been implemented in this PR
    - Document the functionality that was added or changed, remove the sections that are no longer relevant
    - Ensure the constitution reflects the current state of the codebase

Note: This command assumes a complete task breakdown exists in tasks.md. If tasks are incomplete or missing, suggest running `/tasks` first to regenerate the task list.
