---
description: Configure AI agents, skills, and MCP server by running specialized sub-agents
---

## User Input

```text
$ARGUMENTS
```

Options: `--skip-agents`, `--skip-mcp`

## Purpose

Orchestrate the AI tooling setup by running sub-agents:
1. `/speckit.agents` → Generate agents + configure skills
2. `/speckit.mcp` → Configure MCP server

---

## Step 1: Agents & Skills

Run `/speckit.agents` as a sub-agent.

This will:
- Detect project technology stack
- Generate specialized subagents for SpecKit workflow
- Configure skills based on detected frameworks

**Skip if**: `--skip-agents` flag provided

---

## Step 2: MCP Server

Run `/speckit.mcp` as a sub-agent.

This will:
- Detect services (Docker, npm scripts, etc.)
- Generate MCP server configuration
- Configure tools for testing and automation

**Skip if**: `--skip-mcp` flag provided

---

## Completion Report

```markdown
## Agents Setup Complete

### Agents & Skills
- Status: ✓ Configured / Skipped
- See /speckit.agents output for details

### MCP Server
- Status: ✓ Configured / Skipped
- See /speckit.mcp output for details

### Next Steps
1. Review generated agents
2. Test MCP server if configured
3. Run /speckit.setup-bootstrap if not done
```
