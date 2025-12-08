---
description: Execute the implementation planning workflow using the plan template to generate design artifacts.
handoffs:
  - label: Create Tasks
    agent: speckit.tasks
    prompt: Break the plan into tasks
    send: true
  - label: Create Checklist
    agent: speckit.checklist
    prompt: Create a checklist for the following domain...
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

The user input may specify:
- A specific domain to plan for (e.g., "Authentication", "Preview & Containers")
- A feature within a domain
- Cross-domain functionality that spans multiple domains

## Outline

1. **Setup**: Run `.specify/scripts/bash/setup-plan.sh --json` from repo root and parse JSON for FEATURE_SPEC, IMPL_PLAN, SPECS_DIR, BRANCH. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. **Load context**:
   - Read FEATURE_SPEC and `.specify/memory/constitution.md`
   - Load IMPL_PLAN template (already copied)
   - **Load domain context**: Check for `analysis/domains.md` in SPECS_DIR
   - If domains.md exists, parse domain boundaries and ownership

3. **Domain-aware planning**:
   - Identify which domain(s) the feature belongs to
   - Respect domain boundaries during design
   - Flag any cross-domain dependencies
   - Ensure contracts are defined for cross-domain interactions

4. **Execute plan workflow**: Follow the structure in IMPL_PLAN template to:
   - Fill Technical Context (mark unknowns as "NEEDS CLARIFICATION")
   - Fill Constitution Check section from constitution
   - **Fill Domain Context section** (if domains exist)
   - Evaluate gates (ERROR if violations unjustified)
   - Phase 0: Generate research.md (resolve all NEEDS CLARIFICATION)
   - Phase 1: Generate data-model.md, contracts/, quickstart.md
   - Phase 1: Update agent context by running the agent script
   - Re-evaluate Constitution Check post-design

5. **Stop and report**: Command ends after Phase 2 planning. Report branch, IMPL_PLAN path, domain assignments, and generated artifacts.

## Domain Context

### Loading Domain Information

If `{SPECS_DIR}/analysis/domains.md` exists:

1. **Parse domain inventory**:
   - Extract list of domains and their descriptions
   - Identify team ownership and dependencies
   - Map entity ownership to domains

2. **Identify target domain(s)**:
   - Analyze the feature spec to determine which domain(s) are affected
   - If feature spans multiple domains, list all affected domains
   - Identify the primary/owning domain

3. **Check domain contracts**:
   - For cross-domain features, identify required API contracts
   - Check existing contracts in `contracts/` directory
   - Flag missing contracts that need to be defined

### Domain Context Section (add to plan.md)

```markdown
## Domain Context

### Target Domain(s)

| Domain | Role | Impact Level |
|--------|------|--------------|
| [Primary Domain] | Owner | High |
| [Secondary Domain] | Consumer | Medium |

### Domain Boundaries

**This feature MUST respect the following boundaries:**

- Entities owned by [Domain]: [Entity list]
- Entities consumed from [Other Domain]: [Entity list] (read-only access)

### Cross-Domain Dependencies

| Dependency | Provider Domain | Contract Required |
|------------|-----------------|-------------------|
| [Capability] | [Domain] | [Yes/No - existing/new] |

### Team Coordination

| Team | Coordination Need |
|------|-------------------|
| [Team A] | [What needs to be coordinated] |
```

## Phases

### Phase 0: Outline & Research

1. **Extract unknowns from Technical Context** above:
   - For each NEEDS CLARIFICATION → research task
   - For each dependency → best practices task
   - For each integration → patterns task
   - **For each cross-domain dependency → contract research task**

2. **Generate and dispatch research agents**:

   ```text
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   For each cross-domain integration:
     Task: "Define contract for {source domain} → {target domain} integration"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]
   - **Domain impact**: [how this affects domain boundaries]

**Output**: research.md with all NEEDS CLARIFICATION resolved

### Phase 1: Design & Contracts

**Prerequisites:** `research.md` complete

1. **Extract entities from feature spec** → `data-model.md`:
   - Entity name, fields, relationships
   - **Domain ownership** (which domain owns this entity)
   - Validation rules from requirements
   - State transitions if applicable

2. **Generate API contracts** from functional requirements:
   - For each user action → endpoint
   - Use standard REST/GraphQL patterns
   - **Organize by domain** (group endpoints by owning domain)
   - **Define cross-domain contracts** (explicit interfaces between domains)
   - Output OpenAPI/GraphQL schema to `/contracts/`

3. **Domain-specific outputs**:
   - Group data model by domain in `data-model.md`
   - Create separate contract files per domain if needed
   - Document domain integration points

4. **Agent context update**:
   - Run `.specify/scripts/bash/update-agent-context.sh claude`
   - These scripts detect which AI agent is in use
   - Update the appropriate agent-specific context file
   - Add only new technology from current plan
   - Preserve manual additions between markers

**Output**: data-model.md (domain-organized), /contracts/* (domain-specific), quickstart.md, agent-specific file

### Phase 2: Domain Validation

**Prerequisites:** Phase 1 complete

1. **Validate domain boundaries**:
   - Ensure no entity is owned by multiple domains
   - Verify cross-domain access is through defined contracts
   - Check for unintended coupling

2. **Validate contracts**:
   - Each cross-domain dependency has a defined contract
   - Contracts specify data format, error handling, versioning
   - Consumer domains only depend on contract, not implementation

3. **Flag domain concerns**:
   - HIGH: New shared entity ownership → requires domain decision
   - HIGH: Missing cross-domain contract → must define before implementation
   - MEDIUM: Tight coupling detected → consider decoupling
   - LOW: Domain boundary unclear → document and continue

## Key Rules

- Use absolute paths
- ERROR on gate failures or unresolved clarifications
- **ERROR if cross-domain feature lacks required contracts**
- **WARN if domain boundaries are unclear** - flag for team review
- **Group all outputs by domain** when domains exist
- If no domains.md exists, proceed without domain context (legacy mode)

## Domain-Aware Output Structure

When domains are defined, organize outputs by domain:

```
specs/{feature}/
├── plan.md                      # Main plan with domain context
├── research.md                  # Research with domain impact notes
├── data-model.md                # Entities organized by domain
├── quickstart.md                # Setup guide
└── contracts/
    ├── {domain-1}-api.yaml      # Domain 1 API contract
    ├── {domain-2}-api.yaml      # Domain 2 API contract
    └── cross-domain/
        └── {domain-1}-to-{domain-2}.yaml  # Cross-domain contracts
```

## Example: Domain-Aware Planning

**Feature**: "Add iterative commits to GitHub Integration"

**Domain Analysis**:
- Primary Domain: GitHub Integration
- Secondary Domain: Projects (for file state)
- Cross-Domain Contract: GitHub Integration → Projects (read file contents)

**Domain Context Section**:
```markdown
## Domain Context

### Target Domain(s)

| Domain | Role | Impact Level |
|--------|------|--------------|
| GitHub Integration | Owner | High |
| Projects | Provider | Low |

### Domain Boundaries

**This feature MUST respect the following boundaries:**

- Entities owned by GitHub Integration: Project.github* fields
- Entities consumed from Projects: ProjectFile (read-only)

### Cross-Domain Dependencies

| Dependency | Provider Domain | Contract Required |
|------------|-----------------|-------------------|
| Get current file state | Projects | Yes - use existing `getProjectFiles()` |
| File change events | Chat (SSE) | Yes - subscribe to file_change events |

### Team Coordination

| Team | Coordination Need |
|------|-------------------|
| Integration Team | Primary implementation |
| Core Team | API contract review for file access |
```

## Report Format

At completion, report:

```markdown
## Planning Complete

**Branch**: {BRANCH}
**Plan Location**: {IMPL_PLAN path}

### Domain Summary

| Domain | Role | New Entities | New Contracts |
|--------|------|--------------|---------------|
| [Domain 1] | Owner | [count] | [count] |
| [Domain 2] | Consumer | [count] | [count] |

### Generated Artifacts

- [x] plan.md (with domain context)
- [x] research.md
- [x] data-model.md (domain-organized)
- [x] contracts/{domain}-api.yaml
- [x] contracts/cross-domain/*.yaml (if applicable)
- [x] quickstart.md

### Domain Concerns Flagged

- [HIGH/MEDIUM/LOW] [Concern description]

### Next Steps

1. Review domain context with team leads
2. Validate cross-domain contracts
3. Run `/speckit.tasks` to generate implementation tasks
```
