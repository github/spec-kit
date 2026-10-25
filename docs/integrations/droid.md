# Factory Droid

Install [Factory Droid](https://docs.factory.ai/cli/getting-started/overview) before setup.
The integration key is `droid`.

## Multi-Install Safety

This integration is declared multi-install safe. See the
[shared multi-install rules](cli.md#can-i-install-multiple-integrations-in-the-same-project).

## Setup

```bash
specify init my-project --integration droid
```

For an existing Spec Kit project, use `specify integration install droid`.
See [integration management](cli.md) for activation, upgrades, and removal.

## Installed Skills

Skills are installed as `.factory/skills/speckit-<command>/SKILL.md`.
Invoke them in the agent's chat, for example `/speckit-specify` or
`/speckit-bug-assess` for the installed bug extension.

Generated skills are both user- and model-invocable by default.

## User-Invocable-Only Skills

To stop Droid invoking the core Spec Kit command skills automatically:

```bash
specify init my-project --integration droid --integration-options="--no-model-invocation"
```

This writes `disable-model-invocation: true` into the core command skills.
Droid runs them only when the user invokes `/speckit-<command>`. Factory's
[skills documentation](https://docs.factory.com/cli/configuration/skills) does
not say whether a skill with this flag keeps its description out of Droid's
context.

- Extension skills stay model-invocable, because mandatory extension hooks rely
  on the model invoking them. If an extension's mandatory hook runs a core
  command (its `command:` is a core `speckit.<command>`), leave this option off:
  the model cannot run that hook while the core skill is user-invocable only.
- The option is stored with the integration's other options and reapplied by
  `specify integration upgrade droid`. Passing `--integration-options` to
  `upgrade` replaces all stored options; `--integration-options=""` clears
  them. Re-running `specify init` likewise stores only the options passed to it.
- Core command skills that a preset overrides, or stops overriding, are reverted
  to the default by commands that re-register preset skills without reinstalling
  Droid: commands that install, remove or update presets (including `specify
  bundle` commands that carry presets), `specify integration use droid`, and
  `specify integration switch droid` when Droid is installed but not the
  default. To reapply the option, run `specify integration upgrade droid
  --force` while Droid is the default integration (`--force` is needed because
  those commands modify installed skill files, and it overwrites local edits to
  Spec Kit-managed files).

## Workflow Dispatch

Workflow steps use `droid exec <prompt>`, forwarding `--model` and requesting
`--output-format json` when appropriate. Spec Kit does not add a
permission-bypass flag. Operators can explicitly configure permission flags
through `SPECKIT_INTEGRATION_DROID_EXTRA_ARGS`; those arguments follow Spec
Kit's model/output flags and may override them under duplicate-flag parsing.
The only integration-specific setup option is `--no-model-invocation`.
