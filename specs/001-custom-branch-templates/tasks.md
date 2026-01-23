# Tasks: Customizable Branch Naming Templates

**Input**: Design documents from `/specs/001-custom-branch-templates/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: Tests are NOT explicitly requested in the specification. Tasks focus on implementation only.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

Per plan.md, this is a single-project CLI tool:
- Python CLI: `src/specify_cli/__init__.py`
- Bash scripts: `scripts/bash/`
- PowerShell scripts: `scripts/powershell/`
- Templates: `templates/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the settings template file and establish shared utilities

- [X] T001 Create settings template file at templates/settings.toml with documented branch template options per data-model.md schema
- [X] T002 [P] Add TOML parsing utility functions to scripts/bash/common.sh (load_branch_template, get_toml_value)
- [X] T003 [P] Add TOML parsing utility functions to scripts/powershell/common.ps1 (Get-BranchTemplate, Get-TomlValue)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core template resolution logic that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement resolve_username function in scripts/bash/common.sh (Git config → OS fallback per FR-005)
- [X] T005 [P] Implement Resolve-Username function in scripts/powershell/common.ps1 (Git config → OS fallback per FR-005)
- [X] T006 [P] Implement resolve_email_prefix function in scripts/bash/common.sh
- [X] T007 [P] Implement Resolve-EmailPrefix function in scripts/powershell/common.ps1
- [X] T008 Implement validate_branch_name function in scripts/bash/common.sh (validate: no leading `-`, no `..`, no `~^:?*[\` chars, no `.lock` suffix, no trailing `/`, no `//`, max 244 bytes)
- [X] T009 [P] Implement Test-BranchName function in scripts/powershell/common.ps1 (validate: no leading `-`, no `..`, no `~^:?*[\` chars, no `.lock` suffix, no trailing `/`, no `//`, max 244 bytes)
- [X] T010 Implement get_highest_for_prefix function in scripts/bash/common.sh (per-user number scoping per FR-008; this design eliminates race conditions between users by giving each prefix its own sequence)
- [X] T011 [P] Implement Get-HighestNumberForPrefix function in scripts/powershell/common.ps1 (per-user number scoping per FR-008; this design eliminates race conditions between users by giving each prefix its own sequence)

**Checkpoint**: Foundation ready - all template resolution utilities available

---

## Phase 3: User Story 1 - Configure Team Branch Template (Priority: P1) 🎯 MVP

**Goal**: Enable teams to configure custom branch naming templates via settings file

**Independent Test**: Create `.specify/settings.toml` with `template = "{username}/{number}-{short_name}"`, run create-new-feature script, verify branch name matches pattern

### Implementation for User Story 1

- [X] T012 [US1] Integrate load_branch_template into scripts/bash/create-new-feature.sh (read template from settings file)
- [X] T013 [P] [US1] Integrate Get-BranchTemplate into scripts/powershell/create-new-feature.ps1 (read template from settings file)
- [X] T014 [US1] Implement template variable resolution in scripts/bash/create-new-feature.sh (replace {username}, {email_prefix}, {number}, {short_name})
- [X] T015 [P] [US1] Implement template variable resolution in scripts/powershell/create-new-feature.ps1 (replace {username}, {email_prefix}, {number}, {short_name})
- [X] T016 [US1] Add branch name validation call before git checkout in scripts/bash/create-new-feature.sh
- [X] T017 [P] [US1] Add branch name validation call before git checkout in scripts/powershell/create-new-feature.ps1
- [X] T018 [US1] Update error messages in scripts/bash/create-new-feature.sh per FR-006 (syntax errors, invalid branch, unresolved variables)
- [X] T019 [P] [US1] Update error messages in scripts/powershell/create-new-feature.ps1 per FR-006

**Checkpoint**: User Story 1 complete - teams can configure and use custom branch templates

---

## Phase 4: User Story 2 - Default Template Without Configuration (Priority: P2)

**Goal**: Ensure backward compatibility when no settings file exists

**Independent Test**: Remove any `.specify/settings.toml`, run create-new-feature script, verify branch follows `{number}-{short_name}` pattern

### Implementation for User Story 2

- [X] T020 [US2] Add fallback to default template `{number}-{short_name}` when settings file missing in scripts/bash/create-new-feature.sh
- [X] T021 [P] [US2] Add fallback to default template `{number}-{short_name}` when settings file missing in scripts/powershell/create-new-feature.ps1
- [X] T022 [US2] Add fallback when `branch.template` key is missing but settings file exists in scripts/bash/create-new-feature.sh
- [X] T023 [P] [US2] Add fallback when `branch.template` key is missing but settings file exists in scripts/powershell/create-new-feature.ps1

**Checkpoint**: User Story 2 complete - existing workflows continue unchanged

---

## Phase 5: User Story 3 - Resolve Username from Git Config (Priority: P3)

**Goal**: Automatically detect and normalize username from Git configuration

**Independent Test**: Set `git config user.name "Jane Smith"`, use template with `{username}`, verify branch contains `jane-smith`

### Implementation for User Story 3

- [X] T024 [US3] Verify resolve_username handles "Jane Smith" → "jane-smith" normalization in scripts/bash/common.sh
- [X] T025 [P] [US3] Verify Resolve-Username handles "Jane Smith" → "jane-smith" normalization in scripts/powershell/common.ps1
- [X] T026 [US3] Verify OS username fallback works when git config user.name is unset in scripts/bash/common.sh
- [X] T027 [P] [US3] Verify OS username fallback works when git config user.name is unset in scripts/powershell/common.ps1
- [X] T028 [US3] Verify resolve_email_prefix extracts "jsmith" from "jsmith@company.com" in scripts/bash/common.sh
- [X] T029 [P] [US3] Verify Resolve-EmailPrefix extracts "jsmith" from "jsmith@company.com" in scripts/powershell/common.ps1

**Checkpoint**: User Story 3 complete - username resolution works across platforms

---

## Phase 6: User Story 4 - Initialize Settings File (Priority: P4)

**Goal**: Provide CLI command to generate settings file with documented examples

**Independent Test**: Run `specify init --settings`, verify `.specify/settings.toml` created with documented examples

### Implementation for User Story 4

- [X] T030 [US4] Add `--settings` flag to init command in src/specify_cli/__init__.py
- [X] T031 [US4] Add `--force` flag for overwrite confirmation in src/specify_cli/__init__.py
- [X] T032 [US4] Implement settings file generation logic in src/specify_cli/__init__.py (copy from templates/settings.toml)
- [X] T033 [US4] Add overwrite protection with user prompt when settings file exists in src/specify_cli/__init__.py
- [X] T034 [US4] Add success/error output messages per contracts/cli.md in src/specify_cli/__init__.py

**Checkpoint**: User Story 4 complete - teams can initialize settings via CLI

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, versioning, and final cleanup

- [X] T035 Update CHANGELOG.md with feature description for version increment
- [X] T036 [P] Increment version in pyproject.toml (minor version bump for new feature)
- [X] T037 [P] Update README.md with branch template configuration documentation
- [X] T038 [P] Update docs/quickstart.md with settings file usage example
- [X] T039 Verify all scripts work on macOS, Linux, and Windows (manual cross-platform test)

**Checkpoint**: Feature complete and documented

---

## Dependencies & Parallel Execution

### Dependency Graph (by User Story)

```
Phase 1 (Setup) ──────────────────────────────────────────────────┐
  T001, T002, T003 (all parallel)                                 │
                                                                  ▼
Phase 2 (Foundational) ───────────────────────────────────────────┤
  T004 → T005 (parallel)                                          │
  T006 → T007 (parallel)                                          │
  T008 → T009 (parallel)                                          │
  T010 → T011 (parallel)                                          │
                                                                  ▼
┌─────────────────────────────────────────────────────────────────┤
│ Phase 3: US1 (P1)        Phase 4: US2 (P2)     Phase 5: US3 (P3)│
│ T012-T019                T020-T023              T024-T029       │
│ (can start after P2)     (can start after P2)  (can start after P2)
└─────────────────────────────────────────────────────────────────┤
                                                                  │
Phase 6: US4 (P4) ────────────────────────────────────────────────┤
  T030-T034 (can start after Phase 2)                             │
                                                                  ▼
Phase 7 (Polish) ─────────────────────────────────────────────────┘
  T035, T036, T037, T038 (parallel)
  T039 (after all implementation complete)
```

### Parallel Execution Groups

After Phase 2 completes, these user story phases can run in parallel:
- **Group A**: US1 tasks (T012-T019) - Core template configuration
- **Group B**: US2 tasks (T020-T023) - Backward compatibility
- **Group C**: US3 tasks (T024-T029) - Username resolution verification
- **Group D**: US4 tasks (T030-T034) - CLI init --settings

Within each phase, tasks marked `[P]` can run in parallel with other `[P]` tasks in the same phase.

---

## Implementation Strategy

### MVP Scope (Recommended)

**Minimum Viable Product**: Complete Phase 1, Phase 2, and Phase 3 (User Story 1)

This delivers:
- Settings file template
- Template resolution utilities
- Full custom branch template support
- Backward compatibility (default template when no settings)

**MVP Task Range**: T001-T019 (19 tasks)

### Incremental Delivery

1. **MVP** (T001-T019): Custom branch templates work end-to-end
2. **+US2** (T020-T023): Explicit backward compatibility verification
3. **+US3** (T024-T029): Username resolution edge cases
4. **+US4** (T030-T034): CLI convenience command
5. **+Polish** (T035-T039): Documentation and version bump

---

## Summary

| Metric | Value |
|--------|-------|
| Total tasks | 39 |
| Setup tasks | 3 |
| Foundational tasks | 8 |
| US1 tasks | 8 |
| US2 tasks | 4 |
| US3 tasks | 6 |
| US4 tasks | 5 |
| Polish tasks | 5 |
| Parallelizable tasks | 22 (marked with [P]) |
| MVP scope | T001-T019 (19 tasks) |

### Format Validation

✅ All tasks follow checklist format: `- [ ] [TaskID] [P?] [Story?] Description with file path`
✅ Task IDs are sequential (T001-T039)
✅ [P] markers indicate parallelizable tasks
✅ [US#] markers link tasks to user stories (Phases 3-6)
✅ File paths included in all implementation tasks
