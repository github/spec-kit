---
description: Execute the implementation planning workflow using the plan template to generate design artifacts.
scripts:
  sh: scripts/bash/setup-plan.sh --json
  ps: scripts/powershell/setup-plan.ps1 -Json
agent_scripts:
  sh: scripts/bash/update-agent-context.sh __AGENT__
  ps: scripts/powershell/update-agent-context.ps1 -AgentType __AGENT__
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

1. **Setup**: Run `{SCRIPT}` from repo root and parse JSON for FEATURE_SPEC, IMPL_PLAN, SPECS_DIR, BRANCH. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. **Detect brownfield mode** (optional):
   - Check if working in existing codebase with established patterns
   - Indicators: Large codebase (>20 files), existing architecture, team conventions
   - If brownfield context detected, analyze existing patterns BEFORE planning

3. **Load context**: Read FEATURE_SPEC and `/memory/constitution.md`. Load IMPL_PLAN template (already copied).

4. **Execute plan workflow**: Follow the structure in IMPL_PLAN template to:
   - Fill Technical Context (mark unknowns as "NEEDS CLARIFICATION")
   - Fill Constitution Check section from constitution
   - Evaluate gates (ERROR if violations unjustified)
   - Phase 0: Generate research.md (resolve all NEEDS CLARIFICATION)
   - Phase 1: Generate data-model.md, contracts/, quickstart.md
   - Phase 1: Update agent context by running the agent script
   - Re-evaluate Constitution Check post-design

5. **Stop and report**: Command ends after Phase 2 planning. Report branch, IMPL_PLAN path, and generated artifacts.

## Brownfield Analysis (Optional)

**When to use**: If implementing features in an existing codebase with established patterns.

**Skip if**: Greenfield (0→1) development or new project.

### Pattern Discovery Process

1. **Check for existing codebase**:
   - Count files in repository: `find . -type f -name "*.js" -o -name "*.py" -o -name "*.go" | wc -l`
   - If > 20 files and existing architecture detected, proceed with brownfield analysis
   - If < 20 files, skip to Phase 0 (greenfield mode)

2. **Discover existing patterns** (use Grep/Glob tools):
   - **Architecture patterns**: Find similar feature implementations
   - **Coding conventions**: Naming standards for files, functions, classes
   - **Testing patterns**: Test framework, structure, common patterns
   - **Integration points**: How new features are typically added

3. **Document discovered constraints** in research.md:
   ```markdown
   ## Brownfield Constraints (Existing Codebase Patterns)

   ### Architecture Patterns Discovered
   - Services pattern: `src/services/*.service.ts`
   - Repository pattern: `src/repositories/*.repository.ts`

   ### Naming Conventions
   - File naming: kebab-case (e.g., `user-service.ts`)
   - Function naming: camelCase with verb prefix (e.g., `getUserById`)

   ### Testing Requirements
   - Framework: Jest with React Testing Library
   - Test location: `__tests__/` adjacent to source
   - Coverage requirement: 80% (from existing config)

   ### Integration Points
   - New routes registered in: `src/routes/index.ts`
   - Services wired in: `src/di/container.ts`
   ```

4. **Feed constraints into plan**:
   - Reference discovered patterns in Technical Context
   - Ensure plan follows existing conventions
   - Document any necessary deviations with justification

## Phases

### Phase 0: Outline & Research

1. **Extract unknowns from Technical Context** above:
   - For each NEEDS CLARIFICATION → research task
   - For each dependency → best practices task
   - For each integration → patterns task

2. **Generate and dispatch research agents**:
   ```
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

### Phase 1: Design & Contracts

**Prerequisites:** `research.md` complete

1. **Extract entities from feature spec** → `data-model.md`:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable

2. **Generate API contracts** from functional requirements:
   - For each user action → endpoint
   - Use standard REST/GraphQL patterns
   - Output OpenAPI/GraphQL schema to `/contracts/`

3. **Agent context update**:
   - Run `{AGENT_SCRIPT}`
   - These scripts detect which AI agent is in use
   - Update the appropriate agent-specific context file
   - Add only new technology from current plan
   - Preserve manual additions between markers

**Output**: data-model.md, /contracts/*, quickstart.md, agent-specific file

## Key rules

- Use absolute paths
- ERROR on gate failures or unresolved clarifications

