# Tasks: Guard CLI MVP Completion

**Input**: Design documents from `/home/royceld/Programming/Personal/spec-kit/specs/001-guard-cli/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md, MVP-SCOPE.md

**Status**: MVP implementation complete (33/96 original tasks), now polishing for release

**Organization**: Tasks focused on MVP completion, validation, and release preparation

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (MVP = MVP completion)
- Include exact file paths in descriptions

## Path Conventions

Single project structure (extending existing specify-cli):
- **Source**: `src/specify_cli/guards/`
- **Tests**: `tests/unit/guards/`, `tests/api/guards/`
- **Guard Types**: `guards/types/` (distributed), `.specify/guards/types/` (local)
- **Registry**: `.specify/guards/list/`, `.specify/guards/history/`, `.specify/guards/index.json`

---

## Phase 1: MVP Completion Guards (MANDATORY)

**Purpose**: Create validation guards for MVP completion criteria per plan.md Guard Validation Strategy

**Existing Guards**:
- ✅ G001: all-unit-tests (21 tests passing)
- ✅ G002: test-commands (command tests)
- ✅ G003: user-endpoints (API scaffolder validation)
- ✅ G004: guard-unit-tests (scaffold created)

**Required Custom Guard**: mvp-validation (verifies MVP scope met)

- [ ] T001 [MVP] Create custom guard type 'mvp-validation' for MVP completion validation [Guard: G005]
  Command: uv run specify guard create-type --name mvp-validation --category validation --description "Validates MVP completion criteria"
  Location: .specify/guards/types-custom/mvp-validation/
  
- [ ] T002 [MVP] Implement mvp-validation scaffolder in .specify/guards/types-custom/mvp-validation/scaffolder.py [Guard: G005]
  Validates: version=0.0.25, only 2 guard types (unit-pytest, api), CHANGELOG updated, no non-MVP types
  
- [ ] T003 [MVP] Create mvp-validation template in .specify/guards/types-custom/mvp-validation/templates/validate.py.j2 [Guard: G005]
  Template checks: pyproject.toml version, guards/types/ contents, CHANGELOG entries, tests pass
  
- [ ] T004 [MVP] Create MVP completion guard [Guard: G005]
  Command: uv run specify guard create --type mvp-validation --name mvp-completion
  Result: G005 created
  
- [ ] T005 [MVP] Run G005 to validate MVP completion [Guard: G005 ✓]
  Command: uv run specify guard run G005
  Must pass before marking MVP complete

**Checkpoint**: MVP validation guard exists and passes ✓

---

## Phase 2: Documentation & Release Prep (Polish)

**Purpose**: Finalize documentation and prepare for v0.0.25 release

- [X] T006 [P] Update pyproject.toml to version 0.0.25
- [X] T007 [P] Update CHANGELOG.md with v0.0.25 release notes
- [X] T008 [P] Create MVP-SCOPE.md documenting what's in/out of MVP
- [X] T009 [P] Create CUSTOM-TYPES.md documenting custom guard types architecture
- [X] T010 [P] Create COMPLETION-SUMMARY.md with delivery summary
- [X] T011 [P] Update plan.md with Guard Validation Strategy and completion status
- [ ] T012 [P] Update README.md with guard CLI section and examples [Guard: G001]
- [ ] T013 [P] Create guards/types/README.md explaining official guard types [Guard: G001]
- [ ] T014 [P] Verify .gitignore includes guard directories properly [Guard: G005]

**Checkpoint**: Documentation complete ✓

---

## Phase 3: Final Validation (CRITICAL)

**Purpose**: Run all guards to ensure MVP is ready for release

- [ ] T015 Run all existing guards to validate implementation [Guard: G001 ✓, G002 ✓, G003 ✓, G005 ✓]
  Commands:
  - uv run specify guard run G001  # All unit tests
  - uv run specify guard run G002  # Command tests
  - uv run specify guard run G003  # API scaffolder
  - uv run specify guard run G005  # MVP completion
  All must pass (exit code 0)

- [ ] T016 Verify guard list shows all 5 guards correctly [Guard: G005]
  Command: uv run specify guard list
  Expected: G001-G005 with correct types and status
  
- [ ] T017 Verify guard types shows only MVP types [Guard: G005]
  Command: uv run specify guard types
  Expected: unit-pytest, api (no database, lint-ruff, docker-playwright)
  
- [ ] T018 [P] Run smoke test: create and run new guard [Guard: G005]
  Commands:
  - uv run specify guard create --type unit-pytest --name smoke-test
  - uv run specify guard run G006
  - uv run specify guard list (verify G006 appears)

**Checkpoint**: All guards passing, MVP validated ✓

---

## Phase 4: Git & Release (Final)

**Purpose**: Prepare for commit and release

- [ ] T019 Review git status and verify all new files are intentional [Guard: G005]
  Command: git status
  Check: All files in specs/, src/, guards/, tests/, templates/ are expected
  
- [ ] T020 Stage all guard CLI files for commit [Guard: G005]
  Command: git add src/specify_cli/guards/ guards/types/ tests/ specs/001-guard-cli/ pyproject.toml CHANGELOG.md templates/commands/ .gitignore memory/constitution.md Makefile
  
- [ ] T021 Verify guard tests still pass after staging [Guard: G001 ✓]
  Command: uv run specify guard run G001
  Ensures no files were missed or incorrectly modified

- [ ] T022 Create commit with guard CLI implementation
  Message: "feat: Add guard CLI system for validation checkpoints (v0.0.25)"
  Body: See CHANGELOG.md for full details
  
- [ ] T023 Verify commit includes all guard CLI files
  Command: git show --stat HEAD
  Check: All expected files present

**Checkpoint**: Ready for PR to main ✓

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Guards)**: No dependencies - create MVP validation guard
- **Phase 2 (Documentation)**: Can run in parallel with Phase 1
- **Phase 3 (Validation)**: Depends on Phase 1 (needs G005) and Phase 2 (docs ready)
- **Phase 4 (Release)**: Depends on Phase 3 (all guards passing)

### Critical Path

```
Create mvp-validation guard type (T001-T004)
  ↓
Create MVP completion guard G005 (T004)
  ↓
Run G005 + all guards (T015)
  ↓
Git commit (T019-T023)
  ↓
Release Ready!
```

---

## Guard Integration Summary

**All validation checkpoints have guards**:
- ✅ Guard CLI implementation → G001 (all-unit-tests)
- ✅ Command logic → G002 (test-commands)
- ✅ API scaffolder → G003 (user-endpoints)
- ✅ Guard unit tests → G004 (guard-unit-tests)
- ⏳ MVP completion → G005 (mvp-validation) - CREATE IN T001-T004

**Guard execution workflow**:
1. Create mvp-validation custom guard type (T001-T003)
2. Create G005 using mvp-validation type (T004)
3. Run G005 to validate MVP (T005)
4. Run all guards before commit (T015)
5. Only proceed to release if all guards pass

**Success criteria**: All guards (G001-G005) pass with exit code 0

---

## Task Count Summary

- **Phase 1 (Guards)**: 5 tasks
- **Phase 2 (Documentation)**: 9 tasks (5 complete)
- **Phase 3 (Validation)**: 4 tasks
- **Phase 4 (Release)**: 5 tasks

**Total**: 23 tasks (10 already complete, 13 remaining)
**Guards**: 5 guards total (G001-G005)
**MVP Status**: Implementation complete, validation and release prep in progress

