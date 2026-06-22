# Implementation Plan: Agent-Context Extension Full Opt-In

**Branch**: `001-agent-context-full-optin` | **Date**: 2026-06-22 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-agent-context-full-optin/spec.md`

## Summary

Make the bundled `agent-context` extension the sole owner of agent context/instruction file management. Remove every agent-context concern from the Specify CLI (Python) source: config-file I/O, context-section upsert/remove (including the upstream plural `context_files` support and its `_resolve_context_files` / `_resolve_context_file_values` / `_format_context_file_values` helpers), marker resolution, extension-enabled gating, the `__CONTEXT_FILE__` config lookup, the auto-install + config-write during `specify init`, and the inline deprecation warning. The extension already ships self-contained bash/PowerShell scripts and its own `agent-context-config.yml`, so removing the CLI-side logic makes the extension a true opt-in without losing end-user functionality. Existing projects keep working: previously written files are left intact and simply unmanaged by the CLI.

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

Evaluated against **Spec Kit Constitution v1.0.0** (`.specify/memory/constitution.md`, present on `upstream/main`). All five binding principles pass; the feature is a net reduction in complexity and surface area.

| Principle | Verdict | Notes |
|-----------|---------|-------|
| **I. Code Quality & Architectural Discipline** | ✅ PASS | Preserves the registry + base-class pattern. Principle I lists `context_file` as a required class attribute "where applicable" — so R1 (keep `context_file` as inert metadata) is *mandated*, not optional. We reinforce the single-source-of-truth rule by making the `agent-context` extension the sole owner of context management. No new cross-boundary `_`-private imports. |
| **II. Test-Backed Change (NON-NEGOTIABLE)** | ✅ PASS | Behavioral change ships with tests (FR-009, contracts C1–C7, quickstart). **Parity invariant guard**: every integration MUST keep its registry entry + `tests/integrations/test_integration_<key>.py`; removing upsert/remove from the base layer MUST NOT delete or weaken those parity tests — only the agent-context-specific assertions are pruned/relocated. Security/idempotency suites (path-traversal, manifest, no-clobber) are untouched. Network stays mocked. Must pass the ubuntu+windows × py3.11/3.12/3.13 matrix. |
| **III. CLI & UX Consistency** | ✅ PASS | Making `agent-context` opt-in routes it through the standard extension verbs (`add`/`install`, `enable`/`disable`) instead of a bespoke auto-install — *more* consistent, not less. `init` stays idempotent ("already present" → exit 0). Removing the deprecation line keeps output grammar clean. User-facing behavior change → update `docs/` (FR-010). |
| **IV. Offline-First Performance & Resource Discipline** | ✅ PASS | No network paths involved. Removing config-file I/O during setup/teardown *reduces* filesystem writes; remaining writes stay idempotent and hash-tracked. No import-time cost added. |
| **V. Minimal Dependencies & Safe, Idempotent File Operations** | ✅ PASS | Zero new dependencies (net deletion). Backward-compat (FR-008) leaves pre-existing files intact — no clobber, no traversal. User-visible behavior change is called out for SemVer/changelog. |

**Gate result: PASS** (no violations → Complexity Tracking table stays empty).

**Note on environment**: This worktree branched from the fork's `main`, which is **16 commits behind `upstream/main`** and therefore lacks the `.specify/` directory locally. The constitution above is the authoritative `upstream/main` version. Implementation work (`/speckit.tasks`, `/speckit.implement`) should be done on a branch synced with `upstream/main` so `.specify/memory/constitution.md`, the security suites, and CI gates referenced here are actually present.

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
