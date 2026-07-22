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
| `--force`       | Overwrite if the extension is already installed          |
| `--priority <N>`| Resolution priority (default: 10; lower = higher precedence) |

Installs an extension from the catalog, a URL, or a local directory. Extension commands are automatically registered with the currently installed AI coding agent integration.

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
```

| Option        | Description                                        |
| ------------- | -------------------------------------------------- |
| `--available` | Show available (uninstalled) extensions            |
| `--all`       | Show both installed and available extensions       |

Lists installed extensions with their status, version, and command counts.

## Extension Info

```bash
specify extension info <name>
```

Shows detailed information about an installed or available extension, including its description, version, commands, and configuration.

## Update Extensions

```bash
specify extension update [<name>]
```

Updates a specific extension, or all installed extensions if no name is given.

## Enable / Disable an Extension

```bash
specify extension enable <name>
specify extension disable <name>
```

Disable an extension without removing it. Disabled extensions are not loaded and their commands are not available. Re-enable with `enable`.

## Set Extension Priority

```bash
specify extension set-priority <name> <priority>
```

Changes the resolution priority of an extension. When multiple extensions provide a command with the same name, the extension with the lowest priority number takes precedence.

## Catalog Management

Extension catalogs control where `search` and `add` look for extensions. Catalogs are checked in priority order (lower number = higher precedence).

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
| `--install-allowed / --no-install-allowed` | Whether extensions can be installed from this catalog |
| `--description <text>`               | Optional description                               |

Adds a catalog to the project's `.specify/extension-catalogs.yml`.

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
4. **Built-in defaults** — official catalog + community catalog

Example `.specify/extension-catalogs.yml`:

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
The file contains installed extensions, global settings, and hooks that are surfaced before or after Spec Kit commands.

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
| `optional` | Whether the hook is optional. If `true`, the hook is presented with its `prompt` and can be skipped; if `false`, the hook is emitted as an automatic hook (includes `EXECUTE_COMMAND` markers). |
| `priority` | Priority metadata for the hook. Registered hook entries use integer values >= 1; entries installed from manifests default to `10` when no priority is declared. Current command templates surface hooks in their configured YAML order and do not sort them by `priority`. |
| `prompt` | Message shown when asking whether to run an optional hook. |
| `description` | Human-readable explanation of what the hook does. |
| `condition` | Optional expression evaluated by `HookExecutor` (using `config.<path>` or `env.<VAR>` with `is set`, `==`, or `!=`). Current command templates do not evaluate conditions and skip hooks with a non-empty condition. |
Hook event names identify when a hook is invoked. They generally use `before_<command>` or `after_<command>`, such as `before_implement`, `after_implement`, `before_tasks`, and `after_tasks`.

Extension manifests reject invalid hook priorities during installation. For existing `.specify/extensions.yml` entries, `HookExecutor.get_hooks_for_event()` sorts with `normalize_priority()`: missing values, booleans, non-numeric values rejected by `int()`, and values less than `1` fall back to `10`; numeric strings and finite floats are coerced with `int()`, while non-finite floats are unsupported and may fail instead of falling back.

`HookExecutor.get_hooks_for_event()` returns hooks ordered by `priority`, with lower values first. However, current command templates read hook lists directly and surface them in their configured YAML order rather than using priority ordering.

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
