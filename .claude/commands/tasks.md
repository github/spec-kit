---
description: Generate actionable task breakdown organized by milestones from implementation plan and design documents.
scripts:
  sh: scripts/bash/check-task-prerequisites.sh --json
  ps: scripts/powershell/check-task-prerequisites.ps1 -Json
---

Given the context provided as an argument, do this:

1. Run `{SCRIPT}` from repo root and parse FEATURE_DIR and AVAILABLE_DOCS list. All paths must be absolute.
2. Load and analyze available design documents:
   - Always read plan.md for tech stack and libraries
   - IF EXISTS: Read data-design.md for entities and state machines
   - IF EXISTS: Read architecture.md for services and structure
   - IF EXISTS: Read contracts/ for API endpoints
   - IF EXISTS: Read research.md for technical decisions
   - IF EXISTS: Read quickstart.md for test scenarios

   Note: Not all projects have all documents. For example:
   - CLI tools might not have contracts/
   - Simple libraries might not need data-design.md
   - Generate tasks based on what's available

3. Identify milestones based on feature scope:
   - **Small features** (1-5 endpoints): Single milestone with all functionality
   - **Medium features** (6-15 endpoints): Split by logical feature groups
   - **Large features** (16+ endpoints): Split by user workflows or service boundaries
   - Each milestone should deliver a working, testable increment

4. Generate milestone-based tasks following the template:
   - Use `/templates/tasks-template.md` as the base
   - Organize tasks by milestone phases:
     * **Milestone 1 Tests**: Contract tests and integration tests for first milestone
     * **Milestone 1 Implementation**: Core implementation for first milestone
     * **Milestone 2 Tests**: Tests for second milestone (if needed)
     * **Milestone 2 Implementation**: Implementation for second milestone
     * Continue pattern for additional milestones
     * **Final Polish**: Cross-milestone cleanup, performance, documentation

5. Task generation rules:
   - Group related contracts/entities into logical milestones
   - Each milestone: Tests first, then implementation
   - Each contract file → contract test task marked [P]
   - Each entity in data-design → model creation task marked [P]
   - Each endpoint → implementation task (not parallel if shared files)
   - Each user story → integration test marked [P]
   - Different files = can be parallel [P]
   - Same file = sequential (no [P])

6. Milestone ordering principles:
   - Foundation services and models in Milestone 1
   - Core user workflows in early milestones
   - Advanced features in later milestones
   - Administrative/management features last
   - Each milestone builds on previous ones

7. Include parallel execution examples:
   - Group [P] tasks that can run together within each milestone
   - Show actual Task agent commands for each milestone phase

8. Create FEATURE_DIR/tasks.md with:
   - Correct feature name from implementation plan
   - Task Registry section with last task ID and status summary
   - Milestone-organized structure with clear boundaries
   - Numbered tasks (T001, T002, etc.) across all milestones with status tracking
   - Clear file paths for each task
   - Dependency notes within and between milestones
   - Parallel execution guidance per milestone
   - Task status management guidelines

9. Ensure proper task numbering:
   - Start with T001 and increment sequentially
   - No gaps in task numbering sequence
   - Update Task Registry with last task ID used
   - Provide foundation for future task additions

10. Define milestone branch assignments:
   - Assign each task to its appropriate predefined branch
   - Document branch strategy and predefined names in tasks.md
   - Include branch assignment in each task's metadata
   - Ensure branch names follow convention: [###-feature-name]/milestone-N
   - Note: Branches are created on-demand, not automatically

Context for task generation: {ARGS}

The tasks.md should be immediately executable - each task must be specific enough that an LLM can complete it without additional context.
