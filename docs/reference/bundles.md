# Bundles

Bundles compose existing Spec Kit components — extensions, presets, workflows, and steps — into a single, versioned, installable unit. Where extensions and presets are primitives, a bundle is a curated stack that declares everything a team or role needs and installs it in one step through each component's own machinery. Bundles add no new runtime behavior of their own: they are a distribution and composition layer over the primitives you already use.

A bundle is described by a `bundle.yml` manifest and is discovered through the same catalog stack as other components. Installing a bundle resolves its declared components against pinned versions, checks for the single cross-bundle conflict point (the active integration), and applies each component idempotently with full provenance tracking so it can be cleanly removed or refreshed later.

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

Shows full metadata for a bundle along with the **fully expanded component set** it installs — every extension, preset, step, and workflow with its pinned version, plus preset priority and strategy. The output also includes a trust indicator (`verified` vs `community`) so you can judge trust before installing. This preview is the same plan `install` applies, so you can see exactly what will be added before committing. Foreseeable overlaps with components already provided by installed bundles are surfaced here as well.

## Install a Bundle

```bash
specify bundle install <bundle_id | path>
```

| Option           | Description                                                         |
| ---------------- | ------------------------------------------------------------------ |
| `--integration`  | Override the integration used when initializing/installing         |
| `--offline`      | Do not access the network                                          |

Installs a bundle's full component set through each primitive's machinery. The argument may be a catalog bundle id, or a local path to a built `.zip` artifact, a bundle directory, or a `bundle.yml` file; local sources install directly without consulting the catalog stack.

If the current directory is not yet a Spec Kit project, `install` initializes one first so a fresh checkout reaches a working state in a single command. `--integration` selects the integration when initializing a new project, and confirms the target when a bundle pins a specific integration but the project's active integration can't be determined (missing or unreadable `.specify/integration.json`). It does **not** override an already-initialized project's active integration: if a bundle targets a different integration than the project's, install aborts with no changes. Integration-agnostic bundles inherit the project's active integration. Installation is idempotent — components already present are skipped. On failure, no provenance record is written (a failed install records nothing), and the components installed during that run are removed on a best-effort basis — removal errors are swallowed, so partial on-disk state may remain.

## Update Bundles

```bash
specify bundle update [<bundle_id>]
```

| Option       | Description                          |
| ------------ | ------------------------------------ |
| `--all`      | Update every installed bundle        |
| `--offline`  | Do not access the network            |

Re-resolves a bundle and **refreshes** its components through each primitive's update path, bringing already-installed components up to the bundle's newly pinned versions while preserving primitive-level overrides (such as preset priority). Provide a bundle id, or use `--all` to update everything installed.

> **Pin enforcement is install-time only.** Idempotency checks are id-based, not version-aware: a component that is already present is skipped during `install` without comparing its on-disk version to the manifest pin. Version pins are therefore guaranteed to be applied only when the bundler actually installs a component for the first time or refreshes it. Run `specify bundle update` to re-apply every owned component at its pinned version.

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

Reports whether a `bundle.yml` is well-formed and whether every declared component reference resolves. References are checked against bundled components, the project's installed components, and — when online — the active catalogs. Validation fails only when a reference is definitively absent everywhere it could be checked: that is, when an active catalog is reachable and confirms the component is missing. References that cannot be verified — because validation is offline, or because a catalog is unreachable — are downgraded to warnings so authoring can continue, rather than failing the run.

## Build a Bundle Artifact

```bash
specify bundle build
```

| Option      | Description                                              |
| ----------- | ------------------------------------------------------- |
| `--path`    | Bundle directory (default: current directory)           |
| `--output`  | Output directory for the artifact                       |

Produces a single versioned, distributable `.zip` artifact from a bundle directory. The artifact embeds the manifest and can be installed directly with `specify bundle install <artifact.zip>`.

## Manage Catalog Sources

Bundles are discovered through a priority-ordered stack of catalog sources (project, user, and built-in scopes).

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

### Remove a Catalog Source

```bash
specify bundle catalog remove <id_or_url>
```

Removes a project-scoped catalog source. Built-in default sources cannot be deleted.

> **Note:** `search` and `info` work anywhere — with no project they fall back to the built-in/user catalog stack. The remaining state-changing commands (`list`, `update`, `remove`, `catalog`) require a project already initialized with `specify init`. `install` and `init` will initialize a project on demand when run in an uninitialized directory.
