---
description: Generate specialized subagents by running /speckit.agents
---

## User Input

```text
$ARGUMENTS
```

## Purpose

Generate specialized subagents for the SpecKit workflow.

This is a wrapper that runs `/speckit.agents` as a sub-agent.

---

## Execution

Run `/speckit.agents` with any user arguments passed through.

This will:
- Detect project technology stack
- Generate specialized subagents (spec-analyzer, designer, implementer, tester, etc.)
- Configure agents to use available skills

---

## Completion

Report agents status and suggest next steps.
