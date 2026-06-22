# Feature Specification: Agent-Context Extension Full Opt-In

**Feature Branch**: `001-agent-context-full-optin`

**Created**: 2026-06-22

**Status**: Draft

**Input**: User description: "Make the agent-context extension a full opt-in and have no configuration in the Python codebase that deals with any of it. The agent-context extension must fully own its own lifecycle and support should not be coming from the Specify CLI. We also need to make sure the deprecation message is removed if any."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Agent context management is fully owned by the extension (Priority: P1)

A Spec Kit user runs `specify init` for a project and selects a coding agent. Today, the Specify CLI itself writes and maintains the managed "Spec Kit" section inside the agent's context/instruction file (for example `CLAUDE.md`, `AGENTS.md`, or `.github/copilot-instructions.md`) during integration setup, in addition to the bundled `agent-context` extension. The user wants a single, predictable owner: the `agent-context` extension. When the extension is present and enabled, it manages the context section; when it is absent or disabled, nothing in the core CLI touches the context file.

**Why this priority**: This is the core intent of the feature. Dual ownership (CLI + extension) creates ambiguity about who writes the context section, produces duplicate or conflicting updates, and blocks the extension from being a true opt-in. Establishing the extension as the sole owner is the foundational change everything else depends on.

**Independent Test**: Initialize a project with any integration while the `agent-context` extension is NOT installed (or is disabled). Verify the core CLI creates no managed context section and writes no agent-context configuration. Then install/enable the extension and run its update command, and verify the context section is created and maintained by the extension alone.

**Acceptance Scenarios**:

1. **Given** a project initialized with an integration and the `agent-context` extension not installed, **When** integration setup runs, **Then** no managed Spec Kit section is created in the agent context file by the Specify CLI.
2. **Given** a project with the `agent-context` extension installed and enabled, **When** the extension's update command runs, **Then** the managed Spec Kit section in the agent context file is created or refreshed by the extension.
3. **Given** an integration is uninstalled or switched, **When** the operation completes, **Then** the core CLI performs no agent-context-related reads, writes, or cleanup.

---

### User Story 2 - No agent-context configuration lives in the Python codebase (Priority: P1)

A Spec Kit maintainer auditing the Specify CLI codebase wants to confirm that the CLI contains no agent-context-specific configuration logic: no reading or writing of the extension's config file, no `context_file` plumbing used to drive context-section updates, no marker constants used by core flows, and no enabled/disabled gating logic for the extension. All such concerns must live within the `agent-context` extension (its own scripts and config).

**Why this priority**: The user explicitly requires that "no configuration in the Python codebase deals with any of it" and that "support should not be coming from the Specify CLI." Without removing this code, the extension cannot fully own its lifecycle and the separation remains incomplete.

**Independent Test**: Search the Specify CLI source for agent-context concerns (config read/write helpers, context-section upsert/remove methods, extension-enabled gates, marker resolution). Confirm none remain wired into init, integration setup/teardown, or integration switching, and that the test suite still passes.

**Acceptance Scenarios**:

1. **Given** the Specify CLI source, **When** a maintainer inspects integration setup and teardown, **Then** there are no calls that create, update, or remove the managed agent context section.
2. **Given** the Specify CLI source, **When** a maintainer inspects `specify init` and integration switch/uninstall flows, **Then** there is no code that reads or writes the extension's `agent-context-config.yml`.
3. **Given** the Specify CLI source, **When** a maintainer inspects the integration base layer, **Then** there is no extension-enabled gating, marker-resolution, or context-file management logic for the agent-context extension.

---

### User Story 3 - The deprecation message is removed (Priority: P2)

A user running `specify init` or switching integrations currently sees a deprecation warning stating that inline agent-context updates during integration setup "will be disabled in v0.12.0" and pointing them to `specify extension disable agent-context`. Because the inline behavior is being removed entirely (not merely deprecated), this message is no longer accurate and must be removed so users are not warned about behavior that no longer exists.

**Why this priority**: The user explicitly asked to remove the deprecation message "if any." It is a user-visible cleanup that depends on the removal of the inline behavior in User Stories 1 and 2, so it is sequenced after them.

**Independent Test**: Run the flows that previously emitted the deprecation warning (integration setup) and confirm no agent-context deprecation message is printed. Confirm any test asserting the message's presence is removed or updated.

**Acceptance Scenarios**:

1. **Given** an integration setup that previously emitted the agent-context deprecation warning, **When** setup runs, **Then** no agent-context deprecation message is shown.
2. **Given** the test suite, **When** it runs, **Then** no test expects or asserts the removed deprecation message.

---

### Edge Cases

- **Extension disabled or absent**: When the `agent-context` extension is not installed or is explicitly disabled, the core CLI must do nothing to the agent context file — neither create, update, nor remove the managed section.
- **Pre-existing managed section from older versions**: A project initialized by a previous Spec Kit version may already contain a managed Spec Kit section in its context file. After this change, the core CLI must leave that section untouched; only the extension (when run) may update or remove it.
- **Pre-existing extension config file**: Projects that already have `.specify/extensions/agent-context/agent-context-config.yml` written by the old CLI must continue to work; the extension reads its own config, and the CLI must no longer overwrite it.
- **Integration switch with custom markers**: If a user customized the context markers in the extension config, switching integrations must not reset or rewrite those markers from the CLI side.
- **Documentation references**: Project documentation (for example `AGENTS.md`) that describes the CLI writing `context_file` "automatically" must be updated to reflect that the extension owns this behavior.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The Specify CLI MUST NOT create, update, or remove the managed Spec Kit section in any agent context/instruction file during integration setup, teardown, switching, or initialization.
- **FR-002**: The Specify CLI MUST NOT read from or write to the agent-context extension configuration file (`agent-context-config.yml`) in any code path (init, integration setup/teardown, integration switch/uninstall).
- **FR-003**: The integration base layer MUST NOT contain logic that resolves context markers, determines whether the agent-context extension is enabled, or manages the agent context section.
- **FR-004**: The `agent-context` extension MUST remain the sole owner of agent context file management, performing all reads, writes, marker resolution, and enable/disable behavior through its own bundled scripts and configuration.
- **FR-005**: The `agent-context` extension MUST be opt-in: when it is not installed or is disabled, no agent context section management occurs anywhere in Spec Kit.
- **FR-006**: The deprecation warning related to inline agent-context updates MUST be removed from the CLI so it is never emitted.
- **FR-007**: Integration definitions MUST NOT declare a context file. All agent→context-file knowledge (including the per-agent default mapping) MUST live within the `agent-context` extension. The CLI MUST contain no `context_file` field, plumbing, or default mapping in any form.
- **FR-008**: The change MUST NOT break existing projects: projects with previously-created managed sections or extension config files MUST continue to function, with the extension responsible for any further updates.
- **FR-009**: The automated test suite MUST be updated so that tests covering removed CLI behavior (context-section upsert/remove, config read/write, enabled gating, deprecation warning) are removed or relocated to the extension, and the suite passes.
- **FR-010**: Project documentation describing CLI-owned agent-context behavior MUST be updated to state that the `agent-context` extension fully owns this lifecycle.

### Key Entities

- **Agent context file**: The per-agent instruction file (e.g., `CLAUDE.md`, `AGENTS.md`, `.github/copilot-instructions.md`) containing a delimited "managed Spec Kit section."
- **Agent-context extension**: The bundled extension (`extensions/agent-context/`) that provides the update command, hooks, scripts, and configuration responsible for maintaining the managed section.
- **Agent-context configuration**: The extension's config file (`agent-context-config.yml`) holding the target context file path and section markers — read and written only by the extension.
- **Integration**: A Spec Kit agent integration whose setup/teardown previously triggered CLI-side context management.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After integration setup with the extension absent or disabled, 0 changes are made to any agent context file by the Specify CLI.
- **SC-002**: 0 references to agent-context configuration read/write, context-section management, extension-enabled gating, or any `context_file` declaration/plumbing remain in the Specify CLI source (outside the extension itself).
- **SC-003**: The agent-context deprecation message is emitted 0 times across all CLI flows.
- **SC-004**: 100% of the existing automated test suite passes after the relevant tests are removed or relocated to the extension.
- **SC-005**: With the extension installed and enabled, running its update command still produces a correct managed section, demonstrating no loss of end-user functionality.
- **SC-006**: Existing projects created before this change continue to operate without errors when running init, integration switch, or uninstall.

## Assumptions

- The `agent-context` extension's bundled scripts (bash and PowerShell) are already self-contained — they read their own configuration and update the context file independently — and therefore require no changes to keep functioning after CLI-side logic is removed.
- The extension is "bundled" with Spec Kit but treated as opt-in: its presence/enabled state governs whether agent context management happens at all.
- Integration classes MUST NOT declare a context file. The per-agent default mapping is removed from the CLI entirely and ships with the extension as `agent-context-defaults.json`; the extension self-seeds from its own map with no dependency on the CLI registry.
- "No configuration in the Python codebase" refers to logic and configuration handling that drives agent-context behavior (config file I/O, marker resolution, enabled gating, section upsert/remove, and the related calls), not to incidental string constants that may remain only if unused by any active code path.
- Backward compatibility means existing files are left intact and unmanaged by the CLI; it does not require the CLI to migrate or clean up previously written artifacts.
