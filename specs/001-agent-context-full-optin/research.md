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

**Current state**: `agents.py` (~lines 401–410) resolves `__CONTEXT_FILE__` by importing `_load_agent_context_config` and reading the extension's `agent-context-config.yml`, falling back to `init_opts["context_file"]`.

**Decision**: Resolve `__CONTEXT_FILE__` directly from the integration's declared `context_file` (the in-memory metadata from R1), removing the dependency on the extension config file.

**Rationale**: FR-002 forbids the CLI reading the extension config. The integration already knows its own context file path, so the CLI can substitute the placeholder without touching extension-owned files.

**Alternatives considered**:
- *Stop substituting `__CONTEXT_FILE__` and leave the placeholder for the extension to fill*: rejected — placeholder appears in command templates the CLI renders at install time; leaving it unresolved would ship literal `__CONTEXT_FILE__` strings to users.

## R3: Auto-install of the `agent-context` extension during `specify init`

**Current state**: `commands/init.py` (~lines 510–539) auto-installs the bundled `agent-context` extension during init, then writes its config (`context_file`) via `_update_agent_context_config_file` (~lines 541–549). It also appears as a tracker step and in `init.py:379` as a selectable install item.

**Decision**: Make installation **opt-in**. Remove the unconditional auto-install + config-write. The extension is offered through the normal extension-selection mechanism (the user chooses it); when chosen, the extension's own install logic seeds its config. The CLI no longer writes `agent-context-config.yml`.

**Rationale**: FR-005 requires the extension be opt-in; FR-002 forbids the CLI writing the extension config. Seeding config is the extension's responsibility (its bundled template `agent-context-config.yml` ships with the path/markers, and its install flow can populate `context_file`).

**Open implementation detail (defer to tasks)**: Exactly how the extension seeds `context_file` at install (static template vs. install hook reading the selected integration) is an implementation choice for `/speckit.tasks`. The spec only requires the CLI not do it. Default assumption: the extension ships a template config and its update script tolerates an empty/defaulted `context_file` by deriving from the active integration, consistent with the existing self-contained scripts.

**Alternatives considered**:
- *Keep auto-install but stop writing config*: rejected — auto-install still makes the extension non-opt-in, violating FR-005.

## R4: Extension-enabled gating + marker resolution in `base.py`

**Current state**: `base.py` has `_agent_context_extension_enabled()` (reads `.specify/extensions/.registry`) and `_resolve_context_markers()` (reads `agent-context-config.yml`), both used only by the upsert/remove methods.

**Decision**: Remove both helpers along with `upsert_context_section()`, `remove_context_section()`, and all their call sites in `setup()`/`teardown()` across the base classes.

**Rationale**: FR-001/FR-003 — the base layer must not manage the section, gate on the extension, or resolve markers. With the upsert/remove methods gone, these helpers are dead code.

**Alternatives considered**:
- *Keep helpers "just in case"*: rejected — FR-002/FR-003 and SC-002 require zero such references remaining; dead code with config I/O still violates the spec's intent.

## R5: The deprecation warning

**Current state**: `upsert_context_section()` prints a `rich` "Deprecation: …v0.12.0… run `specify extension disable agent-context`" warning every time it runs (base.py ~lines 711–718). A test asserts its presence.

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
