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

## Memory Provider Detection

Before loading constitution:
1. Check for `.specify/config.json` in repo root
2. Parse JSON and read `memory.provider`:
   - If `"hindsight"`: Use Hindsight MCP tools with `bank_id` from `memory.hindsight.bank_id`
   - If `"local"` or config missing: Use `/memory/constitution.md` file
3. If Hindsight configured but MCP tools unavailable: Warn user and fallback to local file

## Outline

1. **Setup**: Run `{SCRIPT}` from repo root and parse JSON for FEATURE_SPEC, IMPL_PLAN, SPECS_DIR, BRANCH. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. **Load context**: Read FEATURE_SPEC. Load IMPL_PLAN template (already copied). For constitution:

   **Hindsight Mode** (when `memory.provider == "hindsight"`):
   ```
   mcp__hindsight__recall(
     query: "constitution principles MUST SHOULD requirements governance",
     bank_id: {bank_id from config}
   )
   ```

   **Local Mode** (default):
   Read `/memory/constitution.md` directly.

   **Fallback**: If Hindsight unavailable, try local file. Warn if both fail.

3. **Execute plan workflow**: Follow the structure in IMPL_PLAN template to:
   - Fill Technical Context (mark unknowns as "NEEDS CLARIFICATION")
   - Fill Constitution Check section from constitution
   - Evaluate gates (ERROR if violations unjustified)
   - Phase 0: Generate research.md (resolve all NEEDS CLARIFICATION)
   - Phase 1: Generate data-model.md, contracts/, quickstart.md
   - Phase 1: Update agent context by running the agent script
   - Re-evaluate Constitution Check post-design

   **Hindsight Mode - Constitution Validation** (optional, when `memory.provider == "hindsight"`):
   For deeper Constitution Check validation, use `mcp__hindsight__reflect`:
   ```
   mcp__hindsight__reflect(
     query: "Do these technical choices violate any project principles? Choices: {list of tech stack decisions}",
     context: "Constitution compliance check for {feature name}",
     budget: "mid",
     bank_id: {bank_id from config}
   )
   ```
   This provides reasoned analysis beyond simple fact retrieval.

4. **Stop and report**: Command ends after Phase 2 planning. Report branch, IMPL_PLAN path, and generated artifacts.

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

### Phase 1: Hindsight Memory (when `memory.provider == "hindsight"`)

After completing Phase 1, store tech stack decisions in Hindsight for cross-project learning:

```
mcp__hindsight__retain(
  content: "Tech Stack for {feature name}:\n- Languages: {languages}\n- Frameworks: {frameworks}\n- Database: {database}\n- Key libraries: {libraries}\n- Architecture: {patterns used}\n\nRationale: {why these choices}",
  context: "project-tech-stack",
  bank_id: {bank_id from config}
)
```

This enables future `/speckit.plan` commands to recall relevant technology choices.

## Key rules

- Use absolute paths
- ERROR on gate failures or unresolved clarifications
