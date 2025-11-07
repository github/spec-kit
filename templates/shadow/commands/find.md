---
description: Semantic code search using natural language
---

# Semantic Code Search

Search the codebase using natural language queries.

## Usage

```bash
{SHADOW_PATH}/scripts/bash/semantic-search{SCRIPT_EXT} "<query>"
```

## Examples

### Find by Purpose
```bash
# Find authentication logic
{SHADOW_PATH}/scripts/bash/semantic-search{SCRIPT_EXT} "user authentication"

# Find database queries
{SHADOW_PATH}/scripts/bash/semantic-search{SCRIPT_EXT} "database queries"
```

### Find by Functionality
```bash
# Find error handling
{SHADOW_PATH}/scripts/bash/semantic-search{SCRIPT_EXT} "error handling"

# Find API endpoints
{SHADOW_PATH}/scripts/bash/semantic-search{SCRIPT_EXT} "REST API endpoints"
```

### Find by Pattern
```bash
# Find specific patterns
{SHADOW_PATH}/scripts/bash/semantic-search{SCRIPT_EXT} "dependency injection"

# Find implementations
{SHADOW_PATH}/scripts/bash/semantic-search{SCRIPT_EXT} "implements interface"
```

## What This Returns

- Relevant files and locations
- Code snippets matching the query
- Confidence scores for matches
- Suggested related files

## Best Practices

- Use descriptive queries
- Be specific about what you're looking for
- Try different phrasings if results aren't relevant
- Combine with traditional grep for exact matches

## Advantages Over Grep

- Understands intent, not just keywords
- Finds semantically similar code
- Works across different naming conventions
- Handles abbreviations and synonyms
