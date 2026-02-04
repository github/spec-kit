---
description: Project setup orchestrator - runs all setup-xxx sub-commands
---

# SpecKit Project Setup

You are the **Setup Orchestrator**. Initialize this project by running sub-commands.

## User Input

```text
$ARGUMENTS
```

**Options**:
- `--skip-constitution`: Skip constitution setup
- `--skip-docs`: Skip docs initialization
- `--skip-skills`: Skip skills configuration
- `--skip-agents`: Skip agents generation
- `--skip-mcp`: Skip MCP server setup
- `--only-xxx`: Only run specific sub-command (e.g., `--only-docs`)
- `from-code`, `from-docs`, `from-specs`: Pass to setup-docs

---

## Sub-Commands

Run each sub-command as a sub-agent, in order:

### 1. Constitution

Run `/speckit.setup-constitution`

Creates `/memory/constitution.md` with project principles.

**Skip if**: `--skip-constitution` or constitution already exists

---

### 2. Docs

Run `/speckit.setup-docs` (pass through `from-code`/`from-docs`/`from-specs` if provided)

Initializes `/docs/{domain}/spec.md` structure.

**Skip if**: `--skip-docs`

---

### 3. Skills

Run `/speckit.setup-skills`

Configures skills based on detected frameworks.

**Skip if**: `--skip-skills`

---

### 4. Agents

Run `/speckit.setup-agents`

Generates specialized subagents for SpecKit workflow.

**Skip if**: `--skip-agents`

---

### 5. MCP

Run `/speckit.setup-mcp`

Configures MCP server for testing and automation.

**Skip if**: `--skip-mcp`

---

## Completion

```markdown
## Setup Complete

| Sub-Command | Status |
|-------------|--------|
| Constitution | ✓ / Skipped |
| Docs | ✓ / Skipped |
| Skills | ✓ / Skipped |
| Agents | ✓ / Skipped |
| MCP | ✓ / Skipped |

### Next Steps
1. Review /memory/constitution.md
2. Review /docs/{domain}/spec.md files
3. Start first feature: /speckit.specify "your feature"
```
