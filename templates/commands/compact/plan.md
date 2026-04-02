---
description: Execute implementation planning workflow to generate design artifacts.
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

## Input

```text
$ARGUMENTS
```

Consider user input before proceeding (if not empty).

## Pre-Execution

Check `.specify/extensions.yml` for `hooks.before_plan`. Run mandatory hooks, show optional. Skip silently if missing/invalid.

## Workflow

1. **Setup**: Run `{SCRIPT}` from repo root, parse JSON for FEATURE_SPEC, IMPL_PLAN, SPECS_DIR, BRANCH.

2. **Load context**: Read FEATURE_SPEC and `/memory/constitution.md`. Load IMPL_PLAN template.

3. **Execute plan**:
   - Fill Technical Context (mark unknowns as "NEEDS CLARIFICATION")
   - Fill Constitution Check from constitution, evaluate gates (ERROR if violations unjustified)
   - Phase 0: Generate research.md (resolve all NEEDS CLARIFICATION)
   - Phase 1: Generate data-model.md, contracts/, quickstart.md
   - Run `{AGENT_SCRIPT}` to update agent context
   - Re-evaluate Constitution Check post-design

4. **Report**: Branch, IMPL_PLAN path, generated artifacts.

5. Check `.specify/extensions.yml` for `hooks.after_plan`. Run mandatory, show optional. Skip silently if missing.

## Phases

### Phase 0: Research

For each unknown in Technical Context → research task. Consolidate in research.md: Decision, Rationale, Alternatives.

### Phase 1: Design & Contracts

Prereqs: research.md complete.
- Extract entities → data-model.md
- Define interface contracts → /contracts/ (skip if purely internal)
- Run `{AGENT_SCRIPT}` for agent context update

## Rules

- Use absolute paths
- ERROR on gate failures or unresolved clarifications
