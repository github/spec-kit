# Phase 1 Data Model: Spec Kit Bundler

**Feature**: Spec Kit Bundler | **Date**: 2026-06-19 | **Plan**: [plan.md](./plan.md)

Entities are derived from the spec's Key Entities and Functional Requirements. These describe logical structure and validation rules — not storage schemas or class definitions. The bundler stores everything as files (YAML manifests, JSON catalogs, YAML catalog config, JSON installed-bundle records).

## Entity: Bundle

A versioned, role-oriented package that composes existing Spec Kit primitives. A meta concept: it expands to concrete component installs and adds no resolution layer of its own.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| id | string (slug) | yes | Unique within a catalog source |
| name | string | yes | Human-readable |
| version | semver string | yes | Reproducibility (FR-002) |
| role | string | yes | Open-ended metadata, not a closed enum (FR-031) |
| description | string | yes | For discovery |
| author | string | yes | Governance |
| license | string | yes | Governance |
| tags | string[] | no | Discovery filters |

**Relationships**: declares one optional `Integration` reference; declares many `Component` references (extensions, presets, steps, workflows); described by exactly one `Bundle Manifest`; published as one `Bundle Artifact`; listed by zero-or-more `Catalog Entry` records.

## Entity: Bundle Manifest (`bundle.yml`)

The hand-written description of a bundle. Source of truth for authoring. No scaffold generates it (FR-007).

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| schema_version | string | yes | Known/supported value |
| bundle | object | yes | Carries the Bundle identity/metadata fields above |
| requires.speckit_version | version constraint | yes | Evaluated with `packaging`; install refuses if unmet (FR-016) |
| requires.tools / requires.mcp | string[] | no | Declared prerequisites |
| integration.id | string | no | Absent ⇒ agnostic bundle inherits active integration (FR-004, FR-014) |
| provides.extensions[] | Component ref | no | Each pinned to version or catalog source (FR-003) |
| provides.presets[] | Component ref + priority + strategy | no | Priority/strategy passed through to preset machinery |
| provides.steps[] | Component ref | no | May be empty until step catalog lands |
| provides.workflows[] | Component ref | no | Pinned references |

**Validation rules** (enforced by `specify bundle validate`, FR-005):

- Manifest is well-formed YAML and matches the schema.
- All identity/metadata required fields present.
- Every `provides.*` reference resolves to a real component in the active catalog stack (or pinned URL/path).
- `requires.speckit_version` is a valid version constraint.
- Preset entries carry a numeric priority and a valid composition strategy (`replace`/`prepend`/`append`/`wrap`).

## Entity: Component (Primitive) Reference

A pointer to an existing Spec Kit unit a bundle installs: integration, extension, preset, workflow step, or workflow.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| id | string | yes | Component identifier |
| version | semver string | yes for installable refs | Pinned for reproducibility |
| source | string (catalog id / URL / path) | no | Defaults to active catalog stack resolution |
| priority | integer | presets only | Lower wins in the preset stack |
| strategy | enum | presets only | `replace`/`prepend`/`append`/`wrap` |

**Behavior**: installed/updated/removed exclusively through the component's own machinery (FR-015). The bundler never re-implements a primitive runtime.

## Entity: Bundle Artifact

The single versioned, distributable package produced from a validated manifest (FR-006).

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| bundle_id | string | yes | Matches manifest |
| version | semver string | yes | Matches manifest |
| contents | packaged files | yes | Manifest + README + any local assets |
| download_url | URL | n/a (set by host) | Recorded in the catalog entry, not the artifact |

**Lifecycle**: `validate` → `build` → host out-of-band → reference from a catalog entry (FR-030). No first-class publish.

## Entity: Catalog Source

A single entry in the priority-ordered catalog stack.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| id | string | yes | Source identifier (e.g. `default`, `community`, org name) |
| url | string (URL/path) | yes | Location of the catalog JSON |
| priority | integer | yes | Lower number = higher precedence in the stack |
| install_policy | enum | yes | `install-allowed` or `discovery-only` (FR-025) |
| scope | enum | derived | project / user / built-in (precedence: project > user > built-in) |

**Validation/behavior**:

- Install permitted only from `install-allowed` sources; `discovery-only` entries appear in `search`/`info` but installing them is refused with a clear message (FR-025, edge cases).
- Unreachable/misconfigured source ⇒ discovery/install fails naming the offending source (edge case).
- Managed via `specify bundle catalog list/add/remove`, persisted to the project-scoped config file with user-scoped and built-in fallbacks (FR-026, R10).

## Entity: Catalog Entry

A bundle's listing within a catalog source (shared shape with other primitive catalogs).

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| id, name, version, role, description, author, license | as Bundle | yes | Discovery/governance metadata (FR-027) |
| download_url | URL | yes | Points at the hosted artifact |
| repository | URL | no | Provenance |
| requires.speckit_version | version constraint | yes | Pre-install compatibility check |
| provides | summary counts | yes | e.g. `{extensions, presets, steps, workflows, integration}` |
| tags | string[] | no | Discovery |
| verified | boolean | yes | Trust indicator (org vs community) |

**Behavior**: `info` exposes each entry's **source catalog** and **install policy** in addition to the above (FR-027).

## Entity: Role

Open-ended metadata identifying the organizational role a bundle targets (e.g. product manager, business analyst, security researcher, developer, platform engineer, QA/release manager). Not a fixed/closed set (FR-031). Used purely for discovery/curation.

## Entity: Project (target)

The Spec Kit project receiving bundles.

| Field | Type | Notes |
|-------|------|-------|
| active_integration | string | Single active integration; the cross-bundle conflict point (FR-019) |
| installed_bundles | InstalledBundleRecord[] | Stacked bundles installed in this project |
| catalog_config | Catalog Source[] | Project-scoped catalog stack overrides |

## Entity: Installed Bundle Record

Tracks an installed bundle so `list`/`remove`/`update` are precise and non-destructive (R10, FR-021..FR-023, SC-004).

| Field | Type | Notes |
|-------|------|-------|
| bundle_id | string | Installed bundle |
| version | semver string | Installed version |
| contributed_components | Component ref[] | Exactly what this bundle added, for safe removal |
| installed_at | timestamp | Provenance |

**Removal rule**: removing a bundle uninstalls only components it contributed that are **not** still required by another installed bundle or installed independently (FR-022, SC-004 zero collateral removals).

## State Transitions

**Bundle (authoring)**: `draft manifest` → `validated` (passes `specify bundle validate`) → `built` (artifact produced) → `published` (hosted + catalog entry added, out-of-band).

**Bundle (in a project)**: `discoverable` (in catalog) → `inspected` (`info` shows expanded set) → `installed` (components added via primitive machinery) → `updated` (components refreshed, overrides preserved) → `removed` (contributed components uninstalled, others untouched).

**Integration conflict guard**: an `installed`/`install` transition that would require a different active integration than the project's current one **halts** with a clear error (no silent state change).
