---
description: Check token usage and budget for current session
---

# Token Budget Check

Display current token usage analysis for the development session.

## Run Token Budget Script

```bash
{SHADOW_PATH}/scripts/bash/token-budget{SCRIPT_EXT}
```

## What This Shows

- **Current token count** - Total tokens used in this session
- **Remaining budget** - Tokens left before hitting limits
- **File breakdown** - Which files contribute most to token usage
- **Recommendations** - Suggestions for pruning if needed

## Token Optimization

If you're approaching token limits:
1. Use `/prune` to compress session context
2. Remove large files from context
3. Use quick references instead of full specifications
4. Focus on specific subsystems rather than entire codebase

## Best Practices

- Check token budget regularly during long sessions
- Prune context before starting new major features
- Use semantic search (`/find`) instead of loading all files
- Keep specifications concise (aim for <2000 tokens per spec)

## Thresholds

- **Green** (<50% used): Plenty of room
- **Yellow** (50-80% used): Consider pruning soon
- **Red** (>80% used): Prune context immediately
