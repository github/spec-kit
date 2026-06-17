# Implementation Plan: Implementation Convergence Command (`/speckit.converge`)

**Branch**: `001-converge-command` | **Date**: 2026-06-10 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-converge-command/spec.md`

## Summary

Add a built-in `/speckit.converge` command that reads a feature's `spec.md`, `plan.md`,
and `tasks.md` as the sole source of intent (with the constitution as governing
constraints), assesses the current codebase to determine which required work is unmet,
incomplete, or only partially satisfied, and appends that remaining work as new tasks to
`tasks.md` so `/speckit.implement` can complete it. The command is delivered primarily as
a new Markdown command template (`templates/commands/converge.md`), following the
established processing pipeline, plus registration of the new command name across the
integration registries, tests, and documentation. No git, no change tracking, no
modification of `spec.md`/`plan.md`/existing tasks.

## Technical Context

**Language/Version**: Python 3.11+ (CLI), plus Markdown command templates and Bash +
PowerShell scripts.

**Primary Dependencies**: Existing `specify_cli` package (Typer-based CLI, integration
registry, command registrar, preset system). No new third-party dependencies.

**Storage**: Filesystem only — feature artifacts under `specs/<feature>/` (`spec.md`,
`plan.md`, `tasks.md`) and the constitution under `.specify/memory/constitution.md`. The
command's only write is an appended "Convergence" phase in `tasks.md`.

**Testing**: `pytest` (existing `tests/` suite), notably the per-integration tests under
`tests/integrations/` and `tests/test_agent_config_consistency.py`.

**Target Platform**: Cross-platform developer workstations (macOS, Linux, Windows) running
a supported AI coding agent. Both `sh` and `ps` script variants must work.

**Project Type**: CLI tool + agent command templates (single project, repository root).

**Performance Goals**: Not performance-sensitive. The command is an interactive,
agent-driven assessment; responsiveness is bounded by the agent, not by Spec Kit code.

**Constraints**: No hard dependency on git or change tracking (Constitution Principle II).
Command must work identically across all supported integrations using the existing
`__SPECKIT_COMMAND_*__` invocation convention. The command must not modify `spec.md`,
`plan.md`, or existing tasks; append-only to `tasks.md`.

**Scale/Scope**: One new command template; registration touch-points across ~5 code
registries, ~5 integration test modules, and the command reference docs. Single-feature
scope per invocation.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Assessment |
|-----------|------------|
| **I. Integration Registry Is the Single Source of Truth** | ✅ Converge is a core command (a template processed for every integration), not a new integration. It adds `"converge"` to the canonical command set; no per-agent metadata is hard-coded outside the registries. |
| **II. Cross-Platform Script Parity (NON-NEGOTIABLE)** | ✅ The command reuses the existing `check-prerequisites.sh`/`.ps1` for path resolution. No new scripts are introduced, so parity is preserved by construction. No git dependency. |
| **III. Test-Backed Changes** | ✅ The plan updates every place that enumerates the core command set (registries + integration tests) in the same change set, and keeps `test_agent_config_consistency.py` green. |
| **IV. Spec-Driven Dogfooding** | ✅ This feature is itself being built through specify → plan → tasks. Manual slash-command validation of `/speckit.converge` is required before merge. |
| **V. Focused, Conventional Contributions** | ✅ Scope is bounded to one command and its registration; user-facing docs are updated in the same change set. A new core command is a material change requiring maintainer agreement (noted as a workflow gate, not a code gate). |

**Result**: PASS. No violations; Complexity Tracking section left empty.

**Post-Design Re-check (after Phase 1)**: PASS. The contracts introduce no new scripts,
no git usage, and no new per-agent metadata; the design remains append-only and bounded
to the existing command-set registries.

## Project Structure

### Documentation (this feature)

```text
specs/001-converge-command/
├── spec.md              # Feature specification (/speckit.specify output)
├── plan.md              # This file (/speckit.plan output)
├── research.md          # Phase 0 output (/speckit.plan)
├── data-model.md        # Phase 1 output (/speckit.plan)
├── quickstart.md        # Phase 1 output (/speckit.plan)
├── contracts/           # Phase 1 output (/speckit.plan)
│   ├── command-interface.md
│   ├── tasks-output.md
│   └── hooks.md
├── checklists/
│   └── requirements.md  # Spec quality checklist (already created)
└── tasks.md             # Phase 2 output (/speckit.tasks — NOT created here)
```

### Source Code (repository root)

The feature touches existing locations in the `spec-kit` repository; it does not introduce
a new top-level structure.

```text
templates/
└── commands/
    └── converge.md                       # NEW — the command template (primary deliverable)

src/specify_cli/
├── __init__.py                           # EDIT — add "converge" to SKILL_DESCRIPTIONS
├── extensions.py                         # EDIT — add "converge" to _FALLBACK_CORE_COMMAND_NAMES
├── commands/
│   └── init.py                           # EDIT — add "converge" to the post-init "Next Steps" panel (after implement)
└── integrations/
    └── claude/__init__.py                # EDIT — keep converge out of Claude argument hints

tests/
├── test_agent_config_consistency.py      # VERIFY — converge token resolves correctly
└── integrations/
    ├── test_integration_base_markdown.py # EDIT — add "converge" to COMMAND_STEMS
    ├── test_integration_base_toml.py     # EDIT — add "converge" to COMMAND_STEMS
    ├── test_integration_base_yaml.py     # EDIT — add "converge" to COMMAND_STEMS
    ├── test_integration_base_skills.py   # EDIT — add "converge" to expected_commands + _SKILL_COMMANDS
    ├── test_integration_copilot.py       # EDIT — add "converge" to expected_commands + _SKILL_COMMANDS
    └── test_integration_generic.py       # EDIT — add "converge" to the constitution-context parametrize list

README.md                                 # EDIT — add "/speckit.converge" to the Core Commands table (the canonical slash-command enumeration; Constitution III & V)
```

> **Docs note**: `docs/reference/core.md` documents the `specify` *CLI* (init/check/version), not slash commands, and `docs/reference/workflows.md` only lists the built-in Full SDD Cycle workflow (specify→plan→tasks→implement) — which converge is not part of. Neither needs editing; the README tables are the only slash-command reference.

**Structure Decision**: Single project at the repository root. The deliverable is a new
core command template plus edits to the existing registries, tests, and docs that
enumerate the core command set. No new packages, directories, or scripts are added; the
command reuses `check-prerequisites` for path resolution to honor the script-parity and
no-git constraints.

## Complexity Tracking

> No Constitution Check violations. This section intentionally left empty.
