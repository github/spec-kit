---
description: Create detailed specifications for selected tasks from the tasks.md file.
scripts:
  sh: scripts/bash/check-task-prerequisites.sh --json
  ps: scripts/powershell/check-task-prerequisites.ps1 -Json
---

Create detailed specifications for selected tasks from the tasks.md file.

This command follows the `/tasks` command in the Spec-Driven Development lifecycle to provide granular task details.

Given the task selection provided as an argument, do this:

1. Run `{SCRIPT}` from repo root and parse FEATURE_DIR and AVAILABLE_DOCS list. All paths must be absolute.

2. Load and validate the tasks.md file:
   - Read tasks.md from the feature directory
   - Parse all task entries (T001, T002, etc.)
   - Validate task numbering and structure
   - Extract milestone organization

3. Parse task selection from arguments:
   - **Single task**: "T005" → detail only T005
   - **Task range**: "T004-T007" → detail T004, T005, T006, T007
   - **Milestone**: "Milestone 1" → detail all tasks in Milestone 1
   - **Multiple selections**: "T001,T005-T007,Milestone 2" → combine selections
   - **All tasks**: "all" → detail every task in tasks.md

4. Load supporting design documents for context:
   - Always read plan.md for tech stack and architecture decisions
   - IF EXISTS: Read data-design.md for entity and state machine details
   - IF EXISTS: Read architecture.md for service structure and patterns
   - IF EXISTS: Read contracts/ for API specifications
   - IF EXISTS: Read research.md for technical decisions and rationale
   - IF EXISTS: Read quickstart.md for user scenarios and acceptance criteria

5. Create tasks directory structure:
   - Create `FEATURE_DIR/tasks/` directory if it doesn't exist
   - For each selected task, create `FEATURE_DIR/tasks/T###-task-name.md`
   - Use task ID and kebab-case description for filename

6. Generate detailed task specifications:
   - Use `/templates/task-detail-template.md` as the base
   - Fill in all sections with specific details for each task:
     * **Title**: Clear, action-oriented task title
     * **Description**: Detailed explanation of what needs to be accomplished
     * **Implementation Details**: Step-by-step technical approach
     * **Acceptance Criteria**: Specific, testable success conditions
     * **Dependencies**: Prerequisites and blocking tasks
     * **Files Affected**: Exact file paths that will be created/modified
     * **Testing Requirements**: How to verify the task is complete
     * **Status Tracking**: Current status and progress indicators

7. Task detail generation rules:
   - **Test tasks**: Include test structure, assertions, mock requirements
   - **Implementation tasks**: Include code structure, patterns, integration points
   - **Integration tasks**: Include connection details, configuration, error handling
   - **Documentation tasks**: Include content outline, format requirements, examples

8. Cross-reference with design documents:
   - Link to relevant sections in plan.md, data-design.md, architecture.md
   - Include specific contract specifications for API tasks
   - Reference entity definitions for model tasks
   - Include user story context for integration tests

9. Validate completeness:
   - All selected tasks have detailed specifications
   - All implementation details are actionable
   - All acceptance criteria are testable
   - All dependencies are clearly identified
   - File paths are consistent with project structure

10. Update tasks.md with detailed task tracking:
    - Mark **Detailed**: Yes for each task that gets detailed specifications
    - Update Task Registry section with latest detailed task count
    - Maintain task numbering consistency
    - Do NOT detail tasks that are simple or well-understood

Context for task detailing: {ARGS}

The detailed task files should provide enough information for any developer to implement the task without additional context or clarification.