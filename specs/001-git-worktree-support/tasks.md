# Tasks: Git Worktree Integration

**Input**: Design documents from `/specs/001-git-worktree-support/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: Not explicitly requested in spec - focusing on manual testing checklist

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create `scripts/bash/manage-worktrees.sh` with file header and source common.sh
- [X] T002 Create `scripts/powershell/manage-worktrees.ps1` with file header and source common.ps1
- [X] T003 [P] Add `.worktrees/` to root `.gitignore` file if not already present

**Checkpoint**: Basic script files created, ready for function implementation

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core utilities that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `ensure_worktree_gitignore()` function in scripts/bash/manage-worktrees.sh
- [X] T005 Implement `get_worktree_status()` function in scripts/bash/manage-worktrees.sh (checks if worktree is active/stale/orphaned by querying git worktree list --porcelain)
- [X] T006 Implement `calculate_disk_usage()` function in scripts/bash/manage-worktrees.sh (uses du -sh for bash)
- [X] T007 [P] Implement `ensure_worktree_gitignore()` function in scripts/powershell/manage-worktrees.ps1
- [X] T008 [P] Implement `get_worktree_status()` function in scripts/powershell/manage-worktrees.ps1
- [X] T009 [P] Implement `calculate_disk_usage()` function in scripts/powershell/manage-worktrees.ps1 (uses Get-ChildItem | Measure-Object)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Automatic Worktree Creation (Priority: P1) 🎯 MVP

**Goal**: Automatically create worktrees when `/speckit.specify` runs, enabling immediate parallel AI agent development

**Independent Test**: Run `/speckit.specify` with any feature description and verify a worktree is created at `.worktrees/<branch-name>/` and linked to the feature branch. Open two terminals (main repo + worktree) and verify both can work simultaneously without conflicts.

### Implementation for User Story 1

- [X] T010 [US1] Implement `prompt_conflict_resolution()` function in scripts/bash/manage-worktrees.sh (interactive prompt with options: 1=stop, 2=cleanup, 3=skip)
- [X] T011 [US1] Implement `create_worktree()` function in scripts/bash/manage-worktrees.sh (calls git worktree add, handles conflicts via prompt_conflict_resolution, calls ensure_worktree_gitignore)
- [X] T012 [US1] Modify `scripts/bash/create-new-feature.sh` after line 191 to source manage-worktrees.sh and call create_worktree with $BRANCH_NAME
- [X] T013 [US1] Add error handling to create-new-feature.sh integration so worktree failure doesn't break branch/spec creation (non-fatal warning)
- [X] T014 [P] [US1] Implement `prompt_conflict_resolution()` function in scripts/powershell/manage-worktrees.ps1
- [X] T015 [P] [US1] Implement `create_worktree()` function in scripts/powershell/manage-worktrees.ps1
- [X] T016 [US1] Modify `scripts/powershell/create-new-feature.ps1` with same integration as bash version
- [X] T017 [US1] Add error handling to create-new-feature.ps1 integration (non-fatal warning)

**Checkpoint**: At this point, `/speckit.specify` automatically creates worktrees and User Story 1 is fully functional

---

## Phase 4: User Story 2 - Manual Worktree Creation (Priority: P2)

**Goal**: Allow developers with existing feature branches to create worktrees retroactively via `/speckit.worktree` command

**Independent Test**: Checkout an existing spec-kit feature branch (like `002-some-feature`), run `/speckit.worktree`, and verify the worktree is created at `.worktrees/002-some-feature/`. Verify graceful error when on main branch or non-feature branch.

### Implementation for User Story 2

- [X] T018 [US2] Create `.claude/commands/speckit.worktree.md` command file with description and workflow for default behavior (create worktree)
- [X] T019 [US2] Add validation in create_worktree() bash function to check if current branch follows ###-feature-name pattern (use regex from common.sh)
- [X] T020 [US2] Add error messages for: on main branch, invalid branch name pattern, not in git repo
- [X] T021 [US2] Test create_worktree() works from subdirectories by using git rev-parse --show-toplevel
- [X] T022 [P] [US2] Add same validation to create_worktree() PowerShell function
- [X] T023 [P] [US2] Add same error messages to PowerShell version
- [X] T024 [US2] Create `templates/commands/worktree.md` for other AI agents (generic version of Claude command)

**Checkpoint**: At this point, User Stories 1 AND 2 both work independently - automatic AND manual worktree creation functional

---

## Phase 5: User Story 3 - View Worktree Status (Priority: P2)

**Goal**: Provide visibility into all worktrees with `/speckit.worktree list` showing branch, path, status, and disk usage

**Independent Test**: Create several worktrees, delete some branches, run `/speckit.worktree list`, and verify: table format with columns, stale worktrees marked, current branch highlighted, total disk usage shown.

### Implementation for User Story 3

- [X] T025 [US3] Implement `list_worktrees()` function in scripts/bash/manage-worktrees.sh that parses git worktree list --porcelain
- [X] T026 [US3] Add logic to detect stale worktrees by checking if branch exists in git branch --list
- [X] T027 [US3] Format output as table with columns: Branch | Path | Status | Disk Usage
- [X] T028 [US3] Highlight current branch's worktree in output (if any)
- [X] T029 [US3] Calculate and display total disk usage across all worktrees at bottom of table
- [X] T030 [US3] Handle case when no worktrees exist (show "No worktrees found" message)
- [X] T031 [P] [US3] Implement `list_worktrees()` function in scripts/powershell/manage-worktrees.ps1 with same features
- [X] T032 [US3] Update `.claude/commands/speckit.worktree.md` to add "list" subcommand documentation
- [X] T033 [US3] Update `templates/commands/worktree.md` with "list" subcommand

**Checkpoint**: All three user stories (US1, US2, US3) now work independently - create automatically, create manually, list status

---

## Phase 6: User Story 4 - Remove Specific Worktree (Priority: P3)

**Goal**: Allow safe removal of specific worktrees with `/speckit.worktree remove [branch]` including uncommitted change warnings

**Independent Test**: Create a worktree, make uncommitted changes, run `/speckit.worktree remove`, verify interactive selection menu appears, verify warning about uncommitted changes, verify branch and specs remain after removal.

### Implementation for User Story 4

- [X] T034 [US4] Implement `check_uncommitted_changes()` function in scripts/bash/manage-worktrees.sh (runs git status --porcelain in worktree path)
- [X] T035 [US4] Implement `remove_worktree()` function in scripts/bash/manage-worktrees.sh with branch name argument (optional)
- [X] T036 [US4] Add interactive selection menu when no branch argument provided (show list of worktrees, number selection)
- [X] T037 [US4] Call check_uncommitted_changes() and prompt for explicit confirmation if uncommitted changes detected
- [X] T038 [US4] Execute git worktree remove <path> followed by directory cleanup (rm -rf for bash)
- [X] T039 [US4] Calculate and display disk space reclaimed after successful removal
- [X] T040 [US4] Add validation: do NOT delete feature branch or specs directory (worktree only)
- [X] T041 [P] [US4] Implement `check_uncommitted_changes()` function in scripts/powershell/manage-worktrees.ps1
- [X] T042 [P] [US4] Implement `remove_worktree()` function in scripts/powershell/manage-worktrees.ps1 with same features
- [X] T043 [US4] Update `.claude/commands/speckit.worktree.md` to add "remove" subcommand documentation
- [X] T044 [US4] Update `templates/commands/worktree.md` with "remove" subcommand

**Checkpoint**: Four user stories complete (US1-US4) - create auto/manual, list, remove all functional

---

## Phase 7: User Story 5 - Clean Up Stale Worktrees (Priority: P3)

**Goal**: Automatically detect and batch-remove stale worktrees with `/speckit.worktree cleanup` command

**Independent Test**: Create worktrees, delete their feature branches, run `/speckit.worktree cleanup`, verify list of stale worktrees displayed, verify batch confirmation prompt, verify all stale worktrees removed and disk space reported.

### Implementation for User Story 5

- [X] T045 [US5] Implement `cleanup_stale_worktrees()` function in scripts/bash/manage-worktrees.sh
- [X] T046 [US5] Detect stale worktrees by checking: branch deleted OR directory exists but not in git worktree list (orphaned)
- [X] T047 [US5] Display list of detected stale worktrees with paths and disk usage
- [X] T048 [US5] Prompt for batch confirmation before removal (Y/N prompt)
- [X] T049 [US5] Loop through stale worktrees calling git worktree remove on each
- [X] T050 [US5] Skip locked or in-use worktrees with warning message (git will prevent removal)
- [X] T051 [US5] Calculate and display total disk space reclaimed after cleanup
- [X] T052 [US5] Handle case when no stale worktrees exist (show "No stale worktrees found" message)
- [X] T053 [P] [US5] Implement `cleanup_stale_worktrees()` function in scripts/powershell/manage-worktrees.ps1 with same features
- [X] T054 [US5] Update `.claude/commands/speckit.worktree.md` to add "cleanup" subcommand documentation
- [X] T055 [US5] Update `templates/commands/worktree.md` with "cleanup" subcommand

**Checkpoint**: All five user stories complete and independently functional

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T056 [P] Update `CLAUDE.md` with worktree workflow section documenting all commands and parallel development patterns
- [X] T057 [P] Update `README.md` with parallel development examples showing two AI agents working simultaneously
- [X] T058 [P] Add troubleshooting section to documentation covering: git version requirements, disk space issues, path handling, cross-platform differences
- [ ] T059 Test all commands on macOS with bash scripts
- [ ] T060 Test all commands on Linux with bash scripts
- [ ] T061 Test all commands on Windows with PowerShell scripts
- [ ] T062 Test with repository paths containing spaces (both bash and PowerShell)
- [ ] T063 Test with `--no-git` repository (verify graceful degradation)
- [ ] T064 Verify `.gitignore` updates work correctly across all platforms
- [ ] T065 Run manual testing checklist from plan.md (11 scenarios)
- [ ] T066 Code review and cleanup of both bash and PowerShell scripts

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P2 → P3 → P3)
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - No dependencies on US1 (independent)
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - No dependencies on US1/US2 (independent)
- **User Story 4 (P3)**: Can start after Foundational (Phase 2) - No dependencies on other stories (independent)
- **User Story 5 (P3)**: Can start after Foundational (Phase 2) - No dependencies on other stories (independent)

### Within Each User Story

- Core functions before integration
- Bash implementation can proceed in parallel with PowerShell implementation (marked [P])
- Command template updates after function implementation
- Each story complete before moving to next priority

### Parallel Opportunities

- T001 and T002 (bash/PowerShell file creation) can run in parallel
- T007-T009 (PowerShell foundational functions) can run in parallel with their bash equivalents
- T014-T015 (PowerShell US1 functions) can run in parallel with bash versions
- T022-T023 (PowerShell US2 validation) can run in parallel with bash versions
- T031 (PowerShell US3 list function) can run in parallel with bash version
- T041-T042 (PowerShell US4 remove functions) can run in parallel with bash versions
- T053 (PowerShell US5 cleanup function) can run in parallel with bash version
- T056-T058 (documentation updates) can run in parallel

---

## Parallel Example: User Story 1 (Bash + PowerShell)

```bash
# Launch bash implementation:
Task: "T010 [US1] Implement prompt_conflict_resolution() in bash"
Task: "T011 [US1] Implement create_worktree() in bash"

# Simultaneously launch PowerShell implementation:
Task: "T014 [P] [US1] Implement prompt_conflict_resolution() in PowerShell"
Task: "T015 [P] [US1] Implement create_worktree() in PowerShell"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup → T001-T003
2. Complete Phase 2: Foundational → T004-T009
3. Complete Phase 3: User Story 1 → T010-T017
4. **STOP and VALIDATE**: Test automatic worktree creation with `/speckit.specify`
5. Verify parallel AI agent workflow works (two terminals, one main repo + one worktree)

**This gives you the core value proposition: automatic worktree creation for parallel development!**

###Incremental Delivery

1. **Foundation** (Phases 1-2) → Basic infrastructure ready
2. **MVP** (Phase 3 / US1) → Automatic creation works → **DEMO THIS!**
3. **Enhancement 1** (Phase 4 / US2) → Manual creation for existing branches → **DEMO THIS!**
4. **Enhancement 2** (Phase 5 / US3) → List/visibility → **DEMO THIS!**
5. **Enhancement 3** (Phase 6 / US4) → Safe removal → **DEMO THIS!**
6. **Enhancement 4** (Phase 7 / US5) → Automated cleanup → **DEMO THIS!**
7. **Polish** (Phase 8) → Documentation and cross-platform testing

Each story adds value without breaking previous stories.

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (T001-T009)
2. Once Foundational is done:
   - **Developer A**: User Story 1 (bash) → T010-T013
   - **Developer B**: User Story 1 (PowerShell) → T014-T017
   - **Developer C**: User Story 2 (bash) → T018-T021
   - **Developer D**: User Story 2 (PowerShell) → T022-T024
3. Stories complete and integrate independently
4. All 5 user stories can theoretically be developed in parallel by different team members

---

## Cross-Platform Testing Matrix

| Test Scenario | macOS (bash) | Linux (bash) | Windows (PowerShell) |
|---------------|--------------|--------------|----------------------|
| Automatic worktree creation | T059 | T060 | T061 |
| Manual worktree creation | T059 | T060 | T061 |
| List worktrees | T059 | T060 | T061 |
| Remove worktree | T059 | T060 | T061 |
| Cleanup stale worktrees | T059 | T060 | T061 |
| Paths with spaces | T062 | T062 | T062 |
| Non-git repository | T063 | T063 | T063 |
| .gitignore updates | T064 | T064 | T064 |

---

## Manual Testing Checklist (from plan.md)

**Run these after T065**:

- [ ] Create worktree automatically with `/speckit.specify`
- [ ] Create worktree manually with `/speckit.worktree`
- [ ] Handle conflict when worktree exists (stop/cleanup/skip)
- [ ] List worktrees with correct status
- [ ] Remove worktree with uncommitted changes (verify prompt)
- [ ] Remove worktree without uncommitted changes
- [ ] Cleanup stale worktrees after branch deletion
- [ ] Verify `.gitignore` contains `.worktrees/`
- [ ] Test with repository paths containing spaces
- [ ] Test with `--no-git` repository (graceful failure)
- [ ] Verify feature creation succeeds even if worktree creation fails

---

## Notes

- [P] tasks = different files, no dependencies - can run in parallel
- [US#] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Bash and PowerShell implementations can proceed in parallel
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Total: 66 tasks organized into 8 phases by user story priority

---

## Task Count Summary

- **Setup**: 3 tasks
- **Foundational**: 6 tasks (blocks all stories)
- **User Story 1 (P1)**: 8 tasks - Automatic creation 🎯 MVP
- **User Story 2 (P2)**: 7 tasks - Manual creation
- **User Story 3 (P2)**: 9 tasks - List/visibility
- **User Story 4 (P3)**: 11 tasks - Remove specific
- **User Story 5 (P3)**: 11 tasks - Cleanup stale
- **Polish**: 11 tasks - Documentation and testing
- **Total**: 66 tasks

**Parallel Opportunities**: 16 tasks marked [P] can run in parallel
**Independent Stories**: All 5 user stories are independently implementable and testable
**Suggested MVP**: Complete Setup + Foundational + User Story 1 (17 tasks) for core value
