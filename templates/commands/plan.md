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

3. **Load source idea (CRITICAL)**: Extract the SOURCE IDEA from spec.md header or locate it:
   - Check spec.md for `**Source**:` or `**Parent Idea**:` links
   - If found, load the linked idea.md file
   - If not found, search `ideas/` directory for matching idea by feature name
   - Extract **Technical Hints** section from idea (if present)
   - Extract any technical details from:
     - "Constraints & Assumptions" → technical constraints
     - "Discovery Notes" → technical decisions made during exploration
     - Feature files → "Technical Hints" or "Notes" sections
   - Store these as IDEA_TECHNICAL_CONSTRAINTS for validation in step 5

4. **Execute plan workflow**: Follow the structure in IMPL_PLAN template to:
   - Fill Technical Context (mark unknowns as "NEEDS CLARIFICATION")
   - Fill Constitution Check section from constitution
   - Evaluate gates (ERROR if violations unjustified)
   - Phase 0: Generate research.md (resolve all NEEDS CLARIFICATION)
   - Phase 1: Generate data-model.md, contracts/, quickstart.md
   - Phase 1: Update agent context by running the agent script
   - Re-evaluate Constitution Check post-design

5. **Validate alignment with source idea (CRITICAL)**:

   Before finalizing, verify that the plan respects IDEA_TECHNICAL_CONSTRAINTS:

   a. **Extract technical requirements from idea**:
      - Commands or scripts that must be executed
      - Specific tools, libraries, or versions mentioned
      - Execution order or sequencing requirements
      - Technical patterns or approaches specified
      - Integration points with specific instructions

   b. **Cross-check with plan.md**:
      - For each technical constraint in the idea:
        - ✅ ALIGNED: Plan explicitly addresses it
        - ⚠️ DIVERGENT: Plan uses different approach → requires justification
        - ❌ MISSING: Plan doesn't address it → add to plan

   c. **Create alignment report** in plan.md:

      ```markdown
      ## Idea Technical Alignment

      **Source Idea**: [path to idea.md]

      ### Technical Constraints from Idea

      | Constraint | Status | Plan Reference |
      |------------|--------|----------------|
      | [constraint from idea] | ✅/⚠️/❌ | [section in plan] |

      ### Divergences (if any)

      | Idea Specified | Plan Proposes | Justification |
      |----------------|---------------|---------------|
      | [original] | [different approach] | [why change is better] |
      ```

   d. **STOP and report if critical divergences**:
      - If plan contradicts explicit technical instructions from idea
      - Ask user to confirm before proceeding
      - Document the decision in research.md

6. **Stop and report**: Command ends after Phase 2 planning. Report branch, IMPL_PLAN path, generated artifacts, and **alignment status with source idea**.

## Phases

### Phase 0: Outline & Research

1. **Extract unknowns from Technical Context** above:
   - For each NEEDS CLARIFICATION → research task
   - For each dependency → best practices task
   - For each integration → patterns task

2. **Generate and dispatch research agents**:

   ```text
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
