# Implementation Plan: Add Simple Hello Command

**Branch**: `002-add-a-simple` | **Date**: 2025-09-13 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-add-a-simple/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → ✅ Loaded feature spec successfully
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → ✅ No NEEDS CLARIFICATION detected - simple CLI command
   → ✅ Project Type: single (CLI tool)
   → ✅ Structure Decision: Option 1 (single project)
3. Evaluate Constitution Check section below
   → ✅ Simple hello command follows all constitutional principles
   → ✅ Update Progress Tracking: Initial Constitution Check
4. Execute Phase 0 → research.md
   → ✅ Generated research.md with CLI command patterns
5. Execute Phase 1 → contracts, data-model.md, quickstart.md, CLAUDE.md
   → ✅ Generated all Phase 1 artifacts
6. Re-evaluate Constitution Check section
   → ✅ No violations detected after design
   → ✅ Update Progress Tracking: Post-Design Constitution Check
7. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
   → ✅ Task generation strategy documented
8. STOP - Ready for /tasks command
   → ✅ Plan complete, ready for next phase
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
Primary requirement: Add a simple `hello` command to the specify CLI tool that displays a greeting message when executed. This command serves as a test case for verifying the `/specify`, `/plan`, and `/tasks` workflow pipeline functionality.

## Technical Context
**Language/Version**: Node.js/TypeScript (existing project stack)
**Primary Dependencies**: Commander.js for CLI parsing (existing)
**Storage**: N/A (simple command output)
**Testing**: Existing test framework (Jest/similar)
**Target Platform**: Cross-platform CLI (existing target)
**Project Type**: single - determines source structure
**Performance Goals**: Immediate response (<10ms for greeting output)
**Constraints**: Must integrate with existing CLI architecture
**Scale/Scope**: Single command, minimal scope for testing purposes

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Simplicity**:
- Projects: 1 (existing CLI project)
- Using framework directly? ✅ (Commander.js directly)
- Single data model? ✅ (simple string output, no complex models)
- Avoiding patterns? ✅ (no unnecessary abstractions for hello command)

**Architecture**:
- EVERY feature as library? ✅ (hello functionality will be in services/)
- Libraries listed: hello-service (simple greeting message generation)
- CLI per library: ✅ specify hello command with --help/--version support
- Library docs: ✅ llms.txt format will be updated

**Testing (NON-NEGOTIABLE)**:
- RED-GREEN-Refactor cycle enforced? ✅ (tests written first)
- Git commits show tests before implementation? ✅ (will follow TDD)
- Order: Contract→Integration→E2E→Unit strictly followed? ✅
- Real dependencies used? ✅ (actual CLI execution)
- Integration tests for: ✅ new command functionality
- FORBIDDEN: ✅ Implementation will come after tests

**Observability**:
- Structured logging included? ✅ (existing logging infrastructure)
- Frontend logs → backend? N/A (CLI only)
- Error context sufficient? ✅ (CLI error handling)

**Versioning**:
- Version number assigned? ✅ (existing semantic versioning)
- BUILD increments on every change? ✅ (existing workflow)
- Breaking changes handled? N/A (new feature, no breaking changes)

## Project Structure

### Documentation (this feature)
```
specs/002-add-a-simple/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
# Option 1: Single project (DEFAULT)
src/
├── models/          # No new models needed
├── services/        # hello-service.ts (new)
├── cli/            # hello-command.ts (new)
└── lib/            # Existing utilities

tests/
├── contract/       # hello.contract.test.ts (new)
├── integration/    # hello.integration.test.ts (new)
└── unit/          # hello.unit.test.ts (new)
```

**Structure Decision**: Option 1 - single project (matches existing CLI tool architecture)

## Phase 0: Outline & Research
✅ **COMPLETED** - Generated research.md

## Phase 1: Design & Contracts
✅ **COMPLETED** - Generated data-model.md, contracts/, quickstart.md, updated CLAUDE.md

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs (contracts, data model, quickstart)
- Each contract → contract test task [P]
- Each entity → service creation task [P]
- Each user story → integration test task
- CLI command implementation tasks to make tests pass

**Ordering Strategy**:
- TDD order: Tests before implementation
- Dependency order: Services before CLI commands
- Mark [P] for parallel execution (independent files)

**Estimated Output**: 8-10 numbered, ordered tasks in tasks.md

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)
**Phase 4**: Implementation (execute tasks.md following constitutional principles)
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*No constitutional violations detected - simple hello command follows all principles*

## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented (none)

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*