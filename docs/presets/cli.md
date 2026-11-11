# Preset CLI reference

All `specify preset` commands require a project initialized with `specify init`.
Run inside that project, or set `SPECIFY_INIT_DIR` to the project root.
Use `specify preset --help` or a subcommand's `--help` for usage.

## Search available presets

```bash
specify preset search [query]
```

| Option | Description |
| --- | --- |
| `--tag <tag>` | Filter by tag |
| `--author <author>` | Filter by author |

Searches the active catalogs. Without a query, lists all available presets.
Discovery-only results are visible but cannot be installed by ID.

## Install a preset

```bash
specify preset add <preset_id>
specify preset add <preset_id> --version <version>
specify preset add --dev <path>
specify preset add --from <archive-url>
```

| Option | Description |
| --- | --- |
| `--dev <path>` | Copy a local source directory |
| `--from <url>` | Download a `.zip`, `.tar.gz`, or `.tgz` archive |
| `--version <version>` | Select an exact release from the winning catalog; ID installs only |
| `--priority <N>` | Resolution priority, a positive integer; default `10`, lower wins |

Choose one source form. Without `--version`, ID installation first uses a
locally bundled preset when available, otherwise the advertised current
catalog release. Direct URL installs do not consult catalogs. An already
installed preset must be removed or updated before reinstalling; `add` has no
`--force` option.

`--version` requires a preset ID and cannot be combined with `--from` or
`--dev`. A requested release absent from the winning catalog is an error;
lower-priority catalogs cannot supply it. Discovery-only catalogs cannot
install any release. Version-specific catalog installs verify the archive's
`preset.yml` ID and version before modifying installed presets. Historical
releases require a SHA-256 digest, verified on download; legacy current
releases may omit it. A bundled release without a download URL can only be
selected when that matching ID and version are present in the installed
Spec Kit package.

The source is copied into `.specify/presets/<id>/`, respecting
[`.presetignore`](developing.md#exclude-development-files-with-presetignore).
Preset command contributions are registered for the active integration in
its selected command or skill format. The generic integration does not
register preset overrides. Required extension dependencies produce warnings
when unmet, not installation failures or automatic dependency installation.

Download URLs must use HTTPS with a hostname; HTTP is allowed only for
`localhost`, `127.0.0.1`, or `::1`. Archives must contain `preset.yml` at their
root or inside one top-level directory.

## Update a preset

```bash
specify preset update <preset_id> [--from <url>] [--dev <path>] [--priority <N>]
```

Replaces an installed preset by running the normal `remove` operation, then
the normal `add` operation. Without an explicit source, add uses its usual
bundled and catalog lookup. This is not a version comparison or an in-place
patch. `update` does not accept `--version`.

> [!WARNING]
> Update is destructive. If removal succeeds and replacement installation
> fails, the previous preset has already been removed. There is no source
> preflight, staging, rollback, automatic repair, or recovery transaction.

Before removing anything, the command rejects combined `--from` and `--dev`,
empty source arguments, priorities below `1`, and an ID that is not installed.
Beyond those checks, it does not inspect the replacement source in advance.
With `--from` or `--dev`, the replacement manifest's ID is not checked against
the requested ID before removal, so a different preset can be installed
instead.

If add fails, the command reports a copy-pastable `specify preset add` retry
command containing the replacement source and priority. On Windows, that
command is formatted for PowerShell.

A successful update re-enables the preset, recreates `installed_at`, and
removes local modifications within the installed preset directory. The
replacement priority defaults to `10`; pass `--priority` to choose another
value. An explicit `--from` or `--dev` is an intentional source change rather
than reuse of recorded catalog provenance.

If constitution synchronization is enabled, both normal remove and add
reconciliation passes run. A failed replacement can leave the generated
constitution reconciled against the stack without the removed preset. The
generated-file guard still protects a hand-edited constitution. There is no
update-specific optimization to suppress rewrites when the final content is
unchanged.

## Remove a preset

```bash
specify preset remove <preset_id>
```

Deletes the installed preset and its registry entry, cleans up recorded
command and skill outputs, and reconciles affected names against the
surviving stack. Removal can also restore outputs in previously active
integration directories recorded by that preset; it is not limited to
deleting files in the current integration.

## List installed presets

```bash
specify preset list
specify preset list --json
```

Lists installed presets with versions, descriptions, contribution counts,
priorities, and enabled status. Output includes disabled presets and is
ordered by precedence: lowest priority number first, then preset ID
alphabetically.

`--json` writes exactly one JSON array to stdout and exits `0` on success.
Every item has these keys:

| Key | Value |
| --- | --- |
| `id`, `name`, `description`, `version` | Preset identity and metadata |
| `author` | Author or `null` when absent |
| `priority` | Resolution priority |
| `enabled` | Whether the preset participates in resolution |
| `source` | `{"kind":"local"}` or `{"kind":"catalog","catalog":"<catalog-name>"}` |
| `provides` | Counts named `commands`, `templates`, and `scripts` |

Local, legacy, and malformed provenance is reported as `{"kind":"local"}`.
The `source` object describes where the preset was installed from, not a
contribution's position in the resolution stack.

Runtime failures after option parsing write exactly one `{"error":"..."}`
object to stderr and exit `1`, without success output. Usage errors with
the raw `--json` token present also use that JSON error shape on stderr,
preserving their usage exit code, normally `2`. Without `--json`, including
for help, human-readable behavior is unchanged.

## Preset info

```bash
specify preset info <preset_id>
specify preset info <preset_id> --versions
specify preset info <preset_id> --json
```

Human-readable output describes an installed preset first, otherwise an
available catalog entry, including metadata, tags, and contributions where
available.

`--versions` consults the catalog, not the installed preset. It lists the
advertised current version first, then historical versions in descending
version order, even for discovery-only entries. Listing versions does not
make them installable.

`--json` describes one installed preset, matched by ID, and writes one JSON
object to stdout. It has the same `id`, `name`, `description`, `version`,
`author`, `priority`, `enabled`, and `source` keys as `list --json`.
Instead of `provides` counts, it has `commands`, `templates`, and `scripts`
arrays. Each array preserves manifest declaration order and contains:

| Key | Value |
| --- | --- |
| `name` | Logical contribution name |
| `description` | Description, or `""` when absent or empty |
| `source` | `{"layer":"preset","presetId":"<id>"}` identifying the contributing preset |
| `sourcePath` | Manifest `file` path, relative to the installed preset |
| `strategy` | `replace`, `prepend`, `append`, or `wrap`; `replace` if omitted |

`--json` cannot be combined with `--versions` (usage error, exit `2`).
A preset that is not installed, including one only in a catalog, or a
missing project produces one JSON error object on stderr and exits `1`.
Usage errors preserve their usage exit code as with `list --json`.

## Resolve a file

```bash
specify preset resolve spec-template
specify preset resolve speckit.specify
```

Accepts an extensionless template name or a dot-separated command name.
Names use lowercase letters, digits, and hyphens; command segments must be
non-empty. This command does not offer a script-type selector.

Shows the highest-priority layer's path and source. If output is composed,
it also shows the contributing composition chain, starting at its effective
base. The displayed path is not a file containing the final composed output.
Invalid composition produces a warning; a missing name is reported as not
found. For all artifact kinds and hidden layers, use the separate
[artifact reference](../overview/artifacts.md).

## Enable or disable a preset

```bash
specify preset enable <preset_id>
specify preset disable <preset_id>
```

Changes whether an installed preset participates in subsequent resolution.
Repeating the current state succeeds without changing it.

Previously registered commands and skills remain in place. Disabling is
useful for comparing template and script behavior, but it does not withdraw
already delivered overrides from an agent. Use removal when those outputs
need to stop taking effect. Constitution reconciliation runs when
`constitution-sync` is enabled.

## Set preset priority

```bash
specify preset set-priority <preset_id> <priority>
```

Changes an installed preset's resolution priority. The value must be a
positive integer; lower numbers take precedence, with alphabetical ID
ordering for ties. This updates the registry and opted-in constitution
reconciliation; it does not itself rescaffold command and skill outputs.

## Catalog management

```bash
specify preset catalog list
specify preset catalog add <url> --name <name>
specify preset catalog remove <name>
```

`list` shows active sources, priorities, and installation permissions.
`add` writes the project's `.specify/preset-catalogs.yml`; `remove` removes
a named entry from that project configuration.

| `catalog add` option | Description |
| --- | --- |
| `--name <name>` | Required catalog name |
| `--priority <N>` | Default `10`; lower numbers are checked first |
| `--install-allowed / --no-install-allowed` | Permit ID installs; default discovery-only |
| `--description <text>` | Optional description |

Re-adding the same named catalog with identical settings succeeds without
rewriting configuration. Different settings for the same name are rejected;
remove the entry first or choose another name.

> [!IMPORTANT]
> A project's `.specify/preset-catalogs.yml` can select an install-allowed
> catalog you did not choose. Inspect `catalog list` in unfamiliar projects.
> Only enable installation for catalogs you own or have vetted; never treat
> `install_allowed` as evidence that preset code has been reviewed.

## See also

- [Preset overview](overview.md)
- [Developing presets](developing.md)
- [API reference](api.md)
- [Catalog configuration, schemas, and trust](catalogs.md)
- [Publishing presets](publishing.md)
