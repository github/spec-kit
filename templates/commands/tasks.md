---
description: Generate an actionable, dependency-ordered tasks.md for the feature based on available design artifacts.
scripts:
  sh: scripts/bash/check-prerequisites.sh --json
  ps: scripts/powershell/check-prerequisites.ps1 -Json
agent_scripts:
  sh: "specify guard types -v; echo '\n=== EXISTING GUARDS ==='; specify guard list"
  ps: "specify guard types -v; Write-Output '\n=== EXISTING GUARDS ==='; specify guard list"
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

1. **Setup**: Run `{SCRIPT}` from repo root and parse FEATURE_DIR and AVAILABLE_DOCS list. All paths must be absolute. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

1.5. **Load Guard Context** (MANDATORY): 
   
   **Step 1 - Check available guard types**:
   ```bash
   uv run specify guard types -v
   ```
   This shows the Category × Type matrix with all available guard types.
   
   **Step 2 - Check existing guards**:
   ```bash
   uv run specify guard list
   ```
   This shows all created guards grouped by category with their status.
   
   Use this information to:
   - Match validation needs from plan.md to available guard types
   - Avoid creating duplicate guards (check guard list)
   - Understand current test coverage
   - **CRITICAL**: If plan.md has "Guard Validation Strategy" section, use it to determine which guards to create

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
   - **Identify guard opportunities** for critical validation checkpoints (see Guard Integration below)
   - Generate tasks organized by user story (see Task Generation Rules below)
   - Generate dependency graph showing user story completion order
   - Create parallel execution examples per user story
   - Validate task completeness (each user story has all needed tasks, independently testable)

4. **Generate tasks.md**: Use `.specify/templates/tasks-template.md` as structure, fill with:
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
   - Task count per user story
   - Parallel opportunities identified
   - Independent test criteria for each story
   - Suggested MVP scope (typically just User Story 1)
   - Format validation: Confirm ALL tasks follow the checklist format (checkbox, ID, labels, file paths)

Context for task generation: {ARGS}

The tasks.md should be immediately executable - each task must be specific enough that an LLM can complete it without additional context.

## Task Generation Rules

**CRITICAL**: Tasks MUST be organized by user story to enable independent implementation and testing.

**Tests are OPTIONAL**: Only generate test tasks if explicitly requested in the feature specification or if user requests TDD approach.

### Checklist Format (REQUIRED)

Every task MUST strictly follow this format:

```text
- [ ] [TaskID] [P?] [Story?] Description with file path
```

**Format Components**:

1. **Checkbox**: ALWAYS start with `- [ ]` (markdown checkbox)
2. **Task ID**: Sequential number (T001, T002, T003...) in execution order
3. **[P] marker**: Include ONLY if task is parallelizable (different files, no dependencies on incomplete tasks)
4. **[Story] label**: REQUIRED for user story phase tasks only
   - Format: [US1], [US2], [US3], etc. (maps to user stories from spec.md)
   - Setup phase: NO story label
   - Foundational phase: NO story label  
   - User Story phases: MUST have story label
   - Polish phase: NO story label
5. **Description**: Clear action with exact file path

**Examples**:

- ✅ CORRECT: `- [ ] T001 Create project structure per implementation plan`
- ✅ CORRECT: `- [ ] T005 [P] Implement authentication middleware in src/middleware/auth.py`
- ✅ CORRECT: `- [ ] T012 [P] [US1] Create User model in src/models/user.py`
- ✅ CORRECT: `- [ ] T014 [US1] Implement UserService in src/services/user_service.py`
- ❌ WRONG: `- [ ] Create User model` (missing ID and Story label)
- ❌ WRONG: `T001 [US1] Create model` (missing checkbox)
- ❌ WRONG: `- [ ] [US1] Create User model` (missing Task ID)
- ❌ WRONG: `- [ ] T001 [US1] Create model` (missing file path)

### Task Organization

1. **From User Stories (spec.md)** - PRIMARY ORGANIZATION:
   - Each user story (P1, P2, P3...) gets its own phase
   - Map all related components to their story:
     - Models needed for that story
     - Services needed for that story
     - Endpoints/UI needed for that story
     - If tests requested: Tests specific to that story
   - Mark story dependencies (most stories should be independent)
   
2. **From Contracts**:
   - Map each contract/endpoint → to the user story it serves
   - If tests requested: Each contract → contract test task [P] before implementation in that story's phase
   
3. **From Data Model**:
   - Map each entity to the user story(ies) that need it
   - If entity serves multiple stories: Put in earliest story or Setup phase
   - Relationships → service layer tasks in appropriate story phase
   
4. **From Setup/Infrastructure**:
   - Shared infrastructure → Setup phase (Phase 1)
   - Foundational/blocking tasks → Foundational phase (Phase 2)
   - Story-specific setup → within that story's phase

### Phase Structure

- **Phase 1**: Setup (project initialization)
- **Phase 2**: Foundational (blocking prerequisites - MUST complete before user stories)
- **Phase 3+**: User Stories in priority order (P1, P2, P3...)
  - Within each story: **Guards (REQUIRED - create custom type if needed)** → Tests (if requested) → Models → Services → Endpoints → Integration
  - Each phase should be a complete, independently testable increment
  - **NO user story is complete without at least one passing guard**
- **Final Phase**: Polish & Cross-Cutting Concerns

### Guard Integration (MANDATORY)

**Constitutional Principle V**: Tasks MUST NOT be marked complete without a passing guard when validation checkpoints exist.

**CRITICAL WORKFLOW**:
1. **Read plan.md "Guard Validation Strategy"** (if exists)
2. **For EACH validation checkpoint** in spec.md user stories:
   - Check if existing guard covers it (from guard context in step 1.5)
   - If NO existing guard → CREATE guard creation task
   - Tag implementation task with `[Guard: G###]`
3. **Guard creation is FIRST task** in each user story phase (before any implementation)
4. **Every user story MUST have at least one guard** (no exceptions)

**When to create guards** (EVERY user story needs validation):

**If guard type exists** (check available types from step 1.5):
- **API endpoints** → 
  ```bash
  uv run specify guard create --type api --name <feature-name> --task <task-id> --tag api
  ```
- **Business logic/algorithms** → 
  ```bash
  uv run specify guard create --type unit-pytest --name <feature-name> --task <task-id> --tag unit
  ```
- Replace `<feature-name>` with kebab-case description (e.g., user-authentication)
- Replace `<task-id>` with the user story ID (e.g., US1, US2, T015)
- Add relevant tags for organization

**If NO guard type matches** (validation checkpoint but no suitable type):
- **MUST create custom guard type FIRST**:
  ```markdown
  Phase X: User Story Y
  - [ ] T### [USY] Create custom guard type for <validation-need>
    Command: specify guard create-type --name <type-name> --category <category>
    Then: Implement scaffolder in .specify/guards/types-custom/<type-name>/
  - [ ] T### [USY] Create guard using new custom type
    Command: specify guard create --type <type-name> --name <feature-name>
  - [ ] T### [USY] Implement <feature> [Guard: G###]
  ```

**Example validation checkpoints requiring custom guards**:
- **Database migrations** → Create `database-migration` guard type
- **UI workflows** → Create `e2e-workflow` guard type
- **Code quality** → Create `lint-<project>` guard type
- **Performance** → Create `performance-benchmark` guard type
- **Security scans** → Create `security-scan` guard type
- **Contract testing** → Create `contract-test` guard type

**Task sequence template**:
```markdown
Phase 3: User Story 1 - <Feature Name>

### Guards (Create FIRST)
- [ ] T015 [US1] Create custom guard type 'checkout-flow' for E2E validation
  Command: specify guard create-type --name checkout-flow --category e2e
- [ ] T016 [US1] Implement checkout-flow scaffolder with Playwright templates
- [ ] T017 [US1] Create guard for checkout workflow
  Command: specify guard create --type checkout-flow --name user-checkout

### Implementation (Tagged with guards)
- [ ] T018 [US1] Implement checkout API endpoint [Guard: G001]
- [ ] T019 [US1] Implement payment processing [Guard: G001]
- [ ] T020 [US1] Implement order confirmation [Guard: G001]
```

**Existing guards** (loaded in step 1.5):
- Reference guard IDs from existing guards when applicable
- Don't create duplicate guards for same validation checkpoint
- Update existing guard if validation requirements changed

**Guard execution**: Guards are executed via `/implement` command before marking tasks complete. Implementation stops if guard fails.


