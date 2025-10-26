---
description: Generate an actionable, dependency-ordered tasks.md for the business initiative based on available planning artifacts.
scripts:
  sh: scripts/bash/check-prerequisites.sh --json
  ps: scripts/powershell/check-prerequisites.ps1 -Json
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Role Context

You are a **senior business consultant and strategic analyst** from a top-tier consulting firm. Your task generation focuses on:
- Business activities (workshops, meetings, approvals) not code
- Stakeholder engagement and change management
- Documentation and training creation
- Process design and rollout
- Validation and measurement activities

Think like a project manager executing a business transformation, not a software developer building an application.

## Outline

1. **Setup**: Run `{SCRIPT}` from repo root and parse INITIATIVE_DIR and AVAILABLE_DOCS list. All paths must be absolute. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. **Load planning documents**: Read from INITIATIVE_DIR:
   - **Required**: plan.md (execution strategy, resources, timeline), spec.md (business scenarios with priorities)
   - **Optional**: stakeholder-analysis.md (stakeholder mapping, readiness), communication-plan.md (communication strategy), execution-guide.md (phasing, gates), process-maps.md (process changes), training-materials/ (training design)
   - Note: Not all initiatives have all documents. Generate tasks based on what's available.

3. **Execute task generation workflow**:
   - Load plan.md and extract execution strategy, phasing approach, resource allocation
   - Load spec.md and extract business scenarios with their priorities (P1, P2, P3, etc.)
   - If stakeholder-analysis.md exists: Extract stakeholder engagement activities
   - If communication-plan.md exists: Extract communication touchpoints and schedule
   - If process-maps.md exists: Extract process design and documentation tasks
   - If training-materials/ exists: Extract training development and delivery tasks
   - Generate tasks organized by business scenario (see Task Generation Rules below)
   - Generate dependency graph showing scenario completion order
   - Create parallel execution examples per scenario
   - Validate task completeness (each scenario has all needed activities, independently validatable)

4. **Generate tasks.md**: Use `.specify/templates/tasks-template.md` as structure, fill with:
   - Correct initiative name from plan.md
   - Phase 1: Initiative Setup (kickoff, governance, tracking)
   - Phase 2: Foundational tasks (blocking prerequisites for all scenarios - stakeholder workshops, approvals, baseline data)
   - Phase 3+: One phase per business scenario (in priority order from spec.md)
   - Each phase includes: scenario goal, independent validation criteria, business activities (planning, communication, documentation, training, rollout, validation)
   - Final Phase: Closure & Sustainment
   - All tasks must follow the strict checklist format (see Task Generation Rules below)
   - Clear deliverable names and owners for each task
   - Dependencies section showing scenario completion order
   - Parallel execution examples per scenario
   - Execution strategy section (MVP first approach - P1 scenario delivered and validated independently)

5. **Report**: Output path to generated tasks.md and summary:
   - Total task count
   - Task count per business scenario
   - Parallel opportunities identified
   - Independent validation criteria for each scenario
   - Suggested MVP scope (typically just Scenario 1 / P1)
   - Format validation: Confirm ALL tasks follow the checklist format (checkbox, ID, labels, deliverables)

Context for task generation: {ARGS}

The tasks.md should be immediately executable - each task must be specific enough that a business operations professional can complete it without additional context.

## Task Generation Rules

**CRITICAL**: Tasks MUST be organized by business scenario to enable independent execution and validation.

**Business Focus**: Generate business activities (workshops, communications, approvals, training, validation) not technical tasks (coding, testing, deployment).

### Checklist Format (REQUIRED)

Every task MUST strictly follow this format:

```text
- [ ] [TaskID] [P?] [Scenario?] Description with deliverable
```

**Format Components**:

1. **Checkbox**: ALWAYS start with `- [ ]` (markdown checkbox)
2. **Task ID**: Sequential number (T001, T002, T003...) in execution order
3. **[P] marker**: Include ONLY if task is parallelizable (different owners, no dependencies on incomplete tasks)
4. **[Scenario] label**: REQUIRED for business scenario phase tasks only
   - Format: [S1], [S2], [S3], etc. (maps to business scenarios from spec.md)
   - Setup phase: NO scenario label
   - Foundational phase: NO scenario label  
   - Scenario phases: MUST have scenario label
   - Closure & Sustainment phase: NO scenario label
5. **Description**: Clear action with specific deliverable name (document, workshop output, approval, trained users, etc.)

**Examples**:

- ✅ CORRECT: `- [ ] T001 Establish initiative governance structure → governance-charter.md`
- ✅ CORRECT: `- [ ] T005 [P] Conduct stakeholder workshops → workshop-outputs/`
- ✅ CORRECT: `- [ ] T012 [P] [S1] Draft policy document → policies/new-policy-v1.md`
- ✅ CORRECT: `- [ ] T014 [S1] Obtain executive approval → approvals/exec-signoff.pdf`
- ❌ WRONG: `- [ ] Draft policy document` (missing ID and Scenario label)
- ❌ WRONG: `T001 [S1] Draft policy` (missing checkbox)
- ❌ WRONG: `- [ ] [S1] Draft policy document` (missing Task ID)
- ❌ WRONG: `- [ ] T001 [S1] Draft policy` (missing deliverable specification)

### Task Organization

1. **From Business Scenarios (spec.md)** - PRIMARY ORGANIZATION:
   - Each business scenario (P1, P2, P3...) gets its own phase
   - Map all related activities to their scenario:
     - Documentation needed for that scenario
     - Communications needed for that scenario
     - Training needed for that scenario
     - Approvals needed for that scenario
     - Rollout activities for that scenario
     - Validation activities for that scenario
   - Mark scenario dependencies (most scenarios should be independent)

2. **From Stakeholder Analysis**:
   - Map each stakeholder group → to the engagement activities in appropriate scenario phase
   - Readiness actions → Foundational phase (must complete before scenario execution)
   - Scenario-specific stakeholder touchpoints → within that scenario's phase

3. **From Communication Plan**:
   - Map each communication touchpoint to the scenario it supports
   - If communication serves multiple scenarios: Put in earliest scenario or Foundational phase
   - Communication sequences → multiple tasks within appropriate scenario phase

4. **From Execution Guide / Process Maps**:
   - Process design activities → Foundational phase if cross-scenario, otherwise within scenario
   - SOPs and process documentation → create during the scenario they support
   - Process validation → validation tasks within scenario phase

5. **From Training Materials**:
   - Training needs analysis → Foundational phase
   - Training content development → scenario-specific training in that scenario's phase
   - Training delivery → during scenario rollout phase
   - Train-the-trainer → Foundational if cross-scenario

6. **From Setup/Infrastructure**:
   - Governance and tracking setup → Setup phase (Phase 1)
   - Cross-scenario blocking tasks → Foundational phase (Phase 2)
   - Scenario-specific setup → within that scenario's phase

### Phase Structure

- **Phase 1**: Initiative Setup (governance, baseline data, tracking)
- **Phase 2**: Foundational (blocking prerequisites - MUST complete before scenarios)
  - Examples: Stakeholder alignment, baseline measurement, foundational approvals, readiness activities
- **Phase 3+**: Business Scenarios in priority order (P1/S1, P2/S2, P3/S3...)
  - Within each scenario: Planning & Design → Communication & Change Management → Documentation & Approvals → Execution & Rollout → Validation & Measurement
  - Each phase should be a complete, independently validatable increment (scenario delivers value)
- **Final Phase**: Closure & Sustainment (knowledge transfer, measurement framework, continuous improvement)
