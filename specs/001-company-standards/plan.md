# Implementation Plan: Company Standards & AGENTS.md

**Branch**: `001-company-standards` | **Date**: 2026-01-26 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-company-standards/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Implement a set of company standard templates (`templates/company-standards/`) covering code style, security, review guidelines, and incident response. Additionally, standardize the AI agent context file mechanism to use `AGENTS.md` as the single source of truth, updating the CLI (`specify init`) and maintenance scripts (`update-agent-context`) to support this unified approach while maintaining backward compatibility where necessary.

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.10+ (CLI), Bash/PowerShell (Scripts), Markdown (Templates)
**Primary Dependencies**: `typer`, `rich` (Existing CLI dependencies)
**Storage**: Filesystem (Templates and Agent Context files)
**Testing**: `pytest` (CLI logic), Manual Verification (Template generation)
**Target Platform**: Cross-platform (macOS, Linux, Windows)
**Project Type**: CLI Tool & Template Library
**Performance Goals**: N/A
**Constraints**: Must maintain backward compatibility for existing projects if possible, or provide clear migration.
**Scale/Scope**: ~10 new template files, modifications to CLI init logic and 2 scripts.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Library-First**: N/A (Feature is CLI enhancement + Templates)
- **CLI Interface**: Yes, extending `specify init`.
- **Test-First**: Yes, will add tests for CLI changes.
- **Integration Testing**: N/A
- **Simplicity**: Consolidating to `AGENTS.md` simplifies the architecture.

## Project Structure

### Documentation (this feature)

```text
specs/001-company-standards/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── cli-init.md
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
templates/
├── company-standards/       # NEW: Standard templates
│   ├── constitution-template.md
│   ├── security-checklist.md
│   ├── review-guidelines.md
│   ├── incident-response.md
│   └── code-style/
│       ├── javascript.md
│       ├── python.md
│       ├── java.md
│       └── go.md

src/specify_cli/
└── __init__.py             # MODIFY: Update init logic for AGENTS.md

scripts/
├── bash/
│   └── update-agent-context.sh   # MODIFY: Support AGENTS.md
└── powershell/
    └── update-agent-context.ps1  # MODIFY: Support AGENTS.md
```

**Structure Decision**: Add new templates in a dedicated `company-standards` directory. Modify existing CLI and scripts in place.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | | |
