# Phase 1 Contracts: CLI Behavioral Contracts

**Feature**: 001-agent-context-full-optin | **Date**: 2026-06-22

This is a CLI tool, so the externally observable "contract" is the behavior of `specify` commands with respect to agent context files and the extension config. Each contract below is a testable assertion that the implementation and test suite must satisfy.

## C1: `specify init` — extension absent/not selected

**Given** a user runs `specify init` with an integration and does not select the `agent-context` extension
**When** initialization and integration setup complete
**Then**:
- No managed Spec Kit section is created in the agent context file by the CLI.
- `.specify/extensions/agent-context/agent-context-config.yml` is not created or written by the CLI.
- No deprecation message is printed.

*Maps to*: FR-001, FR-002, FR-005, FR-006 · SC-001, SC-003

## C2: `specify init` — extension selected (opt-in)

**Given** a user runs `specify init` and opts into the `agent-context` extension
**When** initialization completes
**Then**:
- The extension is installed via the normal extension mechanism.
- Any seeding of `agent-context-config.yml` is performed by the extension's own install logic, not by CLI agent-context helpers.
- Running the extension's update command produces a correct managed section.

*Maps to*: FR-004, FR-005 · SC-005

## C3: Integration setup never writes the context section

**Given** any integration's `setup()` runs (regardless of extension state)
**When** command files are installed
**Then**:
- `__CONTEXT_FILE__` placeholders in rendered templates are substituted from the integration's declared `context_file` metadata.
- No call creates, updates, or removes a managed section in the agent context file.

*Maps to*: FR-001, FR-003, FR-007

## C4: Integration teardown/uninstall never touches the context file or ext config

**Given** an integration is uninstalled or switched
**When** the operation completes
**Then**:
- The CLI does not remove or rewrite any managed section.
- The CLI does not clear or rewrite `agent-context-config.yml`.

*Maps to*: FR-001, FR-002

## C5: No agent-context logic remains in the base/init/switch layers

**Given** the Specify CLI source after this feature
**When** inspected (e.g. by grep/CI check)
**Then** there are zero references to:
- `upsert_context_section`, `remove_context_section`
- `_agent_context_extension_enabled`, `_resolve_context_markers`
- `_AGENT_CTX_EXT_CONFIG`, `_load_agent_context_config`, `_save_agent_context_config`, `_update_agent_context_config_file`
- the v0.12.0 deprecation string

(outside the `extensions/agent-context/` directory and this `specs/` artifact).

*Maps to*: FR-002, FR-003, FR-006 · SC-002, SC-003

## C6: Backward compatibility

**Given** a project created by a previous Spec Kit version (already has a managed section and/or `agent-context-config.yml`)
**When** the user runs `specify init`, an integration switch, or an uninstall
**Then** the commands complete without error and leave the pre-existing files intact (unmanaged by the CLI).

*Maps to*: FR-008 · SC-006

## C7: Extension remains self-contained

**Given** the `extensions/agent-context/` directory
**When** the extension's update command/script runs in an opt-in project
**Then** it reads its own `agent-context-config.yml` and updates the context file independently of any CLI agent-context code.

*Maps to*: FR-004 · SC-005

## Contract Test Matrix

| Contract | Test location (target) | Type |
|----------|------------------------|------|
| C1 | `tests/integrations/` + init tests | integration |
| C2 | `tests/extensions/test_extension_agent_context.py` | integration |
| C3 | `tests/integrations/test_integration_base_*.py` | unit |
| C4 | `tests/integrations/` switch/uninstall tests | unit/integration |
| C5 | new static/grep guard test (or CI check) | static |
| C6 | new backward-compat test | integration |
| C7 | `tests/extensions/test_extension_agent_context.py` (layout/script) | integration |
