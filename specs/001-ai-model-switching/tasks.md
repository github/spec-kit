# Tasks: AI Model Switching and Task Tracking UI

**Input**: Design documents from `/specs/001-ai-model-switching/`
**Prerequisites**: plan.md ✓, research.md ✓, data-model.md ✓, contracts/ ✓

## Execution Flow (main)
```
1. Load plan.md from feature directory ✓
   → Tech stack: Node.js/TypeScript, Commander.js, Blessed.js, fs-extra, Jest
   → Structure: Single project (src/, tests/ at root)
2. Load design documents ✓:
   → data-model.md: 4 entities → model tasks
   → contracts/: 5 CLI commands, 4 UI components → contract test tasks
   → quickstart.md: 4 scenarios → integration test tasks
3. Generate tasks by category ✓:
   → Setup: project structure, dependencies, TypeScript config
   → Tests: contract tests (9), integration tests (4)
   → Core: models (4), services (4), CLI commands (5)
   → UI: components (4), terminal rendering
   → Polish: unit tests, performance validation, docs
4. Apply task rules ✓:
   → Different files = [P] for parallel
   → Tests before implementation (TDD enforced)
5. Number tasks sequentially T001-T035 ✓
6. Dependencies: Setup → Tests → Models → Services → CLI → UI → Polish ✓
7. Validation: All contracts tested, all entities modeled, TDD order ✓
8. Return: SUCCESS (35 tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- All file paths are absolute from repository root

## Path Conventions
- **Single project structure**: `src/`, `tests/` at repository root
- **TypeScript**: `.ts` extension for source, `.test.ts` for tests
- **Testing**: Jest with contract/, integration/, unit/ subdirectories

## Phase 3.1: Setup
- [ ] T001 Create project structure with src/{models,services,cli,lib}/ and tests/{contract,integration,unit}/ directories
- [ ] T002 Initialize TypeScript configuration for Node.js CLI with strict mode and module resolution
- [ ] T003 [P] Install and configure dependencies: commander, blessed, fs-extra, chalk, semver, uuid
- [ ] T004 [P] Configure Jest testing framework with TypeScript support and test environments
- [ ] T005 [P] Setup ESLint and Prettier for TypeScript code formatting and linting

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### Contract Tests (CLI Commands)
- [ ] T006 [P] Contract test `specify switch-model claude` in tests/contract/switch-model.test.ts
- [ ] T007 [P] Contract test `specify list-models --format json` in tests/contract/list-models.test.ts
- [ ] T008 [P] Contract test `specify detect-project --validate` in tests/contract/detect-project.test.ts
- [ ] T009 [P] Contract test `specify reset-project --backup` in tests/contract/reset-project.test.ts
- [ ] T010 [P] Contract test `specify track-tasks enable --sidebar` in tests/contract/track-tasks.test.ts

### Contract Tests (UI Components)
- [ ] T011 [P] Contract test TaskTrackingSidebar real-time updates in tests/contract/task-sidebar.test.ts
- [ ] T012 [P] Contract test ModelSwitchDialog interaction flow in tests/contract/model-dialog.test.ts
- [ ] T013 [P] Contract test ProgressIndicator display modes in tests/contract/progress-indicator.test.ts
- [ ] T014 [P] Contract test ProjectDetectionPanel validation display in tests/contract/detection-panel.test.ts

### Integration Tests (User Scenarios)
- [ ] T015 [P] Integration test: Switch from Gemini to Claude preserving specs in tests/integration/model-switching.test.ts
- [ ] T016 [P] Integration test: Auto-detect existing project without init in tests/integration/auto-detection.test.ts
- [ ] T017 [P] Integration test: Task tracking UI during complex command in tests/integration/task-tracking.test.ts
- [ ] T018 [P] Integration test: Error recovery and backup restoration in tests/integration/error-recovery.test.ts

## Phase 3.3: Core Implementation (ONLY after tests are failing)

### Data Models
- [ ] T019 [P] ProjectConfig entity with JSON schema validation in src/models/ProjectConfig.ts
- [ ] T020 [P] AIModelSettings entity with capability definitions in src/models/AIModelSettings.ts
- [ ] T021 [P] TaskState entity with status transitions in src/models/TaskState.ts
- [ ] T022 [P] MigrationState entity with rollback support in src/models/MigrationState.ts

### Service Libraries
- [ ] T023 [P] ModelSwitcher service for AI model management in src/services/ModelSwitcher.ts
- [ ] T024 [P] ProjectDetector service for automatic project detection in src/services/ProjectDetector.ts
- [ ] T025 [P] TaskTracker service for task state management in src/services/TaskTracker.ts
- [ ] T026 [P] ConfigManager service for atomic file operations in src/services/ConfigManager.ts

### CLI Commands
- [ ] T027 SwitchModelCommand implementation with migration logic in src/cli/SwitchModelCommand.ts
- [ ] T028 ListModelsCommand with compatibility checking in src/cli/ListModelsCommand.ts
- [ ] T029 DetectProjectCommand with validation and repair in src/cli/DetectProjectCommand.ts
- [ ] T030 ResetProjectCommand with backup creation in src/cli/ResetProjectCommand.ts
- [ ] T031 TrackTasksCommand with UI toggle in src/cli/TrackTasksCommand.ts

## Phase 3.4: UI Components
- [ ] T032 TaskTrackingSidebar blessed.js component with real-time updates in src/lib/ui/TaskTrackingSidebar.ts
- [ ] T033 Terminal layout manager for sidebar and main content in src/lib/ui/LayoutManager.ts

## Phase 3.5: Integration
- [ ] T034 CLI entry point integrating all commands with Commander.js in src/cli/index.ts

## Phase 3.6: Polish
- [ ] T035 [P] Unit tests for JSON schema validation in tests/unit/validation.test.ts

## Dependencies
**Critical Path**: Setup (T001-T005) → Tests (T006-T018) → Models (T019-T022) → Services (T023-T026) → CLI (T027-T031) → UI (T032-T033) → Integration (T034) → Polish (T035)

**Blocking Relationships**:
- T019-T022 (models) block T023-T026 (services)
- T023-T026 (services) block T027-T031 (CLI commands)
- T025 (TaskTracker) blocks T032 (TaskTrackingSidebar)
- T027-T031 (CLI commands) block T034 (CLI integration)
- All implementation (T019-T034) requires tests (T006-T018) to be failing first

## Parallel Execution Examples

### Phase 3.2 (All Contract Tests)
```bash
# Launch T006-T014 together - different test files, no dependencies:
Task: "Contract test specify switch-model claude in tests/contract/switch-model.test.ts"
Task: "Contract test specify list-models --format json in tests/contract/list-models.test.ts"
Task: "Contract test specify detect-project --validate in tests/contract/detect-project.test.ts"
Task: "Contract test specify reset-project --backup in tests/contract/reset-project.test.ts"
Task: "Contract test specify track-tasks enable --sidebar in tests/contract/track-tasks.test.ts"
Task: "Contract test TaskTrackingSidebar real-time updates in tests/contract/task-sidebar.test.ts"
Task: "Contract test ModelSwitchDialog interaction flow in tests/contract/model-dialog.test.ts"
Task: "Contract test ProgressIndicator display modes in tests/contract/progress-indicator.test.ts"
Task: "Contract test ProjectDetectionPanel validation display in tests/contract/detection-panel.test.ts"
```

### Phase 3.2 (All Integration Tests)
```bash
# Launch T015-T018 together - different test files, independent scenarios:
Task: "Integration test: Switch from Gemini to Claude preserving specs in tests/integration/model-switching.test.ts"
Task: "Integration test: Auto-detect existing project without init in tests/integration/auto-detection.test.ts"
Task: "Integration test: Task tracking UI during complex command in tests/integration/task-tracking.test.ts"
Task: "Integration test: Error recovery and backup restoration in tests/integration/error-recovery.test.ts"
```

### Phase 3.3 (All Data Models)
```bash
# Launch T019-T022 together - different model files, no dependencies:
Task: "ProjectConfig entity with JSON schema validation in src/models/ProjectConfig.ts"
Task: "AIModelSettings entity with capability definitions in src/models/AIModelSettings.ts"
Task: "TaskState entity with status transitions in src/models/TaskState.ts"
Task: "MigrationState entity with rollback support in src/models/MigrationState.ts"
```

### Phase 3.3 (All Service Libraries)
```bash
# Launch T023-T026 together - different service files, depend only on models:
Task: "ModelSwitcher service for AI model management in src/services/ModelSwitcher.ts"
Task: "ProjectDetector service for automatic project detection in src/services/ProjectDetector.ts"
Task: "TaskTracker service for task state management in src/services/TaskTracker.ts"
Task: "ConfigManager service for atomic file operations in src/services/ConfigManager.ts"
```

## Notes
- **TDD Enforcement**: All tests (T006-T018) must be written and failing before any implementation (T019-T035)
- **[P] Constraints**: Only tasks operating on different files can run in parallel
- **File System**: Use atomic writes for all configuration changes to prevent corruption
- **Terminal Compatibility**: Test UI components across different terminal sizes and capabilities
- **Backward Compatibility**: Ensure model switching preserves existing project structure and data

## Task Generation Rules Applied
1. **From Contracts**: 5 CLI commands + 4 UI components → 9 contract tests (T006-T014)
2. **From Data Model**: 4 entities → 4 model creation tasks (T019-T022)
3. **From User Stories**: 4 quickstart scenarios → 4 integration tests (T015-T018)
4. **From Architecture**: 4 service libraries → 4 service tasks (T023-T026)
5. **Ordering**: Setup → Tests → Models → Services → CLI → UI → Polish

## Validation Checklist ✅
- [x] All contracts have corresponding tests (T006-T014 cover all CLI commands and UI components)
- [x] All entities have model tasks (T019-T022 cover all 4 data model entities)
- [x] All tests come before implementation (T006-T018 before T019-T035)
- [x] Parallel tasks truly independent (different files, no shared dependencies)
- [x] Each task specifies exact file path (absolute paths from repository root)
- [x] No task modifies same file as another [P] task (verified file isolation)

---

**Tasks Status**: ✅ Complete - Ready for implementation execution (35 tasks generated)