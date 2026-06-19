# Phase 0 Research: Spec Kit Bundler

**Feature**: Spec Kit Bundler | **Date**: 2026-06-19 | **Plan**: [plan.md](./plan.md)

This document resolves the open/uncertain items from the Technical Context and records the key design decisions, grounded in how the existing Spec Kit primitives (`specify extension|preset|workflow|integration`) actually behave. No `NEEDS CLARIFICATION` markers remain.

## R1. CLI placement, tech stack & packaging

- **Decision**: Implement the bundler as a `bundle` Typer sub-app **inside the existing `specify_cli` package**, registered on the root `specify` CLI alongside the `extension`/`preset`/`workflow` groups — surfaced as `specify bundle ...`. No separate package or entry point. Runtime is the existing Python ≥ 3.11 / `hatchling` build; dependencies (`typer`, `click`, `rich`, `pyyaml`, `packaging`, `platformdirs`) are already present. Default assets ship via the existing wheel `force-include` for offline/air-gapped installs.
- **Rationale**: User directive — the bundler must be a `specify bundle` subcommand, not a standalone CLI. Living in-package lets it call the existing primitive machinery in-process and reuse all conventions with zero new dependencies or distribution surface.
- **Alternatives considered**: Standalone package `spec_kit_bundler` with its own `bundle` entry point (rejected by user directive, despite the vision documents' "standalone CLI" framing); Go/Rust single-binary (rejected — diverges from the Python ecosystem the primitives live in, blocking direct in-process reuse of their machinery).

## R2. Authoring model (no scaffold)

- **Decision**: No `specify bundle create`/`new`/scaffold command. Bundles are hand-written `bundle.yml` manifests; the CLI provides only `validate` (lint + reference resolution) and `build` (package).
- **Rationale**: Verified that `specify extension`, `specify preset`, and `specify workflow` expose **no** authoring command — their surface is purely consumer-side (`list/add/remove/search/info/update/catalog`). Authoring is hand-written manifests (`extension.yml`, `preset.yml`) hosted and referenced from a catalog. Clarification Q1 resolved to align with this. Explicit, inspectable manifests beat generated boilerplate.
- **Alternatives considered**: Interactive wizard / full generator (rejected — inconsistent with siblings; risks implicit behavior).

## R3. Catalog model & install policy

- **Decision**: Adopt the sibling **catalog-stack** model: a priority-ordered list of catalog sources, each carrying install-policy metadata (`install allowed` vs `discovery only`), persisted to a bundle-catalog config file with a built-in default stack as fallback. `specify bundle catalog list/add/remove` manages sources. Install is permitted only from `install-allowed` sources; `discovery-only` entries remain visible in `search`/`info` but cannot be installed.
- **Rationale**: Confirmed directly from `specify extension catalog list`, which shows a priority-ordered stack (`default` priority 1 = "install allowed", `community` priority 2 = "discovery only") configured via `.specify/extension-catalogs.yml` with a built-in default fallback. This is the real, shipped model; Clarification Q2 resolved to adopt it wholesale, superseding the earlier "dual-catalog + `BUNDLE_CATALOG_URL` env var" framing.
- **Alternatives considered**: Dual-catalog + single env-var override (rejected — narrower than the real model, loses discovery-only nuance); env-var override retained as an extra lever (rejected for v1 — unnecessary given the config file; can be added later without breaking the model).

## R4. Install & init orchestration

- **Decision**: `specify bundle install` is self-sufficient: it idempotently ensures `specify init` has run, then installs each declared component through that component's own machinery. Integration/script resolution precedence: explicit flag (`--integration`/`--script`) > bundle's declared value > default (`copilot` + OS-appropriate script). A bundle declaring no integration inherits the project's already-active integration.
- **Rationale**: Directly from the spec (FR-011..FR-015) and the vision. Delegating to `specify init` keeps a single source of truth for project scaffolding and offline behavior. Copilot + OS-appropriate script matches `specify init`'s own non-interactive default.
- **Alternatives considered**: Requiring a separate `specify bundle init` before install (rejected — spec makes install self-sufficient; separate init remains optional for pinning the integration up front).

## R5. Update semantics

- **Decision**: `specify bundle update [<bundle>|all]` re-resolves the bundle's declared component set and refreshes each component via that primitive's normal update path. No bundle-level merge/conflict logic. Primitive-level user overrides (e.g. a manually set preset/extension priority) are preserved because they live in the primitive's own config, not the bundle.
- **Rationale**: `specify extension update` is deliberately simple ("update to latest version", single or all, no override-merge flags). Clarification Q3 resolved to mirror this and keep the "bundles add no resolution layer" principle intact.
- **Alternatives considered**: Full reinstall (remove+add) discarding drift (rejected — destroys legitimate user overrides); per-component interactive diff/prompt (rejected — adds a bundle-level resolution layer the design forbids).

## R6. Distribution / publishing

- **Decision**: No first-class publish/export in the core surface. `specify bundle build` produces a single versioned artifact (e.g. a `.zip`); the author hosts it out-of-band and adds a catalog entry whose `download_url` points at it. Any `publish`/`export` helper is optional and non-core.
- **Rationale**: Verified that no sibling primitive (`extension`/`preset`/`workflow`) has a publish/export/build command in its surface; distribution is out-of-band via hosting + catalog entry. Clarification Q4 resolved to match. The new vision itself calls publish/export "optional, not the primary architecture."
- **Alternatives considered**: First-class `bundle publish` to GitHub releases / OCI (rejected for v1 — couples the tool to a hosting channel; left as an open implementation question for distribution channel choice).

## R7. Conflict detection & resolution boundaries

- **Decision**: The bundler **detects and reports**, it does not resolve. Because it can compute the fully expanded component set before installing, it warns proactively (e.g. two presets overriding the same template; a bundle expecting `claude` while `copilot` is active). The one hard failure is the integration clash: installing a bundle that expects a different integration than the active one **fails with a clear error** asking the user to choose — never a silent switch/skip. All other conflicts resolve at the primitive level (preset priority/strategy stack; additive extensions/workflows/steps).
- **Rationale**: Spec FR-018..FR-020 and the "bundles expand, they don't overlay" section. Keeps resolution where it already lives.
- **Alternatives considered**: A bundle-level precedence/override system (rejected explicitly by the spec).

## R8. Role model

- **Decision**: `role` is open-ended discovery/curation metadata, not a fixed/closed enum. Any role can be expressed as a bundle without a system change. v1 proves the model with a representative subset (PM, BA, security researcher, developer); platform engineer and QA/release manager are supported examples, not required deliverables.
- **Rationale**: Clarification Q5; the vision stresses "examples, not limitations." Keeps acceptance achievable while preserving extensibility.
- **Alternatives considered**: Fixed enum of roles (rejected — not extensible); committing v1 to all six named roles (rejected — over-commits acceptance).

## R9. Versioning, pinning & compatibility checks

- **Decision**: Bundles and their declared components are semver-pinned. `specify bundle validate` checks the manifest is well-formed and that every reference resolves against the active catalog stack. `specify bundle install`/`update` refuse when a bundle's declared minimum Spec Kit version exceeds the installed version, with a clear explanation. Use the `packaging` library for version parsing/constraint evaluation (as `specify-cli` does).
- **Rationale**: Spec FR-002, FR-005, FR-016; reproducibility principle. Reusing `packaging` keeps constraint semantics identical to the rest of Spec Kit.
- **Alternatives considered**: Loose/unpinned references (rejected — breaks reproducibility and governance).

## R10. State & file locations

- **Decision**: Bundle catalog sources live in a project-scoped config file (mirroring `.specify/extension-catalogs.yml`, e.g. `.specify/bundle-catalogs.yml`) with a user-scoped fallback via `platformdirs`, and the built-in default stack beneath that — yielding the project > user > built-in precedence the vision describes. Installed-bundle records (which bundles, versions, and the components each contributed) are tracked under the project's `.specify/` tree so `list`/`remove` are precise and non-destructive to other bundles' components.
- **Rationale**: Matches the sibling catalog config pattern and the spec's transparency/reversibility and non-collateral-removal requirements (FR-021..FR-023, SC-004).
- **Alternatives considered**: Inferring installed bundles from component state alone (rejected — cannot reliably attribute shared components to the right bundle for safe removal).
