---
description: Compress session context to reduce token usage
---

# Prune Session Context

Compress the current session context to free up token budget.

## Run Session Prune Script

```bash
{SHADOW_PATH}/scripts/bash/session-prune{SCRIPT_EXT}
```

## What This Does

- Identifies large files consuming tokens
- Suggests files that can be removed from context
- Generates compressed summaries of key information
- Creates quick-reference versions of specifications

## Pruning Strategies

### Remove Noise
- Generated files (build artifacts, logs)
- Test fixtures and mock data
- Large configuration files
- Dependency manifests

### Summarize Documents
- Convert full specs to quick references
- Extract key points from long discussions
- Create function signature lists
- Generate symbol indexes

### Focus Context
- Keep only files relevant to current task
- Remove completed feature context
- Archive historical decisions
- Maintain only active specifications

## After Pruning

Check token usage again:
```bash
{SHADOW_PATH}/scripts/bash/token-budget{SCRIPT_EXT}
```

## Best Practices

- Prune proactively, not reactively
- Save important context before pruning
- Keep a clear mental model of what was pruned
- Re-add context as needed for specific tasks
