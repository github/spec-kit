# Implementation Plan: Agent-Context Extension Full Opt-In

**Branch**: `001-agent-context-full-optin` | **Date**: 2026-06-22 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-agent-context-full-optin/spec.md`

## Summary

Make the bundled `agent-context` extension the sole owner of agent context/instruction file management. Remove every agent-context concern from the Specify CLI (Python) source: config-file I/O, context-section upsert/remove, marker resolution, extension-enabled gating, the `__CONTEXT_FILE__` config lookup, the auto-install + config-write during `specify init`, and the inline deprecation warning. The extension already ships self-contained bash/PowerShell scripts and its own `agent-context-config.yml`, so removing the CLI-side logic makes the extension a true opt-in without losing end-user functionality. Existing projects keep working: previously written files are left intact and simply unmanaged by the CLI.

## Technical Context

**Language/Version**: Python 3.11+ (Specify CLI), plus bash/PowerShell extension scripts (unchanged)

**Primary Dependencies**: Typer/Click CLI, `rich` console, PyYAML; no new dependencies

**Storage**: Filesystem only — project files (`CLAUDE.md`, `AGENTS.md`, etc.), `.specify/extensions/agent-context/agent-context-config.yml`, `.specify/extensions/.registry`

**Testing**: pytest (`tests/`), existing suite including `tests/extensions/test_extension_agent_context.py` and `tests/integrations/`

**Target Platform**: Cross-platform CLI (macOS/Linux/Windows)

**Project Type**: Single project — Python CLI with bundled extensions

**Performance Goals**: N/A (no runtime-perf-sensitive paths; this is a removal/refactor)

**Constraints**: No behavior change when the extension is installed+enabled and its update command runs; backward compatible with existing projects; no orphaned references that break imports or tests

**Scale/Scope**: ~6 CLI source files touched, ~40 integration subclasses share the inherited base behavior, 1 deprecation message removed, test suite updated/relocated

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

No constitution file exists at `memory/constitution.md` or `.specify/memory/constitution.md`. The Constitution Check gate is a no-op (no project principles to enforce). PASS.

## Project Structure

### Documentation (this feature)

```text
specs/001-agent-context-full-optin/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (CLI behavioral contracts)
│   └── cli-behavior.md
├── checklists/
│   └── requirements.md  # From /speckit.specify
└── spec.md
```

### Source Code (repository root)

```text
src/specify_cli/
├── __init__.py                     # REMOVE: _AGENT_CTX_EXT_CONFIG + _load/_save/_update_agent_context_config helpers
├── agents.py                       # CHANGE: __CONTEXT_FILE__ resolution no longer reads extension config
├── commands/
│   └── init.py                     # CHANGE: stop auto-installing agent-context + stop writing its config
└── integrations/
    ├── base.py                     # REMOVE: upsert/remove_context_section, _agent_context_extension_enabled,
    │                               #          _resolve_context_markers, marker constants usage, deprecation msg,
    │                               #          and all setup()/teardown() call sites
    ├── _helpers.py                 # REMOVE: agent-context config clear/update on switch + uninstall
    └── <agent>/__init__.py         # KEEP context_file as inert metadata (decision in research.md)

extensions/agent-context/           # UNCHANGED — already self-contained (scripts + config + commands + hooks)

tests/
├── extensions/test_extension_agent_context.py   # RELOCATE/PRUNE: drop CLI-side gating + deprecation tests;
│                                                 #   keep extension-layout/script-driven tests
└── integrations/                                 # UPDATE: drop assertions that CLI writes context sections
```

**Structure Decision**: Single-project Python CLI. Changes are concentrated in the integration base layer and the init/switch/uninstall flows. The extension directory and its scripts are deliberately untouched — they are the new single owner.

## Complexity Tracking

No constitution violations. The work is a net *reduction* in complexity (deleting dual-ownership code paths). Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none) | — | — |
