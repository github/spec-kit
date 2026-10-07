# Supported AI Coding Agent Integrations

The Specify CLI supports a wide range of AI coding agents. When you run `specify init`, the CLI sets up the appropriate command files and directory structures for your chosen AI coding agent — so you can start using Spec-Driven Development immediately, regardless of which tool you prefer.

## Supported AI Coding Agents

| Agent                                                                                | Key              | Notes                                                                                                                                     |
| ------------------------------------------------------------------------------------ | ---------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| [Alquimia AI](https://docs.alquimia.ai)                                              | `alquimia`       | Skills-based integration; installs skills into `.alquimia/skills` and invokes them as `/speckit-<command>`                                |
| [Amp](https://ampcode.com/)                                                          | `amp`            |                                                                                                                                           |
| [Antigravity (agy)](https://antigravity.google/)                                     | `agy`            | Skills-based integration; installs skills into `.agents/skills/` and invokes them as `/speckit-<command>`. In headless non-interactive runs, automatic tool approval via `--dangerously-skip-permissions` can be enabled by setting `SPECKIT_AGY_ALLOW_ALL_TOOLS=1` or `SPECKIT_INTEGRATION_AGY_ALLOW_ALL_TOOLS=1`. |
| [Auggie CLI](https://docs.augmentcode.com/cli/overview)                              | `auggie`         |                                                                                                                                           |
| [Claude Code](https://www.anthropic.com/claude-code)                                 | `claude`         | Skills-based integration; installs skills in `.claude/skills`                                                                              |
| [Cline](https://github.com/cline/cline)                                              | `cline`          | IDE-based agent                                                                                                                           |
| [CodeBuddy CLI](https://www.codebuddy.cn/docs/cli/installation)                      | `codebuddy`      |                                                                                                                                           |
| [Codex CLI](https://github.com/openai/codex)                                         | `codex`          | Skills-based integration; installs skills into `.agents/skills` and invokes them as `$speckit-<command>` |
| [Command Code](https://commandcode.ai/docs)                                          | `command-code`   | Skills-based integration; installs skills into `.commandcode/skills/` and invokes them as `$speckit-<command>` |
| [Cursor](https://cursor.sh/)                                                         | `cursor-agent`   |                                                                                                                                           |
| [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness)                  | `dsh`            | Skills-based integration; installs skills into `.dsh/skills` and invokes them as `/speckit-<command>` |
| [Devin for Terminal](https://cli.devin.ai/docs)                                      | `devin`          | Skills-based integration; installs skills into `.devin/skills/` and invokes them as `/speckit-<command>` |
| [Docker Agent](https://docs.docker.com/ai/docker-agent/)                              | `docker-agent`   | Skills-based integration; installs skills into `.agents/skills/` (the same directory used by Codex and Zed). In the selected agent YAML, enable local skills with `skills: true` and provide filesystem read access. Detects either the standalone `docker-agent` binary or the Docker CLI plugin (`docker agent`). Configure workflow dispatch with `SPECKIT_INTEGRATION_DOCKER_AGENT_EXTRA_ARGS=./agent.yaml`; the Spec Kit prompt is appended after these arguments. Not multi-install safe by default because the skills directory is shared. |
| [Factory Droid](https://docs.factory.ai/cli/getting-started/overview)               | `droid`          | Skills-based integration; installs skills into `.factory/skills/` and invokes them as `/speckit-<command>`                               |
| [Firebender](https://firebender.com/)                                                | `firebender`     | IDE-based agent for Android Studio / IntelliJ                                                                                             |
| [Forge](https://forgecode.dev/)                                                      | `forge`          |                                                                                                                                           |
| [Gemini CLI](https://github.com/google-gemini/gemini-cli)                            | `gemini`         |                                                                                                                                           |
| [GitHub Copilot](https://code.visualstudio.com/)                                     | `copilot`        | Skills-based by default; installs `speckit-<command>/SKILL.md` under `.github/skills/`. Pass `--integration-options="--commands"` to use the supported commands layout: `.agent.md` files under `.github/agents/`, companion `.prompt.md` files under `.github/prompts/`, and a `.vscode/settings.json` merge. |
| [Goose](https://goose-docs.ai/)                                                      | `goose`          | Uses YAML recipe format in `.goose/recipes/`                                                                                              |
| [Grok Build](https://docs.x.ai/build/overview)                                       | `grok`           | Skills-based integration; installs skills into `.grok/skills` and invokes them as `/speckit-<command>`                                    |
| [Hermes](https://github.com/NousResearch/hermes-agent)                               | `hermes`         | Skills-based integration; installs skills globally into `~/.hermes/skills/`                                                                |
| [IBM Bob](https://www.ibm.com/products/bob)                                          | `bob`            | Skills-based integration by default; installs skills as `speckit-<command>/SKILL.md` under `.bob/skills/` and invokes them as `/speckit-<command>`. Pass `--integration-options="--legacy-commands"` to scaffold the deprecated Bob 1.x layout (`.bob/commands/*.md`) instead; that flag will be removed in a future release. Existing legacy installs can migrate with `specify integration upgrade bob --integration-options="--skills"`, which converts them to the skills layout and removes the old command files. If preset overrides are installed, the migration is rejected with an actionable error (preset artifacts cannot yet be reconciled across a layout change) — remove the preset(s), migrate, then reinstall them. |
| [Junie](https://junie.jetbrains.com/)                                                | `junie`          |                                                                                                                                           |
| [Kilo Code](https://github.com/Kilo-Org/kilocode)                                    | `kilocode`       | Installs commands into `.kilo/commands`; legacy `.kilocode/workflows` installs remain supported as a registration fallback                 |
| [Kimi Code](https://code.kimi.com/)                                                  | `kimi`           | Skills-based integration; installs into `.kimi-code/skills/`. `--migrate-legacy` moves old `.kimi/skills/` installs to the new paths |
| [Kiro CLI](https://kiro.dev/docs/cli/)                                               | `kiro-cli`       | Kiro CLI does not substitute `$ARGUMENTS` in file-based prompts, so Spec Kit ships a prose fallback at render time (see [Manage prompts](https://kiro.dev/docs/cli/chat/manage-prompts/) and issue [#1926](https://github.com/github/spec-kit/issues/1926)). Alias: `--integration kiro` |
| [Lingma](https://lingma.aliyun.com/)                                                 | `lingma`         | Skills-based integration; skills are installed automatically                                                                               |
| [MiniMax Code](https://github.com/MiniMax-AI/minimax-code)                          | `mcode`          | Skills-based integration; installs skills into `.minimax/skills` and invokes them as `/speckit-<command>`. Headless workflow dispatch uses `--permission full` so tool actions are not blocked by headless permission gating; set `SPECKIT_INTEGRATION_MCODE_EXTRA_ARGS="--permission smart"` to use MiniMax Code's stricter policy. |
| [Mistral Vibe](https://github.com/mistralai/mistral-vibe)                            | `vibe`           |                                                                                                                                           |
| [Muse Code](https://dev.meta.ai/docs/muse-code)                                     | `muse`           | Skills-based integration; installs skills into `.agents/skills` and invokes them as `/speckit-<command>`                                   |
| [Oh My Pi](https://www.npmjs.com/package/@oh-my-pi/pi-coding-agent)                  | `omp`            | Installs slash commands into `.omp/commands`                                                                                               |
| [opencode](https://opencode.ai/)                                                     | `opencode`       |                                                                                                                                           |
| [Pi Coding Agent](https://pi.dev)                                                    | `pi`             | Pi doesn't have MCP support out of the box, so `taskstoissues` won't work as intended. MCP support can be added via [extensions](https://github.com/badlogic/pi-mono/tree/main/packages/coding-agent#extensions) |
| [Qoder CLI](https://qoder.com/cli)                                                   | `qodercli`       |                                                                                                                                           |
| [Qwen Code](https://github.com/QwenLM/qwen-code)                                     | `qwen`           |                                                                                                                                           |
| [RovoDev](https://www.atlassian.com/software/rovo-dev)                               | `rovodev`        | Generates `.rovodev/skills/`, prompt wrappers, and `prompts.yml`; runtime dispatch uses `acli rovodev`                                   |
| [SHAI (OVHcloud)](https://github.com/ovh/shai)                                       | `shai`           | Workflow `command` and `prompt` steps can't run through SHAI: its CLI accepts prompt text (as arguments, on stdin, or through `shai agent`), but hands it to its auto-fix agent and never loads `.shai/commands`, so those steps fail |
| [Tabnine CLI](https://docs.tabnine.com/main/getting-started/tabnine-cli)             | `tabnine`        |                                                                                                                                           |
| [Trae](https://www.trae.ai/)                                                         | `trae`           | Skills-based integration; skills are installed automatically                                                                               |
| [ZCode](https://zcode.z.ai/)                                                         | `zcode`          | Skills-based integration; installs skills into `.zcode/skills/` and invokes them as `$speckit-<command>`                                  |
| [Zed](https://zed.dev/)                                                              | `zed`            | Skills-based integration; installs skills into `.agents/skills` and invokes them as `/speckit-<command>`                                  |
| Generic                                                                              | `generic`        | Bring your own agent — use `--integration generic --integration-options="--commands-dir <path>"` for AI coding agents not listed above; add `--skills` for the `speckit-<name>/SKILL.md` layout |

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

Use the form exposed by your agent. Copilot's default skills are installed under
`.github/skills/`; its opt-in commands layout is selected with
`--integration-options="--commands"`. In that layout, Copilot CLI can select an
agent through `/agents` or address it directly in a prompt.

## List Available Integrations

```bash
specify integration list
```

| Option      | Description                                                                                                             |
| ----------- | ----------------------------------------------------------------------------------------------------------------------- |
| `--catalog` | Also browse the catalog, including external integrations not installed in this project. |

Shows built-in and trusted installed external integrations, which one is
currently installed, and whether each requires a CLI tool or is IDE-based.
When multiple integrations are installed, the list marks the default integration separately from the other installed integrations.
The list also shows whether each integration is declared multi-install safe.

## Search Available Integrations

```bash
specify integration search [query]
```

| Option     | Description        |
| ---------- | ------------------ |
| `--tag`    | Filter by tag      |
| `--author` | Filter by author   |

Searches the active catalog stack for integrations matching the query. Without a query, lists all available integrations. Must be run inside a Spec Kit project.

## Integration Info

```bash
specify integration info <integration_id>
specify integration info <integration_id> --versions
```

Shows catalog details for a single integration, including its description, author, license, tags, source catalog, repository (when available), and whether it is currently active. Must be run inside a Spec Kit project.
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

Installs the specified integration into the current project. If another integration is already installed, the command only proceeds automatically when all involved integrations are declared multi-install safe. Otherwise, use `switch` to replace the default integration or pass `--force` to explicitly opt in to multi-install. If the installation fails partway through, it automatically rolls back to a clean state.

**Catalog history is metadata only.** `integration install` still resolves
registered built-in implementations, not historical catalog records. There is
no `integration install --version` or catalog-based integration distribution
contract, even when a catalog source is marked install-allowed. Community
catalogs remain discovery-only.

Installing an additional integration does not change the default integration. Use `specify integration use <key>` to change the default.

Installed extensions and presets are not registered for a non-default integration at install time — they follow the currently active (default) integration only. `specify integration use <key>` (or `switch <key>`) is what rescaffolds them for the newly active integration.

> **Note:** All integration management commands require a project already initialized with `specify init`. To start a new project with a specific agent, use `specify init <project> --integration <key>` instead.

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
Catalog listing/search/info do not import catalog code. Required external entry
fields are a map key matching the descriptor ID, name, version, description,
and an archive `download_url`; an optional explicit `id` must match the map key;
an archive `sha256` digest is recommended. Downloads support ZIP, tar.gz, and tgz,
HTTPS or loopback HTTP, and the existing authenticated GitHub asset flow.
See the [catalog schema](../../integrations/README.md#catalog-schema).
Search advertises `specify integration install <id>` for install-enabled sources;
discovery-only results do not advertise installation.

A package contains root `integration.yml` and `__init__.py`, not a copied
inventory of Spec Kit's commands. The host renders shared templates through the
adapter and registers installed extension/preset contributions for the default
integration. Code persists under `.specify/integrations/packages/<id>/`,
separately from generated agent files and their manifests. New CLI processes
load the trusted package without consulting the catalog. Missing, modified, or
incompatible code is an error, not a silent fallback. Upgrade installs the
catalog's current adapter version; uninstall removes its persisted code while
preserving modified generated files by default.
Metadata-only `workflow status` and `workflow info` remain available without
loading adapter code, including when an installed adapter is damaged. Workflow
execution and resume still report adapter-loading failures explicitly.

Execution consent is stored in `~/.specify/integration-trust.json`, bound to
the canonical project root, integration ID, and complete verified package
digest. It is checked before loading, even when adapter configuration is
cached. A project's `packages.json` is provenance, not permission; copying
it cannot transfer consent. The managed `.specify/.gitignore` excludes
`integrations/packages/` and `integrations/packages.json`.
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

Review the [external adapter API](../../design/integration.md#external-adapter-package-contract)
before publishing a package. No pip installation or source-registry edit is
needed for adapters using the host API and standard library.

**Version note:** Controlled multi-install support was introduced in Spec Kit 0.8.5. If `specify integration install <key>` says another integration is already installed and only suggests `switch` or `uninstall`, check your local CLI with `specify version` and upgrade it. Running a one-shot command such as `uvx --from git+https://github.com/github/spec-kit.git specify ...` uses a temporary copy for that command only; it does not update the persistent `specify` executable on your `PATH`.

## Uninstall an Integration

```bash
specify integration uninstall [<key>]
```

| Option    | Description                                         |
| --------- | --------------------------------------------------- |
| `--force` | Remove files even if they have been modified         |

Uninstalls the current integration (or the specified one). Spec Kit tracks every file created during install along with a SHA-256 hash of the original content:

- **Unmodified files** are removed automatically.
- **Modified files** (where you've made manual edits) are preserved so your customizations are not lost.
- Use `--force` to remove all integration files regardless of modifications.

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

If the target integration is not already installed, equivalent to running `uninstall` followed by `install` in a single step. In this mode, `--force` controls whether modified files from the removed integration are deleted. If the target integration is already installed, `switch` only changes the default integration, like `use`; in this mode, `--force` controls whether managed shared templates are overwritten while the default changes. `--integration-options` is rejected for already-installed targets because changing integration options requires reinstalling managed files; run `upgrade <key> --integration-options ...` first, then `use <key>`. Like `use`, `switch` rescaffolds installed extensions and presets for the target integration once it becomes the default.

## Use an Installed Integration

```bash
specify integration use <key>
```

| Option    | Description                                         |
| --------- | --------------------------------------------------- |
| `--force` | Overwrite managed shared templates while changing the default |

Sets the default integration without uninstalling any other installed integrations. This also refreshes managed shared templates so command references match the new default integration's invocation style. Modified or untracked shared templates are preserved unless `--force` is used.

`use` is also the activation point for installed extensions and presets: it re-registers every enabled extension's and preset's command overrides (and skills, for skills-mode agents) for the newly active integration, so artifacts installed while a different integration was active are rescaffolded here rather than at install time.

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

For external adapters, `upgrade --force` and `uninstall --force` can also recover
missing, modified, incompatible, or import-failing installed code using validated
user-local registrar/path ownership metadata, rejecting edited project cleanup
claims and overlap with another integration's root. Without local ownership
proof, old-only generated files are preserved with a manual-cleanup warning.
A trusted replacement can still overwrite files at its declared destination
under `upgrade --force`. Recovery is reported explicitly and does not bypass source policy
or the replacement package's trust decision. Failed lifecycle operations restore
only operation-owned changes. Independent workflow progress and unowned user
files are preserved; conflicting concurrent managed-file edits are reported with
retained recovery snapshots.
Rollback snapshots are lazy and bounded to 128 MiB of file content and 4,096
entries per operation; an oversized snapshot refuses the affected mutation.
No-op operations do not copy agent directories or the installed package store.
Custom adapters must journal writes to existing files through the host's
before-write helpers or `IntegrationManifest.record_file()`. Recording a new
or unchanged file afterward remains supported; an unobserved overwrite is
reported as unrecoverable rather than deleting the resulting file.
Host writes reject symlinked destinations and ancestors before writing; forced
removal of an owned leaf symlink unlinks only the link. Concurrent workflow
dispatch pins the requested project's adapter and verified imports until the
dispatch finishes, without serializing independent agent processes.

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

Catalogs are resolved in this order (first match wins):

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
  "schema_version": "1.0",
  "integrations": {
    "my-agent": {
      "id": "my-agent",
      "name": "My Agent",
      "author": "example",
      "version": "2.0.0",
      "description": "Current release",
      "repository": "https://example.com/my-agent/current",
      "releases": {
        "1.0.0": {
          "description": "Historical release",
          "repository": "https://example.com/my-agent/v1",
          "requires": {"speckit_version": ">=0.7"}
        }
      }
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

Some integrations accept additional options via `--integration-options`:

| Integration | Option              | Description                                                    |
| ----------- | ------------------- | -------------------------------------------------------------- |
| `generic`   | `--commands-dir`    | Required. Directory for command files                          |
| `generic`   | `--skills`          | Render commands and installed extension invocations as `speckit-<name>/SKILL.md` directories under `--commands-dir` instead of flat `speckit.<name>.md` files. Command references and next-step guidance switch to `/speckit-<name>`. |
| `kimi`      | `--migrate-legacy`  | Migrate legacy `.kimi/skills/` installs to `.kimi-code/skills/` (including dotted→hyphenated skill naming, e.g. `speckit.xxx` → `speckit-xxx`) |
| `copilot`   | `--commands`        | Scaffold `.github/agents/*.agent.md` commands with `.github/prompts/*.prompt.md` companions and merge `.vscode/settings.json` instead of using the default skills layout. |
| `copilot`   | `--skills`          | Force the default skills layout, overriding an existing commands layout during an explicit migration. |

Example:

```bash
specify integration install generic --integration-options="--commands-dir .myagent/cmds"
specify integration install generic --integration-options="--commands-dir .myagent/skills --skills"
```

Once `generic` is the active integration, `specify extension add` registers
extension commands in its configured `--commands-dir` (as command files or
skills according to `--skills`). `specify extension remove` removes unchanged
extension-owned artifacts while leaving core commands, user files, and edited
extension files intact. The core `speckit.taskstoissues` command remains
available; installing the GitHub extension adds the namespaced replacement
without deprecating or removing the core command.

## Scaffold a New Integration

```bash
specify integration scaffold <key>
```

Creates a minimal built-in integration package and a matching test skeleton in the Spec Kit repository, then prints the next steps for wiring it up. Run this command from the Spec Kit repository root. The `<key>` must be lowercase kebab-case (for example, `my-agent`).

| Option   | Description                                                       |
| -------- | ---------------------------------------------------------------- |
| `--type` | Scaffold template to use: `markdown` (default), `skills`, `toml`, or `yaml` |

## FAQ

### Can I install multiple integrations in the same project?

Yes, but it is intended for team portability rather than the default workflow. Multiple integrations are allowed automatically only when the installed integration and the new integration are declared multi-install safe by Spec Kit. For other combinations, pass `--force` to acknowledge that multiple agents may see unrelated agent-specific instructions or commands.

Spec Kit tracks one default integration in `.specify/integration.json` with `default_integration`, all installed integrations with `installed_integrations`, per-integration runtime settings with `integration_settings`, and a dedicated `integration_state_schema` for future state migrations. The legacy `integration` field remains as an alias for the default integration.

### Which integrations are multi-install safe?

An integration is multi-install safe when it uses a static, unique agent root and command directory, stable command invocation settings, and a separate install manifest whose managed files do not overlap another safe integration. Registry tests enforce those path and manifest invariants. Shared Spec Kit templates remain aligned to the single default integration.

The Command directory column below lists the directory each integration installs its commands or skills into. Context-file targeting is a separate concern from integration multi-install safety: `multi_install_safe` is an integration declaration about command/skill paths, whereas the optional agent-context extension manages a per-agent context file (for example `AGENTS.md` or `CLAUDE.md`) and can even synchronize several anchors at once via its `context_files` setting. Multiple agents mapping to the same context file is expected there and does not affect whether an integration is multi-install safe; see the agent-context extension for details.

The currently declared multi-install safe integrations are:

| Key | Command directory |
| --- | ----------------- |
| `alquimia` | `.alquimia/skills` |
| `auggie` | `.augment/commands` |
| `claude` | `.claude/skills` |
| `cline` | `.clinerules/workflows` |
| `codebuddy` | `.codebuddy/commands` |
| `codex` | `.agents/skills` |
| `command-code` | `.commandcode/skills` |
| `cursor-agent` | `.cursor/skills` |
| `droid` | `.factory/skills` |
| `firebender` | `.firebender/commands` |
| `gemini` | `.gemini/commands` |
| `grok` | `.grok/skills` |
| `junie` | `.junie/commands` |
| `kilocode` | `.kilo/commands` |
| `kiro-cli` | `.kiro/prompts` |
| `lingma` | `.lingma/skills` |
| `mcode` | `.minimax/skills` |
| `omp` | `.omp/commands` |
| `opencode` | `.opencode/commands` |
| `pi` | `.pi/prompts` |
| `qodercli` | `.qoder/skills` |
| `qwen` | `.qwen/commands` |
| `shai` | `.shai/commands` |
| `tabnine` | `.tabnine/agent/commands` |
| `trae` | `.trae/skills` |
| `zcode` | `.zcode/skills` |

Integrations that share a command directory with another integration, require dynamic install paths such as `--commands-dir`, or merge shared tool settings are not declared safe by default. They can still be installed alongside another integration with `--force`.

### What happens to my changes when I uninstall or switch?

Files you've modified are preserved automatically. Only unmodified files (matching their original SHA-256 hash) are removed. Use `--force` to override this.

### How do I know which key to use?

Run `specify integration list` to see all available integrations with their keys, or check the [Supported AI Coding Agents](#supported-ai-coding-agents) table above.

### Do I need the AI coding agent installed to use an integration?

CLI-based integrations (like Claude Code, Gemini CLI) require the tool to be installed. IDE-based integrations (like Cursor) work through the IDE itself. Some agents like GitHub Copilot support both IDE and CLI usage. `specify integration list` shows which type each integration is.

### When should I use `upgrade` vs `switch`?

Use `upgrade` when you've upgraded Spec Kit and want to refresh an installed integration's managed files. Use `switch` when you want to replace the current default with another integration; if the target is already installed, `switch` behaves like `use`.

### Do extensions and presets I install apply to every installed integration?

No. Extensions (`specify extension add`) and presets (`specify preset add`) register their command overrides for the currently active (default) integration only, even if other integrations are installed. A non-default integration does not receive those artifacts until it becomes the default: `specify integration use <key>` (or `switch <key>`) rescaffolds every enabled extension and preset for the newly active integration. `specify integration upgrade` follows the same rule — it only re-registers extensions and presets when upgrading the active integration.
