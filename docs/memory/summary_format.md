# Summary Format Optimization (T078)

## Optimized Memory Entry Format

### Lessons (lessons.md)
```markdown
## [Title] - [Category]

**Context**: What were you working on?
**Problem**: What went wrong?
**Solution**: How did you fix it?

### One-Liner
[Brief 50-char summary for headers-first reading]

### Details
[Full explanation when deep-read]

### Related
- Pattern: [pattern-name]
- Architecture: [decision-name]
```

### Patterns (patterns.md)
```markdown
## [Pattern Name]

**Category**: [architecture|code|workflow|testing]

### One-Liner
[Brief 50-char description]

### When to Use
- [Condition 1]
- [Condition 2]

### Implementation
```python
[Code example]
```

### Benefits
- [Benefit 1]
- [Benefit 2]

### Trade-offs
- [Trade-off 1]
- [Trade-off 2]
```

### Architecture (architecture.md)
```markdown
## [Decision Title]

**Status**: [Proposed|Accepted|Deprecated]
**Date**: YYYY-MM-DD

### One-Liner
[Brief 50-char summary]

### Context
[What problem does this solve?]

### Decision
[What was decided?]

### Rationale
[Why this decision?]

### Alternatives Considered
- [Alternative 1]: [Why rejected]
- [Alternative 2]: [Why rejected]

### Consequences
- **Positive**: [Impact]
- **Negative**: [Trade-offs]
```

## Token Efficiency

| Format | Tokens | Usage |
|--------|--------|-------|
| One-liner only | ~50 | Headers-first scan |
| Full entry | ~500-2000 | Deep read |
| Optimized ratio | 3-10% | Navigation overhead |

## Best Practices

1. **One-liners must be under 50 characters**
2. **Include category/tags for filtering**
3. **Link related entries**
4. **Use code blocks for examples**
5. **Mark status for architecture decisions**
