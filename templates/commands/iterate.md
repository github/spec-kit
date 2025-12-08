---
description: Transform a feature idea into a complete implementation plan with Linear epics and tasks, then track execution.
tools: ['mcp__linear-server__list_projects', 'mcp__linear-server__list_teams', 'mcp__linear-server__create_issue', 'mcp__linear-server__list_issues', 'mcp__linear-server__update_issue', 'mcp__linear-server__create_comment']
handoffs:
  - label: Implement Tasks
    agent: speckit.implement
    prompt: Start implementing the planned tasks
    send: true
  - label: Refine Specification
    agent: speckit.clarify
    prompt: Clarify any ambiguous requirements
    send: true
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty). If empty, ask the user to describe the feature they want to build.

## Overview

This command takes a natural language feature description and:
1. Creates a detailed implementation plan with architecture decisions
2. Creates a **parent User Story issue** (with `epic` and `user-story` labels) to track the request
3. Creates **ordered subtasks** as implementation steps under the parent
4. Optionally creates a **third level of subtasks** for complex tasks that need their own breakdown
5. Provides real-time tracking as work progresses

## Linear Issue Hierarchy (TDD-Enforced)

```
User Story (Parent) [labels: epic, user-story, tdd]
├── 1. [SETUP] Configure test framework
├── 2. [TEST] Write failing tests for feature A
├── 3. [IMPL] Implement feature A to pass tests
├── 4. [TEST] Write failing tests for feature B
├── 5. [IMPL] Implement feature B to pass tests
├── 6. [TEST] Complex feature tests (may have subtasks)
│   ├── 6.1 [TEST] Unit tests for component X
│   ├── 6.2 [TEST] Unit tests for component Y
│   └── 6.3 [TEST] Integration tests
├── 7. [IMPL] Implement complex feature to pass tests
└── 8. [REFACTOR] Final cleanup (tests must stay green)
```

**TDD Rules**:
- Always create ONE parent User Story with labels `epic`, `user-story`, and `tdd`
- **Test tasks [TEST] MUST come before implementation tasks [IMPL]**
- Each [IMPL] task must reference the [TEST] task it satisfies
- Subtasks are numbered and ordered by TDD sequence (RED → GREEN → REFACTOR)
- Complex features: break down [TEST] tasks into subtasks, then single [IMPL] to pass all
- Final task should validate all tests pass with coverage threshold

## Outline

### 1. Initial Setup & Validation

1. **Check for existing feature context**:
   - Run `.specify/scripts/bash/check-prerequisites.sh --json` to check if we're in an existing feature branch
   - If FEATURE_DIR exists with spec.md or plan.md, use that context to enrich the plan
   - If not, we'll work from the user input alone

2. **Validate Linear connection**:
   - Use `mcp__linear-server__list_teams` to verify Linear MCP is available
   - If not available, ERROR: "Linear MCP server not connected. Please configure the Linear MCP server first."
   - Store the team ID for later use

3. **Find or create Linear project**:
   - Use `mcp__linear-server__list_projects` to find existing projects
   - Match by feature name from user input or existing spec
   - If no match found, we'll create issues without a project (just team-level)
   - If match found, store project ID for issue creation

### 2. Analyze Feature & Generate Plan

1. **Parse user input** to extract:
   - **Core objective**: What is the main goal?
   - **Key actors**: Who uses this feature?
   - **Critical flows**: What are the main user journeys?
   - **Technical hints**: Any mentioned technologies, integrations, or constraints?
   - **Scope indicators**: Any explicit inclusions/exclusions?

2. **If existing spec/plan available**, enrich with:
   - User stories from spec.md
   - Technical stack from plan.md
   - Entities from data-model.md
   - API contracts from contracts/

3. **Generate Implementation Plan**:

   Structure the plan with these sections:

   ```markdown
   # Implementation Plan: [Feature Name]

   ## Summary
   [One paragraph describing the feature and its value]

   ## Technical Approach
   - **Architecture**: [Chosen architecture pattern]
   - **Key Technologies**: [Primary tech stack]
   - **Integration Points**: [External systems/APIs]
   - **Data Storage**: [Database/storage approach]

   ## Implementation Tasks Overview
   [Numbered list of implementation steps with brief descriptions]

   ## Risk Assessment
   - **Technical Risks**: [Potential blockers]
   - **Dependencies**: [External dependencies]
   - **Assumptions**: [Key assumptions made]
   ```

### 3. Break Into Ordered Tasks (TDD Pattern)

1. **Generate TDD Task Pairs**:

   Create a numbered, ordered list following strict TDD sequence:

   ```markdown
   ## Implementation Tasks (TDD)

   1. **[SETUP] Configure test framework** - Set up testing infrastructure
      - File(s): vitest.config.ts, package.json
      - Depends on: None

   2. **[TEST] Write failing tests for User model** - Define expected behavior
      - File(s): tests/models/user.test.ts
      - Depends on: 1
      - Acceptance: Tests compile but FAIL (RED phase)

   3. **[IMPL] Implement User model to pass tests** - Make tests green
      - File(s): src/models/user.ts
      - Depends on: 2
      - Acceptance: All tests from task 2 PASS (GREEN phase)

   4. **[TEST] Write failing tests for UserService** - Define service behavior
      - File(s): tests/services/user.test.ts
      - Depends on: 3
      - Acceptance: Tests compile but FAIL

   5. **[IMPL] Implement UserService to pass tests** - Make tests green
      - File(s): src/services/user.ts
      - Depends on: 4
      - Acceptance: All tests from task 4 PASS

   6. **[TEST] Complex API tests** ⚠️ Complex - Multiple test files needed
      - File(s): tests/api/*.test.ts
      - Depends on: 5
      - Subtasks:
        - 6.1 [TEST] Write endpoint validation tests
        - 6.2 [TEST] Write authentication tests
        - 6.3 [TEST] Write integration tests

   7. **[IMPL] Implement API to pass all tests** - Make all tests green
      - File(s): src/api/*.ts
      - Depends on: 6
      - Acceptance: All tests from task 6 PASS

   8. **[REFACTOR] Final cleanup** - Improve code quality
      - File(s): All modified files
      - Depends on: 7
      - Acceptance: All tests still PASS, coverage >= 80%
   ```

   **TDD Task Generation Rules**:
   - **ALWAYS start with [SETUP] for test framework** (task 1)
   - **[TEST] tasks MUST precede their corresponding [IMPL] tasks**
   - Number tasks sequentially following TDD order (TEST → IMPL → TEST → IMPL...)
   - Each [TEST] task defines acceptance criteria for the [IMPL] task
   - Each [IMPL] task references which [TEST] task(s) it satisfies
   - Keep task pairs small enough to complete in 1-4 hours
   - End with [REFACTOR] task to clean up while keeping tests green

2. **Identify Complex Test Tasks**:
   - A feature is "complex" if it needs multiple test files
   - Break down [TEST] tasks into subtasks (6.1, 6.2, etc.)
   - Keep [IMPL] as single task that makes ALL subtask tests pass
   - This ensures implementation satisfies complete test coverage

### 4. Create Linear Issues (TDD-Labeled)

1. **Create Parent User Story**:

   Use `mcp__linear-server__create_issue`:

   ```json
   {
     "team": "[team-name]",
     "title": "User Story: [Feature Name]",
     "description": "## User Story\n\n**As a** [actor],\n**I want** [goal],\n**So that** [benefit].\n\n## Summary\n[Feature summary]\n\n## TDD Approach\nThis feature follows strict Test-Driven Development:\n1. Write failing tests first (RED)\n2. Implement to pass tests (GREEN)\n3. Refactor while keeping tests green\n\n## Acceptance Criteria\n- [ ] All [TEST] tasks completed with failing tests\n- [ ] All [IMPL] tasks completed with passing tests\n- [ ] Test coverage >= 80%\n- [ ] [Feature-specific criterion 1]\n- [ ] [Feature-specific criterion 2]\n\n## Test Summary\n_Updated after implementation_\n\n## Implementation Tasks\nSee subtasks for TDD-ordered implementation steps.",
     "project": "[project-name if available]",
     "priority": 2,
     "labels": ["epic", "user-story", "tdd"]
   }
   ```

   **Store the created issue ID** to use as parent for all subtasks.

2. **Create TDD Subtasks**:

   **For [TEST] tasks**, use `mcp__linear-server__create_issue`:

   ```json
   {
     "team": "[team-name]",
     "title": "[N]. [TEST] [Task description]",
     "description": "## Overview\nWrite failing tests that define expected behavior.\n\n## File(s)\n[test file paths]\n\n## Test Cases to Write\n- [ ] [Test case 1 description]\n- [ ] [Test case 2 description]\n- [ ] [Test case 3 description]\n\n## Acceptance Criteria\n- [ ] Tests compile successfully\n- [ ] Tests FAIL (RED phase) - this is expected\n- [ ] Tests cover all specified behavior\n- [ ] Test file follows project conventions\n\n## Acceptance Criteria Results\n_To be filled after task completion_",
     "parentId": "[user-story-issue-id]",
     "project": "[project-name if available]",
     "priority": 2,
     "labels": ["test", "tdd-red"]
   }
   ```

   **For [IMPL] tasks**, use `mcp__linear-server__create_issue`:

   ```json
   {
     "team": "[team-name]",
     "title": "[N]. [IMPL] [Task description]",
     "description": "## Overview\nImplement feature to make tests pass.\n\n## File(s)\n[implementation file paths]\n\n## Related Test Task\nMakes tests from task [N-1] pass.\n\n## Implementation Notes\n[Specific implementation details]\n\n## Acceptance Criteria\n- [ ] All tests from task [N-1] PASS (GREEN phase)\n- [ ] No new test failures introduced\n- [ ] Code follows project conventions\n- [ ] No TypeScript/linting errors\n\n## Acceptance Criteria Results\n_To be filled after task completion with test output_",
     "parentId": "[user-story-issue-id]",
     "project": "[project-name if available]",
     "priority": 2,
     "labels": ["implementation", "tdd-green"]
   }
   ```

   **For [REFACTOR] tasks**, use `mcp__linear-server__create_issue`:

   ```json
   {
     "team": "[team-name]",
     "title": "[N]. [REFACTOR] [Task description]",
     "description": "## Overview\nRefactor code while keeping all tests green.\n\n## File(s)\n[files to refactor]\n\n## Refactoring Goals\n- [ ] [Improvement 1]\n- [ ] [Improvement 2]\n\n## Acceptance Criteria\n- [ ] ALL tests still PASS after refactoring\n- [ ] Code quality improved (cleaner, more readable)\n- [ ] No functionality changes\n- [ ] Coverage maintained or improved\n\n## Acceptance Criteria Results\n_To be filled after task completion_",
     "parentId": "[user-story-issue-id]",
     "project": "[project-name if available]",
     "priority": 3,
     "labels": ["refactor", "tdd-refactor"]
   }
   ```

3. **Create Third-Level Subtasks** (only for complex [TEST] tasks):

   If a [TEST] task needs breakdown:

   ```json
   {
     "team": "[team-name]",
     "title": "[N.M]. [TEST] [Subtask description]",
     "description": "## Parent Task\n[Link to parent TEST task]\n\n## Test Focus\n[What this specific test file covers]\n\n## Test Cases\n- [ ] [Test case 1]\n- [ ] [Test case 2]\n\n## Acceptance Criteria\n- [ ] Tests compile and FAIL as expected",
     "parentId": "[complex-test-task-issue-id]",
     "project": "[project-name if available]",
     "priority": 3,
     "labels": ["test", "subtask", "tdd-red"]
   }
   ```

4. **Create Task Registry**:

   Build and display a TDD-aware mapping table:

   ```markdown
   | # | Type | Linear ID | Title | Status | Dependencies |
   |---|------|-----------|-------|--------|--------------|
   | - | EPIC | FAY-100   | User Story: Feature Name | Backlog | - |
   | 1 | SETUP | FAY-101  | Configure test framework | Backlog | None |
   | 2 | TEST | FAY-102   | Write failing User model tests | Backlog | 1 |
   | 3 | IMPL | FAY-103   | Implement User model | Backlog | 2 |
   | 4 | TEST | FAY-104   | Write failing UserService tests | Backlog | 3 |
   | 5 | IMPL | FAY-105   | Implement UserService | Backlog | 4 |
   | 6 | TEST | FAY-106   | Complex API tests | Backlog | 5 |
   | 6.1 | TEST | FAY-107 | Endpoint validation tests | Backlog | 6 |
   | 6.2 | TEST | FAY-108 | Authentication tests | Backlog | 6 |
   | 7 | IMPL | FAY-109   | Implement API | Backlog | 6.1, 6.2 |
   | 8 | REFACTOR | FAY-110 | Final cleanup | Backlog | 7 |
   ```

### 5. Report & Next Steps

1. **Summary Report**:

   Display:
   ```markdown
   ## Summary

   **User Story**: [FAY-XXX](link) - [Title]
   **TDD Approach**: Enabled
   **Total Tasks**: X
   **Test Tasks [TEST]**: Y
   **Implementation Tasks [IMPL]**: Z
   **Refactor Tasks**: W

   ### TDD Task Breakdown

   | # | Type | Linear ID | Title | Labels | Dependencies |
   |---|------|-----------|-------|--------|--------------|
   | 1 | SETUP | FAY-XXX | Configure tests | setup | None |
   | 2 | TEST | FAY-XXX | User model tests | tdd-red | 1 |
   | 3 | IMPL | FAY-XXX | User model impl | tdd-green | 2 |

   ### TDD Execution Order

   Phase 1 (Setup): Task 1 - Test framework
   Phase 2 (RED): Task 2 - Write failing tests
   Phase 3 (GREEN): Task 3 - Make tests pass
   Phase 4 (RED): Task 4 - Write failing tests
   Phase 5 (GREEN): Task 5 - Make tests pass
   ...
   Final (REFACTOR): Task N - Cleanup with tests green

   ### Test Coverage Target
   - Minimum: 80%
   - All [IMPL] tasks must pass their corresponding [TEST] tasks
   ```

2. **Suggest Next Actions**:
   - If ready to implement: Recommend starting with Task 1 (test framework setup)
   - Remind: "Follow strict TDD - complete each [TEST] before its [IMPL]"
   - If needs clarification: Recommend `/speckit.clarify`
   - If plan needs revision: User can re-run `/speckit.iterate` with modifications

## Error Handling

- **No user input**: Ask for feature description before proceeding
- **Linear unavailable**: Warn user but continue with local artifact generation
- **Issue creation fails**: Retry once, then log error and continue with remaining issues
- **Existing issues found**: Ask user whether to reuse, archive, or create new

## Linear MCP Reference

**Creating Issues**:
- `mcp__linear-server__create_issue` - Create new issue with title, description, priority, labels, parentId

**Querying**:
- `mcp__linear-server__list_projects` - List all projects
- `mcp__linear-server__list_teams` - List all teams
- `mcp__linear-server__list_issues` - List issues with filters
- `mcp__linear-server__get_issue` - Get issue details

**Updating**:
- `mcp__linear-server__update_issue` - Update issue properties
- `mcp__linear-server__create_comment` - Add comment to issue

**Status Values**:
- `Backlog` - Not started
- `Todo` - Ready to start
- `In Progress` - Currently working
- `In Review` - Pending validation
- `Done` - Completed
- `Canceled` - Skipped

## Guidelines

### TDD Requirements (MANDATORY)
- **Test First**: Every [IMPL] task MUST have a preceding [TEST] task
- **RED-GREEN-REFACTOR**: Follow the TDD cycle strictly
- **No Skipping Tests**: Implementation cannot start until tests are written
- **Labels**: Use `tdd-red`, `tdd-green`, `tdd-refactor` labels to track TDD phase
- **Coverage Gate**: Target 80% minimum test coverage

### Task Structure
- **Flat Hierarchy**: Prefer 2 levels (User Story → Tasks). Only use 3 levels for complex [TEST] breakdowns.
- **TDD Order**: Tasks numbered in TDD sequence (SETUP → TEST → IMPL → TEST → IMPL → REFACTOR)
- **Clear Dependencies**: [IMPL] tasks depend on their [TEST] tasks
- **Granularity**: TEST/IMPL pairs should be completable in 1-4 hours combined
- **Clarity**: Every task must specify files and acceptance criteria
- **Traceability**: All tasks link back to the parent User Story
- **Labels**:
  - Parent: `epic` + `user-story` + `tdd`
  - Test tasks: `test` + `tdd-red`
  - Impl tasks: `implementation` + `tdd-green`
  - Refactor tasks: `refactor` + `tdd-refactor`

### Acceptance Criteria Format
- [TEST] tasks: "Tests compile and FAIL as expected"
- [IMPL] tasks: "All tests from task [N] PASS"
- [REFACTOR] tasks: "All tests still PASS, code quality improved"
