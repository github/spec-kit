# Integrations

Integrations connect Spec Kit to your AI coding agent through commands, skills,
or recipes. Use [none](none.md) for shared scaffolding without an agent.
Choose an integration below for prerequisites, setup, invocation syntax,
and integration-specific options or limitations.

## Set Up Your Agent

See the [installation guide](../installation.md) for CLI prerequisites and
installation, and the [SDD quickstart](../quickstart.md) for your first process.

For a new project:

```bash
specify init my-project --integration <key>
```

Invoke process commands inside your coding agent, not in the terminal.
The documentation commonly uses `/speckit.*` notation, but your agent may use
hyphenated skills, `$` skills, or another native form. See your integration's
page and the [command invocation comparison](cli.md#command-invocation).

## Adding Another Agent

In an initialized project, use
[`specify integration install <key>`](cli.md#install-an-integration).
Check the agent's guide for its multi-install safety status and follow the
[shared multi-install rules](cli.md#can-i-install-multiple-integrations-in-the-same-project).

Installing another integration does not change the default. Use
[`specify integration use <key>`](cli.md#use-an-installed-integration)
to activate it.

## Removing an Agent

Use [`specify integration uninstall <key>`](cli.md#uninstall-an-integration)
to remove an agent's Spec Kit integration, not the agent application itself.
See the uninstall reference for modified-file handling and cleanup exceptions.

To replace an integration instead, use
[`specify integration switch <key>`](cli.md#switch-to-a-different-integration).

## Working in a Team

Mixed-agent teams can start from an agent-neutral project:

```bash
specify init my-project --integration none
```

Each developer switches to their chosen agent in their local checkout:

```bash
specify integration switch <key>
```

After development, switch back before staging the commit:

```bash
specify integration switch none
```

> [!IMPORTANT]
> Do not manually edit Spec Kit-generated agent commands or skills. Maintain
> customizations in reviewed [presets](../reference/presets.md) or
> [project-local overrides](../guides/customization.md#project-local-overrides-and-resolution).
> Before committing, use
> [`specify integration status`](cli.md#report-integration-status) to verify
> that `none` is the only installed and default integration. Review the Git diff
> and any retained agent files.

Teams can add CI checks for the committed baseline and optional pre-commit
checks of staged files.

## Choose an Integration

Use the exact key shown below with `--integration <key>`. CLI-based integrations
require the agent's CLI to be installed; IDE-based integrations run through the
agent's chat window in your IDE. Each page links to the agent's installation documentation.

| Integration | Key |
| --- | --- |
| [Alquimia AI](alquimia.md) | `alquimia` |
| [Amp](amp.md) | `amp` |
| [Antigravity](agy.md) | `agy` |
| [Auggie CLI](auggie.md) | `auggie` |
| [Claude Code](claude.md) | `claude` |
| [Cline](cline.md) | `cline` |
| [CodeBuddy CLI](codebuddy.md) | `codebuddy` |
| [Codex CLI](codex.md) | `codex` |
| [Command Code](command-code.md) | `command-code` |
| [Cursor](cursor-agent.md) | `cursor-agent` |
| [DeepSeek Harness](dsh.md) | `dsh` |
| [Devin for Terminal](devin.md) | `devin` |
| [Docker Agent](docker-agent.md) | `docker-agent` |
| [Factory Droid](droid.md) | `droid` |
| [Firebender](firebender.md) | `firebender` |
| [Forge](forge.md) | `forge` |
| [Gemini CLI](gemini.md) | `gemini` |
| [GitHub Copilot](copilot.md) | `copilot` |
| [Goose](goose.md) | `goose` |
| [Grok Build](grok.md) | `grok` |
| [Hermes](hermes.md) | `hermes` |
| [IBM Bob](bob.md) | `bob` |
| [Junie](junie.md) | `junie` |
| [Kilo Code](kilocode.md) | `kilocode` |
| [Kimi Code](kimi.md) | `kimi` |
| [Kiro CLI](kiro-cli.md) | `kiro-cli` |
| [Lingma](lingma.md) | `lingma` |
| [MiniMax Code](mcode.md) | `mcode` |
| [Mistral Vibe](vibe.md) | `vibe` |
| [Muse Code](muse.md) | `muse` |
| [None: shared scaffolding only](none.md) | `none` |
| [Oh My Pi](omp.md) | `omp` |
| [opencode](opencode.md) | `opencode` |
| [Pi Coding Agent](pi.md) | `pi` |
| [Qoder CLI](qodercli.md) | `qodercli` |
| [Qwen Code](qwen.md) | `qwen` |
| [RovoDev](rovodev.md) | `rovodev` |
| [SHAI (OVHcloud)](shai.md) | `shai` |
| [Tabnine CLI](tabnine.md) | `tabnine` |
| [Trae](trae.md) | `trae` |
| [ZCode](zcode.md) | `zcode` |
| [Zed](zed.md) | `zed` |
| [Generic: bring your own agent](generic.md) | `generic` |

## Shared Management and External Integrations

The [integration CLI reference](cli.md) documents shared
installation, upgrade, removal, status, catalogs, and default-selection behavior.
Those rules apply across integrations rather than being repeated on each page.
The individual guides also identify whether workflow CLI dispatch is supported;
an IDE setup that needs no CLI does not imply that workflow steps can run
without one.

For agents not listed here, use the [generic integration](generic.md) or
[discover an external adapter](cli.md#search-available-integrations).
Review external adapter code before authorizing its execution. Catalog discovery
is not a security endorsement; the default community catalog is discovery-only.
See [catalog-installed external adapters](cli.md#catalog-installed-external-adapters)
for trust and installation requirements.

The [catalog reference](catalog.md) describes descriptor and catalog metadata.
See [contributing integrations](contributing.md) to develop a built-in
integration or publish an external adapter.
