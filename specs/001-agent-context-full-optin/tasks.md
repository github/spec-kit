# Tasks: Agent-Context Extension Full Opt-In

**Input**: Design documents from `/specs/001-agent-context-full-optin/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli-behavior.md, quickstart.md

**Tests**: INCLUDED. FR-009 requires test updates and Constitution Principle II (Test-Backed Change) is NON-NEGOTIABLE, so test tasks are mandatory here.

**Organization**: Grouped by the three user stories. Note: US1 (remove section management) and US2 (remove config I/O) are both P1 and tightly coupled — US1's `upsert/remove` methods are the only callers of US2's config readers, and US3 (deprecation removal) falls out of US1 because the warning lives inside `upsert_context_section`. The foundational phase makes `__CONTEXT_FILE__` resolution config-independent so the config helpers can be deleted cleanly.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1, US2, US3
- All paths are repository-relative.

## Path Conventions

Single project: Specify CLI source under `src/specify_cli/`, tests under `tests/`, bundled extension under `extensions/agent-context/`, docs at repo root and `docs/`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish baseline and the static guard that defines "done".

- [ ] T001 Run `pytest -q` from repo root and record the baseline pass state and the exact set of currently-passing agent-context tests that this feature will modify (`tests/extensions/test_extension_agent_context.py`, `tests/integrations/test_integration_{claude,codex,cursor_agent}.py`, `tests/integrations/test_registry.py`, `tests/integrations/test_integration_base_{markdown,skills}.py`).
- [ ] T002 [P] Add a static guard test `tests/extensions/test_agent_context_cli_free.py` that asserts `src/specify_cli/**` contains **zero** references to `upsert_context_section`, `remove_context_section`, `_agent_context_extension_enabled`, `_resolve_context_markers`, `_resolve_context_files`, `_AGENT_CTX_EXT_CONFIG`, `_load_agent_context_config`, `_save_agent_context_config`, `_update_agent_context_config_file`, the string `agent-context-config`, and the string `Inline agent-context updates`. This test is EXPECTED TO FAIL now and pass at the end (maps to contract C5).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Remove `__CONTEXT_FILE__` resolution from the CLI and drop the placeholder from the core templates, so the config helpers can be deleted without leaving unresolved placeholders.

**⚠️ CRITICAL**: T003–T004 MUST complete before US2 (config-helper deletion).

- [ ] T003 In `src/specify_cli/agents.py`, delete the `__CONTEXT_FILE__` resolution block entirely (including the local `from . import _load_agent_context_config` import). The CLI no longer substitutes the placeholder.
- [ ] T004 In `src/specify_cli/integrations/base.py`, delete `_resolve_context_file_values`, `_format_context_file_values`, and `_resolve_context_files` outright — no context-file helper survives (R1/R2). Remove the `__CONTEXT_FILE__` placeholder from `templates/commands/plan.md`.
- [ ] T005 [P] Add/extend a unit test in `tests/integrations/test_integration_base_markdown.py` asserting that no `__CONTEXT_FILE__` placeholder survives in rendered command files and that the CLI never reads `agent-context-config.yml`.

**Checkpoint**: Template rendering no longer depends on the extension config.

---

## Phase 3: User Story 1 - Extension is sole owner of context management (Priority: P1) 🎯 MVP

**Goal**: The CLI no longer creates/updates/removes the managed context section; the `agent-context` extension owns it entirely and self-seeds its own config.

**Independent Test**: Run an integration `setup()`/`teardown()` in a `tmp_path` project with no extension installed → no managed section is written/removed by the CLI. With the extension installed+enabled, its update command still produces a correct section.

### Tests for User Story 1

- [ ] T006 [P] [US1] Update `tests/integrations/test_integration_claude.py` to assert `setup()` does NOT create a `CLAUDE.md` managed section (remove the upsert assertion); keep the command-file install assertions.
- [ ] T007 [P] [US1] Update `tests/integrations/test_integration_codex.py` similarly (drop context-section assertions; keep skill/command assertions).
- [ ] T008 [P] [US1] Update `tests/integrations/test_integration_cursor_agent.py` similarly (drop `.mdc` managed-section + frontmatter assertions tied to upsert/remove).
- [ ] T009 [P] [US1] Update `tests/integrations/test_registry.py` to drop the unique-`context_file`-per-integration assertion if it exercises section management; keep the registry parity assertions (Principle II parity invariant MUST remain).
- [ ] T010 [P] [US1] In `tests/extensions/test_extension_agent_context.py`, prune the CLI-side section-management classes (`TestContextMarkerResolution`, `TestUpsertWithCustomMarkers`, `TestExtensionEnabledGate`) and relocate any still-valid behavior to extension-script-driven tests; keep `TestExtensionLayout` and `TestCatalogEntry`.
- [ ] T011 [P] [US1] Add an extension-driven test (in `tests/extensions/test_extension_agent_context.py`) that runs the bundled `extensions/agent-context/scripts/bash/update-agent-context.sh` in a `tmp_path` project (guarded with `@requires_bash`) and asserts it creates/refreshes the managed section from its own config (maps to contracts C2, C7).

### Implementation for User Story 1

- [ ] T012 [US1] Remove `upsert_context_section()` and `remove_context_section()` methods from `src/specify_cli/integrations/base.py` (these contain the per-file `for context_file in context_files:` loops and the deprecation warning).
- [ ] T013 [US1] Remove all `self.upsert_context_section(project_root)` / `self.remove_context_section(project_root)` call sites in `setup()`/`teardown()` across the base classes in `src/specify_cli/integrations/base.py` (the 6 call sites: IntegrationBase, MarkdownIntegration, plus the Toml/Yaml/Skills/Copilot-style setups, and the teardown).
- [ ] T014 [US1] Remove now-dead helpers `_agent_context_extension_enabled()`, `_resolve_context_markers()`, `_resolve_context_files()`, `_build_context_section()`, and the `CONTEXT_MARKER_START`/`CONTEXT_MARKER_END` constants from `src/specify_cli/integrations/base.py` if no remaining code references them (verify with grep).
- [ ] T015 [US1] Make the `agent-context` extension self-seed its target context file so it no longer depends on the CLI writing `context_file`/`context_files`. Update `extensions/agent-context/scripts/bash/update-agent-context.sh` and `extensions/agent-context/scripts/powershell/update-agent-context.ps1` (and, if needed, `extensions/agent-context/agent-context-config.yml` defaults) so the script derives the context file from the active integration/registry when the config value is empty (R3, contract C7).

**Checkpoint**: CLI setup/teardown touches no context file; extension manages it end-to-end.

---

## Phase 4: User Story 2 - No agent-context configuration in the Python codebase (Priority: P1)

**Goal**: Remove every agent-context config read/write from the CLI source.

**Independent Test**: `grep` of `src/specify_cli/` for the config helper symbols and `agent-context-config` returns nothing (T002 guard passes); `specify init` writes no `agent-context-config.yml`.

### Tests for User Story 2

- [ ] T016 [P] [US2] In `tests/extensions/test_extension_agent_context.py`, remove `TestExtensionConfigWriters` (it asserts CLI writes/clears the extension config) and replace with a test asserting the CLI does NOT create `.specify/extensions/agent-context/agent-context-config.yml` during integration switch/uninstall.
- [ ] T017 [P] [US2] Add an init-level test (in the appropriate `tests/` location, e.g. `tests/test_init*.py` or `tests/integrations/`) asserting that `specify init` WITHOUT selecting the extension creates no managed section and no extension config (contract C1, SC-001), and that init remains idempotent.

### Implementation for User Story 2

- [ ] T018 [US2] Remove `_AGENT_CTX_EXT_CONFIG`, `_load_agent_context_config()`, `_save_agent_context_config()`, and `_update_agent_context_config_file()` from `src/specify_cli/__init__.py` (~lines 269–328, including the `context_files`/`preserve_context_files` handling).
- [ ] T019 [US2] In `src/specify_cli/commands/init.py`, remove the `_update_agent_context_config_file` import (~line 174), the agent-context auto-install block (~lines 510–539), and the config-write block (~lines 541–549). Ensure the extension is offered only through the normal opt-in extension-selection mechanism (R3, contract C2); remove the dedicated tracker step if it forced installation.
- [ ] T020 [US2] In `src/specify_cli/integrations/_helpers.py`, remove the agent-context config clearing on uninstall (~lines 108–134) and the config updating on integration switch (~lines 280–324), including the `_AGENT_CTX_EXT_CONFIG` / `_update_agent_context_config_file` imports and `context_file`/`context_files` popping that exists solely to feed the extension config.
- [ ] T021 [US2] Grep `src/specify_cli/` to confirm no remaining import or reference to the removed `__init__.py` helpers; fix any stragglers (e.g. `agents.py` should already be clean from T003).

**Checkpoint**: T002 guard test passes; CLI is config-free for agent-context.

---

## Phase 5: User Story 3 - Deprecation message removed (Priority: P2)

**Goal**: The v0.12.0 deprecation warning is never emitted.

**Independent Test**: Integration setup prints no agent-context deprecation message; no test asserts it.

### Tests for User Story 3

- [ ] T022 [US3] In `tests/extensions/test_extension_agent_context.py`, remove `TestDeprecationWarning` (asserts the message is/ isn't emitted). The behavior it tested no longer exists.

### Implementation for User Story 3

- [ ] T023 [US3] Verify the deprecation `console.print("…Inline agent-context updates…")` block is gone (it was removed with `upsert_context_section` in T012). Grep `src/specify_cli/` for `Inline agent-context updates` and `v0.12.0` to confirm zero matches (contract C5, SC-003).

**Checkpoint**: No deprecation output anywhere.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Docs, backward-compat verification, lint, and full validation.

- [ ] T024 [P] Update `AGENTS.md` "Context file behavior" section to state the `agent-context` extension fully owns context-file creation/update/removal; remove the "`context_file` is written automatically … when `specify init` or `specify integration use` is run" language and the references to `upsert_context_section()` / `remove_context_section()` as Python-layer gates (FR-010).
- [ ] T025 [P] Update user-facing docs under `docs/` and `extensions/agent-context/README.md` to describe the extension as opt-in and the sole owner; add a `CHANGELOG.md` entry noting the behavior change (SemVer / Principle V).
- [ ] T026 [P] Update `src/specify_cli/integration_scaffold.py` (and `tests/` for it): remove the `context_file = "AGENTS.md"` line from the scaffold template and any comment/assertion referencing it, so newly scaffolded integrations declare no context file.
- [ ] T027 Add a backward-compatibility test: a `tmp_path` project pre-seeded with a legacy managed section and an `agent-context-config.yml` survives `init` / integration switch / uninstall unchanged by the CLI (contract C6, SC-006).
- [ ] T028 [P] Run `ruff check src/` and `markdownlint-cli2` on changed docs; fix violations (Security & Cross-Platform Constraints gate).
- [ ] T029 Run the full `pytest -q` suite and confirm green, including the T002 guard and the new extension-driven test (SC-004). Cross-platform note: bash-script test (T011) auto-skips on Windows via `@requires_bash`.
- [ ] T030 Execute `specs/001-agent-context-full-optin/quickstart.md` Validations 1–5 and confirm each passes (grep guards empty, init makes no context changes, extension update still works, legacy projects unaffected).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies. T002 establishes the failing guard.
- **Foundational (Phase 2)**: Depends on Setup. BLOCKS US2 (must decouple `__CONTEXT_FILE__` from the config before deleting config helpers).
- **US1 (Phase 3)**: Depends on Foundational. Removing `upsert/remove` also removes the deprecation warning (enables US3) and the only callers of the config readers (enables US2).
- **US2 (Phase 4)**: Depends on Foundational + US1 (the config readers are dead once US1 removes their callers).
- **US3 (Phase 5)**: Depends on US1 (warning removed with `upsert`); mostly verification + test cleanup.
- **Polish (Phase 6)**: Depends on US1–US3 complete.

### User Story Dependencies

- **US1 (P1)**: Foundational only. The MVP slice — delivers "extension is sole owner".
- **US2 (P1)**: Builds on US1 (shared base.py file; sequence US1 → US2 to avoid churn).
- **US3 (P2)**: Effectively completed by US1; isolated here for traceability and test cleanup.

### Within Each User Story

- Update/relocate tests alongside the code change in the same file to keep the suite green per task group.
- `base.py` edits (T012–T014) are sequential (same file). `__init__.py`, `commands/init.py`, `_helpers.py` edits (T018–T020) touch different files and can parallelize once US1 lands.

### Parallel Opportunities

- T002 ‖ T001 follow-up.
- Test updates T006–T011 are different files → all `[P]`.
- US2 implementation T018 ‖ T019 ‖ T020 (different files), then T021 verification.
- Polish docs T024 ‖ T025 ‖ T026 ‖ T028.

---

## Parallel Example: User Story 1 test updates

```bash
# Different test files — safe to run/edit in parallel:
Task: "Update tests/integrations/test_integration_claude.py (T006)"
Task: "Update tests/integrations/test_integration_codex.py (T007)"
Task: "Update tests/integrations/test_integration_cursor_agent.py (T008)"
Task: "Update tests/integrations/test_registry.py (T009)"
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Phase 1 Setup → Phase 2 Foundational → Phase 3 US1.
2. **STOP and VALIDATE**: CLI setup/teardown touches no context file; extension still manages it. This is a shippable, behavior-correct increment.

### Incremental Delivery

1. US1 → extension is sole owner (MVP).
2. US2 → CLI is fully config-free (T002 guard goes green).
3. US3 → confirm/clean deprecation removal.
4. Polish → docs, backward-compat, lint, full suite, quickstart.

### Constitution Gates (must hold throughout)

- Principle II parity: every integration keeps its registry entry + `test_integration_<key>.py`; do not delete parity tests (only context-section assertions).
- Network mocked; security/idempotency suites untouched.
- `ruff` + `markdownlint` + full pytest matrix green before merge.

---

## Notes

- `[P]` = different files, no dependencies.
- Remove `context_file` class attributes from all integrations — the CLI holds no context-file state; the per-agent defaults map lives in the extension (`agent-context-defaults.json`).
- Commit after each task or logical group; keep the suite green at every checkpoint.
- The bundled extension scripts are the new single owner — T015 is the one place extension behavior changes (self-seeding); all other extension files stay intact.
