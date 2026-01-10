# Contract: Parallel Execution Interface

**Feature**: 001-parallel-commands
**Date**: 2026-01-10

## Overview

This contract defines the interface for parallel subagent execution in spec-kit commands. All parallelized commands must follow this contract for consistency.

## Flag Interface

### `--sequential`

Forces single-agent mode, bypassing parallel execution.

**Behavior**:
- When present: Execute command in current (sequential) mode
- When absent: Use parallel mode if applicable

**Syntax**:
```bash
/speckit.analyze --sequential
/speckit.checklist --sequential
/speckit.plan --sequential
/speckit.clarify --sequential
/speckit.taskstoissues --sequential
/speckit.specify --sequential
```

## Task Tool Interface

### Subagent Spawning

```yaml
Tool: Task
Parameters:
  subagent_type: "general-purpose"
  prompt: |
    [Task-specific instructions]

    Context files to read:
    - {context_file_1}
    - {context_file_2}

    Output: Write results to {result_path}
  description: "{command}:{work_unit} - {short_description}"
```

### Prompt Template

```markdown
## Task: {task_id}

{task_description}

### Context
Read the following files for context:
{context_files}

### Instructions
{task_specific_instructions}

### Output
Write your results to: `.claude/workspace/results/{task_id}-result.md`

Format your output as:
```markdown
# Result: {task_id}

## Summary
[Brief summary of findings/output]

## Details
[Detailed findings/output]

## Metadata
- Duration: {duration}
- Status: completed|failed
- Issues found: {count}
```
```

## Workspace Interface

### Directory Structure

```
.claude/workspace/
├── context.md              # Shared context (written by parent)
├── results/                # Subagent outputs
│   ├── {task_id}-result.md
│   └── ...
└── gates/                  # Gate validation (optional)
    └── {batch_id}-gate.md
```

### Context File Format

```markdown
# Parallel Execution Context

## Command
{command_name}

## Feature
{feature_path}

## Configuration
- Max parallel: {max_parallel}
- Timeout: {timeout}s
- Batch: {batch_id}

## Shared Context
{shared_context_excerpt}
```

**Size Limits**:
- Maximum context.md size: 50KB (to fit within subagent context window)
- If shared context exceeds limit: truncate with `[TRUNCATED - see full context in {file_path}]` marker
- Per-subagent context_scope files: no limit (subagent reads directly)

### Result File Format

```markdown
# Result: {task_id}

## Summary
{brief_summary}

## Details
{detailed_findings}

## Metadata
- Duration: {duration_ms}ms
- Status: {completed|failed|incomplete}
- Output count: {count}
- Error: {error_message}  # Only if failed/incomplete
```

**Status Values**:
- `completed`: Task finished successfully with full output
- `failed`: Task encountered error, no usable output
- `incomplete`: Task timed out or cancelled, partial output available (marked with `[INCOMPLETE]` in merge)

## Progress Reporting Interface

### Display Format

```
[{progress_bar}] {completed}/{total} {unit_name} complete
  {status_icon} {task_id} ({duration}s) - {summary}
  {status_icon} {task_id} ({duration}s) - {summary}
  ⏳ {task_id}...
```

### Status Icons

| Icon | Meaning |
|------|---------|
| ✓ | Task completed successfully |
| ✗ | Task failed |
| ⏳ | Task in progress |
| ⟳ | Task retrying |

### Progress Bar

```
Empty:    [░░░░░░░░░░]
25%:      [██░░░░░░░░]
50%:      [█████░░░░░]
75%:      [███████░░░]
Complete: [██████████]
```

## Error Handling Interface

### Retry Behavior

```yaml
Retry Policy:
  max_attempts: 3
  backoff: exponential
  delays: [1s, 2s, 4s]

On failure:
  1. Log error with task_id
  2. Wait backoff_delay
  3. Increment attempts
  4. Retry if attempts < max_attempts
  5. Mark failed if attempts >= max_attempts
```

### Circuit Breaker

```yaml
Circuit Breaker:
  pause_threshold: 3 consecutive failures
  abort_threshold: 10 total failures

States:
  closed: Normal operation
  open: Paused, awaiting user input
  half-open: Testing recovery

Transitions:
  closed → open: 3 consecutive failures
  open → half-open: User acknowledges
  half-open → closed: Success
  half-open → open: Failure
```

### Error Messages

```
[speckit] ✗ {task_id} failed: {error_message}
[speckit] ⟳ Retrying {task_id} (attempt {n}/3)
[speckit] ⚠ Circuit breaker: 3 consecutive failures, pausing...
[speckit] ✗ Circuit breaker: 10 total failures, aborting
```

## Merge Interface

### Merge Strategies

| Strategy | When Used | Behavior |
|----------|-----------|----------|
| concat | analyze, checklist | Concatenate results by category |
| prioritize | clarify | Sort by priority score, take top N |
| merge | specify | Deduplicate and combine entities |
| none | taskstoissues | Independent results, no merge |

**Merge Order** (for concat/merge strategies):
- Primary: Alphabetical by task_id (deterministic ordering)
- Within category: Preserve original finding order from each result file
- Incomplete results: Appended last with `[INCOMPLETE]` prefix

### Conflict Resolution

```yaml
Conflict Types:
  duplicate:
    detection: Same content hash or >90% text similarity (Jaccard index)
    resolution: Keep first occurrence (by task_id alphabetical order)

  overlap:
    detection: >50% content overlap (shared tokens / total tokens)
    resolution: Union of findings, deduplicate identical sentences

  contradiction:
    detection: Mutually exclusive recommendations (opposite actions on same entity)
    resolution: Flag to user with both values, require explicit choice
```

### Conflict Report Format

```markdown
## Conflicts Detected

### Contradiction 1
**Source A** ({task_id_1}): {recommendation_1}
**Source B** ({task_id_2}): {recommendation_2}

**Resolution required**: Please choose which recommendation to follow.
```

## Command-Specific Contracts

### analyze

```yaml
Work Units:
  - duplication
  - ambiguity
  - underspecification
  - constitution
  - coverage
  - inconsistency

Parallelism: All 6 concurrent (no limit)
Merge: concat by category
Output: Unified analysis report
```

### checklist

```yaml
Work Units:
  - completeness
  - clarity
  - consistency
  - measurability
  - coverage
  - edge_cases

Parallelism: All 6 concurrent (no limit)
Merge: concat by dimension
Output: Quality checklist file
```

### plan

```yaml
Work Units:
  Phase 0: [research_task_1, research_task_2, ...]
  Phase 1: [data-model.md, contracts/, quickstart.md]

Parallelism: Within phase only
Merge: Sequential phases
Output: Plan artifacts
```

### clarify

```yaml
Work Units:
  - functional_scope
  - data_model
  - ux_flow
  - non_functional
  - edge_cases
  - constraints
  - terminology
  - completion
  - integration
  - misc

Parallelism: All 10 concurrent (no limit)
Merge: Priority queue (highest impact first)
Output: Prioritized question candidates

Priority Scoring:
  formula: priority = (ambiguity_severity * 0.4) + (affected_requirements * 0.3) + (implementation_risk * 0.3)
  ambiguity_severity: 1-5 scale (1=minor clarification, 5=blocking ambiguity)
  affected_requirements: count of FR/NFR referencing the ambiguous term
  implementation_risk: 1-5 scale (1=cosmetic, 5=architectural impact)
  top_n: 5 (present top 5 questions to user)
```

### taskstoissues

```yaml
Work Units:
  - issue_1 through issue_N

Parallelism: All N concurrent (no limit)
Merge: None (independent)
Output: GitHub issue URLs
Rate Limiting: Respect GitHub API limits
```

### specify

```yaml
Work Units:
  - actors
  - actions
  - data
  - constraints

Parallelism: 4 concurrent
Merge: Deduplicate and combine
Output: Unified spec entities
```
