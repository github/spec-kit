# Phase 1 Data Model: Agent-Context Extension Full Opt-In

**Feature**: 001-agent-context-full-optin | **Date**: 2026-06-22

This feature has no database or persistent domain model. The relevant "entities" are filesystem artifacts and the ownership boundary between the Specify CLI and the `agent-context` extension. This document captures those entities, their fields, and the ownership transition the feature enforces.

## Entities

### 1. Agent context file

The per-agent instruction file that may contain a delimited managed section.

| Field | Description |
|-------|-------------|
| `path` | Project-relative path, e.g. `CLAUDE.md`, `AGENTS.md`, `.github/copilot-instructions.md`, `.cursor/rules/specify-rules.mdc` |
| `managed_section` | Text delimited by start/end markers, holding the Spec Kit plan reference |
| `user_content` | Any content outside the managed section (must never be touched) |

**Ownership transition**:
- *Before*: written/updated/removed by the CLI (`upsert_context_section` / `remove_context_section`) **and** by the extension.
- *After*: written/updated/removed **only** by the `agent-context` extension's scripts.

**Validation rules**:
- The CLI must make zero modifications to this file in any flow (FR-001, SC-001).
- The extension only manages the region between its configured markers; user content is preserved.

### 2. Agent-context extension configuration

`.specify/extensions/agent-context/agent-context-config.yml`

| Field | Description |
|-------|-------------|
| `context_file` | Target context file path the extension manages |
| `context_markers.start` | Start delimiter (default `<!-- SPECKIT START -->`) |
| `context_markers.end` | End delimiter (default `<!-- SPECKIT END -->`) |

**Ownership transition**:
- *Before*: read by CLI (`_load_agent_context_config`, marker resolution, `__CONTEXT_FILE__`) and written by CLI (`_save/_update_agent_context_config_file`) during init/switch/uninstall.
- *After*: read and written **only** by the extension (its scripts/install logic).

**Validation rules**:
- No CLI code path reads or writes this file (FR-002, SC-002).

### 3. Extension registry entry

`.specify/extensions/.registry` → `extensions["agent-context"]`

| Field | Description |
|-------|-------------|
| `version` | Installed extension version |
| `enabled` | Whether the extension is active |

**Ownership transition**:
- *Before*: CLI gating (`_agent_context_extension_enabled`) read this to decide whether to run inline context updates.
- *After*: the registry still records install/enabled state (managed by the generic extension subsystem), but **no agent-context-specific gating logic** reads it. Whether the extension runs is governed by the normal extension/hook mechanism.

**Validation rules**:
- No agent-context-specific enabled-gate helper remains in `base.py` (FR-003, SC-002).

### 4. Integration definition

`src/specify_cli/integrations/<agent>/__init__.py`

| Field | Description |
|-------|-------------|
| `key` | Integration identifier |
| `context_file` | Declared context file path — **inert metadata** after this feature |
| `registrar_config`, `config` | Unchanged command/output metadata |

**Ownership transition**:
- *Before*: `context_file` triggered CLI context-section management via inherited `setup()`/`teardown()`.
- *After*: `context_file` is informational only — consumed for `__CONTEXT_FILE__` template substitution (R2) and as the value the extension may seed from. It never triggers CLI section writes.

**Validation rules**:
- Reading/declaring `context_file` must not cause the CLI to modify any agent context file (FR-007).

## State Transition: Section Ownership

```text
                 BEFORE                                AFTER
   ┌─────────────────────────────┐      ┌─────────────────────────────┐
   │ specify init / setup        │      │ specify init / setup        │
   │   → CLI upserts section     │      │   → CLI does nothing to      │
   │   → CLI writes ext config   │      │     context file/ext config  │
   │   → prints deprecation msg  │      │   (no message)               │
   ├─────────────────────────────┤      ├─────────────────────────────┤
   │ extension update (opt-in)   │      │ extension update (opt-in)    │
   │   → extension upserts       │      │   → extension upserts        │  ← sole owner
   ├─────────────────────────────┤      ├─────────────────────────────┤
   │ teardown / uninstall        │      │ teardown / uninstall         │
   │   → CLI removes section     │      │   → CLI does nothing          │
   │   → CLI clears ext config   │      │   (extension owns cleanup)   │
   └─────────────────────────────┘      └─────────────────────────────┘
```

## No-op / Removed Constructs

These cease to exist (or cease to be referenced) after the feature:

- `IntegrationBase.upsert_context_section`, `remove_context_section` (and their per-file loops over `context_files`)
- `IntegrationBase._agent_context_extension_enabled`, `_resolve_context_markers`
- `IntegrationBase._resolve_context_files`, and the extension-config-reading branches of `_resolve_context_file_values` / `_format_context_file_values` (retain at most a pure metadata formatter for `__CONTEXT_FILE__`)
- The plural `context_files` config key consumption in the CLI
- `_AGENT_CTX_EXT_CONFIG`, `_load_agent_context_config`, `_save_agent_context_config`, `_update_agent_context_config_file`
- Auto-install + config-write of `agent-context` in `commands/init.py`
- The v0.12.0 deprecation warning
