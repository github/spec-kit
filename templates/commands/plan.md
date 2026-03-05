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

2. **Artifact reuse and token discipline**:
   - If an artifact was already loaded earlier in this conversation and has not changed (same path and newer content not detected), reuse prior extracted context instead of re-reading the full file.
   - Re-read a full artifact only when required (file changed, first access, or current phase needs sections not yet extracted).
   - Prefer targeted section reads over whole-file reads.
   - Keep status updates concise; avoid repetitive "re-confirm/re-load" narration for unchanged artifacts.

3. **Load context**: Read FEATURE_SPEC and `/memory/constitution.md`. Load IMPL_PLAN template (already copied). Also discover formal workflow artifacts using this precedence:
   - PRD: `SPECS_DIR/prd.md`, then `docs/PRD/<feature-prefix>-*.md`
   - AR: `SPECS_DIR/ar.md`, then `docs/AR/<feature-prefix>-*.md`
   - SEC: `SPECS_DIR/sec.md`, then `docs/SEC/<feature-prefix>-*.md`
   - If PRD exists: Read it as enriched requirements source (MoSCoW requirements, prioritized user stories, technical constraints). Use alongside or in preference to spec.md for requirements extraction.
   - If AR exists: Read it for architecture decisions, component design, and technical constraints. Incorporate selected option and implementation guardrails into the plan.
   - If SEC exists: Read it for security requirements (SEC-* IDs), trust boundaries, and data classifications. Incorporate security tasks into the plan.

4. **Mode + Risk Gate** (read execution mode and risk triggers before artifact generation):

   a. Determine the execution mode and risk trigger state. **Preferred**: run `scripts/bash/check-prerequisites.sh --json` to obtain `EXECUTION_MODE`, `HAS_RISK_TRIGGERS`, and `RISK_TRIGGERS` from the authoritative shell functions. **Fallback** (if script unavailable): read manually:
      - Read `EXECUTION_MODE` from `SPECS_DIR/.feature-config.json` (key: `mode`), falling back to project default (`defaultMode` in `.specify/config.json`), then to `"balanced"` if neither exists
      - **Backward compatibility**: If `.feature-config.json` does not exist (features created before adaptive execution modes were added), display: `"Note: No execution mode configured for this feature. Defaulting to balanced. Run /speckit.specify to set a mode explicitly."` and continue with balanced mode.
      - **Validate** the mode is one of `fast`, `balanced`, or `detailed`. If invalid, emit: `"ERROR: Unknown execution mode '{value}'. Valid values: fast, balanced, detailed. Re-run /speckit.specify to reset."` and halt.
      - Read `RISK_TRIGGERS` by scanning FEATURE_SPEC for risk-indicating keywords (see `contracts/risk-triggers.md` for the canonical keyword catalog)
      - Set `HAS_RISK_TRIGGERS` to `true` if any keywords matched, `false` otherwise

   b. **Risk Trigger Notification** (if triggers detected in fast or balanced mode):
      If `HAS_RISK_TRIGGERS` is `true` AND `EXECUTION_MODE` is `fast` or `balanced`, display this notification **before** any AR/SEC artifact generation begins: `"⚠️  Risk triggers detected in spec: [<matched keywords>]. Adding Architecture Review (AR) and Security Review (SEC) to this run. Continuing with escalated artifact set..."`

   c. **AR/SEC Artifact Gating** (mode-dependent):

      | Mode | HAS_RISK_TRIGGERS | AR | SEC | Plan Depth |
      | --- | --- | --- | --- | --- |
      | `fast` | `false` | Skip | Skip | Condensed: merge Summary and Technical Context into single block, omit PRD cross-reference section |
      | `fast` | `true` | Generate | Generate | Condensed (same as above) |
      | `balanced` | `false` | Skip | Skip | Full: all Technical Context fields, all sections |
      | `balanced` | `true` | Generate | Generate | Full |
      | `detailed` | any | Generate | Generate | Full, with explicit decision rationale section |

      - When generating AR: write to `SPECS_DIR/ar.md`
      - When generating SEC: write to `SPECS_DIR/sec.md`
      - For `detailed` mode: generate AR first, then SEC, then proceed to plan — establishing the rationale-before-implementation sequence. Include explicit decision rationale section in plan output.
      - For `fast` or `balanced` with triggers: generate AR and SEC before plan artifact generation

   d. Track `escalated` status: set to `true` if risk triggers caused AR/SEC to be added in fast or balanced mode; `false` otherwise (including detailed mode where AR/SEC are always included)

5. **Execute plan workflow**: Follow the structure in IMPL_PLAN template to:
   - Fill Technical Context (mark unknowns as "NEEDS CLARIFICATION")
   - Fill Constitution Check section from constitution
   - Evaluate gates (ERROR if violations unjustified)
   - Phase 0: Generate research.md (resolve all NEEDS CLARIFICATION)
   - Phase 1: Generate data-model.md, contracts/, quickstart.md
   - Phase 1: Update agent context by running the agent script
   - Re-evaluate Constitution Check post-design
   - Apply plan depth rules from step 4c (condensed for fast, full for balanced/detailed)

6. **Run Summary Generation** (always, after plan is complete):

   After all artifacts are generated, create `SPECS_DIR/run-summary.md` with this structure:

   ```markdown
   # Run Summary: {BRANCH}

   **Date**: {YYYY-MM-DD}
   **Execution Mode**: {EXECUTION_MODE} ({MODE_SOURCE from .feature-config.json})

   ## Risk Assessment

   **Triggers Detected**: {comma-separated keywords, or "None"}
   **Escalated**: {Yes/No — true if triggers caused AR/SEC to be added in fast/balanced mode}

   ## Artifacts Generated

   - {list each filename created during this run, e.g., spec.md, plan.md, ar.md, sec.md, research.md, data-model.md, quickstart.md, run-summary.md}

   ## Token Estimate

   **Estimated tokens this run**: {N}

   *Token count is self-reported by the AI agent based on approximate context window usage during this plan run.*
   ```

   - `run-summary.md` is overwritten on each plan run (not appended)
   - Token count should be the AI's best estimate of total tokens consumed during the full `/speckit.plan` workflow

7. **Stop and report**: Command ends after Phase 2 planning. Report branch, IMPL_PLAN path, and generated artifacts (including run-summary.md).

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

1. **Extract entities from feature spec (or PRD if available)** → `data-model.md`:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable

2. **Define interface contracts** (if project has external interfaces) → `/contracts/`:
   - Identify what interfaces the project exposes to users or other systems
   - Document the contract format appropriate for the project type
   - Examples: public APIs for libraries, command schemas for CLI tools, endpoints for web services, grammars for parsers, UI contracts for applications
   - Skip if project is purely internal (build scripts, one-off tools, etc.)

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
