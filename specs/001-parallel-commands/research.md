# Research: Parallel Command Optimization

**Feature**: 001-parallel-commands
**Date**: 2026-01-10

## Research Tasks Completed

### R1: Claude Code Task Tool Best Practices

**Decision**: Use `subagent_type: "general-purpose"` for all parallel work.

**Rationale**:
- General-purpose agents have access to all tools (file read/write, bash, etc.)
- Specialized agents (Bash, Explore) are too narrow for command execution
- Reference implementation in `speckit.implement.md` uses this pattern successfully

**Alternatives Considered**:
- `subagent_type: "Explore"` - Too limited, only for codebase exploration
- `subagent_type: "Bash"` - Too limited, only for shell commands
- Direct tool calls without subagents - No parallelism possible

### R2: Inter-Agent Communication Pattern

**Decision**: File-based shared memory via `.claude/workspace/`.

**Rationale**:
- Claude Code agents can read/write files reliably
- No shared memory or message passing available between agents
- File-based approach proven in `speckit.implement.md` parallel mode
- Directory structure:
  - `context.md` - Shared context (spec excerpts, configuration)
  - `results/{task_id}-result.md` - Individual subagent outputs
  - `gates/` - Gate validation results (for implement command compatibility)

**Alternatives Considered**:
- Environment variables - Not accessible across agent boundaries
- Stdout piping - Not supported in Task tool
- MCP server state - Overly complex for this use case

### R3: Progress Reporting Implementation

**Decision**: Progress bar + per-task completion lines (hybrid format).

**Rationale** (from clarification session):
- Progress bar provides at-a-glance completion status
- Per-task lines provide audit trail and detailed status
- Hybrid format balances information density with readability
- Format:
  ```
  [████░░░░] 4/6 passes complete
    ✓ duplication (2.1s) - 0 issues
    ✓ ambiguity (3.4s) - 1 issue
    ⏳ underspec...
  ```

**Alternatives Considered**:
- Compact single-line only - Less visual feedback
- Silent until completion - Poor UX for long operations
- Progress bar only - No detail on what completed

### R4: Timeout and Retry Strategy

**Decision**: 120-second default timeout with exponential backoff retry.

**Rationale** (from clarification session):
- 120s balances responsiveness with tolerance for slow operations
- Exponential backoff (1s → 2s → 4s) prevents thundering herd
- Max 3 retries keeps worst-case under 6 minutes
- Circuit breaker (pause at 3, abort at 10) prevents runaway failures

**Alternatives Considered**:
- 60s timeout - Too aggressive, may timeout legitimate operations
- 180s timeout - Too slow feedback on failures
- Linear backoff - Less effective at spreading retry load

### R5: Conflict Resolution Strategy

**Decision**: Auto-merge duplicates/overlaps; flag semantic contradictions to user.

**Rationale** (from clarification session):
- Duplicates are common (e.g., multiple passes find same issue)
- Overlaps can be safely merged (union of findings)
- Semantic contradictions (mutually exclusive recommendations) require human judgment
- Example contradiction: One pass recommends "add auth", another says "auth not needed"

**Alternatives Considered**:
- All conflicts require user resolution - Too conservative, slows workflow
- Last-write-wins - May lose important findings
- Confidence scoring - Adds complexity without clear benefit

### R6: Reference Implementation Analysis

**Decision**: Use `speckit.implement.md` parallel mode as reference pattern.

**Findings from existing implementation**:
- Workspace setup: `mkdir -p .claude/workspace/results`
- Context sharing: Write to `.claude/workspace/context.md`
- Task spawning pattern:
  ```
  Task(
    subagent_type: "general-purpose",
    prompt: "Implement task {task_id}: {description}..."
    description: "Task {task_id}: {short_description}"
  )
  ```
- Result collection: Read from `.claude/workspace/results/{task_id}-result.md`
- Batch processing: Phase-by-phase with gate validation

**Adaptations for other commands**:
- analyze: Results are findings, not files
- checklist: Results are dimension evaluations
- plan: Results are research outputs
- clarify: Results are question candidates
- taskstoissues: Results are issue URLs (or error messages)
- specify: Results are concept extractions

### R7: Command-Specific Parallelization Analysis

| Command | Parallelizable Units | Independence | Merge Complexity |
|---------|---------------------|--------------|------------------|
| analyze | 6 detection passes | Full | Low (concatenate) |
| checklist | 6 quality dimensions | Full | Low (concatenate) |
| plan | N research + 3 artifacts | Partial (phases) | Medium (sequence) |
| clarify | 10 taxonomy categories | Full | Medium (prioritize) |
| taskstoissues | N issues | Full | None (independent) |
| specify | 4 concept dimensions | Full | High (merge concepts) |

**Findings**:
- `analyze` and `checklist` are easiest - fully independent passes
- `plan` requires phase ordering (research before design)
- `clarify` needs priority queue from all results
- `taskstoissues` is embarrassingly parallel
- `specify` requires careful merge to avoid duplication

## Resolved Clarifications

All NEEDS CLARIFICATION items from Technical Context have been resolved:

| Item | Resolution | Source |
|------|------------|--------|
| Default timeout | 120 seconds | Clarification session |
| Progress format | Progress bar + per-task lines | Clarification session |
| Conflict resolution | Auto-merge duplicates, flag contradictions | Clarification session |
| Task tool subagent type | general-purpose | Reference implementation |
| Inter-agent communication | File-based workspace | Reference implementation |
| Retry policy | Exponential backoff (1s, 2s, 4s), max 3 | Best practice |
| Circuit breaker | Pause at 3 failures, abort at 10 | Spec requirement |

## Open Questions (None)

All research tasks completed. No outstanding unknowns blocking implementation.
