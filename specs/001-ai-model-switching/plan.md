# Implementation Plan: AI Model Switching and Task Tracking UI

**Branch**: `001-ai-model-switching` | **Date**: 2025-09-13 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-ai-model-switching/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path ✓
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION) ✓
   → Detect Project Type from context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Evaluate Constitution Check section below ✓
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
4. Execute Phase 0 → research.md ✓
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
5. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file ✓
6. Re-evaluate Constitution Check section ✓
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
7. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md) ✓
8. STOP - Ready for /tasks command ✓
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
Primary requirement: Enable AI model switching (Gemini ↔ Claude) without losing project progress, automatic project detection to eliminate redundant init, and a visual CLI task tracking sidebar showing completed/remaining/failed tasks in real-time.

Technical approach: CLI-first architecture with project state management, model migration utilities, and terminal-based UI components for task visualization.

## Technical Context
**Language/Version**: Node.js/TypeScript (detected from existing CLI structure)
**Primary Dependencies**: Commander.js, Chalk, Blessed (terminal UI), fs-extra
**Storage**: JSON config files, project metadata in .specify directory
**Testing**: Jest with integration tests for CLI commands
**Target Platform**: Cross-platform CLI (Linux, macOS, Windows)
**Project Type**: single - CLI tool with library components
**Performance Goals**: <100ms command response, real-time UI updates
**Constraints**: Terminal compatibility, backward compatibility with existing projects
**Scale/Scope**: Individual developer projects, 1-1000 specs per project

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Simplicity**:
- Projects: 1 (CLI tool)
- Using framework directly? Yes (Commander.js, Blessed)
- Single data model? Yes (project config + task state)
- Avoiding patterns? Yes (direct file operations, no ORM)

**Architecture**:
- EVERY feature as library? Yes
- Libraries listed:
  - model-switcher (AI model management)
  - project-detector (automatic project detection)
  - task-tracker (task state management)
  - ui-renderer (terminal UI components)
- CLI per library: model-switch, detect-project, track-tasks, render-ui commands
- Library docs: llms.txt format planned

**Testing (NON-NEGOTIABLE)**:
- RED-GREEN-Refactor cycle enforced? YES
- Git commits show tests before implementation? YES
- Order: Contract→Integration→E2E→Unit strictly followed? YES
- Real dependencies used? YES (actual file system, real terminal)
- Integration tests for: new libraries, contract changes, CLI commands? YES
- FORBIDDEN: Implementation before test, skipping RED phase

**Observability**:
- Structured logging included? YES (JSON + human readable)
- Frontend logs → backend? N/A (CLI tool)
- Error context sufficient? YES (detailed error messages)

**Versioning**:
- Version number assigned? YES (following existing semver)
- BUILD increments on every change? YES
- Breaking changes handled? YES (migration scripts)

## Project Structure

### Documentation (this feature)
```
specs/001-ai-model-switching/
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
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/
```

**Structure Decision**: Option 1 - Single project (CLI tool with library components)

## Phase 0: Outline & Research

**Research Tasks Completed:**

1. **AI Model Configuration Management**:
   - Decision: JSON-based configuration files in .specify/config/
   - Rationale: Simple, human-readable, easy to migrate
   - Alternatives considered: YAML (more complex), binary (not readable)

2. **Terminal UI Framework Selection**:
   - Decision: Blessed.js for rich terminal interfaces
   - Rationale: Mature, well-documented, supports complex layouts
   - Alternatives considered: Ink (React-based, overkill), raw ANSI (too complex)

3. **Project Detection Strategy**:
   - Decision: Check for .specify directory and config files
   - Rationale: Clear indicator, allows version detection
   - Alternatives considered: Package.json detection (not reliable), git hooks (too invasive)

4. **State Persistence Approach**:
   - Decision: File-based JSON storage with atomic writes
   - Rationale: Simple, reliable, human-inspectable
   - Alternatives considered: SQLite (overkill), in-memory (no persistence)

**Output**: research.md with all technical decisions resolved

## Phase 1: Design & Contracts

**Data Model Entities** (see data-model.md):
- ProjectConfig: stores AI model, version, initialization state
- TaskState: individual task status with timing and error info
- MigrationState: tracks model switching progress
- AIModelSettings: model-specific configuration requirements

**API Contracts** (see contracts/):
- CLI commands for model switching, project detection, task tracking
- File system contracts for configuration management
- Terminal UI contracts for rendering components

**Generated Artifacts**:
- data-model.md: Entity definitions and relationships
- contracts/: CLI command specifications
- quickstart.md: User getting started guide
- CLAUDE.md: Updated with new context (AI model management, task tracking UI)

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs (contracts, data model, quickstart)
- Each CLI command → contract test task [P]
- Each entity → model creation task [P]
- Each user story → integration test task
- Implementation tasks to make tests pass

**Ordering Strategy**:
- TDD order: Tests before implementation
- Dependency order: Models before services before CLI before UI
- Mark [P] for parallel execution (independent files)

**Estimated Output**: 28-32 numbered, ordered tasks in tasks.md

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)
**Phase 4**: Implementation (execute tasks.md following constitutional principles)
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*No constitution violations identified*

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
- [x] Complexity deviations documented (none found)

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*