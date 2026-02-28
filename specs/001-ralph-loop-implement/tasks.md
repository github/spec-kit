# Tasks: Ralph Loop Implementation Support

**Input**: Design documents from `/specs/001-ralph-loop-implement/`  
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4, US5)
- Exact file paths included in descriptions

---

## Phase 1: Setup

**Purpose**: Create project structure and shared infrastructure for ralph loop

- [x] T001 Create ralph iteration prompt template in templates/ralph-prompt.md per contracts/prompt-template.md spec
- [x] T002 [P] Add progress.txt file format documentation to data-model.md if needed
- [x] T003 [P] Verify .gitignore includes progress.txt patterns appropriately

**Checkpoint**: Template and documentation infrastructure ready

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core CLI entry point and shared utilities that ALL user stories depend on

**⚠️ CRITICAL**: No user story implementation can begin until this phase is complete

- [x] T004 Add `ralph` command skeleton to src/specify_cli/__init__.py with Typer
- [x] T005 Add `--max-iterations` option with default value of 10
- [x] T006 Add `--model` option for AI model selection (default: claude-sonnet-4.5)
- [x] T007 Implement prerequisite validation (tasks.md exists, copilot CLI available, git repo)
- [x] T008 [P] Create scripts/powershell/ralph-loop.ps1 skeleton with parameter handling
- [x] T009 [P] Create scripts/bash/ralph-loop.sh skeleton with parameter handling

**Checkpoint**: CLI entry point functional, can invoke (empty) platform scripts

---

## Phase 3: User Story 1 - Basic Ralph Loop Execution (Priority: P1) 🎯 MVP

**Goal**: Run a CLI command that iterates through tasks using Copilot CLI until completion or limit

**Independent Test**: Run `specify ralph` on a project with tasks.md; observe agent iterates through tasks

### Tests for User Story 1

- [x] T010 [P] [US1] Unit test for prompt template placeholder replacement in tests/unit/test_ralph_prompt.py
- [x] T011 [P] [US1] Integration test for loop execution with mock agent in tests/integration/test_ralph_loop.py

### Implementation for User Story 1

- [x] T012 [US1] Implement prompt template placeholder replacement in ralph-loop.ps1
- [x] T013 [US1] Implement Copilot CLI invocation with --agent speckit.implement flag in ralph-loop.ps1
- [x] T014 [US1] Implement iteration loop with counter and max-iterations check in ralph-loop.ps1
- [x] T015 [US1] Implement `<promise>COMPLETE</promise>` token detection for loop termination in ralph-loop.ps1
- [x] T016 [US1] Implement iteration summary output (iteration number, status) in ralph-loop.ps1
- [x] T017 [P] [US1] Implement prompt template placeholder replacement in ralph-loop.sh
- [x] T018 [P] [US1] Implement Copilot CLI invocation with --agent flag in ralph-loop.sh
- [x] T019 [P] [US1] Implement iteration loop with counter and max-iterations check in ralph-loop.sh
- [x] T020 [P] [US1] Implement `<promise>COMPLETE</promise>` token detection in ralph-loop.sh
- [x] T021 [P] [US1] Implement iteration summary output in ralph-loop.sh
- [x] T022 [US1] Wire Python CLI to invoke correct platform script based on OS

**Checkpoint**: Basic loop execution works - can run `specify ralph` and see iterations

---

## Phase 4: User Story 2 - Progress Tracking and Learning Persistence (Priority: P2)

**Goal**: Maintain a progress log so each fresh agent context learns from previous iterations

**Independent Test**: Run multiple iterations; verify progress.txt is updated and readable

### Implementation for User Story 2

- [x] T021 [US2] Create initial progress.txt with header on first iteration in ralph-loop.ps1
- [x] T022 [US2] Implement progress entry append after each iteration in ralph-loop.ps1
- [x] T023 [US2] Add Codebase Patterns section handling in ralph-loop.ps1
- [x] T024 [P] [US2] Create initial progress.txt with header on first iteration in ralph-loop.sh
- [x] T025 [P] [US2] Implement progress entry append after each iteration in ralph-loop.sh
- [x] T026 [P] [US2] Add Codebase Patterns section handling in ralph-loop.sh
- [x] T027 [US2] Update prompt template to include progress file reading instructions

**Checkpoint**: Progress tracking works - iterations persist learnings

---

## Phase 5: User Story 3 - Task Status Synchronization (Priority: P2)

**Goal**: Track which tasks are complete so iterations pick up where previous ones left off

**Independent Test**: Complete one task manually; start ralph loop; verify it picks next task

### Implementation for User Story 3

- [x] T028 [US3] Implement tasks.md checkbox parsing to count incomplete tasks in ralph-loop.ps1
- [x] T029 [US3] Implement early termination when no incomplete tasks remain in ralph-loop.ps1
- [x] T030 [P] [US3] Implement tasks.md checkbox parsing in ralph-loop.sh
- [x] T031 [P] [US3] Implement early termination when no incomplete tasks in ralph-loop.sh
- [x] T032 [US3] Update prompt template to instruct agent on checkbox update format

**Checkpoint**: Task synchronization works - loop respects existing task completion

---

## Phase 6: User Story 4 - Configurable Iteration Limits (Priority: P3)

**Goal**: Control maximum iterations to prevent runaway execution

**Independent Test**: Set `--max-iterations 3`; verify loop stops after 3 iterations

### Implementation for User Story 4

- [x] T033 [US4] Pass max-iterations parameter from Python CLI to PowerShell script
- [x] T034 [US4] Implement configurable limit enforcement in ralph-loop.ps1
- [x] T035 [US4] Add termination message when limit reached (vs completion) in ralph-loop.ps1
- [x] T036 [P] [US4] Pass max-iterations parameter from Python CLI to Bash script
- [x] T037 [P] [US4] Implement configurable limit enforcement in ralph-loop.sh
- [x] T038 [P] [US4] Add termination message when limit reached in ralph-loop.sh

**Checkpoint**: Iteration limits work - loop respects configured maximum

---

## Phase 7: User Story 5 - Multi-Agent CLI Support (Priority: P3)

**Goal**: Support different agent CLIs (MVP: Copilot only with architecture for future agents)

**Independent Test**: Run with non-Copilot agent; see informative error about MVP limitation

### Implementation for User Story 5

- [x] T039 [US5] Detect configured agent from .specify/config or project initialization
- [x] T040 [US5] Add agent validation in Python CLI (Copilot only for MVP)
- [x] T041 [US5] Display helpful error message for unsupported agents
- [x] T042 [US5] Document agent extension points in code comments for future agents

**Checkpoint**: Agent detection works - clear error for non-Copilot, ready for future agents

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Error handling, edge cases, graceful interruption, documentation

- [x] T043 Implement graceful Ctrl+C handling with progress preservation in ralph-loop.ps1
- [x] T044 [P] Implement graceful Ctrl+C handling with progress preservation in ralph-loop.sh
- [x] T045 Implement consecutive failure tracking (skip after 3 failures) in ralph-loop.ps1
- [x] T046 [P] Implement consecutive failure tracking in ralph-loop.sh
- [x] T047 Add error handling for missing tasks.md with guidance to run /speckit.tasks
- [x] T048 Add error handling for missing copilot CLI with installation instructions
- [x] T049 Add warning when git has uncommitted changes before starting
- [x] T050 Update quickstart.md with final usage examples and troubleshooting
- [x] T051 Add --verbose flag for detailed iteration output

**Checkpoint**: Production-ready with proper error handling and documentation

---

## Dependencies

```
Phase 1 (Setup) ──────────────────────────────────────────────┐
                                                              │
Phase 2 (Foundational) ───────────────────────────────────────┤
    │                                                         │
    ├── Phase 3 (US1: Basic Loop) ─── 🎯 MVP COMPLETE ────────┤
    │       │                                                 │
    │       ├── Phase 4 (US2: Progress Tracking) ─────────────┤
    │       │                                                 │
    │       ├── Phase 5 (US3: Task Sync) ─────────────────────┤
    │       │                                                 │
    │       ├── Phase 6 (US4: Iteration Limits) ──────────────┤
    │       │                                                 │
    │       └── Phase 7 (US5: Multi-Agent) ───────────────────┤
    │                                                         │
    └── Phase 8 (Polish) ─────────────────────────────────────┘
```

**Key Points**:
- Phases 1-2 must complete before any user story work
- Phase 3 (US1) is the MVP - delivers core value
- Phases 4-7 can be worked in priority order after US1
- Phase 8 can be done incrementally throughout or at the end

## Parallel Execution Opportunities

**Within Phase 2**:
- T008 (PowerShell skeleton) ∥ T009 (Bash skeleton)

**Within Phase 3 (US1)**:
- PowerShell implementation (T010-T014) ∥ Bash implementation (T015-T019)

**Within Phase 4 (US2)**:
- PowerShell progress (T021-T023) ∥ Bash progress (T024-T026)

**Within Phase 5 (US3)**:
- PowerShell task parsing (T028-T029) ∥ Bash task parsing (T030-T031)

**Within Phase 8**:
- T043 (PS Ctrl+C) ∥ T044 (Bash Ctrl+C)
- T045 (PS failure tracking) ∥ T046 (Bash failure tracking)

## Summary

| Phase | Tasks | Parallel | Description |
|-------|-------|----------|-------------|
| 1. Setup | 3 | 2 | Template and docs |
| 2. Foundational | 6 | 2 | CLI entry + script skeletons |
| 3. US1 (P1) 🎯 | 11 | 5 | Basic loop execution (MVP) |
| 4. US2 (P2) | 7 | 3 | Progress tracking |
| 5. US3 (P2) | 5 | 2 | Task synchronization |
| 6. US4 (P3) | 6 | 3 | Iteration limits |
| 7. US5 (P3) | 4 | 0 | Multi-agent support |
| 8. Polish | 9 | 4 | Error handling & docs |
| **Total** | **51** | **21** | |

**MVP Scope**: Phases 1-3 (20 tasks) delivers a working ralph loop with basic iteration
