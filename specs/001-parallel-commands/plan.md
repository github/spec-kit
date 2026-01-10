# Implementation Plan: Parallel Command Optimization for Claude Code

**Branch**: `001-parallel-commands` | **Date**: 2026-01-10 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-parallel-commands/spec.md`

## Summary

Optimize 6 spec-kit commands (`analyze`, `checklist`, `plan`, `clarify`, `taskstoissues`, `specify`) for parallel subagent execution using Claude Code's Task tool. Each command will dispatch independent work units to concurrent subagents (unlimited parallelism), with file-based coordination via `.claude/workspace/`, retry policies with exponential backoff, and circuit breaker patterns for reliability.

## Technical Context

**Language/Version**: Markdown command files (Claude Code native)
**Primary Dependencies**: Claude Code Task tool, Claude Code CLI
**Storage**: File-based workspace at `.claude/workspace/` (context.md, results/, gates/)
**Testing**: Manual verification via command execution, timing comparisons
**Target Platform**: Claude Code CLI (macOS, Linux, Windows via WSL)
**Project Type**: Single (command file modifications)
**Performance Goals**: 2-5x speedup depending on command (spec defines: analyze 3x, checklist 2x, plan 2x, taskstoissues 5x)
**Constraints**: No subagent cap (Claude Code supports unlimited parallel subagents), 120s default timeout per subagent
**Scale/Scope**: 6 command files to modify, shared parallel execution infrastructure

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The project constitution (`/memory/constitution.md`) contains template placeholders rather than project-specific principles. No specific gates to evaluate.

**Status**: PASS (no constitution violations - template file)

## Project Structure

### Documentation (this feature)

```text
specs/001-parallel-commands/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
.claude/commands/
├── speckit.analyze.md      # P1: Add parallel 6-pass detection
├── speckit.checklist.md    # P1: Add parallel quality dimension evaluation
├── speckit.plan.md         # P2: Add parallel research dispatch
├── speckit.clarify.md      # P2: Add parallel taxonomy scan
├── speckit.taskstoissues.md # P3: Add parallel issue creation
├── speckit.specify.md      # P3: Add parallel concept extraction
└── speckit.implement.md    # ALREADY PARALLEL (reference implementation)

.claude/workspace/           # Shared memory (created at runtime)
├── context.md              # Shared context for subagents
├── results/                # Subagent output files
└── gates/                  # Gate validation results
```

**Structure Decision**: Modifications to existing command files in `.claude/commands/`. No new directories needed except runtime workspace.

## Complexity Tracking

> No constitution violations to justify.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | - | - |

## Architecture Overview

### Parallel Execution Pattern

Each command follows this pattern:

```
1. Parse --sequential flag (if present, use current behavior)
2. Identify parallelizable work units
3. Setup shared workspace (.claude/workspace/context.md)
4. Dispatch subagents via Task tool (unlimited concurrent)
5. Monitor progress (progress bar + per-task completion lines)
6. Handle failures (retry with exponential backoff, circuit breaker)
7. Merge results (auto-merge duplicates, flag semantic contradictions)
8. Clean up workspace
```

### Command-Specific Parallelization

| Command | Work Units | Max Parallel | Merge Strategy |
|---------|-----------|--------------|----------------|
| analyze | 6 detection passes | All 6 | Concatenate findings by category |
| checklist | 6 quality dimensions | All 6 | Concatenate by dimension |
| plan | N research tasks + 3 Phase 1 artifacts | All N+3 | Sequential phase, parallel within |
| clarify | 10 taxonomy categories | All 10 | Priority queue from all results |
| taskstoissues | N issues | All N | Independent (no merge needed) |
| specify | 4 concept dimensions | All 4 | Merge into unified spec |

### Shared Infrastructure

All commands share:
- **Workspace setup**: `.claude/workspace/` directory structure
- **Progress reporting**: Progress bar + per-task lines format
- **Retry policy**: Exponential backoff (1s, 2s, 4s), max 3 attempts
- **Circuit breaker**: Pause at 3 failures, abort at 10
- **Conflict resolution**: Auto-merge duplicates, flag contradictions
- **Flag parsing**: `--sequential` to force single-agent mode

## Design Decisions

### D1: Task Tool Usage Pattern

Each subagent is spawned via:
```
Task(
  subagent_type: "general-purpose",
  prompt: "[task-specific prompt]",
  description: "[short description]"
)
```

### D2: File-Based Coordination

Subagents write results to `.claude/workspace/results/{task_id}-result.md`. Parent agent monitors completion and merges.

### D3: Progress Reporting Format

```
[████░░░░] 4/6 passes complete
  ✓ duplication (2.1s) - 0 issues
  ✓ ambiguity (3.4s) - 1 issue
  ✓ constitution (1.8s) - 0 issues
  ✓ coverage (4.2s) - 2 issues
  ⏳ underspec...
  ⏳ inconsistency...
```

### D4: Timeout Configuration

- Default: 120 seconds per subagent
- Configurable per-task via prompt context
- Timeout triggers retry with exponential backoff

### D5: Conflict Resolution

- **Duplicates/overlaps**: Auto-merge (keep first occurrence)
- **Semantic contradictions**: Flag to user with both values

## Implementation Phases

### Phase 1: Shared Infrastructure (Foundation)
- Progress reporting module
- Workspace setup/teardown
- Retry policy implementation
- Circuit breaker logic
- Flag parsing (`--sequential`)

### Phase 2: P1 Commands (analyze, checklist)
- Highest impact, clearest parallelization
- Validate infrastructure with real usage

### Phase 3: P2 Commands (plan, clarify)
- More complex coordination
- Multi-phase parallelism

### Phase 4: P3 Commands (taskstoissues, specify)
- Lower priority
- External API considerations (GitHub rate limits)

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Subagent timeout | 120s default + retry with backoff |
| User-set --max-parallel limit exceeded | Greedy queue dispatch |
| Conflicting results | Auto-merge duplicates, flag contradictions |
| User cancellation | Graceful termination, report partial results |
| Context size limits | Minimal context per subagent via workspace files |

## Success Validation

- [ ] All 6 commands support `--sequential` flag
- [ ] `/speckit.analyze` shows 3x speedup (6 parallel passes)
- [ ] `/speckit.checklist` shows 2x speedup (6 parallel dimensions)
- [ ] `/speckit.taskstoissues` shows 5x speedup (all issues in parallel)
- [ ] Progress bar + per-task lines visible during execution
- [ ] Failed subagents retry automatically
- [ ] Circuit breaker triggers at 3 failures
