<!--
Sync Impact Report
==================
Version change: [INITIAL] → 1.0.0
Modified principles: N/A (initial version - Auror fork)
Added sections: All core sections (8 Principles, Development Workflow, Quality Standards, Governance)
Removed sections: None
Auror-specific adaptations:
  - Branch naming uses Linear ticket format (F-{TicketNumber}_{description})
  - Integration with Auror git workflow (CLAUDE.md conventions)
  - References to Auror-specific tooling and patterns
Templates requiring updates:
  ✅ .specify/templates/plan-template.md - Added detailed Constitution Check section with all 8 principles, updated branch format to F-{LinearTicket}-{description}
  ✅ .specify/templates/spec-template.md - Updated branch format to F-{LinearTicket}-{description}, added Auror convention note
  ✅ .specify/templates/tasks-template.md - Already aligned with user story independence principle (Principle III)
  ⚠ .claude/commands/*.md - Command files should reference constitution and Auror conventions (manual review recommended)
Follow-up TODOs:
  - Update branch creation scripts (.specify/scripts/bash/create-new-feature.sh) to accept Linear ticket IDs
  - Verify /speckit.specify command prompts for Linear ticket ID
  - Ensure consistency with parent CLAUDE.md git workflow rules (NEVER force push, commit format F-XXXXX description)
  - Add Linear ticket validation to branch creation workflow
  - Consider adding constitution reference to command prompt templates
-->

# Auror Spec-Kit Constitution

**Project Context**: This is an Auror-specific fork of Spec-Kit, adapted to integrate with Auror's engineering workflows including Linear ticket tracking and branch naming conventions.

## Core Principles

### I. Structured Workflow Automation

Every feature follows a defined workflow progression: Specify → Plan → Tasks → Implement. Each phase must complete successfully before proceeding to the next. Artifacts from each phase serve as inputs to subsequent phases, ensuring traceability and consistency.

**Rationale**: Structured workflows prevent incomplete specifications, reduce rework, and ensure LLM agents have sufficient context to generate quality outputs at each stage.

### II. Template-Driven Generation

All artifacts (specifications, plans, tasks, checklists) MUST be generated from templates located in `.specify/templates/`. Templates define required sections, formatting conventions, and validation criteria. Custom templates may be created but must follow the established template structure.

**Rationale**: Templates ensure consistency, completeness, and enable automated validation. They provide clear contracts for what each artifact should contain.

### III. User Story Independence

Features MUST be decomposed into independently testable user stories with explicit priorities (P1, P2, P3...). Each user story must deliver standalone value and be implementable without dependencies on other user stories (except shared foundational components). Tasks MUST be organized by user story to enable incremental delivery.

**Rationale**: Independent user stories enable true MVP delivery, parallel development, and flexible scope management. P1 stories can be delivered without waiting for P2/P3 completion.

### IV. Specification Quality Gates

Specifications MUST pass quality validation before proceeding to planning. Quality gates include:
- No more than 3 [NEEDS CLARIFICATION] markers (prioritized by scope > security > UX)
- All functional requirements are testable and unambiguous
- Success criteria are measurable and technology-agnostic
- All mandatory template sections are complete
- No implementation details (languages, frameworks, tools) leak into specifications

**Rationale**: High-quality specifications are prerequisites for effective planning and implementation. Catching ambiguities early prevents costly rework during implementation.

### V. Constitution Compliance Verification

Every planning phase MUST include a Constitution Check section that validates adherence to these principles. Violations must be explicitly justified with documented rationale explaining why the violation is necessary and what simpler alternatives were rejected.

**Rationale**: Explicit compliance checking prevents gradual erosion of project standards. Requiring justification for violations ensures complexity is intentional, not accidental.

### VI. Technology-Agnostic Requirements

Specifications and success criteria MUST be written without reference to specific technologies, frameworks, languages, or implementation approaches. Technical decisions belong in the planning phase (research.md, plan.md), not in feature specifications.

**Rationale**: Separating "what" from "how" keeps specifications focused on user value, enables technology changes without rewriting requirements, and makes specs accessible to non-technical stakeholders.

### VII. Auror Workflow Integration

All Spec-Kit workflows MUST integrate seamlessly with Auror's existing development practices:
- **Linear Tickets**: Feature branches use configurable Linear ticket prefixes (e.g., AFR-1234, ASR-42, F-XXXXX). Prefix is configured during `specify init` and stored in `.specify/config.json`. Different teams use different prefixes matching their Linear workspace.
- **Git Conventions**: Follow Auror's git workflow defined in parent `CLAUDE.md` (never force push, proper commit messages)
- **PR Labels**: Support Auror's PR labels (`ready for approach feedback`, `do not merge`, etc.)
- **Observability**: Generated code should align with Auror's observability standards (Honeycomb, Sumo Logic, Application Insights)
- **Testing Standards**: When tests are requested, follow Auror's xUnit + AutoFixture + FluentAssentials patterns

**Rationale**: Spec-Kit is a tool to enhance Auror's existing workflows, not replace them. Seamless integration ensures adoption and prevents friction. Configurable ticket prefixes enable multi-team usage within the same organization.

### VIII. Versioned Governance

This constitution follows semantic versioning (MAJOR.MINOR.PATCH):
- MAJOR: Backward-incompatible changes (principle removal/redefinition)
- MINOR: New principles, sections, or material expansions
- PATCH: Clarifications, wording improvements, non-semantic refinements

All amendments require documentation in the Sync Impact Report, approval from project maintainers, and verification that dependent templates remain consistent.

**Rationale**: Versioned governance makes constitutional evolution transparent and traceable. Teams can understand exactly what changed and when.

## Development Workflow

### Workflow Phases

1. **Specify** (`/speckit.specify`): Create feature specification from natural language description
   - Output: `specs/[###-feature-name]/spec.md`
   - Gates: Quality checklist validation, max 3 clarifications

2. **Plan** (`/speckit.plan`): Generate technical design and implementation plan
   - Prerequisites: Approved spec.md
   - Output: plan.md, research.md, data-model.md, contracts/, quickstart.md
   - Gates: Constitution Check, technical feasibility

3. **Tasks** (`/speckit.tasks`): Generate dependency-ordered, actionable task list
   - Prerequisites: plan.md, spec.md (required); data-model.md, contracts/ (optional)
   - Output: tasks.md organized by user story
   - Gates: All user stories have complete task coverage, independent test criteria defined

4. **Implement** (`/speckit.implement`): Execute tasks with progress tracking
   - Prerequisites: tasks.md
   - Process: Execute tasks in dependency order, mark complete as finished
   - Gates: All tasks complete, acceptance criteria met per user story

### Branch Management

- Feature branches use configurable Linear ticket convention: `{PREFIX}-{TicketNumber}-{description}` (e.g., `AFR-1234-add-user-auth`, `ASR-42-improve-detection`)
- Prefix is configured during `specify init` and stored in `.specify/config.json` (team-shared configuration)
- Branch numbers can be auto-incremented or explicitly specified for existing Linear tickets
- Commits follow format: `{PREFIX}-{TicketNumber} description` (e.g., `AFR-1234 add authentication endpoint`, `ASR-42 improve detection accuracy`)
- One feature per branch; branch created during `/speckit.specify` or via `.specify/scripts/bash/create-new-feature.sh`
- Legacy format `001-feature-name` is supported for backward compatibility (projects without `.specify/config.json`)
- Integration with Auror's existing git workflow (see parent `CLAUDE.md` for git rules)

### Clarification Process

- Specifications may include up to 3 [NEEDS CLARIFICATION] markers
- Use `/speckit.clarify` command to systematically resolve ambiguities
- Clarifications are presented as multiple-choice questions with suggested answers
- Resolved clarifications are encoded back into spec.md

## Quality Standards

### Artifact Completeness

All generated artifacts MUST:
- Follow the structure defined in corresponding templates
- Replace all placeholder tokens (no `[BRACKETED_TOKENS]` left unexplained)
- Include absolute file paths where relevant
- Be immediately actionable (no "TODO" or "TBD" without explicit justification)

### Task Format Requirements

Tasks in tasks.md MUST follow strict checklist format:
```
- [ ] [TaskID] [P?] [Story?] Description with exact file path
```

Where:
- `TaskID`: Sequential (T001, T002, T003...)
- `[P]`: Present only if parallelizable (different files, no dependencies)
- `[Story]`: Present for user story tasks ([US1], [US2], etc.)
- Description includes concrete file paths

### Testing Philosophy

Testing is OPTIONAL and context-dependent:
- If feature specification requests tests, generate test tasks using Test-First approach (tests written → fail → implement)
- If tests are not requested, omit test tasks from tasks.md
- When included, organize tests by user story alongside implementation tasks
- Integration and contract tests are preferred over unit tests for validating user-facing behavior

**Rationale**: Different projects have different testing needs. Spec-Kit does not mandate TDD but supports it when explicitly requested.

## Governance

### Amendment Process

1. Propose changes with clear rationale and impact analysis
2. Draft updated constitution with version bump (MAJOR/MINOR/PATCH)
3. Generate Sync Impact Report listing:
   - Modified principles
   - Added/removed sections
   - Templates requiring updates
   - Follow-up tasks
4. Update affected templates and verify consistency
5. Merge only after all dependent artifacts are synchronized

### Compliance Review

All PRs introducing new workflows, commands, or templates MUST:
- Reference relevant constitutional principles
- Include Constitution Check if adding planning phases
- Justify any principle violations with documented rationale
- Update constitution version if changing governance

### Living Document

This constitution is a living document that evolves with project needs. However, evolution must be:
- Deliberate (not accidental drift)
- Documented (Sync Impact Report)
- Versioned (semantic versioning)
- Consistent (templates updated in sync)

**Version**: 1.0.0 | **Ratified**: 2025-11-14 | **Last Amended**: 2025-11-14
