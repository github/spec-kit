# Data Model: Parallel Command Optimization

**Feature**: 001-parallel-commands
**Date**: 2026-01-10

## Entities

### SubagentTask

A discrete unit of work dispatched to a Task tool subagent.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| id | string | Unique task identifier | Format: `{command}-{pass}-{timestamp}` |
| prompt | string | Full prompt for subagent | Required, max 100KB |
| context_scope | string[] | Files to include in context | Absolute paths |
| timeout | integer | Timeout in seconds | Default: 120, min: 10, max: 600 |
| status | enum | Current execution state | pending, running, completed, failed, retrying |
| attempts | integer | Number of execution attempts | Default: 0, max: 3 |
| started_at | timestamp | When execution began | ISO 8601 |
| completed_at | timestamp | When execution finished | ISO 8601, nullable |
| duration_ms | integer | Execution duration | Calculated field |
| result_path | string | Path to result file | `.claude/workspace/results/{id}-result.md` |
| error | string | Error message if failed | Nullable |

**State Transitions**:
```
pending → running → completed
                  → failed → retrying → running
                           → failed (after max attempts)
```

### ParallelBatch

A group of subagent tasks that can run concurrently.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| batch_id | string | Unique batch identifier | Format: `{command}-batch-{n}` |
| tasks | SubagentTask[] | Tasks in this batch | No limit (Claude Code supports unlimited) |
| max_parallel | integer | Concurrent execution limit | Default: unlimited, min: 1 |
| status | enum | Batch execution state | pending, running, completed, failed |
| completed_count | integer | Tasks completed | 0 to tasks.length |
| failed_count | integer | Tasks failed | 0 to tasks.length |
| started_at | timestamp | When batch began | ISO 8601 |
| completed_at | timestamp | When batch finished | ISO 8601, nullable |

**Invariants**:
- `completed_count + failed_count <= tasks.length`
- `status = completed` when `completed_count = tasks.length`
- `status = failed` when `failed_count > circuit_breaker_threshold`

### Workspace

Shared file-based memory for inter-agent communication.

| Field | Type | Description | Location |
|-------|------|-------------|----------|
| root | string | Workspace root directory | `.claude/workspace/` |
| context_file | string | Shared context for subagents | `context.md` |
| results_dir | string | Subagent output directory | `results/` |
| gates_dir | string | Gate validation results | `gates/` |

**Directory Structure**:
```
.claude/workspace/
├── context.md              # Shared context (read by all subagents)
├── results/
│   ├── {task_id}-result.md # Individual subagent outputs
│   └── ...
└── gates/
    └── {batch_id}-gate.md  # Gate validation results
```

### ProgressEvent

Real-time status update from subagent completion.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| task_id | string | Which task completed | References SubagentTask.id |
| status | enum | Task outcome | completed, failed |
| duration_ms | integer | Execution time | Positive integer |
| output_summary | string | Brief result description | Max 100 chars |
| timestamp | timestamp | When event occurred | ISO 8601 |

**Display Format**:
```
✓ {task_id} ({duration_s}s) - {output_summary}
✗ {task_id} ({duration_s}s) - {error_summary}
⏳ {task_id}...
```

### CircuitBreakerState

Tracks failure patterns for circuit breaker logic.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| consecutive_failures | integer | Failures without success | Reset on success |
| total_failures | integer | Total failures in session | Cumulative |
| state | enum | Circuit breaker state | closed, open, half-open |
| last_failure_at | timestamp | Most recent failure | ISO 8601, nullable |

**State Transitions**:
```
closed → open (at 3 consecutive failures, pause and warn)
open → half-open (after user acknowledges)
half-open → closed (on success)
half-open → open (on failure)

Any state → abort (at 10 total failures)
```

### CommandConfig

Configuration for parallel execution per command.

| Field | Type | Description | Default |
|-------|------|-------------|---------|
| command_name | string | Command being parallelized | Required |
| work_units | WorkUnit[] | Parallelizable work items | Command-specific |
| max_parallel | integer | Max concurrent subagents | Unlimited (configurable) |
| default_timeout | integer | Timeout per subagent (seconds) | 120 |
| merge_strategy | enum | How to combine results | concat, prioritize, merge |
| sequential_fallback | boolean | Honor --sequential flag | true |

**Work Units by Command**:

| Command | Work Units |
|---------|-----------|
| analyze | Duplication, Ambiguity, Underspecification, Constitution, Coverage, Inconsistency |
| checklist | Completeness, Clarity, Consistency, Measurability, Coverage, EdgeCases |
| plan | Research tasks (N), data-model.md, contracts/, quickstart.md |
| clarify | FunctionalScope, DataModel, UXFlow, NonFunctional, EdgeCases, Constraints, Terminology, Completion, Integration, Misc |
| taskstoissues | Issue N (one per task) |
| specify | Actors, Actions, Data, Constraints |

## Relationships

```
CommandConfig 1──* ParallelBatch
ParallelBatch 1──* SubagentTask
SubagentTask 1──1 ProgressEvent (on completion)
Workspace 1──* SubagentTask (via result files)
CircuitBreakerState 1──1 CommandConfig (per execution)
```

## Validation Rules

### SubagentTask
- `timeout` must be between 10 and 600 seconds
- `attempts` must not exceed 3
- `result_path` must be under `.claude/workspace/results/`
- `id` must be unique within batch

### ParallelBatch
- All tasks must have unique IDs
- `max_parallel` must not exceed tasks.length (if set)

### Workspace
- Must be created before any subagent dispatch
- Must be cleaned up after command completion
- Results directory must exist before task execution

### CircuitBreakerState
- Abort when `total_failures >= 10`
- Pause when `consecutive_failures >= 3`
- Reset `consecutive_failures` on any success
