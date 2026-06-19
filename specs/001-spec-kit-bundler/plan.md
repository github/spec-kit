# Implementation Plan: Spec Kit Bundler

**Branch**: `001-spec-kit-bundler` | **Date**: 2026-06-19 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-spec-kit-bundler/spec.md`

**Note**: This plan was produced by the `/speckit.plan` command. It covers Phase 0 (research) and Phase 1 (design & contracts). Task breakdown is produced separately by `/speckit.tasks`.

## Summary

Spec Kit Bundler adds a `specify bundle ...` subcommand group to the existing `specify` CLI that lets organizations define, distribute, discover, and install **role-oriented bundles** — versioned, one-stop-shop packages that compose existing Spec Kit primitives (integration, extensions, presets, workflow steps, workflows) into a single installable unit. The bundler is a **composition and distribution layer only**: it expands a hand-written manifest into concrete component installs and delegates every install/update/remove and all conflict resolution to each primitive's existing machinery (preset priority stack, single-active-integration rule, additive extensions/workflows/steps).

Technical approach: implement the bundler **inside the `specify-cli` package** as a `bundle` Typer sub-app registered on the root `specify` app — no separate package or entry point. It reuses the same language/runtime, CLI framework, manifest/catalog conventions, and air-gapped packaging as the rest of `specify`, and calls the existing primitive machinery in-process. Distribution reuses the sibling **catalog-stack model**: a priority-ordered stack of catalog sources, each carrying install-policy metadata (`install-allowed` vs `discovery-only`), managed via a `specify bundle catalog list/add/remove` config file with a built-in default stack. There is no authoring scaffold and no first-class publish command — `specify bundle build` produces a versioned artifact that is hosted out-of-band and surfaced via a catalog entry, exactly as the sibling primitives are distributed.

## Technical Context

**Language/Version**: Python ≥ 3.11 (matches `specify-cli` `requires-python = ">=3.11"`).

**Primary Dependencies**: `typer` + `click` + `rich` (CLI UX), `pyyaml` (manifest + catalog config), `packaging` (semver/version constraint checks), `platformdirs` (user-level config/cache locations). These are already `specify-cli` dependencies — the bundler adds no new ones and runs inside the existing CLI.

**Storage**: Files only — hand-written `bundle.yml` manifests, JSON catalog files, a YAML catalog-source config (project + user scope), and an installed-bundle record inside the target project's `.specify/` tree. No database.

**Testing**: `pytest` (with `pytest-cov`), mirroring the existing `tests/` layout and conventions in this repo.

**Target Platform**: Cross-platform developer workstations / CI (Linux, macOS, Windows). Must be air-gap friendly — installable from pinned URLs or local paths without network access (the artifact bundles its own default assets via hatchling `force-include`, the same way `specify init` works offline).

**Project Type**: A `bundle` subcommand group **within** the existing `specify` CLI (single project), implemented in the `specify_cli` package and registered on the root Typer app — no separate package or entry point. Packaged with the existing `hatchling` build.

**Performance Goals**: Interactive CLI latency — discovery/inspection/install operations feel instantaneous for human-scale catalogs (hundreds of bundles, dozens of components per bundle). No throughput targets; correctness and predictability dominate.

**Constraints**: Composition-only — MUST NOT re-implement primitive runtimes; MUST delegate install/update/remove and conflict resolution to the underlying `specify extension|preset|workflow|integration` machinery. MUST be fully transparent (inspection equals what install does) and reversible (clean remove). Offline-capable.

**Scale/Scope**: v1 surface ≈ a dozen commands (`init`, `validate`, `build`, `search`, `info`, `install`, `update`, `list`, `remove`, `catalog list/add/remove`). Catalogs scale to hundreds of bundle entries; bundles compose up to a few dozen components each. A representative set of role bundles (PM, BA, security researcher, developer) proves the model.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Evaluated against the ratified **Spec Kit Constitution v1.0.0** (`.specify/memory/constitution.md`), Principles I–V:

- **I. Code Quality & Architectural Discipline** — PASS. The `bundle` group is a Typer sub-app under `src/specify_cli/commands/bundle/` with importable, Typer-free logic under `src/specify_cli/bundler/` (models/services/lib), registered via a `register(app)` function. New modules use `from __future__ import annotations` and modern typing. No private cross-package imports. (See Project Structure; Structure Decision.)
- **II. Test-Backed Change (NON-NEGOTIABLE)** — PASS. The plan defines `tests/contract`, `tests/integration`, and `tests/unit`, with contract tests for the manifest/catalog schemas and CLI surface, and mandatory security tests (path-traversal/symlink) for the resolver/installer per Principle II/V. All tests must pass the ubuntu+windows × Py 3.11–3.13 matrix with network mocked.
- **III. CLI & UX Consistency** — PASS. The command surface reuses the shared verb vocabulary (`list/install/remove/search/info/update`) and the `bundle catalog list|add|remove` catalog-stack + install-policy model, mirroring `extension|preset|workflow`. Rich output grammar and `--json`→stdout / logs→stderr conventions apply. (See `contracts/cli-commands.md`.)
- **IV. Offline-First Performance & Resource Discipline** — PASS. Default assets ship via the existing wheel `force-include`; resolution prefers bundled, then source, then network (lazy, timeout-bounded, cache-fallback). Installs are idempotent and hash-tracked through the existing manifest machinery; symlink/traversal escapes are refused. The bundler reuses primitive machinery in-process rather than adding eager startup cost.
- **V. Minimal Dependencies & Safe, Idempotent File Operations** — PASS. Zero new runtime dependencies (typer/click/rich/pyyaml/packaging/platformdirs already present). Paths from manifest/catalog input are confined to the project root; errors are explicit and chained; bundles and components are SemVer-pinned. (See FR-002/003/015/018, research R1.)

**Complexity Tracking**: no deviations to justify — the design adds no parallel installer/resolution layer and introduces no new dependencies or distribution surface.

**Gate result**: PASS (all five binding principles satisfied; re-validated after Phase 1 design).

## Project Structure

### Documentation (this feature)

```text
specs/001-spec-kit-bundler/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   ├── cli-commands.md          # specify bundle command contract surface
│   ├── bundle-manifest.schema.md # bundle.yml manifest schema contract
│   └── bundle-catalog.schema.md  # bundle catalog entry/source schema contract
├── checklists/
│   └── requirements.md  # Spec quality checklist (/speckit.specify output)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

The bundler lives **inside the `specify_cli` package** as a `bundle` Typer sub-app, mirroring how the existing primitive command groups (`extension`, `preset`, `workflow`) are organized. It is not a separate package or entry point; `specify bundle ...` dispatches into these modules.

```text
src/specify_cli/commands/bundle/
├── __init__.py          # registers the `bundle` Typer sub-app on the root `specify` app
├── init.py              # specify bundle init
├── validate.py          # specify bundle validate
├── build.py             # specify bundle build
├── search.py            # specify bundle search
├── info.py              # specify bundle info
├── install.py           # specify bundle install
├── update.py            # specify bundle update
├── list.py              # specify bundle list
├── remove.py            # specify bundle remove
└── catalog.py           # specify bundle catalog list/add/remove

src/specify_cli/bundler/   # non-CLI logic (importable, testable independently of Typer)
├── models/              # manifest, catalog entry, catalog source, install policy, role
│   ├── manifest.py
│   ├── catalog.py
│   └── records.py       # installed-bundle record
├── services/            # orchestration (no primitive runtime re-implementation)
│   ├── resolver.py      # expand manifest → concrete component set; resolve from catalog stack
│   ├── catalog_stack.py # priority-ordered source stack + install-policy enforcement
│   ├── installer.py     # dispatch to existing extension|preset|workflow|integration machinery (in-process)
│   ├── conflict.py      # pre-install detection/reporting (integration clash, preset overlap)
│   └── packager.py      # build artifact from a validated manifest
└── lib/                 # shared helpers (versioning, yaml/json io, project detection)

tests/
├── contract/            # manifest schema, catalog schema, CLI command contracts
├── integration/         # end-to-end install/update/remove against a Spec Kit project
└── unit/                # resolver, catalog stack, conflict detection, packager
```

**Structure Decision**: A `bundle` Typer sub-app registered on the root `specify` CLI (single project), implemented inside the `specify_cli` package alongside the existing `extension`/`preset`/`workflow` command groups, with non-CLI logic under `specify_cli/bundler/` so it is testable independently. There is no separate package or entry point — `specify bundle ...` is the user-facing surface. The bundler calls the existing primitive machinery **in-process** rather than re-implementing it (see `bundler/services/installer.py`). This satisfies the directive to ship the bundler as a `specify` subcommand (overriding the vision documents' "standalone CLI" framing).

## Complexity Tracking

> No constitutional violations to justify (constitution is the unfilled template; no binding gates). Section intentionally empty.
