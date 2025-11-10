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

2. **Load context**: Read FEATURE_SPEC and `/memory/constitution.md`. Load IMPL_PLAN template (already copied).

3. **Execute plan workflow**: Follow the structure in IMPL_PLAN template to:
   - Fill Technical Context (mark unknowns as "NEEDS CLARIFICATION")
   - Fill Constitution Check section from constitution
   - Evaluate gates (ERROR if violations unjustified)
   - Phase 0: Resolve all NEEDS CLARIFICATION and document decisions in Technical Analysis section
   - Phase 1: Design data model and API contracts inline in plan.md sections
   - Phase 1: Update agent context by running the agent script
   - Re-evaluate Constitution Check post-design

4. **Stop and report**: Command ends after Phase 1 planning. Report branch, IMPL_PLAN path. All design details are documented inline in plan.md.

## Phases

### Phase 0: Technical Analysis & Decisions

1. **Extract unknowns from Technical Context** above:
   - For each NEEDS CLARIFICATION → research and make decision
   - For each dependency → identify best practices
   - For each integration → document patterns

2. **Research and resolve unknowns**:

   ```text
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   ```

3. **Document findings directly in plan.md**:
   - Add to "Technical Analysis" section
   - Document each decision with:
     - Decision: [what was chosen]
     - Rationale: [why chosen]
     - Alternatives considered: [what else evaluated]

**Output**: All technical decisions documented inline in plan.md

### Phase 1: Design & Architecture

**Prerequisites:** All technical decisions documented in Technical Analysis section

1. **Extract entities from feature spec** → Document in plan.md:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable
   - Add to appropriate sections in plan.md

2. **Generate API contracts** from functional requirements → Document in plan.md:
   - For each user action → endpoint
   - Use standard REST/GraphQL patterns
   - Document API interfaces and type definitions
   - Include OpenAPI/GraphQL schema inline if needed

3. **Document integration scenarios** → Add to plan.md:
   - Test scenarios from user stories
   - Integration paths and dependencies
   - End-to-end test cases

4. **Agent context update**:
   - Run `{AGENT_SCRIPT}`
   - These scripts detect which AI agent is in use
   - Update the appropriate agent-specific context file
   - Add only new technology from current plan
   - Preserve manual additions between markers

**Output**: Complete plan.md with all design details (data model, API contracts, test scenarios) documented inline

## Key rules

- Use absolute paths
- ERROR on gate failures or unresolved clarifications
