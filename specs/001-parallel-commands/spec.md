# Feature Specification: Parallel Command Optimization for Claude Code

**Feature Branch**: `001-parallel-commands`
**Created**: 2026-01-10
**Status**: Draft
**Input**: User description: "Optimize all spec-kit commands for Claude Code parallel subagents"

## Clarifications

### Session 2026-01-10

- Q: What is the default timeout for individual subagent tasks? → A: 120 seconds
- Q: What format should progress reporting use for subagent status updates? → A: Progress bar + per-task completion lines
- Q: When subagents produce conflicting results, what makes a conflict "unresolvable"? → A: Auto-merge duplicates/overlaps; flag semantic contradictions to user

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Parallel Artifact Analysis (Priority: P1)

A developer runs `/speckit.analyze` on a feature with spec.md, plan.md, and tasks.md. Instead of waiting for 6 sequential detection passes (Duplication, Ambiguity, Underspecification, Constitution Alignment, Coverage Gaps, Inconsistency), all 6 passes run concurrently via parallel subagents, reducing analysis time significantly.

**Why this priority**: `/speckit.analyze` has the clearest parallelization opportunity - 6 independent detection passes that currently run sequentially. High-frequency command used before every implementation.

**Independent Test**: Can be fully tested by running `/speckit.analyze` on any feature and observing 6 concurrent Task tool invocations completing faster than sequential execution.

**Acceptance Scenarios**:

1. **Given** a feature with spec.md, plan.md, and tasks.md, **When** user runs `/speckit.analyze`, **Then** 6 detection passes execute concurrently via Task tool subagents
2. **Given** analyze running in parallel mode, **When** all subagents complete, **Then** results are merged into a single unified analysis report
3. **Given** user prefers sequential mode, **When** user runs `/speckit.analyze --sequential`, **Then** analyze runs in single-agent mode (current behavior)

---

### User Story 2 - Parallel Checklist Generation (Priority: P1)

A developer runs `/speckit.checklist` to generate requirements quality validation. Instead of evaluating checklist dimensions sequentially, parallel subagents evaluate Completeness, Clarity, Consistency, Measurability, Coverage, and Edge Cases concurrently.

**Why this priority**: Checklist generation involves independent quality dimension evaluations. Running these in parallel provides immediate speedup with minimal coordination overhead.

**Independent Test**: Can be fully tested by running `/speckit.checklist ux` and observing concurrent evaluation of quality dimensions.

**Acceptance Scenarios**:

1. **Given** a feature spec, **When** user runs `/speckit.checklist`, **Then** quality dimension evaluations run concurrently via subagents
2. **Given** multiple checklists requested (e.g., `ux`, `security`, `api`), **When** run together, **Then** each checklist type generates in parallel

---

### User Story 3 - Parallel Research in Planning (Priority: P2)

A developer runs `/speckit.plan` and Phase 0 identifies 4 research tasks (e.g., "Research auth patterns", "Research database options", "Research API design", "Research caching strategy"). All 4 research tasks run concurrently instead of sequentially.

**Why this priority**: Plan command already has placeholder for "dispatch research agents" but lacks actual parallel execution. Research tasks are independent and benefit significantly from parallelization.

**Independent Test**: Can be fully tested by running `/speckit.plan` on a spec with multiple NEEDS CLARIFICATION items and observing concurrent research subagents.

**Acceptance Scenarios**:

1. **Given** a spec with multiple NEEDS CLARIFICATION items, **When** user runs `/speckit.plan`, **Then** Phase 0 research tasks run concurrently via subagents
2. **Given** Phase 1 design tasks, **When** data-model.md, contracts/, and quickstart.md can be generated independently, **Then** they generate in parallel

---

### User Story 4 - Parallel Ambiguity Research (Priority: P2)

A developer runs `/speckit.clarify` and the system identifies ambiguities across 10 taxonomy categories (Functional Scope, Data Model, UX Flow, Non-Functional, Edge Cases, Constraints, Terminology, Completion, Integration, Misc). Research for each category runs concurrently to identify candidate clarification questions faster.

**Why this priority**: Clarify command scans many taxonomy categories. Parallelizing the scan phase reduces time to first question.

**Independent Test**: Can be fully tested by running `/speckit.clarify` and observing parallel category scans before question presentation.

**Acceptance Scenarios**:

1. **Given** a feature spec, **When** user runs `/speckit.clarify`, **Then** taxonomy category scans run concurrently
2. **Given** parallel scan results, **When** questions are prioritized, **Then** highest-impact questions surface from all categories

---

### User Story 5 - Parallel GitHub Issue Creation (Priority: P3)

A developer runs `/speckit.taskstoissues` with 15 tasks. Instead of creating issues one at a time, all 15 subagents create GitHub issues concurrently, respecting API rate limits.

**Why this priority**: Issue creation is I/O bound and embarrassingly parallel. Lower priority because it's less frequently used than other commands.

**Independent Test**: Can be fully tested by running `/speckit.taskstoissues` on a feature with 15+ tasks and observing concurrent issue creation.

**Acceptance Scenarios**:

1. **Given** a tasks.md with 15 tasks, **When** user runs `/speckit.taskstoissues`, **Then** all 15 issues create concurrently
2. **Given** GitHub API rate limits, **When** limit approached, **Then** subagents back off gracefully with exponential retry

---

### User Story 6 - Parallel Requirement Exploration (Priority: P3)

A developer runs `/speckit.specify` with a feature description. Instead of sequentially extracting actors, actions, data, and constraints, parallel subagents explore each dimension concurrently and merge findings.

**Why this priority**: Specify is typically fast enough, but parallelization could help with complex feature descriptions. Lower priority due to less time savings.

**Independent Test**: Can be fully tested by running `/speckit.specify` with a complex description and observing concurrent exploration.

**Acceptance Scenarios**:

1. **Given** a complex feature description, **When** user runs `/speckit.specify`, **Then** concept extraction runs concurrently for actors, actions, data, constraints
2. **Given** parallel extraction results, **When** spec is generated, **Then** all findings merge coherently

---

### Edge Cases

- What happens when a subagent times out during parallel execution? → Parent agent retries with exponential backoff, then surfaces error to user
- What happens when user sets --max-parallel limit and it's exceeded? → Queue overflow tasks, start queued task when slot frees (greedy refill)
- What happens when subagents produce conflicting results? → Parent agent auto-merges duplicates/overlaps; semantic contradictions (mutually exclusive recommendations) flagged to user for resolution
- What happens when user cancels mid-parallel-execution? → All subagents terminate gracefully, partial results reported
- What happens when both `--sequential` and `--max-parallel N` are provided? → `--sequential` takes precedence; `--max-parallel` is ignored with warning message
- What is "graceful termination" for timeouts/cancellation? → Subagent is signaled to stop, has 5 seconds to write partial results to result file with `status: incomplete`, then forcibly terminated
- What happens with partial results on timeout? → Partial output saved to `{task_id}-result.md` with `status: incomplete` and `error: timeout after {N}s`; parent includes partial findings in merge with `[INCOMPLETE]` marker
- What happens after circuit breaker abort (10 failures)? → Workspace preserved for debugging; parent reports: completed tasks, failed tasks with errors, suggested recovery (re-run with `--sequential`); no auto-cleanup until user runs next command

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST support `--sequential` flag on all optimized commands to force single-agent mode
- **FR-002**: System MUST use Task tool with `subagent_type: "general-purpose"` for parallel subagent spawning
- **FR-003**: System SHOULD allow configurable max concurrent subagents (default: unlimited, user can set via --max-parallel)
- **FR-004**: System MUST implement greedy queue dispatch (start queued task when slot frees)
- **FR-005**: System MUST use file-based shared memory via `.claude/workspace/` for inter-agent communication
- **FR-006**: System MUST provide consistent progress reporting format across all parallel commands: overall progress bar + per-task completion lines showing status, duration, and summary
- **FR-007**: System MUST merge subagent results into unified output (report, checklist, spec, etc.)
- **FR-008**: `/speckit.analyze` MUST run 6 detection passes concurrently: Duplication, Ambiguity, Underspecification, Constitution, Coverage, Inconsistency
- **FR-009**: `/speckit.checklist` MUST evaluate quality dimensions concurrently: Completeness, Clarity, Consistency, Measurability, Coverage, Edge Cases
- **FR-010**: `/speckit.plan` MUST run Phase 0 research tasks concurrently and Phase 1 artifact generation (where independent) concurrently
- **FR-011**: `/speckit.clarify` MUST run taxonomy category scans concurrently before question prioritization
- **FR-012**: `/speckit.taskstoissues` MUST create GitHub issues concurrently (all tasks in parallel)
- **FR-013**: `/speckit.specify` MUST explore requirement dimensions (actors, actions, data, constraints) concurrently for complex descriptions
- **FR-014**: System MUST implement retry policy with exponential backoff for failed subagents (max 3 attempts)
- **FR-015**: System MUST implement circuit breaker (pause at 3 failures, abort at 10 failures)

### Key Entities

- **Subagent Task**: A discrete unit of work dispatched to a Task tool subagent (id, prompt, context_scope, timeout=120s default)
- **Parallel Batch**: A group of subagent tasks that can run concurrently (batch_id, tasks[], max_parallel)
- **Workspace**: Shared file-based memory at `.claude/workspace/` (context.md, results/, gates/)
- **Progress Event**: Real-time status update from subagent completion (task_id, status, duration, output_summary)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 6 commands (`analyze`, `checklist`, `plan`, `clarify`, `taskstoissues`, `specify`) support `--sequential` flag
- **SC-002**: `/speckit.analyze` achieves at least 3x speedup on features with complex artifacts (6 parallel passes vs sequential)
- **SC-003**: `/speckit.checklist` achieves at least 2x speedup when evaluating multiple quality dimensions
- **SC-004**: `/speckit.plan` achieves at least 2x speedup when multiple research tasks are identified
- **SC-005**: `/speckit.taskstoissues` achieves at least 5x speedup when creating 10+ issues
- **SC-006**: All parallel commands produce semantically identical output to sequential mode (same findings, same recommendations - ordering may differ due to parallel timing)
- **SC-007**: Failed subagents recover gracefully without crashing the parent command (retry policy effective)
- **SC-008**: Progress reporting updates within 1 second of subagent completion
