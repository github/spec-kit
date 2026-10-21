# Integration CLI Reference

This reference documents shared `specify integration` commands, catalog
management, and lifecycle behavior. For agent-specific setup, installed paths,
options, and limitations, start with the [integration guides](index.md).

Run these commands inside a project initialized with `specify init`.
For a new project, use `specify init <project> --integration <key>`.

## Supported AI Coding Agents

The [integration directory](index.md#choose-an-integration)
lists supported agents and their exact keys, with a dedicated guide for each
integration. Run `specify integration list` to inspect local availability.

## Command Invocation

Invoke Spec Kit's process steps inside your coding agent, not in the terminal.
In GitHub Copilot's default mode, these are skills you invoke in the agent's
chat. CLI installation and setup commands are separate terminal operations.
The steps are the same across integrations, but their spelling depends on the
agent and its installed mode:

| Integration or mode | SDD example | Extension example |
| --- | --- | --- |
| GitHub Copilot, default skills mode | `/speckit-specify` | `/speckit-bug-assess` |
| Dotted slash-command notation used in the references | `/speckit.specify` | `/speckit.bug.assess` |
| Codex, Command Code, ZCode skills | `$speckit-specify` | `$speckit-bug-assess` |
| Kimi skills | `/skill:speckit-specify` | `/skill:speckit-bug-assess` |

Use the form exposed by your agent. See the
[GitHub Copilot guide](copilot.md) for its skills and commands
layouts, or choose another agent from the [integration directory](index.md).

## List Available Integrations

```bash
specify integration list
```

| Option      | Description                                                                                                             |
| ----------- | ----------------------------------------------------------------------------------------------------------------------- |
| `--catalog` | Also browse the catalog, including external integrations not installed in this project. |

Shows built-in and trusted installed external integrations, their setup
requirements, and their multi-install safety declarations. Installed
integrations and the default are marked separately.
The `CLI Required` column reports the agent CLI requirement declared by
`config.requires_cli`, not whether the integration is IDE-only. External adapters
can separately require executables through their descriptor's `requires.tools`;
installation and `specify check` validate those tool requirements even when
`CLI Required` is `no`.

## Search Available Integrations

```bash
specify integration search [query]
```

| Option     | Description        |
| ---------- | ------------------ |
| `--tag`    | Filter by tag      |
| `--author` | Filter by author   |

Searches the active catalog stack. Without a query, lists all available integrations.

## Integration Info

```bash
specify integration info <integration_id>
specify integration info <integration_id> --versions
```

Shows an integration's catalog metadata, source catalog, and whether it is active.
`--versions` lists the advertised current and historical versions from the
winning catalog, with the current release first and older releases in descending
version order. Discovery-only sources are labeled as such.

## Install an Integration

```bash
specify integration install <key>
```

| Option                   | Description                                                              |
| ------------------------ | ------------------------------------------------------------------------ |
| `--script sh\|ps\|py`    | Script type: `sh` (bash/zsh), `ps` (PowerShell), or `py` (Python)        |
| `--force`                | Opt in to installing alongside integrations that are not declared multi-install safe |
| `--integration-options`  | Integration-specific options (e.g. `--integration-options="--commands-dir .myagent/cmds"`) |
| `--trust-integration` | After reviewing the code, pre-authorize an external adapter's Python execution without the interactive trust prompt |

Installs the integration into the current project. Multi-install proceeds
automatically only when all involved integrations are declared safe. Otherwise,
use `switch` to replace the default or `--force` to opt in to multi-install.
Failed setup triggers rollback.

**Catalog history is metadata only.** `integration install` still resolves
registered built-in implementations directly, or the current external adapter
release from an install-enabled catalog, not historical catalog records.
There is no `integration install --version`. The default community catalog
remains discovery-only.

Installing an additional integration does not change the default integration. Use `specify integration use <key>` to change the default.

Extensions and presets follow the default integration only. Use `use <key>` or
`switch <key>` to activate another integration and register their commands for it.

### Catalog-installed external adapters

Register a reviewed catalog in the initialized project, then install its adapter:

```bash
specify integration catalog add https://example.com/catalog.json --name samples
specify integration install sample-agent
specify integration use sample-agent
```

Installation prompts for trust **before** downloading/importing Python. For
automation, explicitly authorize code you have reviewed:

```bash
specify integration install sample-agent --trust-integration
specify integration upgrade sample-agent --trust-integration
```

The source must have `install_allowed: true`. The default community catalog is
discovery-only; neither `--force` nor the trust flag bypasses that policy.
Catalog listing/search/info do not import catalog code. See the
[catalog schema](catalog.md#catalog-schema) for required metadata and supported
archive URLs.
Search advertises `specify integration install <id>` for install-enabled sources;
discovery-only results do not advertise installation.

`specify check` probes an external adapter's required descriptor tools rather
than its catalog ID. With no required tools declared, CLI adapters are checked
using their runtime executable; optional tools do not produce missing-tool
errors. These checks do not run the executable or invoke generic version probes.

Installed adapter code persists separately from generated agent files. New CLI
processes load the trusted package without consulting the catalog. Missing,
modified, or incompatible code is an error, not a silent fallback. Upgrade
fetches the catalog's current version; uninstall removes the package while
preserving modified generated files by default.
Metadata-only `workflow status` and `workflow info` remain available without
loading adapter code, including when an installed adapter is damaged. Workflow
execution and resume still report adapter-loading failures explicitly.

Execution consent is user-local and bound to the project, integration, and
verified package contents. Copying project metadata does not transfer consent.
After copying a project or changing users, review the adapter and reauthorize
from an install-enabled catalog:

```bash
specify integration upgrade sample-agent --force --trust-integration
```

Forced uninstall also works when package code is untrusted or its entire
directory is missing; it does not import that code.

For initialization, a project/user catalog or `SPECKIT_INTEGRATION_CATALOG_URL`
can supply an external adapter:

```bash
specify init my-project --integration sample-agent --trust-integration
```

Review the [external adapter API](https://github.com/github/spec-kit/blob/main/design/integration.md#external-adapter-package-contract)
before publishing a package. No pip installation or source-registry edit is
needed for adapters using the host API and standard library.

If your CLI rejects multi-install, check `specify version` and follow the
[upgrade guide](../upgrade.md). A one-shot `uvx` invocation does not update the
persistent `specify` executable on your `PATH`.

## Uninstall an Integration

```bash
specify integration uninstall [<key>]
```

| Option    | Description                                         |
| --------- | --------------------------------------------------- |
| `--force` | Remove files even if they have been modified         |

Removes the specified integration, or the default if no key is given.
Manifest-tracked generated files use content hashes for cleanup:

- **Unmodified files** are removed automatically.
- **Modified files** (where you've made manual edits) are preserved so your customizations are not lost.
- Use `--force` to remove modified tracked files too.

These are the rules for manifest-tracked generated files. Integration-specific
cleanup can differ: [Hermes global skills](hermes.md#global-ownership-and-removal)
and [Kimi legacy skills](kimi.md#legacy-cleanup-on-uninstall)
can be removed without modified-file protection. Check the agent guide before
uninstalling or switching away.

Uninstall also removes the integration's registered extension and preset
artifacts; the extensions and presets themselves stay installed. Removing the
default selects a remaining integration and registers enabled contributions for
it. Removing the last integration does not install `none` automatically.

## Switch to a Different Integration

```bash
specify integration switch <key>
```

| Option                   | Description                                                              |
| ------------------------ | ------------------------------------------------------------------------ |
| `--script sh\|ps\|py`    | Script type: `sh` (bash/zsh), `ps` (PowerShell), or `py` (Python)        |
| `--force`                | Force removal of modified files during uninstall; when the target is already installed, overwrite managed shared templates while changing the default |
| `--refresh-shared-infra` | Also overwrite shared infrastructure files even if you customized them (otherwise customizations are preserved) |
| `--integration-options`  | Options for the target integration when it is not already installed      |
| `--trust-integration` | Authorize downloading and executing a reviewed external adapter without the interactive trust prompt |

- **Target not installed:** removes the current default, installs the target,
  and makes it the default. Other installed integrations remain.
- **Target already installed:** changes the default without removing any
  integrations, like `use`. To change its setup options, run
  `upgrade <key> --integration-options ...` first, then `use <key>`;
  `switch` rejects setup options for installed targets.

Both paths register enabled extensions and presets for the new default.
See the option table for the different meanings of `--force`.

When switching to an external adapter that must be downloaded and installed,
use `--trust-integration` only after reviewing its code:

```bash
specify integration switch sample-agent --trust-integration
```

Switching to an already-installed adapter still validates its existing trust.
The flag does not bypass that validation or a catalog's discovery-only policy.
See [catalog-installed external adapters](#catalog-installed-external-adapters)
for the trust requirements.

## Use an Installed Integration

```bash
specify integration use <key>
```

| Option    | Description                                         |
| --------- | --------------------------------------------------- |
| `--force` | Overwrite managed shared templates while changing the default |

Sets the default integration without uninstalling any other installed integrations. This also refreshes managed shared templates so command references match the new default integration's invocation style. Modified or untracked shared templates are preserved unless `--force` is used.

It also registers enabled extension and preset commands or skills for the new
default, including contributions installed while another integration was active.

## Upgrade an Integration

```bash
specify integration upgrade [<key>]
```

| Option                   | Description                                                              |
| ------------------------ | ------------------------------------------------------------------------ |
| `--force`                | Overwrite files even if they have been modified                          |
| `--script sh\|ps\|py`    | Script type: `sh` (bash/zsh), `ps` (PowerShell), or `py` (Python)        |
| `--integration-options`  | Options for the integration                                              |
| `--trust-integration`    | Authorize downloading/importing the reviewed replacement external adapter |

Reinstalls an installed integration with updated templates and commands (e.g., after upgrading Spec Kit). Defaults to the default integration; if a key is provided, it must be one of the installed integrations. Detects locally modified files and blocks the upgrade unless `--force` is used. Stale files from the previous install that are no longer needed are removed automatically. Shared templates stay aligned with the default integration even when upgrading a non-default integration.

Enabled extensions and presets are re-registered only when upgrading the currently active (default) integration. A non-default upgrade still refreshes that integration's core commands, but does not re-register its extension or preset layers — `use`/`switch` that integration afterward to rescaffold them.

If the generated-file manifest is missing, upgrade reports that there is nothing
to upgrade and leaves the installed adapter package, generated files, and local
recovery ownership unchanged, including with `--force`. Replacement code is
persisted only after the upgrade regenerates the managed files successfully.

If an upgrade would change an integration between command and skills layouts while preset artifacts are registered for it, the upgrade is rejected before changing files. Remove the affected presets, run the layout-changing upgrade, then reinstall them.

For external adapters, forced upgrade or uninstall can recover damaged or
unloadable packages using user-local ownership records. Without that proof,
old-only generated files are preserved with a manual-cleanup warning. Recovery
preserves shared event dispatchers and partially owned settings; a trusted
replacement may still overwrite its declared destinations under `upgrade --force`.
Recovery does not bypass catalog policy or replacement-package trust.

Failed operations roll back their own changes, not unrelated user files or
workflow progress. Conflicting concurrent edits are reported with recovery
snapshots retained. Adapter authors should follow the
[storage, loading, and lifecycle contract](https://github.com/github/spec-kit/blob/main/design/integration.md#storage-loading-and-lifecycle)
for ownership, journaling, and recovery requirements.

## Report Integration Status

```bash
specify integration status
specify integration status --json
```

Reports the current project's integration status without changing files. The
status report includes the default integration, installed integrations,
multi-install safety, missing managed files, modified managed files, invalid
manifest paths, shared Spec Kit infrastructure health, unchecked manifests, and
the target integration for default-sensitive shared templates. The JSON form is
intended for CI and coding agents that need stable machine-readable status data;
it also reports the raw recorded integrations and the integration manifests that
were checked when state repair heuristics differ from the recorded file.
The command exits 0 when the report status is `ok` or `warning`; it exits 1
only when the report status is `error`. In JSON output, `multi_install_safe`
is `null` when no installed integration set can be evaluated, such as when the
integration state is missing, unreadable, lacks a valid recorded integration
list, or records no installed integrations.

## Catalog Management

Integration catalogs control where the discovery commands (`search` and `info`) look for integrations. Catalogs are checked in priority order.

Catalog management, `integration list --catalog`, and `integration info` do not
execute adapter code. Ordinary integration listing, setup, selection, status,
registration, and workflow dispatch load trusted installed implementations.

### List Catalogs

```bash
specify integration catalog list
```

Shows the active catalog sources. Project-level sources (when configured) are removable by index; otherwise the active sources are shown as non-removable.

### Add a Catalog

```bash
specify integration catalog add <url>
```

| Option          | Description                   |
| --------------- | ----------------------------- |
| `--name <name>` | Optional name for the catalog |

Adds a custom catalog URL to the project's `.specify/integration-catalogs.yml`. The URL must use HTTPS (except `http://localhost`, `http://127.0.0.1`, or `http://[::1]` for local testing).

Re-adding the same URL with the same name succeeds without changing the configuration; a different name is rejected.

### Remove a Catalog

```bash
specify integration catalog remove <index>
```

Removes a project catalog source by its 0-based index in `catalog list`.

### Catalog Resolution Order

The first configured layer replaces lower layers. Within that layer, lower
numeric priority wins:

1. **Environment variable** — `SPECKIT_INTEGRATION_CATALOG_URL` overrides all catalogs
2. **Project config** — `.specify/integration-catalogs.yml`
3. **User config** — `~/.specify/integration-catalogs.yml`
4. **Built-in defaults** — official catalog + community catalog

### Historical Integration Metadata

An integration entry may retain the existing top-level fields for its advertised
current release and add a `releases` mapping of historical version to metadata.
Single-version entries remain valid without a `releases` key. For example:

```json
{
  "id": "my-agent",
  "name": "My Agent",
  "version": "2.0.0",
  "description": "Current release",
  "releases": {
    "1.0.0": {
      "description": "Historical release",
      "repository": "https://example.com/my-agent/v1",
      "requires": {"speckit_version": ">=0.7"}
    }
  }
}
```

The top-level fields retain their original meaning for older clients and for
unqualified `search`, `info`, `list --catalog`, and `install` commands. Historical
records may contain `name`, `description`, `author`, `repository`, `license`,
`tags` (a list of strings), and `requires` (a mapping). Shared identity, name,
author, and source policy are retained; current-only metadata such as
description, repository, tags, and requirements is **not** inherited by an
older release unless explicitly supplied in its record. Release records cannot
override `id`, `version`, `releases`, or source policy, and cannot advertise
download URLs or archives.

For programmatic metadata lookup,
`IntegrationCatalog.get_integration_info(id, version="1.0.0")` selects the
exact historical record from the winning source, or returns `None` if that
version is missing. `get_integration_versions(id)` returns the versions
advertised by that same source. PEP 440-equivalent spellings (such as `v1.0`
and `1.0.0`) match the same release while retaining its catalog spelling.
The current release must not be repeated in `releases`; malformed records and
duplicate equivalent versions are rejected. An absent version never falls
through to a lower-priority source or silently selects current. These lookups
do not install an integration.

## Integration-Specific Options

Pass agent-specific setup options through `--integration-options`. Their
semantics, examples, and migration caveats live in the relevant agent guide:

| Integration | Guide |
| --- | --- |
| Generic | [Output directory and skills mode](generic.md#output-options-and-invocation) |
| GitHub Copilot | [Skills and commands layouts](copilot.md#commands-layout) |
| IBM Bob | [Legacy commands and migration](bob.md#legacy-commands-and-migration) |
| Kimi Code | [Legacy migration](kimi.md#legacy-migration) |
| opencode | [Hidden Spec Kit files](opencode.md#hidden-spec-kit-files) |

Other agent-specific details are listed in the
[integration directory](index.md).

## Runtime Events

Event-capable integrations accept `--events true|false` through the setup
`--integration-options` string; the default is enabled. Handler definitions
come from integration defaults, installed extensions, and
`.specify/integration-events.yml`. Enabling events does not create handlers
where none are configured, and an integration emits only the native events
it supports.

To configure project overrides, create `.specify/integration-events.yml`.
Replace `<key>` with your integration key and the example command with an
installed, script-backed Spec Kit command:

```yaml
integrations:
  <key>:
    events:
      post_tool_use:
        - command: speckit.my-extension.check
          matcher: "*"
          timeout: 60
```

Each event accepts a handler mapping or a list of handlers. A handler requires
a non-empty `command` string; `matcher` is an optional native filter string,
and `timeout` is an optional positive integer in seconds.

Integration defaults and extension handlers accumulate. A valid project override
**replaces the entire event map for that integration**, not just the events
listed in the override. Set `events: {}` under the integration key to disable
all its handlers. If the override cannot be read or parsed, or an event fails
validation, Spec Kit warns and retains the defaults and extension handlers.
`--events false` takes precedence over all these sources.

With events enabled, apply configuration changes using
`specify integration upgrade <key>`.

For an event-capable integration, disable Spec Kit event handlers during an upgrade:

```bash
specify integration upgrade <key> --integration-options="--events false"
```

Supplying `--integration-options` replaces stored setup options, so repeat other
options you want to keep. A disabled event set removes previously installed
Spec Kit hooks rather than merely stopping new hook generation.
Agent-specific guides identify native event configuration paths and
limitations. These runtime events are distinct from extension command hooks.

## Workflow CLI Dispatch

The agent guides distinguish IDE setup from workflow CLI support. Some IDE
integrations can dispatch workflow steps if their separate CLI is available;
others explicitly do not support command/prompt dispatch. Adapter support means
Spec Kit can construct the invocation, not that every vendor CLI release has
been exercised against it.

CLI-capable adapters support
`SPECKIT_INTEGRATION_<KEY>_EXECUTABLE` for executable selection and
`SPECKIT_INTEGRATION_<KEY>_EXTRA_ARGS` for additional CLI arguments, where
`<KEY>` is uppercase with hyphens replaced by underscores. Extra arguments are
parsed using POSIX shell quoting. Placement and duplicate-flag behavior differ
by adapter; see the agent guide, especially for Docker Agent and Goose.

Setup `--integration-options` are separate from workflow
[`integration_args` and `integration_options`](../reference/workflows.md#per-step-integration-configuration).
Adapters reject non-empty per-step configuration unless they implement it;
Docker Agent currently exposes structured agent/safety configuration.
Headless approval flags, model forwarding, and structured-output support are
also adapter-specific, not universal guarantees.

## GitHub Issue Creation

The deprecated `speckit.taskstoissues` command still runs with a warning but
will be removed in a future minor release. Install the opt-in GitHub extension
with `specify extension add github` and use `speckit.github.taskstoissues`
instead. See the [extension's migration guide](https://github.com/github/spec-kit/blob/main/extensions/github/README.md#migrating-from-the-core-taskstoissues-command)
for invocation syntax and migration details; the core command does not install
the extension automatically.

## FAQ

### Can I install multiple integrations in the same project?

Yes, but it is intended for team portability rather than the default setup. Multiple integrations are allowed automatically only when the installed integration and the new integration are declared multi-install safe by Spec Kit. For other combinations, pass `--force` to acknowledge that multiple agents may see unrelated agent-specific instructions or commands.

Spec Kit tracks one default integration in `.specify/integration.json` with `default_integration`, all installed integrations with `installed_integrations`, per-integration runtime settings with `integration_settings`, and a dedicated `integration_state_schema` for future state migrations. The legacy `integration` field remains as an alias for the default integration.

### Which integrations are multi-install safe?

For integrations that generate agent files, safety requires static, unique
output paths, stable command invocation settings, and a separate manifest whose
managed files do not overlap another safe integration. Registry tests enforce
those invariants. Shared Spec Kit templates remain aligned to the single default.

Run `specify integration list` to inspect each integration's declaration.
Each integration's guide documents its safety status and installed command
directories.

Integrations that share a command directory with another integration, require dynamic install paths such as `--commands-dir`, or merge shared tool settings are not declared safe by default. They can still be installed alongside another integration with `--force`.

### What happens to my changes when I uninstall or switch?

Manifest-tracked files you've modified are preserved automatically. Only
unmodified tracked files (matching their original SHA-256 hash) are removed.
Use `--force` to override this. See
[uninstall](#uninstall-an-integration) for integration-specific cleanup exceptions.

### How do I know which key to use?

Run `specify integration list` to see all available integrations with their keys,
or check the [integration directory](index.md#choose-an-integration).

### Do I need the AI coding agent installed to use an integration?

CLI-based integrations require the tool to be installed. IDE-based integrations
work through the IDE itself and may not require a separate CLI for setup.
Workflow dispatch can have additional CLI requirements; see your integration's
guide. `specify integration list` shows each integration's setup requirements.

If an integration has no command templates, `specify init` keeps the
project-directory guidance and shows how to choose an integration with
`specify integration list` and switch to it with `specify integration switch <key>`,
rather than recommending unavailable agent commands.

### When should I use `upgrade` vs `switch`?

Use `upgrade` when you've upgraded Spec Kit and want to refresh an installed integration's managed files. Use `switch` when you want to replace the current default with another integration; if the target is already installed, `switch` behaves like `use`.

### Do extensions and presets I install apply to every installed integration?

No. Extensions (`specify extension add`) and presets (`specify preset add`) register their command overrides for the currently active (default) integration only, even if other integrations are installed. A non-default integration does not receive those artifacts until it becomes the default: `specify integration use <key>` (or `switch <key>`) rescaffolds every enabled extension and preset for the newly active integration. `specify integration upgrade` follows the same rule — it only re-registers extensions and presets when upgrading the active integration.
