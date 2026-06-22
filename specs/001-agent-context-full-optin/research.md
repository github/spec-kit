# Phase 0 Research: Agent-Context Extension Full Opt-In

**Feature**: 001-agent-context-full-optin | **Date**: 2026-06-22

This feature is a removal/refactor inside a known codebase, so "research" here resolves the design decisions implied by the spec (notably FR-007 and the Assumptions) rather than evaluating external technologies. Each item records the current state, the decision, the rationale, and rejected alternatives.

## R1: Fate of the `context_file` class attribute on integrations

**Current state**: All ~40 integration subclasses declare `context_file = "..."` (e.g. `claude → CLAUDE.md`). The base layer uses it to (a) drive `upsert_context_section()`/`remove_context_section()` and (b) substitute `__CONTEXT_FILE__` in templates via `process_template(..., context_file=...)`.

**Decision**: **Remove `context_file` entirely** from all integration classes. The CLI keeps no per-agent context-file knowledge of any kind. The per-agent default mapping (key → context file) is relocated to the extension, which ships it as `agent-context-defaults.json` and self-seeds from it. The `__CONTEXT_FILE__` substitution and its supporting `process_template(..., context_file=...)` path are deleted, and the placeholder is removed from the core templates that used it (`templates/commands/plan.md`).

**Rationale**: The hardened requirement (FR-007, revised) is that the CLI carry *no* context-file state — not even inert metadata the CLI can "see, handle, or migrate." Leaving the attribute or the `__CONTEXT_FILE__` resolver in place would keep agent-context concerns coupled to the CLI. Moving the default mapping into the extension makes the extension fully self-contained: it no longer depends on the CLI registry to discover an agent's context file.

**Alternatives considered**:
- *Keep `context_file` as inert metadata (earlier Phase 1 decision)*: rejected on review — the goal is zero agent-context state in the CLI, so even unused metadata and placeholder resolution must go.
- *Keep the mapping in the CLI but stop using it*: rejected — the extension must own the mapping so it works regardless of CLI internals.

## R2: How `__CONTEXT_FILE__` is resolved in `agents.py`

**Current state** (post-sync with upstream/main): `agents.py` resolves `__CONTEXT_FILE__` by importing `_load_agent_context_config`, reading the extension's `agent-context-config.yml`, and passing it through `IntegrationBase._resolve_context_file_values(...)` / `_format_context_file_values(...)`. Upstream generalized the single `context_file` into a **plural `context_files`** concept with extension-config-driven resolution.

**Decision**: **Remove `__CONTEXT_FILE__` resolution from the CLI entirely.** Delete the resolution block in `agents.py` and the `_resolve_context_file_values` / `_format_context_file_values` / `_resolve_context_files` helpers in `base.py`. The CLI no longer substitutes the placeholder; the core templates that referenced it are updated to drop it. Any stray `__CONTEXT_FILE__` that might appear in a template is passed through literally rather than resolved.

**Rationale**: FR-002 forbids the CLI reading the extension config, and the hardened FR-007 forbids the CLI resolving context files at all. With the placeholder removed from the templates the CLI renders, no substitution is needed, so the entire resolver path is dead and is deleted.

**Alternatives considered**:
- *Resolve from integration metadata instead of extension config (earlier Phase 1 decision)*: rejected — that still keeps the `context_file` attribute and a CLI-side resolver, which the hardened requirement disallows.
- *Leave the placeholder unresolved in templates*: avoided by removing the placeholder from the core templates outright, so no literal `__CONTEXT_FILE__` ships to users.


## R3: Auto-install of the `agent-context` extension during `specify init`

**Current state**: `commands/init.py` (~lines 510–539) auto-installs the bundled `agent-context` extension during init, then writes its config (`context_file`) via `_update_agent_context_config_file` (~lines 541–549). It also appears as a tracker step and in `init.py:379` as a selectable install item.

**Decision**: Make installation **opt-in**. Remove the unconditional auto-install + config-write. The extension is offered through the normal extension-selection mechanism (the user chooses it); when chosen, the extension's own install logic seeds its config. The CLI no longer writes `agent-context-config.yml`.

**Rationale**: FR-005 requires the extension be opt-in; FR-002 forbids the CLI writing the extension config. Seeding config is the extension's responsibility (its bundled template `agent-context-config.yml` ships with the path/markers, and its install flow can populate `context_file`).

**Open implementation detail (defer to tasks)**: Exactly how the extension seeds `context_file` at install (static template vs. install hook reading the selected integration) is an implementation choice for `/speckit.tasks`. The spec only requires the CLI not do it. Default assumption: the extension ships a template config and its update script tolerates an empty/defaulted `context_file` by deriving from the active integration, consistent with the existing self-contained scripts.

**Alternatives considered**:
- *Keep auto-install but stop writing config*: rejected — auto-install still makes the extension non-opt-in, violating FR-005.

## R4: Extension-enabled gating + marker resolution in `base.py`

**Current state** (post-sync): `base.py` has `_agent_context_extension_enabled()` (~line 605, reads `.specify/extensions/.registry`) and `_resolve_context_markers()` (~line 645, reads `agent-context-config.yml`), used by `upsert_context_section()` (~line 895) and `remove_context_section()` (~line 948). Upstream additionally added `_resolve_context_file_values()` (~line 738), `_format_context_file_values()` (~line 787), and `_resolve_context_files()` (~line 791); upsert/remove now **iterate over a list of context files** (`for context_file in context_files:`) read from the extension config's plural `context_files` key.

**Decision**: Remove the gating helper, the marker resolver, and the `upsert_context_section()` / `remove_context_section()` methods (and their per-file loops) along with all their call sites in `setup()`/`teardown()` across the base classes (call sites at ~lines 1181, 1200, 1309, 1518, 1725, 1959). Also remove `_resolve_context_files()`, `_resolve_context_file_values()`, and `_format_context_file_values()` outright — with `__CONTEXT_FILE__` resolution gone (R2), no metadata formatter survives.

**Rationale**: FR-001/FR-003 — the base layer must not manage the section, gate on the extension, resolve markers, or read the extension's `context_files` list. With the upsert/remove methods gone, the gating, marker, and config-reading helpers are dead code.

**Alternatives considered**:
- *Keep helpers "just in case"*: rejected — FR-002/FR-003 and SC-002 require zero such references remaining; dead code with config I/O still violates the spec's intent.

## R5: The deprecation warning

**Current state**: `upsert_context_section()` prints a `rich` "Deprecation: …v0.12.0… run `specify extension disable agent-context`" warning every time it runs (base.py ~line 924). A test asserts its presence.

**Decision**: Remove the warning entirely (it disappears with the method) and remove/replace the asserting test.

**Rationale**: FR-006 + SC-003 — the message must never be emitted. Since the inline behavior is removed (not merely deprecated), the message is obsolete.

## R6: Backward compatibility for existing projects

**Current state**: Existing projects may already contain a managed section in their context file and an `agent-context-config.yml`.

**Decision**: Leave existing files untouched. The CLI performs no migration, cleanup, or rewrite. Further updates happen only when the user runs the extension's update command.

**Rationale**: FR-008 + SC-006 — existing projects must keep working without errors. "Unmanaged by the CLI" is sufficient; no migration is required by the spec (stated explicitly in Assumptions).

## R7: Test suite strategy

**Current state**: `tests/extensions/test_extension_agent_context.py` covers CLI-side gating, marker resolution, config writers, and the deprecation warning. `tests/integrations/*` assert that setup writes context sections.

**Decision**: Prune CLI-side tests that exercise removed behavior (gating, upsert/remove, config writers, deprecation). Keep/extend tests that validate the extension is self-contained (layout, scripts read their own config, catalog entry). Update integration tests to assert the CLI no longer writes context sections.

**Rationale**: FR-009 + SC-004 — tests for removed behavior must be removed or relocated, and the suite must pass.

## Summary of Decisions

| ID | Decision |
|----|----------|
| R1 | Remove `context_file` from integrations; extension owns the defaults map |
| R2 | Remove `__CONTEXT_FILE__` resolution from the CLI; drop placeholder from templates |
| R3 | Extension install becomes opt-in; CLI stops writing its config |
| R4 | Remove gating + marker-resolution + upsert/remove from base layer |
| R5 | Remove the deprecation warning and its test |
| R6 | Leave existing files intact; no CLI migration |
| R7 | Prune/relocate tests for removed CLI behavior |

All NEEDS CLARIFICATION resolved. No blocking unknowns remain for design.
