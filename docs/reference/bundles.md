# Bundles

Bundles compose existing Spec Kit components — extensions, presets, workflows, and steps — into a single, versioned, installable unit. Where extensions and presets are primitives, a bundle is a curated stack that declares everything a team or role needs and installs it in one step through each component's own machinery. Bundles add no new runtime behavior of their own: they are a distribution and composition layer over the primitives you already use.

A bundle is described by a `bundle.yml` manifest and is discovered through the same catalog stack as other components. Installing a bundle resolves its declared components against pinned versions, checks active-integration and shared-component-version conflicts, and applies each component idempotently with full provenance tracking so it can be cleanly removed or refreshed later.

For a concrete starting point, see the
[example bundle manifests](https://github.com/github/spec-kit/tree/main/examples/bundles)
for product managers, business analysts, security researchers, and developers.
These demonstrate packaging a role-based setup, not filled generated feature
specs; for end-to-end usage examples, see
[community walkthroughs](../community/walkthroughs.md).

## First-party Bundles

Spec Kit ships a first-party bundle catalog in `bundles/catalog.json`. These bundles are curated, marked `verified: true`, and resolve through the built-in `builtin://default` catalog source.

| Bundle    | Role        | Components                                            | Use case                                |
| --------- | ----------- | ----------------------------------------------------- | --------------------------------------- |
| `bugfix`  | `developer` | `bug` extension + `bugfix` workflow                   | Guided assess → gate → fix → test       |
| `assess`  | `developer` | `assess` extension + `assess` workflow                | Idea triage before Spec-Driven Development |

Install a first-party bundle the same way you install any bundle (`add` is an alias for `install`):

```bash
specify bundle install bugfix
specify bundle add assess
```

The first-party catalog is fetched from the repository online and falls back to the packaged wheel snapshot offline so discovery works without network access. A local bundle manifest can install bundled extensions and workflows with `--offline`. Catalog-discovered bundle manifests still resolve from their `download_url`, so `specify bundle add <id>` requires network today; fully offline catalog installation is tracked as follow-up work.

## Search Available Bundles

```bash
specify bundle search [query]
```

| Option      | Description                  |
| ----------- | ---------------------------- |
| `--offline` | Do not access the network    |
| `--json`    | Emit machine-readable JSON   |

Searches all active catalogs for bundles matching the query. Without a query, lists every available bundle with its version, role, source, and a trust indicator (`verified` for org-curated catalog entries, `community` otherwise) so you can judge trust before installing.

## Bundle Info

```bash
specify bundle info <bundle_id>
```

| Option       | Description                       |
| ------------ | --------------------------------- |
| `--offline`  | Do not access the network         |
| `--json`     | Emit machine-readable JSON        |

Shows full metadata for a bundle along with the **fully expanded component set** it installs — every extension, preset, step, and workflow with its pinned version, plus preset priority and strategy. The output also includes a trust indicator (`verified` vs `community`) so you can judge trust before installing. This preview is the same plan `install` applies, so you can see exactly what will be added before committing. Foreseeable overlaps and version conflicts with components already required by installed bundles are surfaced here as well; a bundle can require a component without having installed it.

## Install a Bundle

```bash
specify bundle install <bundle_id | path>
```

| Option           | Description                                                         |
| ---------------- | ------------------------------------------------------------------ |
| `--integration`  | Override the integration used when initializing/installing         |
| `--offline`      | Do not access the network                                          |
| `--refresh`      | Refresh owned components from the supplied bundle source           |

Installs a bundle's full component set through each primitive's machinery. The argument may be a catalog bundle id, or a local path to a built `.zip` artifact, a bundle directory, or a `bundle.yml` file; local sources install directly without consulting the catalog stack.

If the current directory is not yet a Spec Kit project, `install` initializes one first so a fresh checkout reaches a working state in a single command. `--integration` selects the integration when initializing a new project, and confirms the target when a bundle pins a specific integration but the project's active integration can't be determined (missing or unreadable `.specify/integration.json`). It does **not** override an already-initialized project's active integration: if a bundle targets a different integration than the project's, install aborts with no changes. Integration-agnostic bundles inherit the project's active integration. Without `--refresh`, installation is idempotent — already-installed components matching their pins are skipped. A missing or different installed version cannot satisfy a pin. Only `--refresh` can repair a drifted version owned exclusively by this bundle; independently installed components are skipped and never adopted or replaced. On failure, no provenance record is written (a failed install records nothing), and the components installed during that run are removed on a best-effort basis — removal errors are swallowed, so partial on-disk state may remain.

Installed-bundle records store required component pins separately from contributed components. A compatible independently installed component satisfies a bundle's requirement but remains independently owned: its pin still blocks a later bundle from installing an incompatible version, while removing the bundle does not uninstall it. An unpinned install or refresh cannot replace a component another bundle requires at a pinned version; sharing an already installed matching version without refreshing remains allowed. Shared bundles must also agree on component source and, for presets, priority and strategy before installing or refreshing the shared component. Older records without the requirement list retain their known contributed pins; reinstall or refresh the bundle to record its full requirements.

A normal install rejects a change to an already-recorded bundle's version or owned component metadata (version, source, preset priority, or strategy), including removal of an owned component. This applies even if a local manifest keeps the same bundle version. Reordering unchanged components or adding new components does not require refresh. To apply changes to a local bundle without adding it to a catalog, pass the revised source with `--refresh`:

```bash
specify bundle install ./new-release/bundle.yml --refresh
```

The source may also be a bundle directory or `.zip` artifact. Refresh uses the same primitive update path as `bundle update`, re-applies components owned by a bundle, and removes previously owned components omitted from the new manifest unless another bundle still needs them. Components installed independently remain untouched and are not adopted. The success summary includes refreshed and removed counts. The bundle record advances only after the operation succeeds; as with `bundle update`, already-installed components modified during a failed refresh are not rolled back.

A local bundle source supplies the manifest, not its component payloads. Components resolved through catalogs still require network access to refresh, even when already installed. Add `--offline` only when the components being installed or refreshed ship with Spec Kit; otherwise the command reports which component needs network access. Re-run without `--offline` to fetch that component through its catalog.

> **Step payloads resolve through the step catalog only.** A bundle's `provides.steps` entries still resolve exclusively through the active step catalogs. Bundle-local `steps/<id>/` payloads and relative `provides.steps[].source` overrides are **not** resolved in this release, so a step declared that way cannot be installed offline. To ship a step with a bundle today, publish it to a step catalog the bundle's users can reach.

## Update Bundles

```bash
specify bundle update [<bundle_id>]
```

| Option           | Description                                                                                                            |
| ---------------- | --------------------------------------------------------------------------------------------------------------------- |
| `--all`          | Update every installed bundle                                                                                         |
| `--integration`  | Override the integration used when refreshing components; applied only when the project's active integration can't be determined |
| `--offline`      | Do not access the network                                                                                             |

Re-resolves a bundle and **refreshes** its components through each primitive's update path, bringing already-installed components up to the bundle's newly pinned versions while preserving primitive-level overrides (such as preset priority). Provide a bundle id, or use `--all` to update everything installed.

**Pinned catalog releases.** Extensions, presets, workflows, and steps with version pins select that exact release from the highest-priority active catalog entry. Historical releases must be advertised under `releases` with their own artifact URL and SHA-256 digest; the bundler never guesses an old URL from the current one or falls through to another catalog. The primitive installer uses the selected workflow or step record without re-reading the catalog, and verifies downloaded archive or workflow/step metadata against that release. A pinned workflow that ships with Spec Kit uses its bundled copy when the version matches, and the catalog release when it differs and network access is allowed. A step without a pin installs the current catalog release.

Without an explicit `source`, bundled extensions and presets take precedence over catalog releases. Validation rejects a pin that differs from the bundled version even when a matching catalog release exists; specify the winning catalog as `source` to opt into its release.

> **One installed version per component ID.** Bundles sharing a component must agree on its pinned version. A different or unknown pin from another bundle is rejected before installation, including during `bundle update`; refreshing one bundle cannot replace a version required by another.

A bundle may list a component ID only once per kind; duplicate references in the same manifest are invalid, even if their pins agree.

An optional `source` in a `provides.<kind>` reference names the expected winning component catalog (as displayed by `specify <kind> catalog list`, or `specify workflow step catalog list` for steps). It is **not** an artifact URL and does not override catalog priority or install policy. When specified, the component is verified against that catalog even if already installed, rather than resolved from a Spec Kit-bundled copy; a different winning catalog or a discovery-only source prevents installation. Verifying an explicit source requires network access. Direct primitive `--from` URLs are a separate, explicitly requested route.

## Remove a Bundle

```bash
specify bundle remove <bundle_id>
```

Uninstalls only the components this bundle contributed, leaving any component that another installed bundle still needs in place (no collateral removals).

## List Installed Bundles

```bash
specify bundle list
```

| Option   | Description                  |
| -------- | ---------------------------- |
| `--json` | Emit machine-readable JSON   |

Lists the bundles installed in the project with their versions, component counts, and install timestamps.

## Initialize a Project with a Bundle

```bash
specify bundle init [<bundle_id>]
```

| Option           | Description                              |
| ---------------- | ---------------------------------------- |
| `--integration`  | Integration override                     |
| `--offline`      | Do not access the network                |

Ensures the current directory is a Spec Kit project (initializing it idempotently if needed), then optionally installs the given bundle. Useful as an explicit one-step bootstrap for a new checkout.

## Validate a Bundle

```bash
specify bundle validate
```

| Option       | Description                                                          |
| ------------ | ------------------------------------------------------------------- |
| `--path`     | Bundle directory or `bundle.yml` (default: current directory)       |
| `--offline`  | Verify references against bundled/installed components only          |

Reports whether a `bundle.yml` is well-formed and whether every declared component reference resolves at its pinned version. References are checked against matching bundled or installed components and — when online — the exact release in the winning install-allowed catalog. An explicit `source` is verified against the winning catalog instead of resolving locally. Missing releases, mismatched sources, discovery-only sources, and malformed catalog metadata fail validation; references that cannot be checked offline or because a catalog is unreachable produce warnings. A reference is not reported missing when a readable catalog lacks it but another configured catalog is unreachable; the lookup remains unverified.

## Build a Bundle Artifact

```bash
specify bundle build
```

| Option      | Description                                              |
| ----------- | ------------------------------------------------------- |
| `--path`    | Bundle directory (default: current directory)           |
| `--output`  | Output directory for the artifact                       |

Produces a single versioned, distributable `.zip` artifact from a bundle directory. The artifact embeds the manifest and can be installed directly with `specify bundle install <artifact.zip>`.

## Publish a Bundle

Bundle authors validate and package bundles locally, then host the generated artifact and catalog metadata where users can access it. A bundle catalog entry points at the bundle artifact, but the components declared inside `bundle.yml` still resolve through bundled components, installed components, or active extension, preset, workflow, and step catalogs.

If your bundle references components from non-default catalogs, document those catalog URLs and test the install path from a clean project with those catalogs added. Community bundle submissions should include that dependency-resolution evidence in the [Bundle Submission](https://github.com/github/spec-kit/issues/new?template=bundle_submission.yml) issue.

### What Happens After You Submit

1. GitHub applies the `triage-must-have` verdict when the issue is opened through the Bundle Submission form. Bundle submissions join extension and preset submissions in using this intake automation; the manual triage rubric for other issues remains unchanged.
2. A maintainer reviews the issue during issue triage and applies the separate `bundle-submission` label, which starts the automated catalog validation. On this public repository, contributors cannot apply that label themselves, so there is nothing to label or re-request — the issue simply waits in triage.
3. The automated workflow validates the submission and, when validation passes, updates `bundles/catalog.community.json` and `docs/community/bundles.md` in a draft pull request
4. A maintainer reviews the generated pull request and merges it when approved
5. Your bundle becomes discoverable via `specify bundle search`

## Manage Catalog Sources

Bundles are discovered through a priority-ordered stack of catalog sources (project, user, and built-in scopes). The built-in sources are:

- `builtin://default` — first-party bundles shipped in `bundles/catalog.json` (`bugfix`, `assess`, ...), install-allowed.
- `builtin://community` — community submissions in `bundles/catalog.community.json`, discovery-only.

Each source has an install policy. `install-allowed` sources can be installed
from; `discovery-only` sources appear in `search` and `info` but refuse
installation. Inspect the active stack before installing a bundle from a
non-default source.

> **Vet both the bundle source and its component catalogs.** A project can supply its own bundle catalog and `install-allowed` component catalogs (extension, preset, workflow, and step) under `.specify/`; that project configuration existing is not evidence anything in it was reviewed. Before installing a bundle from an unfamiliar project, run `specify bundle catalog list` — and the equivalent `extension`/`preset`/`workflow catalog list` and `specify workflow step catalog list` commands for the components it pulls in — and treat any source you didn't add yourself as unvetted until you've reviewed it.

### List the Catalog Stack

```bash
specify bundle catalog list
```

Prints the active, priority-ordered catalog stack with each source's scope and install policy.

### Add a Catalog Source

```bash
specify bundle catalog add <url>
```

| Option        | Description                                              |
| ------------- | ------------------------------------------------------- |
| `--policy`    | `install-allowed` or `discovery-only`                   |
| `--priority`  | Source priority (lower = higher precedence; default 10) |
| `--id`        | Explicit source id                                      |

Registers a project-scoped catalog source and persists it.

Re-adding the same source with the same ID, URL, policy, and priority succeeds without changing the configuration; different settings are rejected.

### Remove a Catalog Source

```bash
specify bundle catalog remove <id_or_url>
```

Removes a project-scoped catalog source. Built-in default sources cannot be deleted.

> **Note:** `search` and `info` work anywhere — with no project they fall back to the built-in/user catalog stack. The remaining state-changing commands (`list`, `update`, `remove`, `catalog`) require a project already initialized with `specify init`. `install` and `init` will initialize a project on demand when run in an uninitialized directory.
