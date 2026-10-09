# Extensions

Extensions add new capabilities to Spec Kit — domain-specific commands, external tool integrations, quality gates, and more. They introduce new commands and templates that go beyond the built-in Spec-Driven Development workflow.

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
```

| Option          | Description                                              |
| --------------- | -------------------------------------------------------- |
| `--dev`         | Install from a local directory (for development)         |
| `--from <url>`  | Install from a custom URL instead of the catalog         |
| `--version <v>` | Install an exact version advertised by a catalog        |
| `--force`       | Overwrite if the extension is already installed          |
| `--priority <N>`| Resolution priority (default: 10; lower = higher precedence) |

Installs an extension from the catalog, a URL, or a local directory. Extension commands are registered with the active AI coding agent integration. For `generic`, invocations use the configured `--commands-dir`: flat command files by default, or `speckit-<name>/SKILL.md` with `--skills`. The deprecated core `speckit.taskstoissues` command remains available during migration and will be removed in a future minor release. It warns on invocation and continues its existing workflow without installing or enabling the extension automatically. For GitHub issue tracking, run `specify extension add github` and use the recommended `/speckit.github.taskstoissues` command (slash-hyphen integrations: `/speckit-github-taskstoissues`; Codex, ZCode, and Command Code skills: `$speckit-github-taskstoissues`; Kimi: `/skill:speckit-github-taskstoissues`).

If a generic integration refresh cannot produce every extension invocation (for example, because a command or skill is user-modified or its source is missing), it warns and restores that extension's prior registered artifacts. Other extensions can still refresh.

An unqualified catalog install still selects the advertised current version.
`--version` uses only the winning catalog source for that extension ID; it does
not fall back to a lower-priority source when the requested version is absent.
Discovery-only catalogs remain non-installable. `--version` cannot be combined
with `--dev` or the direct-URL `--from` option. The downloaded archive's extension
ID and version are checked before installation.

> **Note:** All extension commands require a project already initialized with `specify init`.

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
| `--available` | Show available (uninstalled) extensions            |
| `--all`       | Show both installed and available extensions       |
| `--json`      | Write installed extensions as JSON                 |

Lists installed extensions with their status, version, and command counts.

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

Catalogs may keep the current release in the existing top-level fields and add
historical releases in a `releases` mapping. Older single-version catalogs
continue to work unchanged. Each historical release needs its own download URL
and SHA-256 digest; release-specific requirements or provided capabilities must
be placed in that release's record rather than inherited from the current one.
As with current releases, a digest may use a case-insensitive `sha256:` prefix
and surrounding whitespace.

```json
{
  "extensions": {
    "my-extension": {
      "name": "My Extension",
      "version": "0.5.1",
      "download_url": "https://example.com/my-extension-0.5.1.zip",
      "sha256": "<64-character SHA-256 for 0.5.1>",
      "releases": {
        "0.4.12": {
          "download_url": "https://example.com/my-extension-0.4.12.zip",
          "sha256": "<64-character SHA-256 for 0.4.12>"
        }
      }
    }
  }
}
```

The example omits other catalog metadata for brevity. The current version must
not be repeated in `releases`; malformed or duplicate release records are
rejected. Bundle pins still use the current catalog resolution path until the
separate bundle work described in [#4719](https://github.com/github/spec-kit/issues/4719)
adds exact-version component lookup.

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

Disable an extension without removing it. Disabled extensions are not loaded and their commands are not available. Hook-only extensions can be installed, enabled, and disabled even if generic command-output settings are missing or invalid; extensions with commands still require valid settings. Re-enable with `enable`.

For `generic`, disabling removes hash-owned invocations even after the output directory moves, but preserves unrelated same-named files in the new directory.

## Set Extension Priority

```bash
specify extension set-priority <name> <priority>
```

Changes the resolution priority of an extension. When multiple extensions provide a command with the same name, the extension with the lowest priority number takes precedence.

## Catalog Management

Extension catalogs control where `search` and `add` look for extensions. Catalogs are checked in priority order (lower number = higher precedence).

### Trust model: discovery-only vs. install sources

Catalogs come in two kinds, and the distinction is a **security boundary**, not a limitation:

- **Install sources** (`install_allowed: true`) — catalogs you trust as a place to install from. The built-in `default` (official) catalog is one, as is any catalog you author and vet yourself.
- **Discovery-only** catalogs (`install_allowed: false`) — searchable surfaces for *finding* extensions, but not installable. The built-in `community` catalog is discovery-only and is already active for `search` out of the box; you do not need to add it.

`community` is intentionally discovery-only because it is an open, unvetted list. Making everything in it one-command-installable would mean pulling arbitrary third-party code with no review.

> **Do not flip a discovery-only catalog to `install_allowed`.** That defeats the entire point of separating discovery from installation. There are two correct ways to install something you found via `community`:
>
> 1. **Install a single vetted extension directly** with `--from` (no catalog authoring needed). Get the candidate archive URL from `specify extension info <name>` — for a discovery-only entry it prints a "Candidate archive" URL. Review that release archive, then install it:
>
>    ```bash
>    specify extension info <name>          # shows the candidate archive URL
>    specify extension add <name> --from <archive-url>
>    ```
>
>    Treat the URL as untrusted until you have vetted it — it comes from an unvetted catalog.
> 2. **Curate your own catalog** you control and vet, and mark *that* catalog `install_allowed: true` — for when you want a governed, reusable install source (e.g. for an org).

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

### Catalog Resolution Order

Catalogs are resolved in this order (first match wins):

1. **Environment variable** — `SPECKIT_CATALOG_URL` overrides all catalogs
2. **Project config** — `.specify/extension-catalogs.yml`
3. **User config** — `~/.specify/extension-catalogs.yml`
4. **Built-in defaults** — official `default` catalog (install-allowed) + `community` catalog (discovery-only)

Example `.specify/extension-catalogs.yml` for a catalog you own and vet:

```yaml
catalogs:
  - name: "my-org-catalog"
    url: "https://example.com/catalog.json"
    priority: 5
    install_allowed: true
    description: "Our approved extensions"
```

## Extension Configuration

Most extensions include configuration files in their install directory:

```text
.specify/extensions/<ext>/
├── <ext>-config.yml           # Project config (version controlled)
├── <ext>-config.local.yml     # Local overrides (gitignored)
└── <ext>-config.template.yml  # Template reference
```

Configuration is merged in this order (highest priority last):

1. **Extension defaults** (from `extension.yml`)
2. **Project config** (`<ext>-config.yml`)
3. **Local overrides** (`<ext>-config.local.yml`)
4. **Environment variables** (`SPECKIT_<EXT>_*`)

To set up configuration for a newly installed extension, copy the template:

```bash
cp .specify/extensions/<ext>/<ext>-config.template.yml \
   .specify/extensions/<ext>/<ext>-config.yml
```

## Project Extension and Hook Configuration

Spec Kit stores project-level extension registration and hook configuration in:

```text
.specify/extensions.yml
```

The file contains installed extensions, global settings, and hooks that are resolved by pre/post scripts before or after Spec Kit commands.

```yaml
installed:
  - git
  - my-extension

settings:
  auto_execute_hooks: true

hooks:
  before_implement:
    - extension: git
      command: speckit.git.commit
      enabled: true
      optional: true
      priority: 10
      prompt: "Commit outstanding changes before implementation?"
      description: "Auto-commit before implementation"

  after_implement:
    - extension: my-extension
      command: speckit.my-extension.verify
      enabled: true
      optional: false
      priority: 5
      description: "Run verification after implementation"
```

### Configuration fields

The top-level `installed` list records extensions installed in the project. The `settings` mapping stores project-wide extension settings, and `hooks` groups hook registrations by event.

`auto_execute_hooks` defaults to `true`, but is currently reserved and is not consulted when hooks are surfaced or invoked.

Each hook entry supports the following fields:

| Field | Description |
| --- | --- |
| `extension` | ID of the extension that registered the hook. |
| `command` | Extension command associated with the hook. |
| `enabled` | Whether the hook is active. Hooks with `enabled: false` are skipped. |
| `optional` | Whether the hook is optional. If `true`, the hook is presented with its `prompt` and can be skipped; if `false`, the agent invokes it and waits for completion. |
| `priority` | Registered hook entries use integer values >= 1; entries installed from manifests default to `10` when no priority is declared. Core command dispatchers sort by ascending priority, preserving file order for ties. |
| `prompt` | Message shown when asking whether to run an optional hook. |
| `description` | Human-readable explanation of what the hook does. |
| `condition` | Optional expression evaluated by `HookExecutor` (using `config.<path>` or `env.<VAR>` with `is set`, `==`, or `!=`). Core command dispatchers preserve the existing prompt behavior: skip hooks with a non-empty condition rather than evaluating it. |

Hook event names identify when a hook is invoked. They generally use `before_<command>` or `after_<command>`, such as `before_implement`, `after_implement`, `before_tasks`, and `after_tasks`.

Extension manifests reject invalid hook priorities during installation. For existing `.specify/extensions.yml` entries, `HookExecutor.get_hooks_for_event()` sorts with `normalize_priority()`: missing values, booleans, non-numeric values rejected by `int()`, and values less than `1` fall back to `10`; numeric strings and finite floats are coerced with `int()`, while non-finite floats are unsupported and may fail instead of falling back.

Core commands run two hook dispatchers, one before and one after their main work, using the project's selected `sh`, `ps`, or `py` script type. Each variant returns JSON containing the event and an ordered `hooks` array (`extension`, `command`, `optional`, `description`, `prompt`, `priority`). An absent configuration or event returns an empty array. An unreadable or invalid configuration returns an `error` and a nonzero exit code; agents must report that no hooks were checked, including mandatory hooks, and then continue the core command. The dispatchers determine the order but do not execute agent commands.

`specify extension add` and other CLI operations that save `.specify/extensions.yml` also materialize validated, ordered JSON responses under `.specify/hook-dispatch/`. All three script variants use this projection without parsing YAML; the Python script needs only the standard library (but still requires Python 3.11+ on the execution host), and Bash and PowerShell do not invoke Python. CLI saves serialize publication, and the scripts compare the saved YAML snapshot and verify the event index and each response against their generated SHA-256 digests. They fail with refresh guidance if the configuration was manually edited, a projected response was corrupted, the projection is incomplete, or its directory is missing. Bash requires `sha256sum` or `shasum` on the execution host to verify projected responses. Reinstall the affected extension with `specify extension add <name> --force` or refresh the project to regenerate it. Existing projects without a projection continue using their installed YAML resolvers until refreshed; their Python resolver still requires PyYAML.

The CLI validates hook fields across every configured event when materializing the projection. Priorities are truncated to integers in the range `1` through `2147483647`; values outside this range, booleans, and non-integer strings fall back to `10`. Quoted integer strings are accepted, but quoted decimal strings are not.

Native dispatchers also recognize the numeric YAML forms accepted by the Python resolver, including digit separators, hex/binary/octal integers, sexagesimal integers, and decimal floats with exponents. The canonical writer quotes strings that would otherwise be ambiguous to the native parsers and preserves YAML control-character escapes. A NUL character in hook configuration is rejected explicitly because Bash cannot represent it.

Legacy Bash and PowerShell resolvers (before projection generation) support the CLI's pretty-printed `.specify/extensions.yml` layout: a `hooks:` mapping, event names indented two spaces, list items under each event, and single-line scalar fields (including quoted strings and common escapes). Other YAML constructs such as anchors, flow-style hook lists, and block scalars are not supported by the legacy path. The CLI writes hook configuration in this canonical layout without wrapping long scalar values; installing or upgrading shared infrastructure rewrites existing valid YAML to this layout and generates its projection (YAML comments and formatting are not retained). The Python legacy path accepts general YAML through PyYAML. A hook `condition` must be a string or null in all variants.

## FAQ

### Why can't I find an extension with `search`?

Check the spelling of the extension name. The extension may not be published yet, or it may be in a catalog you haven't added. Use `specify extension catalog list` to see which catalogs are active.

### Why doesn't the extension command appear in my AI coding agent?

Verify the extension is installed and enabled with `specify extension list`. If it shows as installed, restart your AI coding agent — it may need to reload for it to take effect.

### How do I set up extension configuration?

Copy the config template that ships with the extension:

```bash
cp .specify/extensions/<ext>/<ext>-config.template.yml \
   .specify/extensions/<ext>/<ext>-config.yml
```

See [Extension Configuration](#extension-configuration) for details on config layers and overrides.

### How do I resolve an incompatible version error?

Update Spec Kit to the version required by the extension.

### Who maintains extensions?

Most extensions are independently created and maintained by their respective authors. The Spec Kit maintainers do not review, audit, endorse, or support extension code. Review an extension's source code before installing and use at your own discretion. For issues with a specific extension, contact its author or file an issue on the extension's repository.
