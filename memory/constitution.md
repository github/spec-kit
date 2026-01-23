<!--
Sync Impact Report
==================
Version change: 0.0.0 → 1.0.0 (initial ratification)
Modified principles: N/A (new constitution)
Added sections:
  - Core Principles (5 principles)
  - Development Workflow
  - Quality Standards
  - Governance
Removed sections: None (template placeholders replaced)
Templates requiring updates:
  ✅ templates/plan-template.md - Constitution Check section aligns with principles
  ✅ templates/spec-template.md - User scenarios align with Specification-First principle
  ✅ templates/tasks-template.md - Phase structure supports iterative development
  ✅ templates/commands/*.md - Generic agent references, no updates needed
  ✅ docs/quickstart.md - Workflow aligns with constitution principles
Follow-up TODOs: None
-->

# Spec Kit Constitution

## Core Principles

### I. Specification-First

All development MUST begin with a clear, complete specification before implementation starts.

- Specifications are the **primary artifact**; code is the generated expression of specifications
- Every feature MUST have a written specification (`spec.md`) that defines:
  - User scenarios with prioritized acceptance criteria
  - Functional requirements using MUST/SHOULD/MAY language
  - Edge cases and error handling expectations
- Implementation plans MUST trace back to specification requirements
- No code changes without corresponding specification updates

**Rationale**: Specifications eliminate the gap between intent and implementation by making
requirements explicit, testable, and version-controlled.

### II. Intent-Driven Development

Development MUST express the team's intent in natural language before translating to code.

- User stories MUST describe the **what** and **why**, not the **how**
- Technical decisions MUST have documented rationale linked to requirements
- The specification serves as the **lingua franca** between stakeholders and implementers
- AI-assisted generation MUST preserve and reference original intent

**Rationale**: Natural language specifications enable broader collaboration, easier pivots,
and clearer communication of purpose across technical and non-technical stakeholders.

### III. Iterative Refinement

Specifications and implementations MUST evolve through continuous refinement cycles.

- Use `/speckit.clarify` to identify and resolve ambiguities before planning
- Use `/speckit.analyze` to validate plans against specifications
- Production feedback MUST inform specification updates for future iterations
- Breaking changes require specification review and version increment

**Rationale**: Software quality improves through iteration. Early ambiguity resolution
prevents costly rework during implementation.

### IV. Traceable Artifacts

Every artifact MUST maintain clear traceability to its source and dependents.

- Implementation plans MUST reference their source specification
- Tasks MUST reference their parent user story (e.g., `[US1]`, `[US2]`)
- Code changes MUST link to their originating task
- Test scenarios MUST map to acceptance criteria in the specification

**Rationale**: Traceability enables impact analysis, simplifies debugging, and ensures
changes propagate correctly through the development chain.

### V. Agent-Agnostic Design

All templates, commands, and workflows MUST work across supported AI agents.

- Command files MUST use generic placeholders (e.g., `$ARGUMENTS`) not agent-specific syntax
- Documentation MUST NOT assume a specific AI assistant
- Scripts MUST support both Bash (`.sh`) and PowerShell (`.ps1`) variants
- New agent integrations MUST follow the patterns documented in `AGENTS.md`

**Rationale**: Teams should choose their preferred AI tools without being locked into
a specific vendor or workflow.

## Development Workflow

All Spec Kit development MUST follow this workflow:

1. **Constitution** → Establish or review project principles (`/speckit.constitution`)
2. **Specification** → Define what to build and why (`/speckit.specify`)
3. **Clarification** → Resolve ambiguities (`/speckit.clarify`)
4. **Planning** → Create technical implementation plan (`/speckit.plan`)
5. **Analysis** → Validate plan against specification (`/speckit.analyze`)
6. **Tasking** → Break down into actionable tasks (`/speckit.tasks`)
7. **Implementation** → Execute tasks per plan (`/speckit.implement`)

Skipping phases is permitted only when explicitly documented and justified.

## Quality Standards

- **Specifications**: MUST use MUST/SHOULD/MAY language per RFC 2119
- **User Stories**: MUST be independently testable and deliverable as MVP increments
- **Acceptance Criteria**: MUST follow Given/When/Then format
- **Code Changes**: MUST include updated documentation when behavior changes
- **CLI Changes**: MUST update `CHANGELOG.md` and increment version in `pyproject.toml`

## Governance

This constitution supersedes all other development practices for Spec Kit.

**Amendment Process**:

1. Propose changes via pull request with rationale
2. Update constitution version following semantic versioning:
   - **MAJOR**: Principle removals or incompatible redefinitions
   - **MINOR**: New principles or materially expanded guidance
   - **PATCH**: Clarifications, wording, or non-semantic refinements
3. Validate consistency with dependent templates
4. Obtain maintainer approval before merging

**Compliance**:

- All pull requests MUST verify alignment with constitution principles
- Deviations MUST be explicitly justified in the PR description
- Use `docs/quickstart.md` and `spec-driven.md` for runtime development guidance

**Version**: 1.0.0 | **Ratified**: 2026-01-23 | **Last Amended**: 2026-01-23
