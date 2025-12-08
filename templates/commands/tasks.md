---
description: Generate an actionable, dependency-ordered tasks.md for the feature based on available design artifacts.
handoffs: 
  - label: Analyze For Consistency
    agent: speckit.analyze
    prompt: Run a project analysis for consistency
    send: true
  - label: Implement Project
    agent: speckit.implement
    prompt: Start the implementation in phases
    send: true
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

1. **Setup**: Run `.specify/scripts/bash/check-prerequisites.sh --json` from repo root and parse FEATURE_DIR and AVAILABLE_DOCS list. All paths must be absolute. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. **Load design documents**: Read from FEATURE_DIR:
   - **Required**: plan.md (tech stack, libraries, structure), spec.md (user stories with priorities)
   - **Optional**: data-model.md (entities), contracts/ (API endpoints), research.md (decisions), quickstart.md (test scenarios)
   - Note: Not all projects have all documents. Generate tasks based on what's available.

3. **Execute task generation workflow**:
   - Load plan.md and extract tech stack, libraries, project structure
   - Load spec.md and extract user stories with their priorities (P1, P2, P3, etc.)
   - If data-model.md exists: Extract entities and map to user stories
   - If contracts/ exists: Map endpoints to user stories
   - If research.md exists: Extract decisions for setup tasks
   - Generate tasks organized by user story (see Task Generation Rules below)
   - Generate dependency graph showing user story completion order
   - Create parallel execution examples per user story
   - Validate task completeness (each user story has all needed tasks, independently testable)

4. **Generate tasks.md**: Use `.specify.specify/templates/tasks-template.md` as structure, fill with:
   - Correct feature name from plan.md
   - Phase 1: Setup tasks (project initialization)
   - Phase 2: Foundational tasks (blocking prerequisites for all user stories)
   - Phase 3+: One phase per user story (in priority order from spec.md)
   - Each phase includes: story goal, independent test criteria, tests (if requested), implementation tasks
   - Final Phase: Polish & cross-cutting concerns
   - All tasks must follow the strict checklist format (see Task Generation Rules below)
   - Clear file paths for each task
   - Dependencies section showing story completion order
   - Parallel execution examples per story
   - Implementation strategy section (MVP first, incremental delivery)

5. **Report**: Output path to generated tasks.md and summary:
   - Total task count
   - **TDD task breakdown**: X [TEST] tasks, Y [IMPL] tasks, Z [REFACTOR] tasks
   - Task count per user story
   - Parallel opportunities identified
   - Independent test criteria for each story
   - Suggested MVP scope (typically just User Story 1)
   - **TDD validation**:
     - Confirm every [IMPL] task has a preceding [TEST] task
     - Confirm test framework setup is in Phase 1
     - Confirm each user story phase follows TDD order
   - Format validation: Confirm ALL tasks follow the checklist format (checkbox, ID, TDD marker, labels, file paths)

Context for task generation: $ARGUMENTS

The tasks.md should be immediately executable - each task must be specific enough that an LLM can complete it without additional context.

## Task Generation Rules

**CRITICAL**: Tasks MUST be organized by user story to enable independent implementation and testing.

**STRICT TDD REQUIREMENT**: Tests are MANDATORY for every user story phase. Each feature/component MUST have a corresponding test task that comes BEFORE the implementation task.

### TDD Task Pattern (REQUIRED)

For each user story, tasks MUST follow this TDD sequence:

```
1. [TEST] Write failing test for feature X
2. [IMPL] Implement feature X to pass tests
3. [TEST] Write failing test for feature Y
4. [IMPL] Implement feature Y to pass tests
...
```

**Test Task Requirements**:
- Every implementation task MUST be preceded by its corresponding test task
- Test tasks are labeled with `[TEST]` marker
- Implementation tasks are labeled with `[IMPL]` marker
- Test tasks define the acceptance criteria for the implementation
- No implementation task can be started until its test task is complete

### Checklist Format (REQUIRED)

Every task MUST strictly follow this format:

```text
- [ ] [TaskID] [TDD] [P?] [Story?] Description with file path
```

**Format Components**:

1. **Checkbox**: ALWAYS start with `- [ ]` (markdown checkbox)
2. **Task ID**: Sequential number (T001, T002, T003...) in execution order
3. **[TDD] marker**: REQUIRED - indicates task type:
   - `[TEST]` - Write tests (RED phase) - comes FIRST
   - `[IMPL]` - Implementation (GREEN phase) - comes AFTER test
   - `[REFACTOR]` - Refactoring (optional, keeping tests green)
   - No marker for Setup/Foundational tasks that don't need TDD
4. **[P] marker**: Include ONLY if task is parallelizable (different files, no dependencies on incomplete tasks)
5. **[Story] label**: REQUIRED for user story phase tasks only
   - Format: [US1], [US2], [US3], etc. (maps to user stories from spec.md)
   - Setup phase: NO story label
   - Foundational phase: NO story label
   - User Story phases: MUST have story label
   - Polish phase: NO story label
6. **Description**: Clear action with exact file path

**Examples**:

- ✅ CORRECT: `- [ ] T001 Create project structure per implementation plan`
- ✅ CORRECT: `- [ ] T002 Configure test framework (vitest/jest/pytest) in project root`
- ✅ CORRECT: `- [ ] T010 [TEST] [US1] Write failing tests for User model in tests/models/user.test.ts`
- ✅ CORRECT: `- [ ] T011 [IMPL] [US1] Create User model to pass tests in src/models/user.ts`
- ✅ CORRECT: `- [ ] T012 [TEST] [P] [US1] Write failing tests for UserService in tests/services/user.test.ts`
- ✅ CORRECT: `- [ ] T013 [IMPL] [P] [US1] Implement UserService to pass tests in src/services/user.ts`
- ❌ WRONG: `- [ ] T010 [US1] Create User model` (missing [TEST] or [IMPL] marker)
- ❌ WRONG: `- [ ] T010 [IMPL] [US1] Create User model` (IMPL without preceding TEST task)
- ❌ WRONG: `- [ ] Create User model` (missing ID, TDD marker, and Story label)
- ❌ WRONG: `T001 [TEST] [US1] Create model` (missing checkbox)

### Task Organization

1. **From User Stories (spec.md)** - PRIMARY ORGANIZATION:
   - Each user story (P1, P2, P3...) gets its own phase
   - Map all related components to their story using TDD pairs:
     - [TEST] Model tests → [IMPL] Models
     - [TEST] Service tests → [IMPL] Services
     - [TEST] Endpoint/API tests → [IMPL] Endpoints/UI
     - [TEST] Integration tests → [IMPL] Integration code
   - Mark story dependencies (most stories should be independent)

2. **From Contracts**:
   - Map each contract/endpoint → to the user story it serves
   - ALWAYS create contract test task [TEST] BEFORE implementation [IMPL]
   - Contract tests define expected request/response shapes

3. **From Data Model**:
   - Map each entity to the user story(ies) that need it
   - If entity serves multiple stories: Put in earliest story or Foundational phase
   - TDD sequence: [TEST] Entity validation tests → [IMPL] Entity model → [TEST] Relationship tests → [IMPL] Relationships

4. **From Setup/Infrastructure**:
   - Shared infrastructure → Setup phase (Phase 1)
   - **Test framework configuration** → Setup phase (MANDATORY)
   - Foundational/blocking tasks → Foundational phase (Phase 2)
   - Story-specific setup → within that story's phase

### Phase Structure (TDD-Enforced)

- **Phase 1**: Setup (project initialization)
  - Project structure
  - **Test framework setup (MANDATORY)** - vitest, jest, pytest, etc.
  - Test utilities and helpers
  - CI/CD test configuration

- **Phase 2**: Foundational (blocking prerequisites)
  - Shared types/interfaces
  - Base classes/utilities
  - Database setup
  - [TEST] Core utility tests → [IMPL] Core utilities

- **Phase 3+**: User Stories in priority order (P1, P2, P3...)
  - **TDD Order within each story** (STRICT):
    1. [TEST] Write failing unit tests for models/entities
    2. [IMPL] Implement models to pass tests
    3. [TEST] Write failing unit tests for services/business logic
    4. [IMPL] Implement services to pass tests
    5. [TEST] Write failing integration/API tests
    6. [IMPL] Implement endpoints/UI to pass tests
    7. [REFACTOR] (optional) Refactor while keeping tests green
  - Each phase should be a complete, independently testable increment
  - **Gate**: All tests MUST pass before moving to next story

- **Final Phase**: Polish & Cross-Cutting Concerns
  - [TEST] E2E tests for critical flows
  - Performance optimization (tests must stay green)
  - Documentation
  - Final test coverage validation (target: 80%+)
