# Bundle CLI reference

The `specify bundle` command group discovers, installs, and authors bundles.
Use `specify bundle <command> --help` for command help. Bundle catalog commands
have their own nested help: `specify bundle catalog --help`.

## Project requirements

| Commands | Project requirement |
| --- | --- |
| `search`, `info` | Work without an initialized project; use user and built-in catalogs, plus any applicable project-scoped configuration |
| `install`, `add`, `init` | Initialize a project on demand |
| `list`, `update`, `remove`, `catalog list/add/remove` | Require an initialized project |
| `validate`, `build` | Work on a local bundle source without initializing a project |

`search`, `info`, and `list` support `--json`; other bundle commands do not.
Successful JSON output shapes are described with each command below. Do not
assume all bundle failures emit a JSON envelope: ordinary bundler errors are
reported as errors with a nonzero exit status.

## Search available bundles

```bash
specify bundle search [query]
```

| Option | Description |
| --- | --- |
| `--offline` | Do not access the network |
| `--json` | Emit JSON to stdout |

Searches all active catalogs. The optional query matches substrings in the
winning entry's ID, name, role, tags, or description. Without a query, lists
every available bundle. Each ID appears once, from its highest-precedence
source, and results are sorted by ID.

Text output shows version, role, source, and trust. JSON is an array of entries
with `id`, `name`, `version`, `role`, `description`, `source`, `install_policy`,
`verified`, and `trust`. Trust is `verified` for entries marked verified and
`community` otherwise; it does not change installation policy.

## Inspect a bundle

```bash
specify bundle info <bundle_id>
specify bundle info <bundle_id> --versions
```

| Option | Description |
| --- | --- |
| `--offline` | Do not access the network |
| `--json` | Emit JSON to stdout |
| `--versions` | List current and historical catalog versions without downloading a manifest |

Without `--versions`, downloads the current manifest and shows the fully
expanded component set, including versions, preset priority and strategy,
integration, source policy, trust, and informational overlaps with installed
bundles. A required component may already be installed; this preview is not a
promise that every component will be newly added or that all installation
gates have passed. Local bundle paths are not supported by `info`.

JSON includes `id`, `name`, `version`, `role`, `description`, `author`,
`license`, `source`, `install_policy`, `provides`, `requires`, `verified`,
`trust`, `integration`, `components`, and `overlaps`. Component entries contain
`kind`, `id`, `version`, and any declared `priority` or `strategy`.

For bundles with references, JSON also includes:

- `references`: each referenced bundle's `id`, `version`, resolved `source`,
  `install_policy`, `via`, `verified`, and `trust`.
- Component `source`, when declared; flat bundles omit this field.
- Component `origin`, when contributed by a referenced bundle, using the
  shortest origin chain.
- Component `overrides`, when replacing declarations. Each item contains the
  replaced `version`, `origin`, and any `source`, `priority`, or `strategy`.
  Every distinct declaring bundle is represented, using its shortest route.
  An overridden parent declaration has an empty origin.

Text output includes a References summary, origin chains, overrides, and
discovery-only notices. Referenced bundles retain their own trust level; they
do not inherit the parent's.

`--versions --json` instead emits an object with `id`, `versions`, `current`,
`source`, and `install_policy`. Versions list the current release first,
followed by historical releases newest first.

If a manifest cannot be downloaded or expanded, `info` fails rather than
substituting catalog component counts for a verified expansion.

## Install a bundle

```bash
specify bundle install <bundle_id-or-path>
specify bundle add <bundle_id-or-path>
```

`add` accepts the same arguments and options as `install`.

| Option | Description |
| --- | --- |
| `--integration <id>` | Select an integration for initialization, or confirm one when the active integration cannot be determined |
| `--offline` | Do not access the network |
| `--refresh` | Reapply owned components from the supplied source |
| `--version <version>` | Select an exact current or historical catalog release |

The argument can be a catalog ID, local bundle directory, manifest file, or
built ZIP with `bundle.yml` at its root. Local sources bypass the bundle catalog
unless they declare bundle references, which resolve through the catalog stack.
An archive URL is not a direct install argument: download it, vet it, and pass
its local path, or use an install-allowed catalog.

### Initialization and integration

If no project exists, installation first resolves the manifest and hard
compatibility gates, then initializes the project. Integration selection uses
the explicit option, the bundle's declared integration, then the CLI's default.

In an existing project, the recorded active integration is authoritative.
`--integration` does not switch it or bypass a bundle integration mismatch.
When a pinned bundle's active project integration cannot be determined because
`.specify/integration.json` is missing or unreadable, confirm the target with
`--integration` or repair the project.

Integration-agnostic bundles inherit the active integration. The root bundle
is the integration gate; differing or indeterminate integration targets in
referenced bundles generate warnings.

### Reinstallation and refresh

An ordinary install skips compatible installed components and preserves their
local edits. A different or unknown installed version cannot satisfy a pin,
except for the packaged patch rule below. Independently installed components
are never adopted or replaced.

An ordinary reinstall rejects changes to the recorded bundle version or owned
component metadata, including removing an owned component, even if a local
manifest keeps the same bundle version. Reordering unchanged components or
adding components does not require refresh.

To apply a revised local source:

```bash
specify bundle install ./new-release/bundle.yml --refresh
```

Refresh reapplies bundle-owned components through their primitive update paths,
preserving primitive-level overrides such as preset priority. It can repair
version drift owned exclusively by this bundle. It removes omitted owned
components unless another bundle still needs them, leaves independently
installed components untouched, and reports refreshed and removed counts.

All bundles requiring a shared component must agree on its pin, source, and
relevant settings. An unpinned refresh cannot replace a version another bundle
requires at a pin; sharing a matching installed version without refreshing is
still allowed. See the API reference for requirement comparison rules.

The bundle record advances only after successful installation. On component
failure, newly installed components are removed on a best-effort basis.
Rollback removal errors are swallowed, so partial disk state may remain.
Previously installed components modified or removed during refresh are not
restored. Initialization is not rolled back either.

### Packaged patch compatibility

For extensions, presets, and workflows shipped with Spec Kit, a newer stable
patch within the pinned major/minor version is accepted with a warning when
no component `source` is declared. For example, packaged `bug` version `1.0.1`
can satisfy a bundle's `1.0.0` pin. Validation uses the same warning.

Downgrades, major/minor differences, and differing prerelease versions are not
covered by this exception. Explicit sources and catalog-resolved releases
retain exact-pin enforcement. A patch release is not a guarantee of unchanged
behavior.

Requested pins remain in `required_components` and `contributed_components`.
Known actual versions are recorded separately under `installed_versions` and
shown by `bundle list --json`.

### Exact catalog releases

`--version` selects a bundle release advertised by the winning catalog. It
does not override component pins inside that release. It cannot be blank,
used with a local source, or combined with `--refresh`.

```bash
specify bundle install team-setup --version 1.1.0
```

A missing version does not fall through to a lower-priority source.
Discovery-only sources remain non-installable, including historical releases.
See the catalog reference for release history requirements.

### Offline limits

A local manifest, directory, or ZIP can install packaged components with
`--offline`. Local bundle assets are not a source of component payloads.
Components resolved through catalogs need network access for installation or
refresh, even when already installed and being refreshed.

Catalog bundle manifests and referenced bundle manifests require network
downloads. A local root can identify the first unresolved bundle reference in
an offline error; a catalog root can fail earlier while fetching its catalog
or root manifest. Packaged catalog snapshots enable discovery, not offline
catalog-ID installation.

Step payloads resolve exclusively through step catalogs. Bundle-local
`steps/<id>/` directories and relative step `source` values are not resolved
as payloads, so bundling a step directory does not make it installable offline.

## Update bundles

```bash
specify bundle update <bundle_id>
specify bundle update --all
```

| Option | Description |
| --- | --- |
| `--all` | Update every installed bundle |
| `--integration <id>` | Confirm an integration only when the project's active integration cannot be determined |
| `--offline` | Do not access the network |

Requires an installed bundle and an install-allowed source. Re-resolves the
parent's current catalog release and its pinned bundle references, then
refreshes owned components using the same lifecycle and patch-compatibility
rules as `install --refresh`. `update` does not retain a historical
`install --version` selection.

Each component pin selects the exact release from its winning catalog; the
bundler does not guess an old download URL or try a lower-priority catalog.
Legacy extension and preset entries advertising no version cannot enforce
their pins or verify the archive's version. Publish versioned entries to make
those pins enforceable. An unpinned step selects the current catalog release.

Without an explicit `source`, bundled extensions and presets take precedence
over catalog releases. An incompatible bundled pin is rejected even if a
matching catalog release exists. A bundled workflow uses the packaged version
when compatible, or its catalog release when appropriate and online.

`--all` processes bundles sequentially and stops on failure; earlier successful
updates are not rolled back.

## Remove a bundle

```bash
specify bundle remove <bundle_id>
```

Uninstalls only contributed components that no other bundle still needs.
Retained components without a remaining owner transfer to a remaining requiring
bundle so later removal can clean them up. Independently installed components
are never adopted.

Removal is not transactional. A component failure can leave a partially
uninstalled project while the bundle record remains unchanged; the command
reports the failure and recovery context.

## List installed bundles

```bash
specify bundle list
```

| Option | Description |
| --- | --- |
| `--json` | Emit JSON to stdout |

Shows installed bundle IDs, versions, required component counts, and original
installation timestamps. Counts include components supplied independently.
JSON is an array of installed records using the API reference's record shape,
including optional `installed_versions` and `bundle_references`.

## Initialize a project with a bundle

```bash
specify bundle init [bundle_id]
```

| Option | Description |
| --- | --- |
| `--integration <id>` | Integration override for initialization |
| `--offline` | Do not access the network |

Ensures a project exists, then optionally installs a bundle. Repeating an
unchanged installation skips existing components and preserves edits. It
follows ordinary install rules, not refresh rules: use `update` or
`install <path> --refresh` for recorded version or owned-component changes.

## Validate a bundle

```bash
specify bundle validate --path ./team-setup
```

| Option | Description |
| --- | --- |
| `--path <path>` | Bundle directory or manifest; defaults to the current directory |
| `--offline` | Check against packaged/installed components without network access |

Checks manifest structure and component resolution. Online validation expands
bundle references and checks cycles, versions, sources, conflicts, and install
policies across the expanded plan. Explicit component sources are checked
against the winning catalog instead of local components.

Missing releases, mismatched or ambiguous sources, discovery-only sources,
and malformed catalog metadata fail validation. Unverifiable component
references, including unreachable catalogs, produce warnings; an unreachable
higher-priority catalog cannot be settled by a lower-priority match.
Bundle-reference fetch failures fail online validation.

Offline validation warns once per declared bundle reference that it was not
expanded. A successful result with warnings is not proof of an installable
full graph. Validation does not check the running CLI against
`requires.speckit_version`; install/update enforce that gate.

## Build a bundle artifact

```bash
specify bundle build --path ./team-setup --output ./dist
```

| Option | Description |
| --- | --- |
| `--path <directory>` | Bundle directory; defaults to the current directory |
| `--output <directory>` | Artifact destination; defaults to the bundle directory |

Produces `<id>-<version>.zip` with the manifest, README, and local assets.
Requires regular, non-symlinked `bundle.yml` and `README.md` files and a
structurally valid manifest. Build does not resolve components or download
referenced bundles; it is not a substitute for online validation.

## Manage catalog sources

```bash
specify bundle catalog list
specify bundle catalog add <url>
specify bundle catalog remove <id-or-url>
```

`list` prints the active stack with IDs, URLs, priorities, scopes, and policies.
`add` and `remove` write project-scoped configuration.

| `catalog add` option | Description |
| --- | --- |
| `--policy <policy>` | `install-allowed` (default) or `discovery-only` |
| `--priority <integer>` | Lower numbers have higher precedence; defaults to `10` |
| `--id <id>` | Explicit source ID; otherwise derived from the URL or path |

Re-adding the same source with matching settings is a no-op; conflicting
settings fail. Built-in sources cannot be deleted. Removing a project override
of a built-in ID restores the lower-scope source.

## See also

- [Bundle overview](overview.md)
- [Manifest, expansion, and record contracts](api.md)
- [Catalog configuration and release history](catalogs.md)
- [Developing bundles](developing.md)
- [Publishing bundles](publishing.md)
