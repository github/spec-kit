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

## Flags

Parse the following flags from user input:

| Flag | Default | Description |
|------|---------|-------------|
| `--sequential` | false | Force single-agent mode (no subagents, current behavior) |

## Execution Mode Detection

**BEFORE starting planning**, determine execution mode:

1. Check if `--sequential` flag is present → **Sequential Mode**
2. Otherwise → **Parallel Mode** (default)

### Parallel Mode (default)

When `--sequential` is NOT set:

```
[speckit] Parallel mode: research and artifact generation
[speckit] Max concurrent subagents: unlimited
```

#### Phase 0: Parallel Research

For each NEEDS CLARIFICATION item in Technical Context, spawn a research subagent:
```
Task(
  subagent_type: "general-purpose",
  prompt: "Research {unknown} for {feature context}.

           Find:
           - Best practices
           - Common patterns
           - Recommended approaches

           Output format:
           - Decision: [what was chosen]
           - Rationale: [why chosen]
           - Alternatives considered: [what else evaluated]

           Write results to: .claude/workspace/results/research-{topic}-result.md",
  description: "plan:research-{topic}"
)
```

**Progress reporting**:
```
[████░░░░░░] 2/4 research tasks complete
  ✓ auth-patterns (5.2s) - OAuth2 recommended
  ✓ database-options (4.8s) - PostgreSQL selected
  ⏳ api-design...
  ⏳ caching-strategy...
```

After all research completes, consolidate into research.md.

#### Phase 1: Parallel Artifact Generation

Spawn subagents for independent artifacts:
```
Task(
  subagent_type: "general-purpose",
  prompt: "Generate {artifact} based on feature spec and research.

           Context:
           - spec: {spec_path}
           - research: {research_path}

           Write to: {artifact_path}",
  description: "plan:generate-{artifact}"
)
```

Artifacts that can run in parallel:
- data-model.md
- contracts/ (API schemas)
- quickstart.md

**Progress reporting**:
```
[██████░░░░] 2/3 artifacts complete
  ✓ data-model.md (8.1s)
  ✓ contracts/ (12.3s)
  ⏳ quickstart.md...
```

### Sequential Mode (fallback)

When `--sequential` is set:

```
[speckit] Sequential mode: single-agent execution
```

Proceed with current behavior (execute Phase 0 and Phase 1 sequentially in main agent).

## Outline

1. **Setup**: Run `{SCRIPT}` from repo root and parse JSON for FEATURE_SPEC, IMPL_PLAN, SPECS_DIR, BRANCH. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. **Load context**: Read FEATURE_SPEC and `/memory/constitution.md`. Load IMPL_PLAN template (already copied).

3. **Execute plan workflow**: Follow the structure in IMPL_PLAN template to:
   - Fill Technical Context (mark unknowns as "NEEDS CLARIFICATION")
   - Fill Constitution Check section from constitution
   - Evaluate gates (ERROR if violations unjustified)
   - Phase 0: Generate research.md (resolve all NEEDS CLARIFICATION)
   - Phase 1: Generate data-model.md, contracts/, quickstart.md
   - Phase 1: Update agent context by running the agent script
   - Re-evaluate Constitution Check post-design

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

## Key rules

- Use absolute paths
- ERROR on gate failures or unresolved clarifications
