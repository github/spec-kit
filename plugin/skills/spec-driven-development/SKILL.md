---
name: spec-driven-development
description: |
  Spec-Driven Development (SDD) methodology guidance. Use this skill when:
  - User mentions "spec-kit", "speckit", "SDD", "spec-driven", or "specification-first"
  - User asks about writing specifications, feature planning, or systematic development
  - User wants to implement a feature following a structured workflow
  - User needs help with PRDs, technical plans, or task breakdowns
  - Project has a `.specify/` directory structure
version: 1.0.0
---

# Spec-Driven Development (SDD)

Spec-Driven Development is a methodology where **specifications become the primary source of truth** that directly generates working implementations. Code serves specifications, not the other way around.

## Core Philosophy

Traditional development: Specs -> Code (specs get outdated)
SDD approach: Specs -> Plans -> Tasks -> Code (specs remain source of truth)

## The SDD Workflow

The spec-kit plugin provides 8 commands that form a complete development workflow:

### 1. `/speckit:constitution` - Establish Project Principles
- Creates/updates `.specify/memory/constitution.md`
- Defines non-negotiable project principles
- All downstream artifacts must align with the constitution

### 2. `/speckit:specify` - Generate Feature Specification
- Takes a natural language feature description
- Creates a structured PRD in `.specify/specs/[feature]/spec.md`
- Focuses on WHAT and WHY (not HOW)
- Generates user stories, requirements, and success criteria
- Creates feature branch automatically

### 3. `/speckit:clarify` - Resolve Ambiguities (Optional)
- Asks up to 5 targeted clarification questions
- Reduces ambiguity before planning
- Records answers directly in the spec

### 4. `/speckit:plan` - Create Implementation Plan
- Generates technical plan with architecture decisions
- Creates supporting artifacts:
  - `research.md` - Technology decisions
  - `data-model.md` - Entity definitions
  - `contracts/` - API specifications
  - `quickstart.md` - Validation scenarios

### 5. `/speckit:tasks` - Break Down Into Tasks
- Generates actionable, dependency-ordered tasks
- Organizes by user story for independent implementation
- Uses strict checklist format with IDs and file paths
- Marks parallelizable tasks with [P]

### 6. `/speckit:analyze` - Consistency Analysis (Optional)
- Cross-artifact consistency check
- Validates spec/plan/tasks alignment
- Identifies gaps, duplications, ambiguities
- Read-only - produces analysis report

### 7. `/speckit:checklist` - Generate Quality Checklists
- Creates "unit tests for requirements"
- Validates requirement quality (not implementation)
- Categories: completeness, clarity, consistency, coverage

### 8. `/speckit:implement` - Execute Implementation
- Processes tasks in order
- Validates checklists before starting
- Marks tasks complete as they're done
- Creates necessary ignore files

### 9. `/speckit:taskstoissues` - Create GitHub Issues
- Converts tasks to GitHub issues
- Respects repository remote URL

## Project Structure

Projects using spec-kit have this structure:

```
project/
├── .specify/
│   ├── memory/
│   │   └── constitution.md     # Project principles
│   ├── scripts/
│   │   ├── bash/               # Bash helper scripts
│   │   └── powershell/         # PowerShell helper scripts
│   ├── templates/
│   │   ├── spec-template.md
│   │   ├── plan-template.md
│   │   ├── tasks-template.md
│   │   └── checklist-template.md
│   └── specs/
│       └── 001-feature-name/
│           ├── spec.md         # Feature specification
│           ├── plan.md         # Implementation plan
│           ├── tasks.md        # Task breakdown
│           ├── data-model.md   # Data schemas
│           ├── research.md     # Tech decisions
│           ├── contracts/      # API specs
│           └── checklists/     # Quality checklists
└── CLAUDE.md                   # Agent guidance
```

## Key Principles

### Specifications Focus on WHAT, Not HOW
- No technology/framework mentions in specs
- Written for business stakeholders
- Success criteria are measurable and technology-agnostic

### Tasks Are Immediately Executable
- Each task has an ID (T001, T002...)
- Includes exact file paths
- Parallelizable tasks marked with [P]
- Story labels link to user stories [US1], [US2]

### Checklists Validate Requirements, Not Implementation
- Question format: "Is X specified?" not "Does X work?"
- Focus on completeness, clarity, consistency
- Include traceability to spec sections

### Constitution is Non-Negotiable
- All artifacts must align with constitution principles
- Constitution violations are always CRITICAL
- Changes require explicit constitution update

## Detecting SDD Projects

A project uses spec-kit if it has:
- `.specify/` directory at the project root
- `.specify/memory/constitution.md`
- `.specify/templates/` with spec/plan/task templates
- Feature specs in `.specify/specs/[NNN-feature-name]/`

## Recommended Workflow

For new features:
1. `/speckit:constitution` (once per project)
2. `/speckit:specify <feature description>`
3. `/speckit:clarify` (optional but recommended)
4. `/speckit:plan <tech stack>`
5. `/speckit:tasks`
6. `/speckit:analyze` (optional quality check)
7. `/speckit:checklist <domain>` (as needed)
8. `/speckit:implement`

## Best Practices

1. **Keep specs focused**: One feature per specification
2. **Be specific in success criteria**: Use measurable outcomes
3. **Document assumptions**: Record reasonable defaults
4. **Limit clarifications**: Max 3 NEEDS CLARIFICATION markers
5. **Organize by user story**: Tasks should enable independent testing
6. **Mark parallel tasks**: Use [P] for tasks that can run concurrently
7. **Validate before implementing**: Run analyze and checklists first
