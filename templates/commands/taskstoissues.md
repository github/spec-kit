---
description: Convert existing tasks.md into actionable, dependency-ordered Linear issues for the feature based on available design artifacts.
tools: ['mcp__linear-server__list_projects', 'mcp__linear-server__list_teams', 'mcp__linear-server__create_issue', 'mcp__linear-server__list_issues', 'mcp__linear-server__update_issue', 'mcp__linear-server__list_issue_labels', 'mcp__linear-server__create_issue_label']
handoffs:
  - label: Implement Tasks
    agent: speckit.implement
    prompt: Start implementing the planned tasks
    send: true
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Overview

This command converts an existing tasks.md file into Linear issues, creating:
1. A **parent Epic issue** for each phase (with `epic` label)
2. **Ordered subtasks** as Linear issues under each phase Epic
3. Proper **TDD labels** (`tdd-red`, `tdd-green`, `tdd-refactor`) based on task type
4. **Dependency tracking** via issue descriptions
5. **Task registry** mapping task IDs to Linear issue IDs

## Linear Issue Hierarchy

```
Feature Epic (Parent) [labels: epic, feature]
├── Phase 1: Setup [labels: epic, phase]
│   ├── T001. Configure project structure
│   └── T002. [SETUP] Configure test framework
├── Phase 2: Foundational [labels: epic, phase]
│   ├── T003. [TEST] Core utility tests [labels: test, tdd-red]
│   └── T004. [IMPL] Core utilities [labels: implementation, tdd-green]
├── Phase 3: User Story 1 [labels: epic, phase, user-story]
│   ├── T005. [TEST] User model tests [labels: test, tdd-red]
│   ├── T006. [IMPL] User model [labels: implementation, tdd-green]
│   └── ...
└── Phase N: Polish [labels: epic, phase]
    └── T0XX. [REFACTOR] Final cleanup [labels: refactor, tdd-refactor]
```

## Outline

### 1. Initial Setup & Validation

1. **Load tasks.md**:
   - Run `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks` from repo root
   - Parse FEATURE_DIR and extract path to tasks.md
   - If tasks.md doesn't exist, ERROR: "No tasks.md found. Run /speckit.tasks first."

2. **Validate Linear connection**:
   - Use `mcp__linear-server__list_teams` to verify Linear MCP is available
   - If not available, ERROR: "Linear MCP server not connected. Please configure the Linear MCP server first."
   - Store the team ID for later use

3. **Find or create Linear project**:
   - Use `mcp__linear-server__list_projects` to find existing projects
   - Match by feature name from tasks.md header or spec.md
   - If no match found, create issues at team-level (no project)
   - If match found, store project ID for issue creation

4. **Check for existing issues**:
   - Use `mcp__linear-server__list_issues` with project filter
   - If issues already exist for this feature:
     - Ask user: "Found X existing issues for this feature. Options: (1) Skip existing, create missing (2) Archive existing, create all new (3) Cancel"
     - Handle based on user choice

### 2. Parse tasks.md Structure

1. **Extract feature metadata**:
   - Feature name from header
   - Total task count
   - Phase breakdown

2. **Parse phases**:
   - Identify phase boundaries (## Phase N: ...)
   - Extract phase name and description
   - Group tasks by phase

3. **Parse individual tasks**:
   For each task line matching `- [ ] T### ...`:

   ```
   - [ ] T001 [TEST] [P] [US1] Description with file path
   ```

   Extract:
   - `taskId`: T001, T002, etc.
   - `tddType`: TEST, IMPL, REFACTOR, SETUP, or null
   - `isParallel`: true if [P] present
   - `userStory`: US1, US2, etc. or null
   - `description`: Full task description
   - `filePath`: Extracted from description (if present)
   - `dependencies`: Inferred from task order and TDD pairing

4. **Build dependency map**:
   - [IMPL] tasks depend on their preceding [TEST] task
   - Sequential tasks depend on previous task in same phase
   - [P] marked tasks can run parallel within their group

### 3. Ensure Required Labels Exist

Before creating issues, ensure these labels exist in the workspace:

```javascript
const requiredLabels = [
  { name: 'epic', color: '#6B46C1' },
  { name: 'phase', color: '#3182CE' },
  { name: 'feature', color: '#38A169' },
  { name: 'user-story', color: '#DD6B20' },
  { name: 'tdd', color: '#E53E3E' },
  { name: 'test', color: '#D69E2E' },
  { name: 'tdd-red', color: '#FC8181' },
  { name: 'implementation', color: '#48BB78' },
  { name: 'tdd-green', color: '#68D391' },
  { name: 'refactor', color: '#4FD1C5' },
  { name: 'tdd-refactor', color: '#76E4F7' },
  { name: 'setup', color: '#A0AEC0' },
  { name: 'parallel', color: '#B794F4' }
];
```

Use `mcp__linear-server__list_issue_labels` to check existing labels.
Use `mcp__linear-server__create_issue_label` to create missing ones.

### 4. Create Linear Issues

#### 4.1 Create Feature Epic (Parent)

Use `mcp__linear-server__create_issue`:

```json
{
  "team": "[team-name]",
  "title": "Feature: [Feature Name]",
  "description": "## Feature Overview\n\n[From spec.md or tasks.md header]\n\n## TDD Approach\nThis feature follows strict Test-Driven Development:\n1. Write failing tests first (RED)\n2. Implement to pass tests (GREEN)\n3. Refactor while keeping tests green\n\n## Phases\n- Phase 1: Setup\n- Phase 2: Foundational\n- Phase 3+: User Stories\n- Final: Polish\n\n## Task Summary\n- Total Tasks: X\n- [TEST] Tasks: Y\n- [IMPL] Tasks: Z\n- [REFACTOR] Tasks: W\n\n## Test Coverage Target\n- Minimum: 80%",
  "project": "[project-name if available]",
  "priority": 2,
  "labels": ["epic", "feature", "tdd"]
}
```

Store the Feature Epic ID as `featureEpicId`.

#### 4.2 Create Phase Epics

For each phase in tasks.md, use `mcp__linear-server__create_issue`:

```json
{
  "team": "[team-name]",
  "title": "Phase [N]: [Phase Name]",
  "description": "## Phase Overview\n\n[Phase description from tasks.md]\n\n## Tasks in this Phase\n[List of task IDs and titles]\n\n## Dependencies\n- Depends on: [Previous phase if any]\n- Blocks: [Next phase]\n\n## Acceptance Criteria\n- [ ] All tasks completed\n- [ ] All tests passing\n- [ ] No regressions from previous phases",
  "parentId": "[featureEpicId]",
  "project": "[project-name if available]",
  "priority": 2,
  "labels": ["epic", "phase", "[user-story if applicable]"]
}
```

Store each Phase Epic ID in `phaseEpicIds` map.

#### 4.3 Create Task Issues

For each task, create a Linear issue based on its TDD type:

**For [TEST] tasks:**

```json
{
  "team": "[team-name]",
  "title": "[TaskID]. [TEST] [Description]",
  "description": "## Overview\nWrite failing tests that define expected behavior.\n\n## File(s)\n`[extracted file path]`\n\n## Test Cases to Write\n- [ ] [Infer test cases from description]\n- [ ] [Additional test case]\n\n## TDD Phase\n**RED** - Tests should compile but FAIL\n\n## Acceptance Criteria\n- [ ] Tests compile successfully\n- [ ] Tests FAIL as expected (RED phase)\n- [ ] Tests cover all specified behavior\n- [ ] Test file follows project conventions\n\n## Acceptance Criteria Results\n_To be filled by /speckit.implement_\n\n## Dependencies\n- Depends on: [Previous task ID if any]\n- Blocks: [Next IMPL task ID]",
  "parentId": "[phaseEpicId]",
  "project": "[project-name if available]",
  "priority": 2,
  "labels": ["test", "tdd-red", "[parallel if P marker]"]
}
```

**For [IMPL] tasks:**

```json
{
  "team": "[team-name]",
  "title": "[TaskID]. [IMPL] [Description]",
  "description": "## Overview\nImplement feature to make tests pass.\n\n## File(s)\n`[extracted file path]`\n\n## Related Test Task\nMakes tests from **[Previous TEST task ID]** pass.\n\n## Implementation Notes\n[From task description]\n\n## TDD Phase\n**GREEN** - Make all tests pass\n\n## Acceptance Criteria\n- [ ] All tests from [TEST task] PASS\n- [ ] No new test failures introduced\n- [ ] Code follows project conventions\n- [ ] No TypeScript/linting errors\n\n## Acceptance Criteria Results\n_To be filled by /speckit.implement with test output_\n\n## Dependencies\n- Depends on: [TEST task ID]\n- Blocks: [Next task ID if any]",
  "parentId": "[phaseEpicId]",
  "project": "[project-name if available]",
  "priority": 2,
  "labels": ["implementation", "tdd-green", "[parallel if P marker]"]
}
```

**For [REFACTOR] tasks:**

```json
{
  "team": "[team-name]",
  "title": "[TaskID]. [REFACTOR] [Description]",
  "description": "## Overview\nRefactor code while keeping all tests green.\n\n## File(s)\n`[extracted file path]`\n\n## Refactoring Goals\n- [ ] [Inferred improvement from description]\n- [ ] Code quality improvement\n\n## TDD Phase\n**REFACTOR** - Improve without breaking tests\n\n## Acceptance Criteria\n- [ ] ALL tests still PASS after refactoring\n- [ ] Code quality improved\n- [ ] No functionality changes\n- [ ] Coverage maintained or improved\n\n## Acceptance Criteria Results\n_To be filled by /speckit.implement_\n\n## Dependencies\n- Depends on: [Previous IMPL task ID]",
  "parentId": "[phaseEpicId]",
  "project": "[project-name if available]",
  "priority": 3,
  "labels": ["refactor", "tdd-refactor"]
}
```

**For [SETUP] or unmarked tasks:**

```json
{
  "team": "[team-name]",
  "title": "[TaskID]. [Description]",
  "description": "## Overview\n[Task description]\n\n## File(s)\n`[extracted file path if any]`\n\n## Acceptance Criteria\n- [ ] Task completed as described\n- [ ] [Additional criteria from description]\n\n## Dependencies\n- Depends on: [Previous task ID if any]",
  "parentId": "[phaseEpicId]",
  "project": "[project-name if available]",
  "priority": 2,
  "labels": ["setup"]
}
```

### 5. Update tasks.md with Linear IDs

After creating all issues, update tasks.md to include Linear issue references:

**Before:**
```markdown
- [ ] T001 Create project structure per implementation plan
- [ ] T002 [TEST] [US1] Write failing tests for User model in tests/models/user.test.ts
```

**After:**
```markdown
- [ ] T001 (FAY-101) Create project structure per implementation plan
- [ ] T002 (FAY-102) [TEST] [US1] Write failing tests for User model in tests/models/user.test.ts
```

### 6. Create Task Registry

Build and save a mapping table in tasks.md (append at end):

```markdown
## Linear Issue Registry

| Task ID | Type | Linear ID | Title | Phase | Dependencies |
|---------|------|-----------|-------|-------|--------------|
| - | FEATURE | FAY-100 | Feature: [Name] | - | - |
| - | PHASE | FAY-101 | Phase 1: Setup | 1 | - |
| T001 | SETUP | FAY-102 | Configure project | 1 | None |
| T002 | SETUP | FAY-103 | Configure test framework | 1 | T001 |
| - | PHASE | FAY-104 | Phase 2: Foundational | 2 | Phase 1 |
| T003 | TEST | FAY-105 | Core utility tests | 2 | T002 |
| T004 | IMPL | FAY-106 | Core utilities | 2 | T003 |
| - | PHASE | FAY-107 | Phase 3: User Story 1 | 3 | Phase 2 |
| T005 | TEST | FAY-108 | User model tests | 3 | T004 |
| T006 | IMPL | FAY-109 | User model | 3 | T005 |

**Created**: [timestamp]
**Total Issues**: X
**Feature Epic**: FAY-100
```

### 7. Report & Next Steps

Display summary:

```markdown
## Summary

**Feature Epic**: [FAY-XXX](linear-link) - [Feature Name]
**Project**: [Project Name]
**Team**: [Team Name]

### Issues Created

| Category | Count |
|----------|-------|
| Feature Epic | 1 |
| Phase Epics | X |
| [TEST] Tasks | Y |
| [IMPL] Tasks | Z |
| [REFACTOR] Tasks | W |
| [SETUP] Tasks | V |
| **Total** | **N** |

### TDD Execution Order

Phase 1 (Setup): T001, T002
Phase 2 (Foundational): T003 [TEST] → T004 [IMPL]
Phase 3 (US1): T005 [TEST] → T006 [IMPL] → T007 [TEST] → T008 [IMPL]
...
Final (Polish): T0XX [REFACTOR]

### Files Updated

- [x] tasks.md - Added Linear issue IDs and registry

### Next Steps

1. Run `/speckit.implement` to start executing tasks
2. Follow strict TDD order: complete each [TEST] before its [IMPL]
3. All tests must pass before marking any [IMPL] task as Done
```

## Error Handling

- **No tasks.md**: ERROR - Run `/speckit.tasks` first
- **Linear unavailable**: ERROR - Configure Linear MCP server
- **Label creation fails**: WARN - Continue without that label
- **Issue creation fails**: Retry once, then log error and continue
- **Duplicate issues found**: Ask user how to handle

## Linear MCP Reference

**Creating Issues**:
- `mcp__linear-server__create_issue` - Create new issue with title, description, priority, labels, parentId

**Querying**:
- `mcp__linear-server__list_projects` - List all projects
- `mcp__linear-server__list_teams` - List all teams
- `mcp__linear-server__list_issues` - List issues with filters
- `mcp__linear-server__list_issue_labels` - List existing labels

**Labels**:
- `mcp__linear-server__create_issue_label` - Create new label

**Updating**:
- `mcp__linear-server__update_issue` - Update issue properties

**Status Values**:
- `Backlog` - Not started
- `Todo` - Ready to start
- `In Progress` - Currently working
- `In Review` - Pending validation
- `Done` - Completed
- `Canceled` - Skipped

## Guidelines

### TDD Label Mapping
- `[TEST]` tasks → `test` + `tdd-red` labels
- `[IMPL]` tasks → `implementation` + `tdd-green` labels
- `[REFACTOR]` tasks → `refactor` + `tdd-refactor` labels
- `[SETUP]` tasks → `setup` label
- `[P]` marker → add `parallel` label

### Issue Hierarchy
- Feature Epic (top-level, no parent)
  - Phase Epics (parent = Feature Epic)
    - Task Issues (parent = Phase Epic)

### Dependency Tracking
- Dependencies tracked in issue descriptions, not Linear's native dependencies
- Format: "Depends on: T001, T002" and "Blocks: T003"
- [IMPL] always depends on its [TEST]

### Acceptance Criteria
- Every issue has `## Acceptance Criteria` section
- Every issue has `## Acceptance Criteria Results` placeholder
- Results filled by `/speckit.implement` after task execution
