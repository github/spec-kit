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
scripts:
  sh: scripts/bash/check-prerequisites.sh --json
  ps: scripts/powershell/check-prerequisites.ps1 -Json
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

1. **Setup**: Run `{SCRIPT}` from repo root and parse FEATURE_DIR and AVAILABLE_DOCS list. All paths must be absolute. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. **Load design documents**: Read from FEATURE_DIR:
   - **Required**: plan.md (tech stack, libraries, structure), spec.md (user stories with priorities)
   - **Optional**: data-model.md (entities), contracts/ (API endpoints), research.md (decisions), quickstart.md (test scenarios)
   - Note: Not all projects have all documents. Generate tasks based on what's available.

3. **Load source idea (CRITICAL for alignment)**:
   - Check plan.md for "Idea Technical Alignment" section → extract source idea path
   - If not found, check spec.md for `**Source**:` or `**Parent Idea**:` links
   - If still not found, search `ideas/` directory for matching idea
   - Load the idea.md and any feature files
   - Extract **Technical Hints** and **Constraints** sections
   - Store as IDEA_TECHNICAL_REQUIREMENTS for validation in step 4

4. **Validate alignment with source idea (BEFORE generating tasks)**:

   CRITICAL: Before generating any tasks, verify alignment with IDEA_TECHNICAL_REQUIREMENTS:

   a. **Extract technical specifics from idea**:
      - Commands or CLI instructions to execute (with order)
      - Specific tools, libraries, or versions mentioned
      - Step-by-step technical procedures
      - Configuration patterns or approaches
      - Integration sequences or protocols

   b. **Cross-check with plan.md**:
      - Verify plan's "Idea Technical Alignment" section exists
      - If plan has divergences, they MUST be carried to tasks (not ignored)
      - If plan is missing alignment section, perform alignment check now

   c. **Pre-generation checklist**:
      ```
      For each technical requirement in idea:
      □ Is it reflected in plan.md?
      □ Will the generated tasks implement it correctly?
      □ Is the execution order preserved?
      □ Are specific commands/tools preserved (not substituted)?
      ```

   d. **STOP if misalignment detected**:
      - If idea specifies technical approach X but plan uses approach Y
      - Report the divergence to user BEFORE generating tasks
      - Ask for explicit confirmation to proceed with plan's approach
      - Document decision in tasks.md header

5. **Execute task generation workflow**:
   - Load plan.md and extract tech stack, libraries, project structure
   - Load spec.md and extract user stories with their priorities (P1, P2, P3, etc.)
   - If data-model.md exists: Extract entities and map to user stories
   - If contracts/ exists: Map endpoints to user stories
   - If research.md exists:
     - Extract decisions for setup tasks
     - **Extract Existing Codebase Analysis** → reuse decisions
     - **Extract reuse/extend/new markers** for each component
   - **Map IDEA_TECHNICAL_REQUIREMENTS to specific tasks** (see Task Generation Rules)
   - **Map REUSE DECISIONS to specific tasks** (see Reuse Task Rules below)
   - Generate tasks organized by user story (see Task Generation Rules below)
   - Generate dependency graph showing user story completion order
   - Create parallel execution examples per user story
   - Validate task completeness (each user story has all needed tasks, independently testable)
   - **Validate technical alignment** (each idea requirement maps to at least one task)
   - **Validate reuse alignment** (reuse decisions from research.md are reflected in tasks)

6. **Generate tasks.md**: Use `templates/tasks-template.md` as structure, fill with:
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
   - **Idea Technical Traceability section** (see below)

7. **Report**: Output path to generated tasks.md and summary:
   - Total task count
   - Task count per user story
   - Parallel opportunities identified
   - Independent test criteria for each story
   - Suggested MVP scope (typically just User Story 1)
   - Format validation: Confirm ALL tasks follow the checklist format (checkbox, ID, labels, file paths)
   - **Idea alignment status**: Confirm all technical requirements from idea are mapped to tasks
   - **Reuse summary**: Count of REUSE/EXTEND/REFACTOR/NEW tasks
   - **Reuse ratio**: If NEW > 50%, flag for review

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
  - Within each story: Tests (if requested) → Models → Services → Endpoints → Integration
  - Each phase should be a complete, independently testable increment
- **Final Phase**: Polish & Cross-Cutting Concerns

### Reuse Task Rules (CRITICAL)

Tasks MUST reflect the reuse decisions from research.md. Use these markers in task descriptions:

**Task Type Markers**:
- `[REUSE]` - Use existing component as-is (just wire it up)
- `[EXTEND]` - Add capabilities to existing component
- `[REFACTOR]` - Modify existing component for broader use
- `[NEW]` - Create new component (must be justified in research.md)

**Examples**:

- ✅ `- [ ] T005 [P] [US1] [REUSE] Wire existing AuthService for user validation`
- ✅ `- [ ] T008 [US2] [EXTEND] Add export method to existing ReportService in src/services/report.py`
- ✅ `- [ ] T012 [US3] [REFACTOR] Generalize NotificationService to support SMS in src/services/notification.py`
- ✅ `- [ ] T015 [P] [US4] [NEW] Create PaymentGateway integration in src/services/payment.py`

**Reuse Task Requirements**:

1. **For [REUSE] tasks**:
   - Reference the existing component path
   - Describe how to integrate/wire it
   - No new file creation needed

2. **For [EXTEND] tasks**:
   - Reference the existing component to extend
   - Describe the new capability to add
   - Specify the extension approach (new method, parameter, etc.)

3. **For [REFACTOR] tasks**:
   - Reference the existing component to refactor
   - Describe the refactoring goal
   - List what other code might be affected
   - Include task to update existing usages if needed

4. **For [NEW] tasks**:
   - Must reference research.md justification
   - Explain why existing code couldn't be used
   - Follow existing patterns from codebase

### Idea Technical Traceability (REQUIRED)

At the end of tasks.md, include a traceability section that maps each technical requirement from the source idea to specific tasks:

```markdown
## Idea Technical Traceability

**Source Idea**: [path to idea.md]

### Technical Requirements Mapping

| Idea Requirement | Task(s) | Status |
|------------------|---------|--------|
| [Command/tool/approach from idea] | T001, T005 | ✅ Mapped |
| [Execution order requirement] | T003 → T004 → T005 | ✅ Order preserved |
| [Specific library/version] | T002 | ✅ Mapped |

### Execution Order Preservation

If the idea specified a particular execution order:

```
Idea specified: Step A → Step B → Step C
Tasks implement: T003 (Step A) → T007 (Step B) → T012 (Step C)
Order preserved: ✅ Yes
```

### Divergences from Idea (if any)

| Idea Specified | Task Implements | Justification |
|----------------|-----------------|---------------|
| [original approach] | [different approach] | [documented reason from plan.md] |
```

**CRITICAL**: If any technical requirement from the idea is NOT mapped to a task:
1. Add the missing task(s)
2. Or document why it was intentionally omitted (with user confirmation)

### Reuse Traceability (REQUIRED)

After the Idea Technical Traceability section, include a reuse summary:

```markdown
## Reuse Traceability

**Source**: research.md (Existing Codebase Analysis)

### Reuse Summary

| Type | Count | Tasks |
|------|-------|-------|
| REUSE | X | T001, T005, ... |
| EXTEND | X | T008, T012, ... |
| REFACTOR | X | T015, ... |
| NEW | X | T020, T021, ... |

### Reuse Decisions

| Component | Decision | Task | Justification |
|-----------|----------|------|---------------|
| AuthService | REUSE | T005 | Existing auth fits requirements |
| ReportService | EXTEND | T008 | Add export capability |
| NotificationService | REFACTOR | T012 | Generalize for SMS support |
| PaymentGateway | NEW | T020 | No existing payment integration |

### New Code Justifications

For each [NEW] task, reference the research.md justification:

| Task | Component | Why Not Reuse? |
|------|-----------|----------------|
| T020 | PaymentGateway | No existing payment code; external API integration required |
```

**CRITICAL**:
- More [REUSE] and [EXTEND] tasks than [NEW] tasks indicates good code reuse
- Every [NEW] task must have explicit justification from research.md
- If ratio of [NEW] > 50%, reconsider if existing code was properly explored
