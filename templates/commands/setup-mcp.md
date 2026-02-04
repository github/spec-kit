---
description: Configure MCP server by running /speckit.mcp
---

## User Input

```text
$ARGUMENTS
```

## Purpose

Configure MCP server for testing and automation.

This is a wrapper that runs `/speckit.mcp` as a sub-agent.

---

## Execution

Run `/speckit.mcp` with any user arguments passed through.

This will:
- Detect services (Docker, npm scripts, etc.)
- Generate MCP server configuration
- Configure tools for testing and automation

---

## Completion

Report MCP status and suggest next steps.
