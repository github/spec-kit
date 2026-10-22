# GitHub Copilot

Set up [GitHub Copilot](https://code.visualstudio.com/) in your editor, or use
Copilot CLI. The integration key is `copilot`; a CLI is not required for IDE setup.

## Multi-Install Safety

This integration is not declared multi-install safe. See the
[shared multi-install rules](cli.md#can-i-install-multiple-integrations-in-the-same-project).

## Setup

```bash
specify init my-project --integration copilot
```

For an existing Spec Kit project, use `specify integration install copilot`.
See [integration management](cli.md) for activation, upgrades, and removal.

## Default Skills Layout

Skills are installed as `.github/skills/speckit-<command>/SKILL.md`.
Invoke them in the agent's chat as `/speckit-specify` or
`/speckit-bug-assess` for the installed bug extension. These are agent skills,
not terminal commands.

## Commands Layout

To opt into the supported commands layout:

```bash
specify init my-project --integration copilot --integration-options="--commands"
```

This installs `.agent.md` files under `.github/agents/`, companion `.prompt.md`
files under `.github/prompts/`, and merges `.vscode/settings.json`.
In this layout, Copilot CLI can select an agent through `/agents` or address
it directly in a prompt.

Use `--integration-options="--skills"` to explicitly select the default skills
layout when migrating an existing commands installation with
`specify integration upgrade copilot`. See the
[shared upgrade rules](cli.md#upgrade-an-integration),
including the restriction on changing layouts while preset artifacts are
registered.

`--skills` and `--commands` are mutually exclusive. Without an explicit layout
flag, existing managed command installations retain their layout on upgrade or
activation; a fresh installation defaults to skills.

The commands layout adds only missing VS Code settings and subkeys. Existing
values remain unchanged. If an existing settings file is JSONC or otherwise
cannot be parsed as a JSON object, the merge is skipped with a warning and
manual instructions. An existing merged settings file is retained on uninstall;
a newly created settings file is manifest-tracked.

## Runtime Events and Workflow Permissions

Native events use `.github/hooks/speckit.json`.
`--integration-options="--events false"` disables Spec Kit event handlers.
See [runtime events](cli.md#runtime-events).

Workflow steps require Copilot CLI separately from the IDE setup. In skills
mode, command steps pass `/speckit-<command>` in the prompt. In commands mode,
they select `--agent speckit.<command>` and pass the user's arguments as the
prompt rather than treating agent files as slash commands.

Headless dispatch adds `--yolo` by default, allowing tools, paths, and URLs
without interactive approval. Set `SPECKIT_COPILOT_ALLOW_ALL_TOOLS=0` to stop
Spec Kit from adding this flag. The deprecated `SPECKIT_ALLOW_ALL_TOOLS` is
accepted only as a fallback. A configured `--model` and requested
`--output-format json` are forwarded.
