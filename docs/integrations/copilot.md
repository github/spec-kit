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
not terminal commands. Generated skills are both user- and model-invocable by
default.

## User-Invocable-Only Skills

To stop Copilot loading the core Spec Kit command skills automatically in the
skills layout:

```bash
specify init my-project --integration copilot --integration-options="--no-model-invocation"
```

This writes `disable-model-invocation: true` into the core command skills.
VS Code's [agent skills documentation](https://code.visualstudio.com/docs/agent-customization/agent-skills)
says this requires manual invocation through the `/` slash command only.
GitHub's Copilot CLI skills documentation does not list the field, but in a
manual check with Copilot CLI 1.0.70 the model called its `skill` tool for
`speckit-specify` without the flag and did not with it, and an explicit
`/speckit-specify` still ran. With the flag the model could still read the
skill's `SKILL.md` as an ordinary file, so it is not a hard block. Neither
source says whether a skill with this flag keeps its description out of the
model's context.

- The option has no effect with `--commands`: the `.agent.md` and `.prompt.md`
  files are not skills and no flag is written.
- Extension skills stay model-invocable, because mandatory extension hooks rely
  on the model invoking them. If an extension's mandatory hook runs a core
  command (its `command:` is a core `speckit.<command>`), leave this option off:
  the model cannot run that hook while the core skill is user-invocable only.
- The option is stored with the integration's other options and reapplied by
  `specify integration upgrade copilot`. Passing `--integration-options` to
  `upgrade` replaces all stored options;
  `--integration-options=""` clears them. Re-running `specify init` likewise
  stores only the options passed to it.
- Core command skills that a preset overrides, or stops overriding, are reverted
  to the default by commands that re-register preset skills without reinstalling
  Copilot: commands that install, remove or update presets (including `specify
  bundle` commands that carry presets), `specify integration use copilot`, and
  `specify integration switch copilot` when Copilot is installed but not the
  default. To reapply the option, run `specify integration upgrade copilot
  --force` while Copilot is the default integration (`--force` is needed because
  those commands modify installed skill files, and it overwrites local edits to
  Spec Kit-managed files).

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
