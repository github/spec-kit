# Implementation Plan: Ralph Loop Implementation Support

**Branch**: `001-ralph-loop-implement` | **Date**: 2026-01-18 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-ralph-loop-implement/spec.md`

## Summary

Add autonomous implementation support to Spec Kit via a ralph loop command that orchestrates GitHub Copilot CLI (`copilot`) in a controlled iteration pattern. The loop spawns fresh agent contexts for each iteration, monitors task completion via tasks.md checkbox changes, persists learnings in a progress file, and terminates when the agent outputs `<promise>COMPLETE</promise>` or the iteration limit (default 10) is reached.

## Technical Context

**Language/Version**: Python 3.11+ (Specify CLI) + PowerShell 6+ and Bash (scripts)  
**Primary Dependencies**: Typer, Rich (existing CLI deps); `copilot` CLI (standalone GitHub Copilot CLI)  
**Storage**: Markdown files (tasks.md, progress.txt) - no database  
**Testing**: pytest (existing test framework)  
**Target Platform**: Windows (PowerShell 6+), macOS/Linux (Bash)  
**Project Type**: Single project - CLI tool with script orchestration  
**Performance Goals**: <2 seconds between iteration starts; <500ms CLI response time  
**Constraints**: Must work without IDE; Copilot CLI must be pre-authenticated (GH_TOKEN or /login)  
**Scale/Scope**: Single developer use; 5-20 tasks per feature typical

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Code Quality** | ✅ Pass | Single responsibility: CLI entry point, loop orchestrator, prompt generator are separate modules |
| **II. Testing Standards** | ✅ Pass | Contract tests for prompt template; integration tests for loop execution with mock agent |
| **III. User Experience Consistency** | ✅ Pass | Follows existing `specify` CLI patterns; progressive disclosure (simple default, optional flags) |
| **IV. Performance Requirements** | ✅ Pass | <2s iteration start meets spec; progress indicators for long operations |

## Project Structure

### Documentation (this feature)

```text
specs/001-ralph-loop-implement/
├── plan.md              # This file
├── spec.md              # Feature specification (completed)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── prompt-template.md
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
src/
└── specify_cli/
    └── __init__.py           # Add `ralph` command to existing CLI

scripts/
├── powershell/
│   ├── common.ps1            # Existing shared functions
│   └── ralph-loop.ps1        # NEW: PowerShell loop orchestrator
└── bash/
    ├── common.sh             # Existing shared functions
    └── ralph-loop.sh         # NEW: Bash loop orchestrator

templates/
├── commands/                 # Existing agent commands
└── ralph-prompt.md           # NEW: Ralph iteration prompt template (user story scope + commit rules)

tests/
├── unit/
│   └── test_ralph_prompt.py  # NEW: Prompt template tests
└── integration/
    └── test_ralph_loop.py    # NEW: Loop integration tests (with mock)
```

**Structure Decision**: Extend existing single-project structure. The ralph loop is implemented as:
1. A thin Python CLI entry point (`specify ralph`) that validates prerequisites and invokes the platform-specific script
2. Platform scripts (PowerShell/Bash) that handle the actual loop iteration and process management
3. **Two-layer agent context**:
   - `speckit.implement` agent profile (`.github/agents/speckit.implement.agent.md`) - provides "how to implement" (TDD, phases, patterns)
   - `ralph-prompt.md` template - provides iteration-specific "what scope and when to commit" rules

This follows the existing pattern where Python handles CLI UX and scripts handle platform-specific operations.

## Complexity Tracking

> No constitution violations requiring justification.
