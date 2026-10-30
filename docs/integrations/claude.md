# Claude Code

Install [Claude Code](https://www.anthropic.com/claude-code) before setup.
The integration key is `claude`.

## Multi-Install Safety

This integration is declared multi-install safe. See the
[shared multi-install rules](cli.md#can-i-install-multiple-integrations-in-the-same-project).

## Setup

```bash
specify init my-project --integration claude
```

For an existing Spec Kit project, use `specify integration install claude`.
See [integration management](cli.md) for activation, upgrades, and removal.

## Installed Skills

Skills are installed as `.claude/skills/speckit-<command>/SKILL.md`.
Invoke them in Claude's chat, for example `/speckit-specify` or
`/speckit-bug-assess` for the installed bug extension.

## User-Invocable-Only Skills

By default every Spec Kit skill installed for Claude Code is model-invocable, so
its description is always in Claude's context and counts toward the
skill-listing budget. In projects with many skills this can push other skills
out of the listing. To make the core Spec Kit command skills user-invocable
only:

```bash
specify init my-project --integration claude --integration-options="--no-model-invocation"
```

This writes `disable-model-invocation: true` into the core command skills.
Claude can run them only when the user invokes `/speckit-<command>`, and their
descriptions stay out of its context.

- Extension skills stay model-invocable, because mandatory extension hooks rely
  on the model invoking them. If an extension's mandatory hook runs a core
  command (its `command:` is a core `speckit.<command>`), leave this option off:
  the model cannot run that hook while the core skill is user-invocable only.
- The option is stored with the integration's other options and reapplied by
  `specify integration upgrade claude`. Passing `--integration-options` to
  `upgrade` replaces all stored options, so repeat any you want to keep (for
  example `--integration-options="--events false --no-model-invocation"`);
  `--integration-options=""` clears them. Re-running `specify init` likewise
  stores only the options passed to it.
- Core command skills that a preset overrides, or stops overriding, are reverted
  to the default by commands that re-register preset skills without reinstalling
  Claude: commands that install, remove or update presets (including `specify
  bundle` commands that carry presets), `specify integration use claude`, and
  `specify integration switch claude` when Claude is installed but not the
  default. To reapply the option, run `specify integration upgrade claude`
  while Claude is the default integration. Managed preset changes do not require
  `--force`; local edits to tracked files still block upgrade unless you
  explicitly use `--force` to overwrite them.

## Runtime Events and Workflow Dispatch

The integration supports native events through `.claude/settings.json`.
Use `--integration-options="--events false"` to disable Spec Kit event handlers;
combine it with `--no-model-invocation` if both settings are wanted.
See [runtime events](cli.md#runtime-events).

Workflow steps use `claude -p <prompt>`, with `--model` when configured and
`--output-format json` when structured output is requested. This adapter does
not add a permission-bypass flag itself.
