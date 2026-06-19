---
description: "Dependency-ordered task list for the Spec Kit Bundler (`specify bundle`) feature"
---

# Tasks: Spec Kit Bundler (`specify bundle` subcommand)

**Input**: Design documents from `/specs/001-spec-kit-bundler/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/, quickstart.md

**Tests**: Contract tests (manifest schema, catalog schema, CLI behavior) are included because the feature ships explicit contracts under `contracts/` and the plan defines `tests/contract/`. Per-story integration tests map to each story's Independent Test criteria. Unit tests cover the pure services (resolver, catalog stack, conflict, packager).

**Organization**: Tasks are grouped by user story so each story can be implemented, tested, and delivered as an independent increment.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story the task belongs to (US1–US4)
- Exact file paths are included in each description

## Path Conventions

The bundler lives **inside the `specify_cli` package** as a `bundle` Typer sub-app (no separate package or entry point). CLI dispatch lives under `src/specify_cli/commands/bundle/`; importable, independently testable logic lives under `src/specify_cli/bundler/`. Tests live under `tests/contract/`, `tests/integration/`, and `tests/unit/`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the bundler package skeleton inside `specify_cli` and wire the empty `bundle` sub-app onto the root `specify` CLI.

- [x] T001 Create the bundler package skeleton: `src/specify_cli/commands/bundle/__init__.py`, `src/specify_cli/bundler/__init__.py`, `src/specify_cli/bundler/models/__init__.py`, `src/specify_cli/bundler/services/__init__.py`, `src/specify_cli/bundler/lib/__init__.py` (empty modules, no logic yet)
- [x] T002 Register an empty `bundle` Typer sub-app in `src/specify_cli/commands/bundle/__init__.py` and mount it on the root `specify` app alongside the existing `extension`/`preset`/`workflow` groups so `specify bundle --help` resolves
- [x] T003 [P] Create the test package layout: `tests/contract/`, `tests/integration/`, `tests/unit/` with `__init__.py` files and shared fixtures (temp project factory, sample manifest/catalog files) in `tests/conftest.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared models and helpers that every user story depends on. No story command can be implemented until this phase is complete.

**⚠️ CRITICAL**: User-story phases (3–6) must not begin until Phase 2 is done.

- [x] T004 [P] Implement shared helpers in `src/specify_cli/bundler/lib/` (`yamlio.py` for YAML/JSON load+dump, `versioning.py` for SemVer compare/range checks via `packaging`, `project.py` for Spec Kit project + active-integration detection)
- [x] T005 [P] Implement the bundle manifest model in `src/specify_cli/bundler/models/manifest.py` (Bundle, Bundle Manifest, Component/Primitive Reference, Role from data-model.md), including parse-from-`bundle.yml` and structural normalization
- [x] T006 [P] Implement catalog models in `src/specify_cli/bundler/models/catalog.py` (Catalog Source with install-policy `install-allowed`/`discovery-only`, Catalog Entry, priority ordering per data-model.md)
- [x] T007 [P] Implement the installed-bundle record model in `src/specify_cli/bundler/models/records.py` (Installed Bundle Record: id, version, installed components, source, timestamp) plus project-state read/write
- [x] T008 Contract test for the manifest schema in `tests/contract/test_manifest_schema.py` asserting a valid `bundle.yml` parses and known-bad manifests (missing required fields, malformed component refs) are rejected — per `contracts/bundle-manifest.schema.md`
- [x] T009 [P] Contract test for the catalog schema in `tests/contract/test_catalog_schema.py` asserting source/entry shape, install-policy values, and priority ordering — per `contracts/bundle-catalog.schema.md`

**Checkpoint**: Models + helpers exist and are schema-validated — user story implementation can begin.

---

## Phase 3: User Story 1 - Consumer configures a project for their role in one step (Priority: P1) 🎯 MVP

**Goal**: `specify bundle install <bundle-id>` (and `specify bundle init`) takes a project from zero to fully role-configured — installing the bundle's declared integration, extensions, presets (with priorities), workflow steps, and workflows in one command.

**Independent Test**: From an empty/freshly initialized project, install a known bundle by name and verify the project now contains the declared integration, extensions, presets (expected priorities), workflow steps, and workflows — with no follow-up install steps.

### Implementation for User Story 1

- [x] T010 [P] [US1] Implement the manifest→component resolver in `src/specify_cli/bundler/services/resolver.py` (expand a manifest into the concrete ordered set of integration + extensions + presets + workflows to install)
- [x] T011 [P] [US1] Implement the catalog stack service in `src/specify_cli/bundler/services/catalog_stack.py` (priority-ordered source stack, resolve a bundle-id to an artifact, enforce per-source install policy, built-in default stack)
- [x] T012 [US1] Implement the in-process installer in `src/specify_cli/bundler/services/installer.py` that dispatches resolved components to the existing `extension`/`preset`/`workflow`/`integration` machinery (no re-implementation), preserving preset priorities and workflow step order, and **confining every resolved/written path to the project root and refusing symlink escapes** (Constitution Principle V) (depends on T010, T011)
- [x] T013 [US1] Record the install outcome (Installed Bundle Record) via `models/records.py` after a successful install in `installer.py`, making the bundle idempotent/re-runnable (depends on T012)
- [x] T014 [US1] Implement `specify bundle install <bundle-id>` in `src/specify_cli/commands/bundle/install.py` (resolve via catalog stack, enforce the FR-016 minimum-Spec-Kit-version gate before installing — refuse with a clear, actionable unmet-requirement message when the bundle's declared minimum exceeds the installed version, using `lib/versioning.py` — then run the installer and report installed components and failures with actionable errors)
- [x] T015 [US1] Implement `specify bundle init [<bundle>]` in `src/specify_cli/commands/bundle/init.py` (initialize a Spec Kit project if needed, then delegate to the install flow)
- [x] T016 [P] [US1] Integration test in `tests/integration/test_install_flow.py` covering the Independent Test: install a known bundle into a temp project and assert integration, extensions, presets (priorities), workflow steps, and workflows are all present after one command — **and assert idempotency: re-running install does not overwrite user-modified files** (Constitution Principle IV)
- [x] T017 [P] [US1] Unit tests for resolver and catalog stack in `tests/unit/test_resolver.py` and `tests/unit/test_catalog_stack.py` (expansion correctness, priority ordering, install-policy enforcement)

**Checkpoint**: A consumer can go from zero to a fully role-configured project with one command — MVP is functional and independently testable.

---

## Phase 4: User Story 2 - Author creates, validates, and publishes a bundle (Priority: P2)

**Goal**: An author hand-writes a `bundle.yml`, validates it (catching broken references), and builds a distributable artifact containing everything needed to install the bundle. No scaffold command; distribution is out-of-band via a catalog entry.

**Independent Test**: Author a manifest by hand, run validation (catch ≥1 deliberately broken reference), fix it, build the artifact, and confirm the artifact contains everything needed to install the bundle.

### Implementation for User Story 2

- [x] T018 [P] [US2] Implement manifest validation in `src/specify_cli/bundler/services/resolver.py` (extend with a `validate()` path) or a dedicated `validator.py`: structural checks plus reference resolution that flags unknown/broken component references
- [x] T019 [US2] Implement the artifact packager in `src/specify_cli/bundler/services/packager.py` (build a versioned, self-contained Bundle Artifact from a validated manifest per the Bundle Artifact entity), **confining all artifact input/output paths to safe roots and refusing symlink escapes** (Constitution Principle V)
- [x] T020 [US2] Implement `specify bundle validate` in `src/specify_cli/commands/bundle/validate.py` (run validation against the local `bundle.yml`, exit non-zero with a clear list of broken references on failure)
- [x] T021 [US2] Implement `specify bundle build` in `src/specify_cli/commands/bundle/build.py` (validate, then emit a versioned artifact; no first-class publish — print the artifact path and the catalog-entry guidance)
- [x] T022 [P] [US2] Integration test in `tests/integration/test_author_flow.py` covering the Independent Test: validate a manifest with a deliberately broken reference (expect failure), fix it, build, and assert the artifact is self-contained
- [x] T023 [P] [US2] Unit tests for the packager in `tests/unit/test_packager.py` (artifact contents, versioning, determinism)

**Checkpoint**: Authors can produce valid, distributable bundles; combined with US1 the supply→consume loop works end to end.

---

## Phase 5: User Story 3 - Consumer discovers and inspects bundles before installing (Priority: P3)

**Goal**: `specify bundle search` and `specify bundle info` let a consumer find bundles in the active catalog stack and inspect exactly what a bundle will install (components, versions, priorities) before committing.

**Independent Test**: With ≥1 bundle in the active catalog, search and confirm the target appears; inspect it and confirm the output enumerates the exact integration, extensions, presets, steps, and workflows (with versions/priorities) it will install.

### Implementation for User Story 3

- [x] T024 [P] [US3] Implement search over the catalog stack in `src/specify_cli/bundler/services/catalog_stack.py` (query across sources honoring priority + discovery-only visibility, dedupe by precedence)
- [x] T025 [US3] Implement `specify bundle search [<query>]` in `src/specify_cli/commands/bundle/search.py` (list matching bundles with source, install-policy, and trust annotations — distinguishing org-curated from community-sourced entries via the catalog source and the entry's verification indicator, per FR-010/FR-027)
- [x] T026 [US3] Implement `specify bundle info <bundle-id>` in `src/specify_cli/commands/bundle/info.py` (resolve the manifest and render the full component plan: integration, extensions, presets w/ priorities, workflow steps, workflows, versions — plus the entry's source catalog, install policy, and verification/trust indicator per FR-010/FR-027) reusing the resolver
- [x] T027 [P] [US3] Integration test in `tests/integration/test_discovery_flow.py` covering the Independent Test: search surfaces the target bundle and info enumerates the exact component set with versions/priorities

**Checkpoint**: Consumers can discover and transparently inspect bundles before install; US1–US3 each work independently.

---

## Phase 6: User Story 4 - Consumer manages bundle lifecycle and resolves conflicts (Priority: P3)

**Goal**: `specify bundle list`, `remove`, and `update` manage installed bundles, and conflict detection blocks unsafe installs (e.g. a bundle demanding a different integration than the active one) with clear, actionable errors. `update` re-resolves and refreshes via primitive paths, preserving primitive-level overrides, with no bundle-level merge.

**Independent Test**: Install two compatible bundles, list to confirm both, remove one and confirm only its components are gone, then attempt to install a bundle demanding a different integration and confirm the install fails with a clear error.

### Implementation for User Story 4

- [x] T028 [P] [US4] Implement conflict detection in `src/specify_cli/bundler/services/conflict.py` (integration clash vs active integration, preset/workflow overlap), returning structured, actionable findings
- [x] T029 [US4] Wire conflict detection into the install path in `installer.py`/`install.py` so unsafe installs abort with a clear message before any change is made (depends on T028, T012)
- [x] T030 [P] [US4] Implement `specify bundle list` in `src/specify_cli/commands/bundle/list.py` (read Installed Bundle Records and show installed bundles, versions, and sources)
- [x] T031 [US4] Implement `specify bundle remove <bundle-id>` in `src/specify_cli/commands/bundle/remove.py` (remove only the named bundle's recorded components, leaving co-installed bundles intact)
- [x] T032 [US4] Implement `specify bundle update [<bundle-id>|--all]` in `src/specify_cli/commands/bundle/update.py` (re-resolve from the catalog stack and refresh components via primitive paths, preserving primitive-level overrides, no bundle-level merge)
- [x] T033 [P] [US4] Integration test in `tests/integration/test_lifecycle_flow.py` covering the Independent Test: install two bundles, list both, remove one (assert only its components gone), and assert an integration-clash install fails with a clear error
- [x] T034 [P] [US4] Unit tests for conflict detection in `tests/unit/test_conflict.py` (integration clash, overlap precedence, message content)

**Checkpoint**: All four user stories are independently functional; lifecycle and safety are covered.

---

## Phase 7: Catalog Management & Polish (Cross-Cutting)

**Purpose**: Cross-cutting catalog configuration commands and final hardening. Catalog management underpins US1/US3/US4 but is exposed as its own command surface.

- [x] T035 [P] Implement `specify bundle catalog list` in `src/specify_cli/commands/bundle/catalog.py` (show the priority-ordered source stack with policy + priority, mirroring `specify extension catalog list`)
- [x] T036 [US4] Implement `specify bundle catalog add <url> [--policy ...] [--priority N]` and `specify bundle catalog remove <id|url>` in `catalog.py`, persisting to the bundler catalog config file with a built-in default fallback
- [x] T037 [P] Contract test for the CLI surface in `tests/contract/test_cli_commands.py` asserting every command in `contracts/cli-commands.md` exists, accepts its documented args, and returns exit code 0 on success / non-zero with a stderr message on failure
- [x] T038 [P] Validate the full feature against `quickstart.md` (scenarios A–G) and capture any gaps as follow-up tasks
- [x] T039 [P] Update user-facing docs (README / `docs/`) to document the `specify bundle` command group, manifest schema, and catalog model
- [x] T040 Final review against spec.md FR-001–FR-031: confirm each functional requirement is covered by an implemented command or service, and that no first-class publish command was introduced (FR-030)
- [x] T041 [P] Author, validate, and build the four representative role bundles (product manager, business analyst, security researcher, developer) as hand-written manifests under `examples/bundles/` (e.g. `examples/bundles/product-manager/bundle.yml`), each passing `specify bundle validate` and `specify bundle build`, and demonstrably installable per SC-005
- [x] T042 [P] Security tests in `tests/unit/test_bundler_path_safety.py` asserting the resolver, installer, and packager reject path-traversal and symlink-escape payloads in manifest/catalog-declared paths and confine all writes to the project root (Constitution Principles II & V), mirroring the existing `tests/test_registrar_path_traversal.py` patterns
- [x] T043 [P] Offline-first integration test in `tests/integration/test_offline_install.py` asserting `specify bundle install` resolves a bundled/local-or-pinned artifact + catalog and completes successfully with network access disabled (Constitution Principle IV), with no real outbound calls (network mocked/blocked)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories.
- **User Stories (Phases 3–6)**: All depend on Foundational. US1 (P1) is the MVP. US2–US4 can proceed in parallel after Foundational if staffed, or sequentially by priority (P1 → P2 → P3 → P3).
- **Catalog & Polish (Phase 7)**: Depends on the user stories whose behavior it finalizes (catalog management is used by US1/US3/US4; the CLI contract test depends on all commands existing). T041 (representative role bundles, SC-005) depends on US2 `validate`/`build` (T020, T021) and US1 `install` (T014) being functional.

### User Story Dependencies

- **US1 (P1)**: Depends only on Foundational. No dependency on other stories.
- **US2 (P2)**: Depends only on Foundational (reuses manifest models + resolver). Independent of US1 at runtime.
- **US3 (P3)**: Depends on Foundational; reuses the resolver and catalog stack from US1's services but is independently testable.
- **US4 (P3)**: Depends on Foundational; conflict wiring touches the US1 install path (T029 depends on T012).

### Within Each User Story

- Services (resolver, catalog stack, installer, packager, conflict) before the CLI commands that call them.
- Models before services (handled in Foundational).
- Integration/unit tests can be written in parallel with or just after the implementation they target.

### Parallel Opportunities

- All `[P]` Setup tasks can run together.
- All `[P]` Foundational model/helper tasks (T004–T007, T009) can run in parallel.
- Within US1, T010 and T011 are parallel; T016 and T017 are parallel.
- After Foundational, US2, US3, and US4 can be staffed in parallel by different developers.

---

## Parallel Example: User Story 1

```bash
# After Foundational completes, launch the two pure services in parallel:
Task: "Implement resolver in src/specify_cli/bundler/services/resolver.py"
Task: "Implement catalog stack in src/specify_cli/bundler/services/catalog_stack.py"

# Then launch US1 tests in parallel:
Task: "Integration test in tests/integration/test_install_flow.py"
Task: "Unit tests in tests/unit/test_resolver.py and tests/unit/test_catalog_stack.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories).
3. Complete Phase 3: User Story 1 (`specify bundle install` / `init`).
4. **STOP and VALIDATE**: Run `tests/integration/test_install_flow.py` and the US1 Independent Test.
5. Demo the one-command role configuration.

### Incremental Delivery

1. Setup + Foundational → foundation ready.
2. US1 → test independently → demo (MVP).
3. US2 (author/build) → test → demo.
4. US3 (discover/inspect) → test → demo.
5. US4 (lifecycle/conflicts) → test → demo.
6. Phase 7 catalog management + polish → finalize.

### Parallel Team Strategy

1. Whole team completes Setup + Foundational.
2. Then split: Dev A → US1, Dev B → US2, Dev C → US3, Dev D → US4.
3. Each story integrates independently; Phase 7 closes out the shared catalog surface and docs.

---

## Notes

- `[P]` tasks touch different files with no incomplete dependencies.
- `[Story]` labels map tasks to spec.md user stories for traceability.
- The bundler calls existing `specify` primitive machinery in-process — do not re-implement extension/preset/workflow/integration installation.
- There is no `specify bundle create` scaffold and no first-class publish command (FR-030) — keep both out of scope.
- Commit after each task or logical group; stop at any checkpoint to validate a story independently.

---

## Implementation Status & Deviations

All tasks T001–T043 are implemented and verified by an 82-test bundler suite
(`tests/{contract,unit,integration}/`), green on the project venv. Notable
deviations from the original task text:

- **T003**: shared test fixtures live in `tests/bundler_helpers.py` (a plain
  helper module), not `tests/conftest.py`, to avoid clobbering the repo's
  existing root `conftest.py`. Test directories intentionally have no
  `__init__.py`; collection works via `testpaths`/`python_files`.
- **File layout**: consume/author command handlers live together in
  `src/specify_cli/commands/bundle/__init__.py` (one Typer group) rather than
  one file per command (`install.py`, `init.py`, …). Behaviour and CLI surface
  match the contract.
- **Catalog config persistence** lives in
  `src/specify_cli/bundler/commands_impl/catalog_config.py`; the
  primitive-dispatch bridge lives in `src/specify_cli/bundler/services/{adapters,primitives}.py`.

## Validation (T038) — captured gaps → follow-ups

Quickstart scenarios A–G were exercised end-to-end (offline) via the Typer
CLI. `search`, `info`, `list`, `validate`, `build`, and `catalog list|add|remove`
pass. Two gaps were found and have since been closed:

- [x] T044 Wire real in-process primitive installation in
  `services/primitives.py` so `DefaultPrimitiveInstaller.install` actually adds
  components through the existing machinery. **Done:** presets and extensions
  install via their reusable managers (`install_from_directory` /
  `install_from_zip`) — bundled assets install fully offline, catalog assets are
  fetched only when the network is permitted; workflows and steps delegate to the
  existing `workflow add` / `workflow step add` command callables in-process
  (no duplicated download/validation logic, honouring Principle I).
  `--offline` is threaded through `DefaultPrimitiveInstaller(allow_network=…)`
  so network-only kinds refuse with an actionable message instead of silently
  reaching out. Verified end-to-end by installing the bundled `agent-context`
  extension offline from a local `.zip`.
- [x] T045 Support `specify bundle install <path-to-artifact|bundle-dir>`.
  **Done:** the install argument now accepts a `.zip` artifact, a bundle
  directory, or a `bundle.yml` file (`_local_manifest_source`), installing
  directly without consulting the catalog stack; bundle-ids still resolve via
  the stack as before.

## FR coverage (T040)

Confirmed: every consume/author/catalog command in `contracts/cli-commands.md`
exists with the documented exit-code behaviour; the FR-016 version gate,
FR-019 integration clash, FR-025 discovery-only refusal, FR-022/SC-004
non-collateral removal, FR-026 catalog precedence, and offline-first behaviour
are implemented and tested. **No first-class publish command was introduced
(FR-030).** Live in-process primitive dispatch is now wired for all four
component kinds (T044), with bundled presets/extensions installing offline.
