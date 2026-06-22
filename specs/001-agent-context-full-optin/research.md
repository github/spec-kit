# Phase 0 Research: Agent-Context Extension Full Opt-In

**Feature**: 001-agent-context-full-optin | **Date**: 2026-06-22

This feature is a removal/refactor inside a known codebase, so "research" here resolves the design decisions implied by the spec (notably FR-007 and the Assumptions) rather than evaluating external technologies. Each item records the current state, the decision, the rationale, and rejected alternatives.

## R1: Fate of the `context_file` class attribute on integrations

**Current state**: All ~40 integration subclasses declare `context_file = "..."` (e.g. `claude → CLAUDE.md`). The base layer uses it to (a) drive `upsert_context_section()`/`remove_context_section()` and (b) substitute `__CONTEXT_FILE__` in templates via `process_template(..., context_file=...)`.

**Decision**: Keep `context_file` as **inert metadata**. Remove its use as a trigger for context-section writes, but retain it as the declared value the extension/templates consume (e.g. it still feeds `__CONTEXT_FILE__` substitution and is the value the extension config is seeded from at install time — by the extension, not the CLI).

**Rationale**: FR-007 explicitly permits keeping the declaration as informational metadata. Templates already reference `__CONTEXT_FILE__`; removing the attribute would force a larger, riskier change across every integration and its tests for no functional gain. The spec's requirement is that the declaration "MUST NOT cause the CLI to manage the context section" — satisfied by removing the call sites, not the attribute.

**Alternatives considered**:
- *Delete `context_file` entirely from all integrations*: rejected — large blast radius, breaks `__CONTEXT_FILE__` template substitution and many per-integration tests, no requirement demands it.
- *Move `context_file` into the extension only*: rejected — the CLI's template processing still needs the value to render `__CONTEXT_FILE__`; relocating ownership now couples template rendering to extension presence.

## R2: How `__CONTEXT_FILE__` is resolved in `agents.py`

**Current state** (post-sync with upstream/main): `agents.py` (~lines 429–458) resolves `__CONTEXT_FILE__` by importing `_load_agent_context_config`, reading the extension's `agent-context-config.yml`, and passing it through `IntegrationBase._resolve_context_file_values(...)` / `_format_context_file_values(...)`. Upstream has generalized the single `context_file` into a **plural `context_files`** concept (config key `context_files`, resolver helpers in `base.py` ~lines 738–833), with an `include_context_files` flag that ignores the extension's configured list when the extension is disabled while still honoring the integration's own declared value.

**Decision**: Resolve `__CONTEXT_FILE__` directly from the integration's declared `context_file` metadata (R1), removing the dependency on `_load_agent_context_config` and the extension-config-driven `context_files` list. A small, self-contained formatting helper for one-or-more declared values may remain in the integration layer, but it MUST NOT read the extension config.

**Rationale**: FR-002 forbids the CLI reading the extension config. The integration already knows its own context file path(s), so the CLI can substitute the placeholder without touching extension-owned files. The plural `context_files` config key (read from `agent-context-config.yml`) is exactly the kind of extension-owned configuration the CLI must stop consuming.

**Alternatives considered**:
- *Stop substituting `__CONTEXT_FILE__` and leave the placeholder for the extension to fill*: rejected — placeholder appears in command templates the CLI renders at install time; leaving it unresolved would ship literal `__CONTEXT_FILE__` strings to users.
- *Keep the plural `context_files` resolver but only drop the config read*: viable; the resolver can stay as pure metadata formatting as long as every branch that reads `agent-context-config.yml` is removed. Decision defers the keep-vs-delete split for these helpers to `/speckit.tasks`, bound by the rule that no remaining branch reads the extension config.

## R3: Auto-install of the `agent-context` extension during `specify init`

**Current state**: `commands/init.py` (~lines 510–539) auto-installs the bundled `agent-context` extension during init, then writes its config (`context_file`) via `_update_agent_context_config_file` (~lines 541–549). It also appears as a tracker step and in `init.py:379` as a selectable install item.

**Decision**: Make installation **opt-in**. Remove the unconditional auto-install + config-write. The extension is offered through the normal extension-selection mechanism (the user chooses it); when chosen, the extension's own install logic seeds its config. The CLI no longer writes `agent-context-config.yml`.

**Rationale**: FR-005 requires the extension be opt-in; FR-002 forbids the CLI writing the extension config. Seeding config is the extension's responsibility (its bundled template `agent-context-config.yml` ships with the path/markers, and its install flow can populate `context_file`).

**Open implementation detail (defer to tasks)**: Exactly how the extension seeds `context_file` at install (static template vs. install hook reading the selected integration) is an implementation choice for `/speckit.tasks`. The spec only requires the CLI not do it. Default assumption: the extension ships a template config and its update script tolerates an empty/defaulted `context_file` by deriving from the active integration, consistent with the existing self-contained scripts.

**Alternatives considered**:
- *Keep auto-install but stop writing config*: rejected — auto-install still makes the extension non-opt-in, violating FR-005.

## R4: Extension-enabled gating + marker resolution in `base.py`

**Current state** (post-sync): `base.py` has `_agent_context_extension_enabled()` (~line 605, reads `.specify/extensions/.registry`) and `_resolve_context_markers()` (~line 645, reads `agent-context-config.yml`), used by `upsert_context_section()` (~line 895) and `remove_context_section()` (~line 948). Upstream additionally added `_resolve_context_file_values()` (~line 738), `_format_context_file_values()` (~line 787), and `_resolve_context_files()` (~line 791); upsert/remove now **iterate over a list of context files** (`for context_file in context_files:`) read from the extension config's plural `context_files` key.

**Decision**: Remove the gating helper, the marker resolver, and the `upsert_context_section()` / `remove_context_section()` methods (and their per-file loops) along with all their call sites in `setup()`/`teardown()` across the base classes (call sites at ~lines 1181, 1200, 1309, 1518, 1725, 1959). Remove `_resolve_context_files()` and the config-reading branches of `_resolve_context_file_values()`; retain only a pure metadata formatter if `__CONTEXT_FILE__` substitution still needs one (R2).

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
| R1 | Keep `context_file` as inert metadata (used for `__CONTEXT_FILE__` only) |
| R2 | Resolve `__CONTEXT_FILE__` from integration metadata, not extension config |
| R3 | Extension install becomes opt-in; CLI stops writing its config |
| R4 | Remove gating + marker-resolution + upsert/remove from base layer |
| R5 | Remove the deprecation warning and its test |
| R6 | Leave existing files intact; no CLI migration |
| R7 | Prune/relocate tests for removed CLI behavior |

All NEEDS CLARIFICATION resolved. No blocking unknowns remain for design.
