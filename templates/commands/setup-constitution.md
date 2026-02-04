---
description: Create or update project constitution by running /speckit.constitution
---

## User Input

```text
$ARGUMENTS
```

## Purpose

Initialize or update the project constitution at `/memory/constitution.md`.

This is a wrapper that runs `/speckit.constitution` as a sub-agent.

---

## Execution

Run `/speckit.constitution` with any user arguments passed through.

This will:
- Check if constitution exists
- If missing: guide user through quick setup interview
- If exists: allow updates with version control
- Propagate changes to dependent templates

---

## Completion

Report constitution status and suggest next steps.
