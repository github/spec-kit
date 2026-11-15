# Extension CLI Reference

Complete reference for managing extensions with `specify extension`.
All extension commands require a project already initialized with `specify init`.

## Search Available Extensions

```bash
specify extension search [query]
```

| Option       | Description                          |
| ------------ | ------------------------------------ |
| `--tag`      | Filter by tag                        |
| `--author`   | Filter by author                     |
| `--verified` | Show only verified extensions        |

Searches all active catalogs for extensions matching the query. Without a query, lists all available extensions.

## Install an Extension

```bash
specify extension add <name>
specify extension add --from <url>
specify extension add --dev <path>
```

| Option          | Description                                              |
| --------------- | -------------------------------------------------------- |
| `--dev`         | Install from a local directory (for development)         |
| `--from <url>`  | Install from a custom URL instead of the catalog         |
| `--version <v>` | Install an exact version advertised by a catalog        |
| `--force`       | Overwrite if the extension is already installed          |
| `--priority <N>`| Resolution priority (default: 10; lower = higher precedence) |

Installs an extension from the catalog, a URL, or a local directory. Extension commands are registered with the active AI coding agent integration. For `generic`, invocations use the configured `--commands-dir`: flat command files by default, or `speckit-<name>/SKILL.md` with `--skills`.

The positional name is required for catalog installs, and `--dev` requires a
local path. With `--from`, the positional name can be omitted; the downloaded
manifest supplies the installed extension ID.

If a generic integration refresh cannot produce every extension invocation (for example, because a command or skill is user-modified or its source is missing), it warns and restores that extension's prior registered artifacts. Other extensions can still refresh.

An unqualified catalog install still selects the advertised current version.
`--version` uses only the winning catalog source for that extension ID; it does
not fall back to a lower-priority source when the requested version is absent.
Discovery-only catalogs remain non-installable. `--version` cannot be combined
with `--dev` or the direct-URL `--from` option. For `--version` catalog installs,
the downloaded archive's extension ID and version are compared with the
requested catalog ID and version before installation. Unqualified catalog
installs and direct `--from` installs validate the manifest but do not compare
its ID or version with expected catalog values.

## Remove an Extension

```bash
specify extension remove <name>
```

| Option          | Description                                    |
| --------------- | ---------------------------------------------- |
| `--keep-config` | Preserve configuration files during removal    |
| `--force`       | Skip confirmation prompt                       |

Removes an installed extension. Configuration files are backed up by default; use `--keep-config` to leave them in place or `--force` to skip the confirmation.

## List Installed Extensions

```bash
specify extension list
specify extension list --json
```

| Option        | Description                                        |
| ------------- | -------------------------------------------------- |
| `--available` | Show installed extensions and an installation hint; does not query catalogs |
| `--all`       | Same current behavior as `--available`              |
| `--json`      | Write installed extensions as JSON                 |

Lists installed extensions with their status, version, and command counts.

Although help describes `--available` and `--all` as including catalog entries,
the current handler does not fetch or list uninstalled extensions. Use
`specify extension search` to discover available extensions.

`--json` writes a JSON array to stdout. Every item has the keys `id`, `name`,
`description`, `version`, `author`, `priority`, `enabled`, `source`, and
`provides`. `author` is `null` when absent; `source` is `{"kind":"local"}`
for local, legacy, or malformed provenance, or
`{"kind":"catalog","catalog":"<catalog-name>"}` for a valid catalog source.
Extension `provides` contains `commands`, `templates`, `scripts`, and `hooks`
counts. `--available` and `--all` do not broaden JSON output beyond installed
extensions. On success, `--json` writes exactly one array to stdout and exits
0. A runtime failure after option parsing writes exactly one
`{"error":"..."}` object to stderr and exits 1. If parsing raises a usage
error and the raw `--json` token is present, it writes that JSON error object
to stderr and preserves the usage exit code (normally 2). Without `--json`,
including for help, the existing human-readable behavior is unchanged.

## Extension Info

```bash
specify extension info <name>
specify extension info <name> --versions
specify extension info <name> --json
```

Shows detailed information about an installed or available extension, including its description, version, commands, and configuration.
`--versions` lists the current and historical versions advertised by the
winning catalog source; it labels discovery-only sources as non-installable.
Equivalent PEP 440 version spellings (for example, `v1.0` and `1.0`) select
the same release; the catalog's advertised spelling remains visible.

See [Historical releases](catalogs.md#historical-releases) for the catalog
format used to advertise older versions and bundle-pin behavior.

`--json` describes one installed extension and writes a single JSON object to
stdout. `<name>` is matched as without `--json`: the extension ID first, then a
unique display name, ignoring case. The object has the same `id`, `name`,
`description`, `version`, `author`, `priority`, `enabled`, and `source` keys as
the matching `specify extension list --json` item. In place of the `provides`
counts it has `commands`, `templates`, `scripts`, and `hooks` arrays. Command,
template, and script entries have `name`, `description` (`""` when absent),
`source` (`{"layer": "extension", "extensionId": "<id>"}`, the extension that
provides it; the top-level `source` is where it was installed from), and
`sourcePath` (the manifest `file`,
relative to the extension directory); script entries also have `runtimes` when
the manifest declares them. Extension entries carry no `strategy`, because
extension-provided files always replace. Each hook entry has `trigger` (the
hook event, such as `after_tasks`), `targetCommand`, `optional` (default
`true`), and `priority` (default `10`). When an event declares the same command
more than once, the last declaration wins, as it does when hooks are
registered. `--json` cannot be combined with `--versions` (usage error, exit 2).
An extension that is not installed, an ambiguous name, or a missing project
writes one `{"error":"..."}` object to stderr and exits 1; usage errors keep
their exit code (normally 2), as with `list --json`.

## Update Extensions

```bash
specify extension update [<name>]
```

Updates a specific extension, or all installed extensions if no name is given.

Bundled extensions (such as `agent-context` and `git`) have no download URL; their updates install from the copy shipped with the running spec-kit release. When the catalog advertises a newer version than your spec-kit release ships, the update is reported as requiring a spec-kit upgrade first.

For `generic`, a failed update restores hash-owned invocations from previously configured `--commands-dir` locations as well as the current location, even if another integration is now active.

## Enable / Disable an Extension

```bash
specify extension enable <name>
specify extension disable <name>
```

Disable an extension without removing it. Disabled extensions are excluded from
registry-driven artifact resolution and future integration registration, and
their declarative hooks are marked disabled in `.specify/extensions.yml`.
Native runtime-event configuration is refreshed on a best-effort basis after
these state changes. If a refresh fails, the command warns, but a stale native
hook may remain active and still execute. Retry the affected integration's
refresh with `specify integration upgrade <key>`.

Non-generic integrations can retain generated command or skill files that
remain invocable until an integration
switch, uninstall, or reconciliation removes them. Disabling is not a universal
execution block. Hook-only extensions can be installed, enabled, and disabled
even if generic command-output settings are missing or invalid; extensions with
commands still require valid settings. Re-enable with `enable`.

For `generic`, disabling removes hash-owned invocations even after the output directory moves, but preserves unrelated same-named files in the new directory.

## Set Extension Priority

```bash
specify extension set-priority <name> <priority>
```

Changes the artifact resolution priority of an extension. Lower numbers take
precedence for contributed artifacts such as templates and scripts; ties are
ordered by extension ID. Installation rejects exact command-name or alias
collisions with installed extensions, and normalized output-name collisions with
core commands. Priority does not permit duplicate command names to be installed.

## Catalog Management

Extension catalogs control where `search` and `add` look for extensions. Catalogs are checked in priority order (lower number = higher precedence).

Discovery-only catalogs can be searched but cannot be installed from. Only
enable installation for a source you own and vet. See the
[catalog trust model](catalogs.md#trust-model-discovery-only-vs-install-sources)
before installing third-party extensions.

### List Catalogs

```bash
specify extension catalog list
```

Shows all active catalogs in the stack with their priorities and install permissions.

### Add a Catalog

```bash
specify extension catalog add <url>
```

| Option                               | Description                                        |
| ------------------------------------ | -------------------------------------------------- |
| `--name <name>`                      | Required. Unique name for the catalog              |
| `--priority <N>`                     | Priority (default: 10; lower = higher precedence)  |
| `--install-allowed / --no-install-allowed` | Mark the catalog as a trusted install source. Only enable for a catalog you own and vet; leave off (the default) for discovery-only sources. Never enable it for an unvetted public catalog. |
| `--description <text>`               | Optional description                               |

Adds a catalog to the project's `.specify/extension-catalogs.yml`.

Re-adding the same named catalog with identical settings succeeds without changing the configuration; different settings are rejected.

### Remove a Catalog

```bash
specify extension catalog remove <name>
```

Removes a catalog from the project configuration.

## See also

- [Extension user guide](overview.md)
- [Extension catalogs](catalogs.md)
- [Extension API reference](api.md)
- [Developing extensions](developing.md)
- [Publishing extensions](publishing.md)
- [Community extensions](../community/extensions.md)
