# Feature Specification: Spec Kit Bundler

**Feature Branch**: `001-spec-kit-bundler`

**Created**: 2026-06-19

**Status**: Draft

**Input**: User description: "Spec Kit Bundler — a way to create, manage, and distribute role-oriented, one-stop-shop bundles of integrations, extensions, presets, workflow steps, and workflows for Spec Kit users, installable into a project with a single command."

## Clarifications

### Session 2026-06-19

- Q: Should the CLI provide a `specify bundle create`/scaffold authoring command, or are bundle manifests strictly hand-written? → A: Align with the sibling primitives. The existing `specify extension|preset|workflow` systems expose no authoring/scaffold command (their surface is consumer-side: list/add/remove/search/info/update/catalog); authoring is hand-written manifests published to a catalog. The bundler does the same — no `specify bundle create`; manifests are hand-written and the CLI only validates and packages them.
- Q: Dual-catalog (org + community) + single env-var override, or the sibling systems' full catalog model? → A: Adopt the sibling catalog model wholesale — a priority-ordered stack of catalog sources, each carrying install-policy metadata (install-allowed vs discovery-only), managed via a `specify bundle catalog list/add/remove` config file with a built-in default stack as fallback. This replaces the earlier dual-catalog + `BUNDLE_CATALOG_URL` framing and folds in the discovery-only concept.
- Q: How does `specify bundle update` reconcile with local user overrides on a bundle's components? → A: Update re-resolves the bundle's declared component set and refreshes each component via that primitive's normal update path, with no bundle-level merge/conflict logic. Primitive-level overrides a user applied (e.g. a set priority) are preserved because they live in the primitive's own config, not the bundle. Matches the simple sibling `update` behavior.
- Q: Should distribution/publishing be a first-class command, or out-of-band like the siblings? → A: Out-of-band. `specify bundle build` produces the versioned artifact; the author hosts it and adds a catalog entry pointing at it — mirroring the sibling primitives, which have no publish/export command. Any `publish`/`export` helper is optional and non-core, not part of the core v1 surface.
- Q: Is the role set fixed, or open-ended; which roles must v1 ship? → A: Roles are open-ended metadata (any role supported), not a fixed enum. v1 must prove the model with a representative subset (product manager, business analyst, security researcher, developer); platform engineer and QA/release manager are supported examples but not required v1 deliverables.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Consumer configures a project for their role in one step (Priority: P1)

A Spec Kit user wants their project set up the way their organization expects for their role (e.g. security researcher, developer, product manager). Instead of discovering and installing the right integration, extensions, presets, and workflows one at a time and in the right order, they install a single named bundle and immediately have a fully role-configured Spec Kit project.

**Why this priority**: This is the core value of the feature — going from zero to a fully role-configured environment with one command. Without it, the bundler has no reason to exist. It is the minimum viable slice.

**Independent Test**: Starting from an empty or freshly initialized project, install a known bundle by name and verify the project now contains the bundle's declared integration, extensions, presets (with the expected priorities), workflow steps, and workflows — with no follow-up "now also install X" steps required.

**Acceptance Scenarios**:

1. **Given** a known role bundle is available in the active catalog, **When** the user installs that bundle into a project that has not yet been initialized, **Then** the project is initialized and all of the bundle's declared components are installed in a single operation.
2. **Given** a project already initialized with the same integration the bundle expects, **When** the user installs the bundle, **Then** all declared components are added without re-initializing or disrupting existing configuration.
3. **Given** a bundle that declares no integration, **When** the user installs it into a project that already has an active integration, **Then** the existing active integration is preserved rather than replaced with a default.
4. **Given** a successful install, **When** the user inspects the project, **Then** every component the bundle promised is present at the declared version/priority.

---

### User Story 2 - Author creates, validates, and publishes a bundle (Priority: P2)

An organization maintainer curates an opinionated, role-specific setup. They hand-write a bundle manifest that pins approved components, validate that it is well-formed and that all references resolve, package it into a distributable artifact, and make it available to their teams by hosting the artifact and adding a catalog entry that points at it — the same out-of-band publishing path the sibling primitives use.

**Why this priority**: Without authoring, there are no bundles to consume. It enables the supply side, but consumption (P1) is what delivers end-user value, so authoring follows it.

**Independent Test**: Author a bundle manifest by hand, run validation against it (catching at least one deliberately broken reference), correct it, build a distributable artifact, and confirm the artifact contains everything needed to install the bundle.

**Acceptance Scenarios**:

1. **Given** a hand-written bundle manifest with a reference to a component that does not resolve, **When** the author validates the bundle, **Then** validation fails and clearly identifies the unresolved reference.
2. **Given** a valid bundle manifest, **When** the author validates the bundle, **Then** validation passes and reports the bundle as well-formed.
3. **Given** a validated bundle manifest, **When** the author builds the bundle, **Then** a single versioned distributable artifact is produced.
4. **Given** a manifest missing a required identity or metadata field, **When** the author validates the bundle, **Then** validation fails and names the missing field.

---

### User Story 3 - Consumer discovers and inspects bundles before installing (Priority: P3)

A Spec Kit user browses the bundles available to them, finds the one that matches their role, and inspects exactly what it will install before committing to it.

**Why this priority**: Discovery and transparency build trust and reduce mis-installs, but a user who already knows the bundle name can install without it. It enhances P1 rather than being required for it.

**Independent Test**: With at least one bundle in the active catalog, search for bundles and confirm the target bundle appears, then inspect it and confirm the inspection enumerates the exact integration, extensions, presets, steps, and workflows (with versions/priorities) it will install.

**Acceptance Scenarios**:

1. **Given** bundles are present in the active catalog(s), **When** the user searches, **Then** the available bundles are listed with enough metadata (name, role, version, description) to choose between them.
2. **Given** a chosen bundle, **When** the user inspects it, **Then** the full expanded set of components it will install is shown, including versions and preset priorities, before any install occurs.

---

### User Story 4 - Consumer manages bundle lifecycle and resolves conflicts (Priority: P3)

A user stacks more than one bundle in a project (e.g. a developer bundle plus a security-researcher bundle), reviews which bundles are installed, and cleanly removes a bundle they no longer need. The system protects them from the one true cross-bundle conflict: two bundles demanding different active integrations.

**Why this priority**: Lifecycle management and conflict handling make the feature safe and predictable for real org use, but they build on top of the core install flow (P1).

**Independent Test**: Install two compatible bundles into one project, list the installed bundles to confirm both are present, remove one and confirm only its components are gone, then attempt to install a bundle that demands a different integration than the active one and confirm the install fails with a clear, actionable error.

**Acceptance Scenarios**:

1. **Given** two bundles whose components do not conflict, **When** both are installed in the same project, **Then** both install successfully and their components coexist.
2. **Given** multiple installed bundles, **When** the user lists installed bundles, **Then** all installed bundles are shown.
3. **Given** an installed bundle, **When** the user removes it, **Then** the components that bundle contributed are uninstalled and components contributed by other bundles or installed independently are left intact.
4. **Given** a project with an active integration, **When** the user installs a bundle that expects a different integration, **Then** the install fails with a clear error that asks the user to choose, rather than silently switching or skipping the integration.
5. **Given** a bundle whose preset and an already-installed preset both override the same template, **When** the user inspects or installs the bundle, **Then** the overlap is surfaced as a proactive warning.
6. **Given** an installed bundle with a newer version available and a user-applied override on one of its components, **When** the user updates the bundle, **Then** its declared components are refreshed via their normal update paths and the user's primitive-level override is preserved.

---

### Edge Cases

- What happens when a bundle's required minimum Spec Kit version is newer than the installed version? The install must refuse and explain the version requirement rather than partially installing.
- What happens when an install fails partway through (e.g. one component cannot be fetched)? The user must be left with a clear report of what did and did not install; the system must not silently leave the project in an ambiguous half-configured state.
- How does the system handle installing a bundle that is already installed (same id/version)? It should be treated as a no-op or explicit re-affirmation, not a duplicate install.
- How does removal behave when two installed bundles both contributed the same component? Removing one bundle must not remove a component still required by another installed bundle.
- What happens when an author references a component version that exists in the catalog but is later removed? Validation at author time passes, but a later install must fail clearly when the reference can no longer be resolved.
- What happens when a catalog source in the active stack is unreachable or misconfigured? Discovery and install must fail with a clear message naming the offending source rather than silently returning empty results.
- What happens when a user tries to install a bundle that resolves only from a discovery-only source? The install must be refused with a clear message that the source is discovery-only, while the bundle remains visible in search/info.
- How are community-sourced bundles distinguished from org-curated ones so users understand the trust level before installing?

## Requirements *(mandatory)*

### Functional Requirements

#### Bundle definition & authoring

- **FR-001**: The system MUST allow a bundle to be defined by a hand-written manifest that declares identity and metadata (id, name, version, role, author, license, description, tags).
- **FR-002**: A bundle manifest MUST be able to declare requirements, including a minimum supported Spec Kit version.
- **FR-003**: A bundle manifest MUST be able to declare its contents: a single AI agent integration, a set of extensions, a set of presets (each with a priority and composition strategy), a set of workflow steps, and a set of workflows — each pinned to a specific version or catalog source.
- **FR-004**: A bundle manifest MUST be able to declare an integration as optional/absent (an "agnostic" bundle) so that it does not force an integration onto the project.
- **FR-005**: The system MUST provide a way to validate a bundle manifest that checks it is well-formed and that every declared component reference resolves to a real, available component.
- **FR-006**: The system MUST provide a way to build a validated bundle into a single, versioned, distributable artifact.
- **FR-007**: The system MUST NOT provide a bundle authoring scaffold/generator (no `specify bundle create`/`new` command). Bundles are authored by hand as manifests and the system only validates and packages them, mirroring the sibling `specify extension|preset|workflow` systems, none of which expose an authoring command.
- **FR-031**: The system MUST treat a bundle's role as open-ended metadata for discovery/curation, not a fixed/closed set; an organization can define a bundle for any role without requiring a change to the system.
- **FR-030**: The system MUST NOT require a first-class publish/export command. Distribution happens out-of-band — the author hosts the built artifact and adds a catalog entry pointing at it — mirroring the sibling primitives, which have no publish/export command. Any `publish`/`export` helper is optional and non-core.

#### Discovery & inspection

- **FR-008**: The system MUST allow users to discover available bundles from the active catalog(s).
- **FR-009**: The system MUST allow users to inspect a bundle and see the full expanded set of components (integration, extensions, presets, steps, workflows) with versions and preset priorities that it will install, before installing.
- **FR-010**: Bundle discovery MUST distinguish org-curated bundles from community-sourced bundles so users can judge trust level before installing.

#### Installation & configuration

- **FR-011**: The system MUST install a bundle into a project in a single user operation that results in a fully role-configured project, with no required follow-up component installs.
- **FR-012**: The install operation MUST ensure the project is initialized first, initializing it idempotently if it is not already initialized.
- **FR-013**: The system MUST resolve which integration and script type to use during init/install with the precedence: explicit user override, then the bundle's declared value, then the default (Copilot integration plus the OS-appropriate script type).
- **FR-014**: When a bundle declares no integration, the install MUST inherit the project's already-active integration rather than imposing a default.
- **FR-015**: The system MUST install each bundle component through that component's normal installation machinery (the bundle does not re-implement how integrations, extensions, presets, steps, or workflows are installed).
- **FR-016**: The system MUST refuse to install a bundle whose declared minimum Spec Kit version exceeds the installed version, and MUST explain the unmet requirement.

#### Stacking & conflict handling

- **FR-017**: The system MUST allow multiple bundles to be installed in the same project (stacking).
- **FR-018**: The system MUST treat component conflicts as resolved by each component type's native rules (preset priority/strategy stack; additive extensions/workflows/steps) and MUST NOT introduce a separate bundle-level resolution layer.
- **FR-019**: When installing a bundle that expects a different integration than the project's currently active integration, the system MUST fail with a clear error that asks the user to choose, and MUST NOT silently switch or skip the integration.
- **FR-020**: The system MUST proactively detect and warn about foreseeable component overlaps (e.g. two presets overriding the same template) by examining the fully expanded component set before installing.

#### Lifecycle

- **FR-021**: The system MUST allow users to list the bundles currently installed in a project.
- **FR-022**: The system MUST allow users to cleanly remove an installed bundle, uninstalling the components it contributed while preserving components still required by other installed bundles or installed independently.
- **FR-023**: Install, inspect, and remove operations MUST be transparent and reversible: the user can always see what a bundle will do or has done, and a removal returns the project toward its prior state.
- **FR-028**: The system MUST allow users to update an installed bundle (single bundle or all). Update MUST re-resolve the bundle's declared component set and refresh each component through that component's normal update path. The system MUST NOT apply any bundle-level merge or conflict-resolution logic during update.
- **FR-029**: Update MUST preserve primitive-level overrides a user has applied to a bundle's components (e.g. a manually set preset/extension priority), because those overrides live in the primitive's own configuration rather than in the bundle.

#### Distribution & governance

- **FR-024**: Bundles MUST be distributed through the same catalog model used by other Spec Kit primitives: a priority-ordered stack of catalog sources, each sharing a common entry shape, with a built-in default stack as the fallback when no project configuration is present.
- **FR-025**: Each catalog source in the stack MUST carry install-policy metadata distinguishing sources whose entries are installable ("install allowed") from sources whose entries are discoverable but not installable ("discovery only"); the system MUST honor that policy, allowing install only from install-allowed sources while still surfacing discovery-only entries in search/info.
- **FR-026**: The system MUST allow users to manage bundle catalog sources — list the active stack, add a source, and remove a source — persisted to a bundle-catalog configuration file, mirroring the sibling `catalog list/add/remove` workflow. Organizations control which bundles their teams can install by curating this stack.
- **FR-027**: A bundle catalog entry MUST carry enough metadata to support discovery and governance (id, name, version, role, description, author, license, requirements, a summary of what it provides, tags, and a verification indicator), and discovery/inspection MUST expose each entry's source catalog and install policy.

### Key Entities *(include if feature involves data)*

- **Bundle**: A versioned, role-oriented package that composes existing Spec Kit primitives. Carries identity/metadata, requirements, and a declared set of contents. It is a meta concept that expands to concrete component installs; it adds no resolution layer of its own.
- **Bundle Manifest**: The hand-written description of a bundle — its identity, requirements, declared integration, and the extensions/presets/steps/workflows it provides, each pinned to a version or source.
- **Bundle Artifact**: The single versioned, distributable package produced from a validated manifest, published like other primitives and referenced from a catalog entry.
- **Bundle Catalog**: A priority-ordered stack of catalog sources through which bundles are discovered, governed, and installed, sharing the entry shape of other Spec Kit primitive catalogs. A built-in default stack applies when no project configuration overrides it.
- **Catalog Source**: A single entry in the catalog stack, with a priority and install-policy metadata (install-allowed vs discovery-only) that governs whether its bundles can be installed or only discovered/inspected.
- **Role**: Open-ended metadata identifying the organizational role a bundle targets (e.g. product manager, business analyst, security researcher, developer, platform engineer, QA/release manager); the organizing principle for curation. Not a fixed/closed set — organizations may define bundles for any role.
- **Component / Primitive**: An existing Spec Kit unit a bundle installs — integration, extension, preset (with priority and composition strategy), workflow step, or workflow.
- **Project**: The target Spec Kit project that receives the bundle; holds a single active integration and the stacked set of installed bundles and their components.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can go from an unconfigured project to a fully role-configured Spec Kit project by installing a single bundle, with zero required follow-up component-install steps.
- **SC-002**: Before installing, a user can see the complete, exact list of components (with versions and priorities) a bundle will add, with 100% agreement between what inspection shows and what the install actually adds.
- **SC-003**: When a bundle's expected integration conflicts with the project's active integration, 100% of such installs stop with a clear, actionable error and never silently change the active integration.
- **SC-004**: Removing one bundle from a project where multiple bundles are stacked never removes a component still required by another installed bundle (zero collateral removals).
- **SC-005**: The role model is open-ended (any role can be expressed as a bundle), and a representative subset (product manager, business analyst, security researcher, developer) is demonstrably shippable as working, installable bundles.
- **SC-006**: An organization can restrict its teams to an approved set of bundles by curating the catalog stack (install-allowed sources) their projects use, such that only approved bundles are installable while others may remain discovery-only.
- **SC-007**: Validating a bundle with a broken or unresolved component reference fails 100% of the time and names the specific offending reference.
- **SC-008**: Time to configure a project for a role drops from a manual multi-step process to a single command, measurably reducing role-setup effort.

## Assumptions

- The feature targets organizations that already use Spec Kit and want to package opinionated, role-specific setups; individual ad-hoc users are a secondary audience.
- The role model is open-ended (any role can be expressed as a bundle); v1 proves it with a representative subset — product manager, business analyst, security researcher, and developer — with developer and security researcher as the most likely primary personas for an early release. Platform engineer and QA/release manager are supported examples, not required v1 deliverables.
- Bundles compose existing Spec Kit primitives and reuse their existing catalog, manifest, versioning, and installation conventions; the bundler orchestrates rather than re-implements those runtimes.
- The workflow-step catalog is still in flight; bundles may declare an empty set of steps until that catalog lands, and the manifest is forward-compatible with steps.
- The bundler is delivered as a `specify bundle` subcommand group within the core `specify` CLI (not a standalone CLI or separate package), reusing the same conventions; the vision documents' "standalone CLI" framing is intentionally overridden in favor of a subcommand.
- Bundles and their pinned contents are version-pinned (semver) so installs are reproducible, and bundles are installable from pinned sources or local paths without requiring network access (air-gapped/enterprise friendly).
- Re-implementing component runtimes, authoring individual extensions/presets/workflows, and hosting a public registry service are out of scope for this feature.
- Open questions that do not block this specification but will need decisions before/within implementation: where the bundle catalog lives (spec-kit repo vs. separate registry), the precise out-of-band artifact hosting channel (e.g. GitHub release vs. other), and the trust/verification model distinguishing community from org bundles.
