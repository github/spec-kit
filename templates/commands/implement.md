---
description: Execute the implementation plan by processing and executing all tasks defined in tasks.md
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

1. Run `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks` from repo root and parse FEATURE_DIR and AVAILABLE_DOCS list. All paths must be absolute. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. **Linear Project Setup & Sync**:
   - Use `mcp__linear-server__list_projects` to find the active project (match by feature name or ask user)
   - Use `mcp__linear-server__list_issues` with `project` filter to fetch all issues
   - Store the project ID and map issues to tasks.md task IDs
   - Build a task registry: `{ taskId: { linearId, identifier, title, status, parentId } }`

   **Issue Status Mapping**:
   - `Backlog` → Task not started
   - `Todo` → Task ready to start
   - `In Progress` → Task currently being worked on
   - `In Review` → Task completed, pending validation
   - `Done` → Task fully completed
   - `Canceled` → Task skipped or deprecated

3. **Check checklists status** (if FEATURE_DIR/checklists/ exists):
   - Scan all checklist files in the checklists/ directory
   - For each checklist, count:
     - Total items: All lines matching `- [ ]` or `- [X]` or `- [x]`
     - Completed items: Lines matching `- [X]` or `- [x]`
     - Incomplete items: Lines matching `- [ ]`
   - Create a status table:

     ```text
     | Checklist | Total | Completed | Incomplete | Status |
     |-----------|-------|-----------|------------|--------|
     | ux.md     | 12    | 12        | 0          | ✓ PASS |
     | test.md   | 8     | 5         | 3          | ✗ FAIL |
     | security.md | 6   | 6         | 0          | ✓ PASS |
     ```

   - Calculate overall status:
     - **PASS**: All checklists have 0 incomplete items
     - **FAIL**: One or more checklists have incomplete items

   - **If any checklist is incomplete**:
     - Display the table with incomplete item counts
     - **STOP** and ask: "Some checklists are incomplete. Do you want to proceed with implementation anyway? (yes/no)"
     - Wait for user response before continuing
     - If user says "no" or "wait" or "stop", halt execution
     - If user says "yes" or "proceed" or "continue", proceed to step 4

   - **If all checklists are complete**:
     - Display the table showing all checklists passed
     - Automatically proceed to step 4

4. Load and analyze the implementation context:
   - **REQUIRED**: Read tasks.md for the complete task list and execution plan
   - **REQUIRED**: Read plan.md for tech stack, architecture, and file structure
   - **IF EXISTS**: Read data-model.md for entities and relationships
   - **IF EXISTS**: Read contracts/ for API specifications and test requirements
   - **IF EXISTS**: Read research.md for technical decisions and constraints
   - **IF EXISTS**: Read quickstart.md for integration scenarios

5. **Project Setup Verification**:
   - **REQUIRED**: Create/verify ignore files based on actual project setup:

   **Detection & Creation Logic**:
   - Check if the following command succeeds to determine if the repository is a git repo (create/verify .gitignore if so):

     ```sh
     git rev-parse --git-dir 2>/dev/null
     ```

   - Check if Dockerfile* exists or Docker in plan.md → create/verify .dockerignore
   - Check if .eslintrc* exists → create/verify .eslintignore
   - Check if eslint.config.* exists → ensure the config's `ignores` entries cover required patterns
   - Check if .prettierrc* exists → create/verify .prettierignore
   - Check if .npmrc or package.json exists → create/verify .npmignore (if publishing)
   - Check if terraform files (*.tf) exist → create/verify .terraformignore
   - Check if .helmignore needed (helm charts present) → create/verify .helmignore

   **If ignore file already exists**: Verify it contains essential patterns, append missing critical patterns only
   **If ignore file missing**: Create with full pattern set for detected technology

   **Common Patterns by Technology** (from plan.md tech stack):
   - **Node.js/JavaScript/TypeScript**: `node_modules/`, `dist/`, `build/`, `*.log`, `.env*`
   - **Python**: `__pycache__/`, `*.pyc`, `.venv/`, `venv/`, `dist/`, `*.egg-info/`
   - **Java**: `target/`, `*.class`, `*.jar`, `.gradle/`, `build/`
   - **C#/.NET**: `bin/`, `obj/`, `*.user`, `*.suo`, `packages/`
   - **Go**: `*.exe`, `*.test`, `vendor/`, `*.out`
   - **Ruby**: `.bundle/`, `log/`, `tmp/`, `*.gem`, `vendor/bundle/`
   - **PHP**: `vendor/`, `*.log`, `*.cache`, `*.env`
   - **Rust**: `target/`, `debug/`, `release/`, `*.rs.bk`, `*.rlib`, `*.prof*`, `.idea/`, `*.log`, `.env*`
   - **Kotlin**: `build/`, `out/`, `.gradle/`, `.idea/`, `*.class`, `*.jar`, `*.iml`, `*.log`, `.env*`
   - **C++**: `build/`, `bin/`, `obj/`, `out/`, `*.o`, `*.so`, `*.a`, `*.exe`, `*.dll`, `.idea/`, `*.log`, `.env*`
   - **C**: `build/`, `bin/`, `obj/`, `out/`, `*.o`, `*.a`, `*.so`, `*.exe`, `Makefile`, `config.log`, `.idea/`, `*.log`, `.env*`
   - **Swift**: `.build/`, `DerivedData/`, `*.swiftpm/`, `Packages/`
   - **R**: `.Rproj.user/`, `.Rhistory`, `.RData`, `.Ruserdata`, `*.Rproj`, `packrat/`, `renv/`
   - **Universal**: `.DS_Store`, `Thumbs.db`, `*.tmp`, `*.swp`, `.vscode/`, `.idea/`

   **Tool-Specific Patterns**:
   - **Docker**: `node_modules/`, `.git/`, `Dockerfile*`, `.dockerignore`, `*.log*`, `.env*`, `coverage/`
   - **ESLint**: `node_modules/`, `dist/`, `build/`, `coverage/`, `*.min.js`
   - **Prettier**: `node_modules/`, `dist/`, `build/`, `coverage/`, `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`
   - **Terraform**: `.terraform/`, `*.tfstate*`, `*.tfvars`, `.terraform.lock.hcl`
   - **Kubernetes/k8s**: `*.secret.yaml`, `secrets/`, `.kube/`, `kubeconfig*`, `*.key`, `*.crt`

6. **Sync Linear Issues with tasks.md**:
   - Parse tasks.md structure and extract:
     - **Task phases**: Setup, Tests, Core, Integration, Polish
     - **Task dependencies**: Sequential vs parallel execution rules
     - **Task details**: ID, description, file paths, parallel markers [P]
     - **Execution flow**: Order and dependency requirements

   - **Match tasks to Linear issues**:
     - Match by task ID in title (e.g., "T001:", "T002:")
     - Match by description similarity
     - For unmatched tasks, log warning: "Task {id} not found in Linear"

   - **Determine starting point**:
     - Find first Epic with status != "Done"
     - Within that Epic, find first subtask with status "Backlog" or "Todo"
     - Display current progress: "Resuming from Phase X, Task Y (FAY-NNN)"

7. **Execute implementation with Linear status updates and Git workflow**:

   **Before starting a phase**:
   - Create a new branch from current branch: `git checkout -b phase-{N}-{short-description}`
   - Create a Pull Request immediately using `gh pr create`:
     - Title: "Phase {N}: {Phase Name}"
     - Body: Brief description of what the phase will implement (will be updated at completion)
     - Set as Draft PR initially
   - Store the PR number for later updates

   **Before starting a task**:
   - Use `mcp__linear-server__update_issue` to set status to "In Progress"
   - Add comment with `mcp__linear-server__create_comment`: "Starting implementation..."

   **During implementation**:
   - **Phase-by-phase execution**: Complete each phase before moving to the next
   - **Respect dependencies**: Run sequential tasks in order, parallel tasks [P] can run together
   - **Follow TDD approach**: Execute test tasks before their corresponding implementation tasks
   - **File-based coordination**: Tasks affecting the same files must run sequentially
   - **Validation checkpoints**: Verify each phase completion before proceeding

   **After completing a task (Strict TDD Validation)**:

   1. **Run Tests** (MANDATORY):
      - Execute the project's test suite: detect test runner from package.json/pyproject.toml/etc.
        - Node.js: `npm test` or `npm run test` or `vitest` or `jest`
        - Python: `pytest` or `python -m pytest`
        - Go: `go test ./...`
        - Rust: `cargo test`
        - Other: Use the test command from plan.md or detect from project config
      - Capture test output including:
        - Total tests run
        - Tests passed
        - Tests failed
        - Test coverage percentage (if available)
      - **If tests fail**: Do NOT proceed. Keep task status as "In Progress" and fix failures first.

   2. **Update Linear Issue with Test Results**:
      - Use `mcp__linear-server__update_issue` to update the issue description:
        - Append an `## Acceptance Criteria Results` section to the description
        - Format:
          ```markdown
          ## Acceptance Criteria Results

          **Test Run**: {timestamp}
          **Status**: {PASS/FAIL}

          | Metric | Value |
          |--------|-------|
          | Tests Run | {X} |
          | Passed | {Y} |
          | Failed | {Z} |
          | Coverage | {N%} |

          ### Criteria Validation
          - [x] {Criterion 1 from original acceptance criteria}
          - [x] {Criterion 2 from original acceptance criteria}
          - [ ] {Criterion 3 - if failed, explain why}

          ### Test Output
          ```
          {relevant test output snippet}
          ```
          ```

   3. **Only if ALL tests pass**:
      - Use `mcp__linear-server__update_issue` to set status to "Done"
      - Add comment with implementation summary: files created/modified, key decisions, test results
      - Update tasks.md: mark task as [X]

   4. **Create a commit** for the completed task:
      - Stage relevant files: `git add <files>`
      - Commit with message: `feat({scope}): {task-id} - {brief description}`
      - Example: `feat(auth): T021 - implement GitHub OAuth strategy`
      - Push the commit: `git push`

   **On task failure (implementation or tests)**:
   - Keep status as "In Progress"
   - Add comment with error details and stack trace
   - Log blocker information for debugging
   - **If tests failed**:
     - Update Linear issue description with failed test results
     - Add comment: "Tests failing. Fixing before proceeding..."
     - Identify failing tests and fix the implementation
     - Re-run tests until all pass
     - Only then proceed to mark as "Done"

   **After completing all tasks in a phase**:
   - **Run full test suite** for the phase:
     - Execute all tests (not just for individual tasks)
     - Ensure no regressions from earlier tasks
     - Capture coverage report
   - Update the PR description with a comprehensive summary:
     - List all tasks completed with their Linear issue IDs
     - List all files created/modified
     - Key architectural decisions made
     - **Test summary**: total tests, passed, failed, coverage %
     - Any known issues or follow-up items
   - Mark PR as "Ready for Review" (remove draft status): `gh pr ready`
   - Update the parent Epic status to "Done" in Linear
   - Add Epic comment with phase test summary:
     ```
     Phase {N} completed.
     - Tasks: X completed
     - Tests: Y passed, Z failed
     - Coverage: N%
     - All acceptance criteria validated
     ```
   - Switch to the base branch and create a new branch for the next phase

8. **Strict TDD Implementation Rules**:

   **TDD Cycle (Red-Green-Refactor)**:
   1. **RED**: Write a failing test first (if test task exists for the feature)
   2. **GREEN**: Write minimum code to make the test pass
   3. **REFACTOR**: Clean up code while keeping tests green

   **Execution Order**:
   - **Setup first**: Initialize project structure, dependencies, configuration
   - **Write tests first**: For each feature/task, write tests BEFORE implementation
   - **Implement to pass tests**: Write only enough code to make tests pass
   - **Run tests after EVERY task**: No exceptions - tests must pass before proceeding
   - **Core development**: Implement models, services, CLI commands, endpoints
   - **Integration work**: Database connections, middleware, logging, external services
   - **Final validation**: All tests green, coverage meets threshold

   **Test Requirements**:
   - Each task MUST have corresponding tests (unit, integration, or e2e as appropriate)
   - Tests MUST be run after task completion - no skipping
   - Failed tests BLOCK task completion - fix before marking "Done"
   - Test coverage should not decrease after any task
   - Update Linear issue with test results (see step 7)

9. **Progress tracking with Linear**:

   **Real-time status updates**:
   - Update issue status immediately when task state changes
   - Add comments for significant milestones within a task
   - Link related issues/PRs when relevant

   **Epic progress tracking**:
   - After completing all subtasks in an Epic, update Epic status to "Done"
   - Add summary comment to Epic: "Phase completed. X tasks done, Y files created."

   **Error handling**:
   - Report progress after each completed task
   - Halt execution if any non-parallel task fails
   - For parallel tasks [P], continue with successful tasks, report failed ones
   - Add detailed error comments to Linear issues
   - Provide clear error messages with context for debugging
   - Suggest next steps if implementation cannot proceed

10. **Completion validation and Linear finalization**:
    - **Final Test Gate** (BLOCKING):
      - Run complete test suite one final time
      - ALL tests MUST pass - no exceptions
      - Coverage must meet or exceed project threshold (default: 80%)
      - If tests fail, do NOT finalize - fix first
    - Verify all required tasks are completed
    - Check that implemented features match the original specification
    - Confirm the implementation follows the technical plan

    **Final Linear updates**:
    - Ensure all issues are in "Done" status with test results in descriptions
    - Update project status if all Epics complete
    - Add final summary comment to main Epic:
      ```
      Implementation complete.
      - Total tasks: X
      - Files created: Y
      - Tests: {total} run, {passed} passed, {failed} failed
      - Coverage: N%
      - All acceptance criteria: VALIDATED
      ```
    - Report final status with summary of completed work

    **Acceptance Criteria Summary**:
    - Review each task's Linear issue to ensure all acceptance criteria are checked
    - Generate a final acceptance criteria report across all tasks
    - Flag any criteria that were not fully validated

## Linear MCP Commands Reference

**Listing & Fetching**:
- `mcp__linear-server__list_projects` - List all projects
- `mcp__linear-server__list_issues` - List issues (filter by project, state, assignee)
- `mcp__linear-server__get_issue` - Get issue details by ID
- `mcp__linear-server__list_issue_statuses` - Get available statuses for a team

**Updating**:
- `mcp__linear-server__update_issue` - Update issue (status, assignee, labels, etc.)
- `mcp__linear-server__create_comment` - Add comment to an issue

**Status Values** (use with `state` parameter):
- `Backlog` - Not started
- `Todo` - Ready to start
- `In Progress` - Currently working
- `In Review` - Completed, pending validation
- `Done` - Fully completed
- `Canceled` - Skipped

Note: This command assumes a complete task breakdown exists in tasks.md and corresponding issues exist in Linear. If tasks are incomplete or missing, suggest running `/speckit.tasks` first to regenerate the task list, then `/speckit.taskstoissues` to sync with Linear.
