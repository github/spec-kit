# Implementation Plan: Customizable Branch Naming Templates

**Branch**: `001-custom-branch-templates` | **Date**: 2026-01-23 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-custom-branch-templates/spec.md`

## Summary

Enable team-friendly branch naming by introducing a `.specify/settings.toml` configuration file with customizable branch templates. Templates support placeholders (`{username}`, `{number}`, `{short_name}`, `{email_prefix}`) that are resolved at branch creation time, with per-user number scoping to avoid conflicts in multi-developer teams.

## Technical Context

**Language/Version**: Python 3.11+ (CLI), Bash 4.x+ (scripts), PowerShell 5.1+ (scripts)
**Primary Dependencies**: `tomli` (Python 3.10 fallback) or `tomllib` (Python 3.11+ stdlib), existing `typer`, `rich`
**Storage**: `.specify/settings.toml` (TOML configuration file)
**Testing**: Manual testing via CLI; integration tests recommended but not required per spec
**Target Platform**: macOS, Linux, Windows
**Project Type**: Single project (CLI tool with supporting shell scripts)
**Performance Goals**: Sub-second template resolution
**Constraints**: Backward compatible - no settings file = current behavior
**Scale/Scope**: Single-developer to team workflows (3+ developers)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Specification-First | ✅ PASS | Spec created and clarified before planning |
| II. Intent-Driven | ✅ PASS | User stories describe what/why, not how |
| III. Iterative Refinement | ✅ PASS | Used `/speckit.clarify` to resolve 3 ambiguities |
| IV. Traceable Artifacts | ✅ PASS | Plan references spec; tasks will reference user stories |
| V. Agent-Agnostic Design | ✅ PASS | Both Bash and PowerShell scripts will be updated |

**Quality Standards Check**:
- CLI Changes: Will require `CHANGELOG.md` update and version increment in `pyproject.toml`

## Project Structure

### Documentation (this feature)

```text
specs/001-custom-branch-templates/
├── spec.md              # Feature specification (complete)
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (CLI interface contracts)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/
└── specify_cli/
    └── __init__.py          # CLI implementation (add --settings flag, settings loading)

scripts/
├── bash/
│   ├── common.sh            # Add settings loading functions
│   └── create-new-feature.sh # Integrate template resolution
└── powershell/
    ├── common.ps1           # Add settings loading functions
    └── create-new-feature.ps1 # Integrate template resolution

templates/
└── settings.toml            # Default settings template (new file)
```

**Structure Decision**: This is an enhancement to an existing single-project CLI tool. All changes integrate into existing file structure. No new directories needed beyond `contracts/` in the feature spec folder.

## Complexity Tracking

No constitution violations. All principles pass.

## Post-Design Constitution Re-Check

*Re-evaluated after Phase 1 design completion.*

| Principle | Status | Post-Design Evidence |
|-----------|--------|----------------------|
| I. Specification-First | ✅ PASS | Design artifacts (data-model.md, contracts/) trace to spec requirements |
| II. Intent-Driven | ✅ PASS | Research decisions document rationale, not just implementation |
| III. Iterative Refinement | ✅ PASS | quickstart.md provides validation scenarios for iteration |
| IV. Traceable Artifacts | ✅ PASS | CLI contract maps to FR-001 through FR-009; data model maps to Key Entities |
| V. Agent-Agnostic Design | ✅ PASS | Contracts specify both Bash and PowerShell function signatures |

**Quality Standards Compliance**:
- ✅ Specifications use MUST/SHOULD/MAY language (spec.md)
- ✅ User stories are independently testable (quickstart.md scenarios)
- ✅ Acceptance criteria follow Given/When/Then format (spec.md)
- ⏳ CLI changes will require CHANGELOG.md and pyproject.toml updates (at implementation)

## Generated Artifacts

| Artifact | Path | Status |
|----------|------|--------|
| Research | [research.md](./research.md) | ✅ Complete |
| Data Model | [data-model.md](./data-model.md) | ✅ Complete |
| CLI Contract | [contracts/cli.md](./contracts/cli.md) | ✅ Complete |
| Quickstart | [quickstart.md](./quickstart.md) | ✅ Complete |
| Tasks | tasks.md | ⏳ Pending (`/speckit.tasks`) |
