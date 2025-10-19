# Implementation Plan: Guard CLI Implementation

**Branch**: `001-guard-cli` | **Date**: 2025-10-19 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/001-guard-cli/spec.md`

## Summary

Implement a guard CLI system for spec-driven development that enables AI agents to create validation checkpoints with opinionated boilerplate code. Guards are executable validation scripts that verify task completion with pass/fail results. The MVP includes core commands (create, run, list, types, create-type), two official guard types (unit-pytest, api), and a custom guard type architecture for extensibility.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: typer (CLI), rich (output), jinja2 (templates), pyyaml (manifests), pytest (testing)  
**Storage**: File-based registry (`.specify/guards/list/`, `history/`, `index.json`)  
**Testing**: pytest with 21 unit tests (registry, executor, types, utils)  
**Target Platform**: Linux/macOS/Windows (cross-platform CLI)  
**Project Type**: Single project (extending existing specify-cli)  
**Performance Goals**: Guard creation < 5s, guard execution with timeout (300s default)  
**Constraints**: Must work offline, no external dependencies for core functionality  
**Scale/Scope**: MVP with 2 guard types (unit-pytest, api), ~1000 LOC implementation

## Guard Validation Strategy

| Validation Checkpoint | Guard Type | Rationale | Status |
|----------------------|------------|-----------|---------|
| Guard CLI commands | unit-pytest | Core business logic validation | ✅ G001, G002 exist |
| Guard registry operations | unit-pytest | File operations, metadata | ✅ Covered by G001 |
| Guard executor | unit-pytest | Subprocess, timeout, history | ✅ Covered by G001 |
| Guard type discovery | unit-pytest | Type scanning both official/custom | ✅ Covered by G001 |
| Guard scaffolder templates | unit-pytest | Template rendering | ✅ Covered by G001 |
| API guard type scaffolder | api | API guard creation works | ✅ G003 exists |
| MVP completion criteria | **[CREATE: mvp-validation]** | Verify MVP scope, version, no non-MVP artifacts | ⏳ TODO in /tasks |

**Custom Guard Type Needed**:
- **mvp-validation** - Validates MVP completion criteria (correct version, only MVP guard types present, all tests pass, documentation complete)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

✅ **Principle I (Incremental Value)**: MVP delivers functional guard creation and execution  
✅ **Principle II (Testability)**: 21 unit tests, guards validate guards (meta-circular)  
✅ **Principle III (Modularity)**: Clean separation (registry, executor, types, scaffolder)  
✅ **Principle IV (Performance)**: Guard creation < 5s, file-based registry  
✅ **Principle V (Guards)**: Guards validate their own implementation (G001-G004)  

**No constitutional violations** - Ready for implementation

## Project Structure

### Documentation (this feature)

```
specs/001-guard-cli/
├── plan.md              # This file
├── research.md          # Technical decisions (file-based registry vs. SQLite)
├── data-model.md        # Guard, GuardType, GuardRegistry entities
├── quickstart.md        # Usage examples
├── tasks.md             # MVP task breakdown
├── MVP-SCOPE.md         # What's in/out of MVP
├── CUSTOM-TYPES.md      # Custom guard types architecture
└── COMPLETION-SUMMARY.md # Delivery summary
```

### Source Code (repository root)

```
src/specify_cli/guards/
├── __init__.py
├── commands.py          # CLI commands (create, run, list, types, create-type)
├── executor.py          # Guard execution with timeout/history
├── registry.py          # File-based registry
├── scaffolder.py        # Base scaffolder class
├── types.py             # Guard type discovery (official + custom)
└── utils.py             # Helper functions

guards/types/            # Official guard types (distributed)
├── unit-pytest/
│   ├── guard-type.yaml
│   ├── scaffolder.py
│   └── templates/
└── api/
    ├── guard-type.yaml
    ├── scaffolder.py
    └── templates/

tests/unit/guards/       # Unit tests (21 passing)
├── conftest.py
├── test_executor.py
├── test_registry.py
├── test_types.py
├── test_utils.py
├── G002_test-commands.py
└── G004_guard-unit-tests.py

tests/api/guards/        # API guard tests
├── G003_user-endpoints.py
└── schemas/
    └── G003_user-endpoints_schema.json
```

**Structure Decision**: Single project structure extending specify-cli. Guards are a new module under `src/specify_cli/guards/`. Guard types distributed in `guards/types/` directory (copied to `.specify/guards/types/` on init). Custom types go to `.specify/guards/types-custom/` and are preserved across updates.

## Phase 0: Research

**Status**: ✅ Complete (see research.md)

Key decisions:
- File-based registry over SQLite (Git-friendly, simpler)
- Two-tier guard types (official in types/, custom in types-custom/)
- History tracking with notes field for self-healing
- Agent integration via YAML frontmatter in slash commands

## Phase 1: Design & Contracts

**Status**: ✅ Complete

### Data Model (see data-model.md)
- Guard: id, type, name, command, status, files, metadata
- GuardType: name, version, category, manifest, scaffolder
- GuardRegistry: file-based storage with list/, history/, index.json

### Contracts (see quickstart.md)
- CLI commands with typer decorators
- File-based registry interface
- Scaffolder base class
- Guard execution protocol

### Agent Context
Updated AGENTS.md with guard CLI capabilities for opencode integration

## Phase 2: Implementation Tasks

See [tasks.md](./tasks.md) for detailed MVP task breakdown.

**MVP Scope** (33/96 tasks complete):
- ✅ Phase 1: Setup (7/7 complete)
- ✅ Phase 2: Foundational (11/11 complete)
- ✅ Phase 3: User Story 1 - Partial (7/21 complete)
- ✅ Phase 4: User Story 3 - Partial (6/14 complete)
- ✅ Phase 5: User Story 2 (5/6 complete)
- ✅ Phase 6: User Story 4 (3/6 complete)

**Post-MVP**: Additional guard types (database, lint-ruff, docker-playwright), marketplace features (install, validate-type)

## Complexity Tracking

No complexity violations. Guard system is intentionally simple:
- File-based storage (no database)
- Subprocess execution (no complex orchestration)
- Template-based code generation (no AST manipulation)
- MVP scope limited to 2 guard types

## Success Criteria

- [X] Guards can be created via `specify guard create`
- [X] Guards can be executed via `specify guard run` with exit codes
- [X] All 21 unit tests pass
- [X] Custom types can be created and used
- [X] History tracking works
- [X] Slash commands have guard integration
- [X] Version updated to 0.0.25
- [X] CHANGELOG updated
- [ ] MVP validation guard created and passing

## Next Steps

1. Run `/tasks` to regenerate tasks.md with guard markers
2. Create mvp-validation custom guard type
3. Run guards to validate completion
4. Commit to 001-guard-cli branch
5. Create PR to main
