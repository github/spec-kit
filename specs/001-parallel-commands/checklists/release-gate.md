# Release Gate Checklist: Parallel Command Optimization

**Purpose**: QA/Release gate validation of requirements quality for 001-parallel-commands
**Created**: 2026-01-10
**Focus**: All aspects (Parallel Execution Core, Error Handling & Resilience, Progress & UX, Inter-Agent Communication)
**Depth**: Comprehensive (Release Gate)
**Audience**: QA / Release validation

---

## Parallel Execution Core

### Flag Interface Requirements

- [ ] CHK001 - Is the `--sequential` flag behavior explicitly defined for each of the 6 commands? [Completeness, Spec §FR-001]
- [ ] CHK002 - Are the flag parsing semantics (present vs absent) unambiguously specified? [Clarity, Contract §Flag Interface]
- [ ] CHK003 - Is the `--max-parallel N` parameter format and validation rules specified (min/max values)? [Clarity, Spec §FR-003]
- [ ] CHK004 - Are flag precedence rules defined when `--sequential` and `--max-parallel` are both provided? [Gap, Conflict]
- [ ] CHK005 - Is the default behavior (parallel vs sequential) explicitly stated when no flags present? [Completeness, Contract §Flag Interface]

### Task Tool Interface Requirements

- [ ] CHK006 - Is the `subagent_type: "general-purpose"` requirement explicitly specified? [Completeness, Spec §FR-002]
- [ ] CHK007 - Is the prompt template structure defined with all required fields? [Completeness, Contract §Prompt Template]
- [ ] CHK008 - Are context file paths required to be absolute vs relative? [Clarity, Data Model §SubagentTask]
- [ ] CHK009 - Is the maximum prompt size (100KB) consistently documented across spec and data model? [Consistency]
- [ ] CHK010 - Is the Task tool description format specified ("`{command}:{work_unit} - {short_description}`")? [Clarity, Contract §Subagent Spawning]

### Subagent Dispatch Requirements

- [ ] CHK011 - Is "unlimited" default parallelism clearly defined (no hard cap)? [Clarity, Spec §FR-003]
- [ ] CHK012 - Is the greedy queue dispatch behavior explicitly specified? [Completeness, Spec §FR-004]
- [ ] CHK013 - Are the work units for each of the 6 commands explicitly enumerated? [Completeness, Data Model §CommandConfig]
- [ ] CHK014 - Is the task ID format (`{command}-{pass}-{timestamp}`) consistently specified? [Consistency, Data Model §SubagentTask]
- [ ] CHK015 - Are subagent spawning order requirements defined (all at once vs staggered)? [Gap]

### Batch Execution Requirements

- [ ] CHK016 - Is the batch_id format (`{command}-batch-{n}`) explicitly defined? [Clarity, Data Model §ParallelBatch]
- [ ] CHK017 - Are batch status transition rules explicitly defined (pending → running → completed/failed)? [Completeness, Data Model §ParallelBatch]
- [ ] CHK018 - Are batch invariants (`completed_count + failed_count <= tasks.length`) formally specified? [Completeness, Data Model §Invariants]
- [ ] CHK019 - Is the relationship between batches and phases clearly defined for multi-phase commands (plan)? [Clarity, Contract §plan]

---

## Error Handling & Resilience

### Timeout Requirements

- [ ] CHK020 - Is the default timeout (120 seconds) specified with measurable precision? [Measurability, Spec §Key Entities]
- [ ] CHK021 - Are minimum (10s) and maximum (600s) timeout bounds explicitly documented? [Completeness, Data Model §Validation Rules]
- [ ] CHK022 - Is timeout behavior defined (graceful termination vs hard kill)? [Gap]
- [ ] CHK023 - Are partial results on timeout addressed in requirements? [Gap, Exception Flow]
- [ ] CHK024 - Is per-command timeout configuration possible, or only global default? [Ambiguity]

### Retry Policy Requirements

- [ ] CHK025 - Is the maximum retry count (3 attempts) explicitly specified? [Completeness, Spec §FR-014]
- [ ] CHK026 - Are exponential backoff delays (1s, 2s, 4s) explicitly enumerated? [Completeness, Contract §Retry Behavior]
- [ ] CHK027 - Is retry behavior defined for different failure types (timeout vs error vs crash)? [Gap, Coverage]
- [ ] CHK028 - Are retry attempts tracked per-task in the data model? [Completeness, Data Model §SubagentTask.attempts]
- [ ] CHK029 - Is the state transition `failed → retrying → running` explicitly documented? [Completeness, Data Model §State Transitions]

### Circuit Breaker Requirements

- [ ] CHK030 - Is the pause threshold (3 consecutive failures) explicitly specified with measurable criteria? [Measurability, Spec §FR-015]
- [ ] CHK031 - Is the abort threshold (10 total failures) explicitly specified? [Measurability, Spec §FR-015]
- [ ] CHK032 - Are circuit breaker states (closed, open, half-open) and transitions fully documented? [Completeness, Data Model §CircuitBreakerState]
- [ ] CHK033 - Is the user interaction on "open" state (pause and warn) explicitly defined? [Clarity, Contract §Circuit Breaker]
- [ ] CHK034 - Is the half-open state test recovery behavior specified? [Completeness, Contract §Transitions]
- [ ] CHK035 - Is the distinction between "consecutive" and "total" failures clearly defined? [Clarity]
- [ ] CHK036 - Is `consecutive_failures` reset behavior on success explicitly documented? [Completeness, Data Model §Validation Rules]

### Failure Recovery Requirements

- [ ] CHK037 - Are partial results handling requirements defined when circuit breaker triggers? [Gap, Recovery Flow]
- [ ] CHK038 - Is user cancellation mid-execution behavior explicitly specified? [Completeness, Spec §Edge Cases]
- [ ] CHK039 - Are graceful termination semantics for cancelled subagents defined? [Gap]
- [ ] CHK040 - Is rollback/cleanup behavior specified after abort? [Gap, Recovery Flow]

---

## Progress Reporting & UX

### Progress Bar Requirements

- [ ] CHK041 - Is the progress bar format (`[████░░░░░░] N/M complete`) explicitly defined? [Completeness, Spec §FR-006]
- [ ] CHK042 - Is progress bar character encoding (Unicode blocks) specified? [Clarity, Contract §Progress Bar]
- [ ] CHK043 - Is the unit name in progress display configurable per command (passes, dimensions, issues)? [Gap]
- [ ] CHK044 - Is progress update frequency/latency specified (within 1 second)? [Measurability, Spec §SC-008]

### Status Icon Requirements

- [ ] CHK045 - Are all status icons (✓, ✗, ⏳, ⟳) explicitly defined with meanings? [Completeness, Contract §Status Icons]
- [ ] CHK046 - Is icon consistency across all 6 commands specified? [Consistency]
- [ ] CHK047 - Are icon display requirements for terminal encoding addressed? [Gap, Edge Case]

### Per-Task Status Requirements

- [ ] CHK048 - Is the per-task status line format (`{icon} {task_id} ({duration}s) - {summary}`) specified? [Completeness, Contract §Display Format]
- [ ] CHK049 - Is the output_summary max length (100 chars) specified? [Clarity, Data Model §ProgressEvent]
- [ ] CHK050 - Is the in-progress task display format (`⏳ {task_id}...`) specified? [Completeness]
- [ ] CHK051 - Are duration display requirements defined (seconds with decimal precision)? [Gap]

### Error Message Requirements

- [ ] CHK052 - Are error message formats for all error types explicitly specified? [Completeness, Contract §Error Messages]
- [ ] CHK053 - Is error message prefix (`[speckit]`) consistently required? [Consistency]
- [ ] CHK054 - Are retry notification messages (`⟳ Retrying {task_id}`) specified? [Completeness, Contract §Error Messages]
- [ ] CHK055 - Is circuit breaker warning message format specified? [Completeness, Contract §Error Messages]

---

## Inter-Agent Communication

### Workspace Structure Requirements

- [ ] CHK056 - Is the workspace root (`.claude/workspace/`) explicitly specified? [Completeness, Spec §FR-005]
- [ ] CHK057 - Is the directory structure (context.md, results/, gates/) explicitly documented? [Completeness, Data Model §Workspace]
- [ ] CHK058 - Are workspace creation timing requirements specified (before dispatch)? [Completeness, Data Model §Validation Rules]
- [ ] CHK059 - Are workspace cleanup requirements specified (after completion)? [Completeness, Data Model §Validation Rules]
- [ ] CHK060 - Is the results directory path format (`{task_id}-result.md`) explicitly defined? [Clarity, Data Model §SubagentTask.result_path]

### Context File Requirements

- [ ] CHK061 - Is the context.md file format explicitly documented? [Completeness, Contract §Context File Format]
- [ ] CHK062 - Are all required fields in context.md enumerated (command, feature, config)? [Completeness]
- [ ] CHK063 - Is shared_context_excerpt content scope defined (full vs excerpt)? [Ambiguity]
- [ ] CHK064 - Are context file size limits specified? [Gap]

### Result File Requirements

- [ ] CHK065 - Is the result file format (markdown with Summary, Details, Metadata) specified? [Completeness, Contract §Result File Format]
- [ ] CHK066 - Are all required metadata fields (duration, status, count) enumerated? [Completeness]
- [ ] CHK067 - Is result file naming convention specified and unique per task? [Clarity, Data Model §SubagentTask.result_path]
- [ ] CHK068 - Are result file encoding requirements (UTF-8) specified? [Gap]

### Result Merging Requirements

- [ ] CHK069 - Are merge strategies (concat, prioritize, merge, none) explicitly defined for each command? [Completeness, Contract §Merge Strategies]
- [ ] CHK070 - Is the merge order/precedence specified when concatenating results? [Gap]
- [ ] CHK071 - Is deduplication criteria for merge strategy specified (content hash, 90% similarity)? [Completeness, Contract §Conflict Resolution]

### Conflict Resolution Requirements

- [ ] CHK072 - Is duplicate detection criteria (content hash or >90% similarity) explicitly defined? [Measurability, Contract §Conflict Types]
- [ ] CHK073 - Is overlap detection criteria (partial content match) quantified? [Ambiguity, Contract §Conflict Types]
- [ ] CHK074 - Is contradiction detection criteria (mutually exclusive) defined with examples? [Clarity, Contract §Conflict Types]
- [ ] CHK075 - Is the conflict report format explicitly documented? [Completeness, Contract §Conflict Report Format]
- [ ] CHK076 - Is user resolution flow for contradictions specified? [Completeness, Spec §Edge Cases]

---

## Command-Specific Requirements

### analyze Command

- [ ] CHK077 - Are all 6 detection passes explicitly enumerated (Duplication, Ambiguity, Underspecification, Constitution, Coverage, Inconsistency)? [Completeness, Spec §FR-008]
- [ ] CHK078 - Is the merge strategy (concat by category) specified for analyze? [Completeness, Contract §analyze]
- [ ] CHK079 - Is the expected 3x speedup measurable with baseline comparison? [Measurability, Spec §SC-002]

### checklist Command

- [ ] CHK080 - Are all 6 quality dimensions explicitly enumerated (Completeness, Clarity, Consistency, Measurability, Coverage, Edge Cases)? [Completeness, Spec §FR-009]
- [ ] CHK081 - Is the merge strategy (concat by dimension) specified for checklist? [Completeness, Contract §checklist]
- [ ] CHK082 - Is the expected 2x speedup measurable? [Measurability, Spec §SC-003]

### plan Command

- [ ] CHK083 - Is Phase 0/Phase 1 sequential vs parallel behavior explicitly documented? [Completeness, Spec §FR-010]
- [ ] CHK084 - Are Phase 1 artifact dependencies (data-model.md, contracts/, quickstart.md) independence criteria specified? [Clarity, Contract §plan]
- [ ] CHK085 - Is the expected 2x speedup measurable? [Measurability, Spec §SC-004]

### clarify Command

- [ ] CHK086 - Are all 10 taxonomy categories explicitly enumerated? [Completeness, Spec §FR-011]
- [ ] CHK087 - Is the priority queue merge strategy (highest impact first) scoring criteria specified? [Gap, Contract §clarify]

### taskstoissues Command

- [ ] CHK088 - Is "all N concurrent" parallelism explicitly specified? [Completeness, Spec §FR-012]
- [ ] CHK089 - Is GitHub API rate limit handling explicitly documented? [Completeness, Contract §taskstoissues]
- [ ] CHK090 - Is the expected 5x speedup measurable for 10+ issues? [Measurability, Spec §SC-005]

### specify Command

- [ ] CHK091 - Are all 4 concept dimensions explicitly enumerated (actors, actions, data, constraints)? [Completeness, Spec §FR-013]
- [ ] CHK092 - Is the deduplicate-and-combine merge strategy criteria specified? [Clarity, Contract §specify]

---

## Cross-Cutting Requirements

### Semantic Equivalence

- [ ] CHK093 - Is semantic equivalence between parallel and sequential output explicitly defined? [Completeness, Spec §SC-006]
- [ ] CHK094 - Are acceptable differences (ordering) explicitly documented? [Clarity, Spec §SC-006]
- [ ] CHK095 - Are unacceptable differences (missing findings, different recommendations) explicitly prohibited? [Clarity]

### Graceful Degradation

- [ ] CHK096 - Is fallback to sequential mode behavior explicitly defined for all failure scenarios? [Gap, Recovery Flow]
- [ ] CHK097 - Are partial completion scenarios addressed (some subagents succeed, some fail)? [Gap, Exception Flow]

### Validation Rules Consistency

- [ ] CHK098 - Are SubagentTask validation rules consistent between spec, data model, and contract? [Consistency]
- [ ] CHK099 - Are CircuitBreakerState thresholds consistent across all documents? [Consistency]
- [ ] CHK100 - Are timeout values consistent between spec (120s default) and data model constraints? [Consistency]

---

## Summary

| Category | Items | Coverage |
|----------|-------|----------|
| Parallel Execution Core | CHK001-CHK019 | 19 |
| Error Handling & Resilience | CHK020-CHK040 | 21 |
| Progress Reporting & UX | CHK041-CHK055 | 15 |
| Inter-Agent Communication | CHK056-CHK076 | 21 |
| Command-Specific | CHK077-CHK092 | 16 |
| Cross-Cutting | CHK093-CHK100 | 8 |
| **Total** | | **100** |

---

## Legend

| Marker | Meaning |
|--------|---------|
| `[Completeness]` | Checking if requirement is present |
| `[Clarity]` | Checking if requirement is unambiguous |
| `[Consistency]` | Checking if requirements align |
| `[Measurability]` | Checking if requirement can be objectively verified |
| `[Gap]` | Missing requirement identified |
| `[Ambiguity]` | Unclear or vague requirement |
| `[Conflict]` | Potentially conflicting requirements |
| `[Spec §X]` | Reference to spec.md section |
| `[Contract §X]` | Reference to contracts/parallel-execution.md |
| `[Data Model §X]` | Reference to data-model.md |
