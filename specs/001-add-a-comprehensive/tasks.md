# Tasks: Add a Quality & Recovery Suite to Spec Kit

## Phase 1: Create Command Templates
- [ ] T001 [P] Create /debug command template in `templates/commands/debug.md`
- [ ] T002 [P] Create /align command template in `templates/commands/align.md`
- [ ] T003 [P] Create /rollback-feature command template in `templates/commands/rollback-feature.md`
- [ ] T004 [P] Create /diagnose command template in `templates/commands/diagnose.md`
- [ ] T005 [P] Create /sync-tasks command template in `templates/commands/sync-tasks.md`

## Phase 2: Implement Backing Scripts (Bash)
- [ ] T006 [P] Implement /debug bash script in `scripts/bash/collect-debug-context.sh`
- [ ] T007 [P] Implement /align bash script in `scripts/bash/apply-align.sh`
- [ ] T008 [P] Implement /rollback-feature bash script in `scripts/bash/rollback-feature.sh`
- [ ] T009 [P] Implement /diagnose bash script in `scripts/bash/run-diagnose.sh`
- [ ] T010 [P] Implement /sync-tasks bash script in `scripts/bash/sync-tasks.sh`

## Phase 3: Implement Backing Scripts (PowerShell)
- [ ] T011 [P] Implement /debug PowerShell script in `scripts/powershell/collect-debug-context.ps1`
- [ ] T012 [P] Implement /align PowerShell script in `scripts/powershell/apply-align.ps1`
- [ ] T013 [P] Implement /rollback-feature PowerShell script in `scripts/powershell/rollback-feature.ps1`
- [ ] T014 [P] Implement /diagnose PowerShell script in `scripts/powershell/run-diagnose.ps1`
- [ ] T015 [P] Implement /sync-tasks PowerShell script in `scripts/powershell/sync-tasks.ps1`

## Phase 4: Integration & Documentation
- [ ] T016 Update release packaging script `.github/workflows/scripts/create-release-packages.sh` to include the five new command templates.
- [ ] T017 Update command reference table in `README.md` to add the new commands.
- [ ] T018 Update workflow documentation in `spec-driven.md` to describe the Quality & Recovery Suite.
- [ ] T019 Update `CHANGELOG.md` with the new feature and update version in `pyproject.toml`.