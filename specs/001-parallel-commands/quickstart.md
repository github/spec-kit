# Quickstart: Parallel Command Optimization

**Feature**: 001-parallel-commands
**Date**: 2026-01-10

## Overview

This guide explains how to use parallel execution in spec-kit commands after implementation.

## Usage

### Default Behavior (Parallel)

All optimized commands run in parallel mode by default:

```bash
# Runs 6 detection passes concurrently
/speckit.analyze

# Runs quality dimension evaluations concurrently
/speckit.checklist ux

# Runs research tasks concurrently
/speckit.plan

# Runs taxonomy scans concurrently
/speckit.clarify

# Creates all issues concurrently
/speckit.taskstoissues

# Explores concept dimensions concurrently
/speckit.specify "Add user authentication"
```

### Sequential Mode (Fallback)

Use `--sequential` to force single-agent execution:

```bash
/speckit.analyze --sequential
/speckit.checklist --sequential
/speckit.plan --sequential
/speckit.clarify --sequential
/speckit.taskstoissues --sequential
/speckit.specify --sequential "Add user authentication"
```

### Limiting Parallelism

Use `--max-parallel N` to limit concurrent subagents:

```bash
# Limit to 3 concurrent subagents
/speckit.analyze --max-parallel 3
```

**When to use sequential mode**:
- Debugging command behavior
- When parallel execution causes issues
- For deterministic output ordering
- When context window is constrained

## Progress Display

During parallel execution, you'll see progress updates per command:

### /speckit.analyze
```
[speckit] Parallel mode: 6 detection passes
[████░░░░░░] 4/6 complete
  ✓ duplication (2.1s) - 0 issues
  ✓ ambiguity (3.4s) - 1 issue
  ✓ constitution (1.8s) - 0 issues
  ✓ coverage (4.2s) - 2 issues
  ⏳ underspec...
  ⏳ inconsistency...
```

### /speckit.checklist
```
[speckit] Parallel mode: 6 quality dimensions
[██████░░░░] 4/6 complete
  ✓ completeness (1.8s)
  ✓ clarity (2.1s)
  ✓ consistency (1.5s)
  ✓ measurability (2.3s)
  ⏳ coverage...
  ⏳ edge_cases...
```

### /speckit.clarify
```
[speckit] Parallel mode: 10 taxonomy categories
[████████░░] 8/10 complete
  ✓ functional_scope (1.2s)
  ✓ data_model (1.8s)
  ✓ ux_flow (2.1s)
  ...
```

### Status Icons

| Icon | Meaning |
|------|---------|
| ✓ | Task completed |
| ✗ | Task failed |
| ⏳ | Task running |
| ⟳ | Task retrying |

## Error Handling

### Automatic Retry

Failed tasks automatically retry up to 3 times with exponential backoff:

```
[speckit] ✗ ambiguity failed: timeout
[speckit] ⟳ Retrying ambiguity (attempt 2/3)
[speckit] ✓ ambiguity (8.2s) - retry succeeded
```

### Circuit Breaker

If multiple failures occur:

```
[speckit] ⚠ Circuit breaker: 3 consecutive failures, pausing...
[speckit] Do you want to continue? (y/n)
```

At 10 total failures, execution aborts:

```
[speckit] ✗ Circuit breaker: 10 total failures, aborting
```

## Workspace Files

During execution, temporary files are created at `.claude/workspace/`:

```
.claude/workspace/
├── context.md              # Shared context
└── results/                # Individual task outputs
    ├── analyze-duplication-result.md
    ├── analyze-ambiguity-result.md
    └── ...
```

These files are automatically cleaned up after command completion.

## Expected Speedups

| Command | Sequential | Parallel | Speedup |
|---------|------------|----------|---------|
| analyze | ~30s | ~10s | 3x |
| checklist | ~20s | ~10s | 2x |
| plan | ~60s | ~30s | 2x |
| clarify | ~25s | ~12s | 2x |
| taskstoissues (N) | ~5s×N | ~10s | Nx/2 |
| specify | ~15s | ~8s | 2x |

*Actual times depend on feature complexity and API latency.*

## Conflict Resolution

When parallel subagents produce conflicting results:

**Duplicates/Overlaps**: Automatically merged (first occurrence kept)

**Semantic Contradictions**: Flagged for your decision:

```markdown
## Conflicts Detected

### Contradiction 1
**Source A** (ambiguity): Recommend adding explicit error types
**Source B** (coverage): Error handling is sufficient as-is

**Resolution required**: Please choose which recommendation to follow.
```

## Troubleshooting

### "Circuit breaker triggered"

**Cause**: Multiple consecutive failures
**Solution**:
1. Check error messages for root cause
2. Try `--sequential` mode to isolate issue
3. Verify spec files exist and are valid

### "Timeout exceeded"

**Cause**: Subagent took longer than 120s
**Solution**:
1. Check for large files in context
2. Simplify spec if very complex
3. Use `--sequential` for detailed debugging

### "Results conflict"

**Cause**: Parallel passes found contradictory issues
**Solution**:
1. Review both recommendations
2. Choose the more appropriate one
3. Consider updating spec to resolve ambiguity

## Best Practices

1. **Run analyze first**: Catches issues before implementation
2. **Use sequential for debugging**: Deterministic output helps troubleshoot
3. **Watch progress bar**: Identify slow passes
4. **Review conflicts carefully**: Don't dismiss contradictions automatically
5. **Keep specs focused**: Smaller scope = faster parallel execution
