---
description: Execute the implementation planning workflow using the plan template to generate design artifacts.
scripts:
  sh: scripts/bash/setup-plan.sh --json
  ps: scripts/powershell/setup-plan.ps1 -Json
agent_scripts:
  sh: "scripts/bash/update-agent-context.sh __AGENT__; python3 -c \"from pathlib import Path; from specify_cli.guards.types import GuardType; import json; guards_base = Path('.specify/guards'); print('\\n=== AVAILABLE GUARD TYPES ==='); [print(f\\\"{t['name']} ({t['category']}) [{t['source']}]: {t['when_to_use']}\\\") for t in GuardType.get_all_types_with_descriptions(guards_base)]\""
  ps: "scripts/powershell/update-agent-context.ps1 -AgentType __AGENT__; python -c \"from pathlib import Path; from specify_cli.guards.types import GuardType; import json; guards_base = Path('.specify/guards'); print('\\n=== AVAILABLE GUARD TYPES ==='); [print(f\\\"{t['name']} ({t['category']}) [{t['source']}]: {t['when_to_use']}\\\") for t in GuardType.get_all_types_with_descriptions(guards_base)]\""
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

1. **Setup**: Run `{SCRIPT}` from repo root and parse JSON for FEATURE_SPEC, IMPL_PLAN, SPECS_DIR, BRANCH. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. **Load context**: Read FEATURE_SPEC and `/memory/constitution.md`. Load IMPL_PLAN template (already copied). **Run {AGENT_SCRIPT} to load guard types and agent context.**

3. **Identify validation requirements** (MANDATORY):
   - Scan feature spec for validation checkpoints (APIs, data models, workflows, business logic, quality standards)
   - For EACH validation checkpoint, determine appropriate guard type:
     * **API endpoints** → `api` guard type
     * **Database/data models** → Create custom `database` or `data-validation` guard type
     * **UI/user workflows** → Create custom `e2e` or `workflow` guard type  
     * **Business logic/algorithms** → `unit-pytest` guard type
     * **Code quality/standards** → Create custom `lint` or `quality` guard type
   - **If no existing guard type matches**: Document need for custom guard type creation
   - Add "Guard Validation Strategy" section to plan.md documenting:
     ```markdown
     ## Guard Validation Strategy
     
     | Validation Checkpoint | Guard Type | Rationale |
     |----------------------|------------|-----------|
     | User auth API        | api        | REST endpoint contract validation |
     | Payment processing   | unit-pytest | Complex business logic |
     | Checkout flow        | [CUSTOM: e2e-checkout] | Multi-step user workflow (create in /tasks) |
     | Code style          | [CUSTOM: lint-project] | Project-specific linting rules (create in /tasks) |
     ```

4. **Execute plan workflow**: Follow the structure in IMPL_PLAN template to:
   - Fill Technical Context (mark unknowns as "NEEDS CLARIFICATION")
   - Fill Constitution Check section from constitution
   - **Add Guard Validation Strategy section** (from step 3 above)
   - Evaluate gates (ERROR if violations unjustified)
   - Phase 0: Generate research.md (resolve all NEEDS CLARIFICATION)
   - Phase 1: Generate data-model.md, contracts/, quickstart.md
   - Phase 1: Update agent context by running the agent script
   - Re-evaluate Constitution Check post-design

5. **Stop and report**: Command ends after Phase 2 planning. Report branch, IMPL_PLAN path, and generated artifacts.

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

