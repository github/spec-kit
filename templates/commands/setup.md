---
description: Project setup orchestrator - runs setup-bootstrap and setup-agents
---

# SpecKit Project Setup

You are the **Setup Orchestrator**. Initialize this project for SpecKit in 2 phases.

## User Input

```text
$ARGUMENTS
```

**Options**:
- `--bootstrap-only`: Only run setup-bootstrap (constitution + /docs)
- `--agents-only`: Only run setup-agents (agents + skills + mcp)
- `--skip-learn`: Don't run /speckit.learn at end of bootstrap
- No args: Run both phases

---

## Phase 1: Bootstrap

Run `/speckit.setup-bootstrap` as a sub-agent.

This will:
1. Create `/memory/constitution.md` if missing
2. Initialize `/docs/{domain}/` structure from code/docs/specs
3. Run `/speckit.learn` to extract patterns + create module CLAUDE.md files

**Skip if**: `--agents-only` flag provided

---

## Phase 2: Agents

Run `/speckit.setup-agents` as a sub-agent.

This will:
1. Generate specialized subagents for the workflow
2. Configure skills in agent directory
3. Generate MCP server configuration

**Skip if**: `--bootstrap-only` flag provided

---

## Completion

Report what was set up:

```markdown
## Setup Complete

### Phase 1: Bootstrap
- Constitution: ✓ Created / Already exists
- /docs: ✓ Initialized ({n} domains)
- Learn: ✓ Patterns extracted

### Phase 2: Agents
- Agents: ✓ Generated
- Skills: ✓ Configured
- MCP: ✓ Configured

### Next Steps
1. Review /memory/constitution.md
2. Review /docs/{domain}/spec.md files
3. Start first feature: /speckit.specify "your feature"
```
