# Tasks: Add Simple Hello Command

**Input**: Design documents from `/specs/002-add-a-simple/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → ✅ Loaded implementation plan successfully
   → ✅ Extract: Node.js/TypeScript, Commander.js, single project structure
2. Load optional design documents:
   → ✅ data-model.md: Extract HelloResponse entity, HelloService interface
   → ✅ contracts/: 2 contract files → 2 contract test tasks
   → ✅ research.md: Extract CLI patterns, TDD approach
3. Generate tasks by category:
   → ✅ Setup: TypeScript project structure, linting
   → ✅ Tests: contract tests, integration tests
   → ✅ Core: HelloResponse model, HelloService, CLI command
   → ✅ Integration: Commander.js registration
   → ✅ Polish: unit tests, performance validation
4. Apply task rules:
   → ✅ Different files = mark [P] for parallel
   → ✅ Same file = sequential (no [P])
   → ✅ Tests before implementation (TDD)
5. Number tasks sequentially (T001, T002...)
6. Generate dependency graph
7. Create parallel execution examples
8. Validate task completeness:
   → ✅ All contracts have tests
   → ✅ All entities have models
   → ✅ All CLI commands implemented
9. Return: SUCCESS (tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Single project**: `src/`, `tests/` at repository root
- Paths shown below assume single project structure per plan.md

## Phase 3.1: Setup
- [ ] T001 Verify existing TypeScript project structure and dependencies
- [ ] T002 [P] Configure hello command build path in existing TypeScript config
- [ ] T003 [P] Update existing linting rules to include new hello command files

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**
- [ ] T004 [P] Contract test HelloService interface in tests/contract/hello-service.contract.test.ts
- [ ] T005 [P] Contract test hello CLI command in tests/contract/hello-command.contract.test.ts
- [ ] T006 [P] Integration test hello command execution in tests/integration/hello.integration.test.ts
- [ ] T007 [P] Integration test hello command help flag in tests/integration/hello-help.integration.test.ts

## Phase 3.3: Core Implementation (ONLY after tests are failing)
- [ ] T008 [P] HelloResponse interface/type in src/models/hello-response.ts
- [ ] T009 [P] HelloService class implementation in src/services/hello-service.ts
- [ ] T010 HelloCommand implementation in src/cli/hello-command.ts
- [ ] T011 Register hello command with Commander.js program in main CLI entry point
- [ ] T012 Add hello command description and help text
- [ ] T013 Implement error handling for hello command execution

## Phase 3.4: Integration
- [ ] T014 Verify hello command integrates with existing CLI logging infrastructure
- [ ] T015 Add hello command to CLI help system and command listing
- [ ] T016 Ensure hello command follows existing CLI error handling patterns
- [ ] T017 Verify hello command version information consistency

## Phase 3.5: Polish
- [ ] T018 [P] Unit tests for HelloService in tests/unit/hello-service.unit.test.ts
- [ ] T019 [P] Unit tests for HelloResponse validation in tests/unit/hello-response.unit.test.ts
- [ ] T020 Performance validation: verify <10ms greeting generation time
- [ ] T021 Performance validation: verify <1000ms total CLI execution time
- [ ] T022 [P] Update CLI help documentation to include hello command
- [ ] T023 Run quickstart.md validation scenarios to verify implementation
- [ ] T024 Final code review and cleanup for hello command implementation

## Dependencies
- Tests (T004-T007) before implementation (T008-T013)
- T008 blocks T009 (HelloService depends on HelloResponse)
- T009 blocks T010 (HelloCommand depends on HelloService)
- T010 blocks T011 (CLI registration depends on command implementation)
- Implementation (T008-T017) before polish (T018-T024)

## Parallel Example
```bash
# Launch T004-T007 together (TDD phase):
# These can run in parallel since they create different test files
Task: "Contract test HelloService interface in tests/contract/hello-service.contract.test.ts"
Task: "Contract test hello CLI command in tests/contract/hello-command.contract.test.ts"
Task: "Integration test hello command execution in tests/integration/hello.integration.test.ts"
Task: "Integration test hello command help flag in tests/integration/hello-help.integration.test.ts"

# Launch T008-T009 together after tests fail:
# These can run in parallel since they create different source files
Task: "HelloResponse interface/type in src/models/hello-response.ts"
Task: "HelloService class implementation in src/services/hello-service.ts"

# Launch T018-T019 together (polish phase):
# These can run in parallel since they create different test files
Task: "Unit tests for HelloService in tests/unit/hello-service.unit.test.ts"
Task: "Unit tests for HelloResponse validation in tests/unit/hello-response.unit.test.ts"
```

## Notes
- [P] tasks = different files, no dependencies between them
- Verify tests fail before implementing (RED-GREEN-Refactor)
- Commit after each task completion
- Hello command is intentionally simple for workflow testing
- Focus on integration with existing CLI architecture

## Task Generation Rules Applied
*Applied during main() execution*

1. **From Contracts**:
   - hello-service.contract.ts → T004 contract test task [P]
   - hello-command.contract.ts → T005 contract test task [P]

2. **From Data Model**:
   - HelloResponse entity → T008 model creation task [P]
   - HelloService interface → T009 service implementation task [P]

3. **From User Stories (quickstart.md)**:
   - Basic execution story → T006 integration test [P]
   - Help flag story → T007 integration test [P]
   - Validation scenarios → T023 quickstart validation task

4. **Ordering Applied**:
   - Setup (T001-T003) → Tests (T004-T007) → Models (T008-T009) → Services (T010-T013) → Integration (T014-T017) → Polish (T018-T024)

## Validation Checklist
*GATE: Checked by main() before returning*

- [x] All contracts have corresponding tests (T004, T005)
- [x] All entities have model tasks (T008 for HelloResponse)
- [x] All tests come before implementation (T004-T007 before T008-T013)
- [x] Parallel tasks truly independent (different files, no shared state)
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task
- [x] TDD cycle enforced (RED phase T004-T007, GREEN phase T008-T024)
- [x] Constitutional principles followed (library-first, testing-first)

## Success Criteria
Implementation is complete when:
- All tasks T001-T024 are completed ✅
- All tests pass (GREEN phase of TDD) ✅
- quickstart.md validation scenarios all pass ✅
- Hello command integrates seamlessly with existing CLI ✅
- Performance requirements (<10ms greeting, <1000ms total) are met ✅