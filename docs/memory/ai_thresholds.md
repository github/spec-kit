# AI Threshold Tuning Guide (T079)

## Importance Classification Thresholds

### Current Thresholds (in classifier.py)

```python
class AIImportanceClassifier:
    # Overall score thresholds
    HIGH_IMPORTANCE = 0.7    # → architecture.md
    MEDIUM_IMPORTANCE = 0.4  # → patterns.md
    LOW_IMPORTANCE = 0.0     # → lessons.md
```

### Threshold Rationale

| Score | Destination | Content Type | Examples |
|-------|-------------|--------------|----------|
| ≥0.7 | architecture.md | Critical decisions | Database choice, API architecture, security model |
| 0.4-0.7 | patterns.md | Reusable patterns | Error handling, auth flow, testing patterns |
| <0.4 | lessons.md | Minor learnings | Bug fixes, minor optimizations, typos |

## Tuning Guidelines

### When to Adjust Thresholds

**Raise HIGH_IMPORTANCE (>0.7)** if:
- Too many entries go to architecture.md
- Architecture file becomes bloated
- Only strategic decisions should be there

**Lower HIGH_IMPORTANCE (<0.7)** if:
- Important decisions are missed
- Architecture file is too sparse
- More technical depth needed

**Raise MEDIUM_IMPORTANCE (>0.4)** if:
- Patterns file is too large
- Only best practices should be patterns

**Lower MEDIUM_IMPORTANCE (<0.4)** if:
- Patterns file is underutilized
- More content should be reusable

## Feedback Loop

1. Monitor memory file sizes weekly
2. Check if destination matches content importance
3. Adjust thresholds in 0.05 increments
4. Document rationale for changes

## Recommended Starting Values

```python
# For new projects (conservative)
HIGH_IMPORTANCE = 0.75   # Only critical decisions
MEDIUM_IMPORTANCE = 0.45  # Clear best practices

# For mature projects (aggressive)
HIGH_IMPORTANCE = 0.65   # Include important patterns
MEDIUM_IMPORTANCE = 0.35  # Capture more learnings
```

## Monitoring Commands

```bash
# Check memory file sizes
du -sh ~/.claude/memory/projects/*/architecture.md
du -sh ~/.claude/memory/projects/*/patterns.md
du -sh ~/.claude/memory/projects/*/lessons.md

# Count entries per file
grep -c "^## " ~/.claude/memory/projects/*/architecture.md
```
