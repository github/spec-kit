# Mistral Vibe

Install [Mistral Vibe](https://github.com/mistralai/mistral-vibe) before setup.
The integration key is `vibe`. The skills layout requires Mistral Vibe
v2.0.0 or newer.

## Multi-Install Safety

This integration is declared multi-install safe. See the
[shared multi-install rules](cli.md#can-i-install-multiple-integrations-in-the-same-project).

## Setup

```bash
specify init my-project --integration vibe
```

For an existing Spec Kit project, use `specify integration install vibe`.
See [integration management](cli.md) for activation, upgrades, and removal.

## Installed Skills

Skills are installed as `.vibe/skills/speckit-<command>/SKILL.md`.
Invoke them in the agent's chat, for example `/speckit-specify` or
`/speckit-bug-assess` for the installed bug extension.

Generated skills are both user- and model-invocable by default. The optional
`--integration-options="--skills"` flag restates the default.

## User-Invocable-Only Skills

To stop Mistral Vibe invoking the core Spec Kit command skills automatically:

```bash
specify init my-project --integration vibe --integration-options="--no-model-invocation"
```

This writes `disable-model-invocation: true` into the core command skills.
Per Mistral Vibe's [README](https://github.com/mistralai/mistral-vibe#skills-system),
such a skill is explicit-only: you can still invoke `/speckit-<command>`, but
the model does not see or invoke it automatically.

- Extension skills stay model-invocable, because mandatory extension hooks rely
  on the model invoking them. If an extension's mandatory hook runs a core
  command (its `command:` is a core `speckit.<command>`), leave this option off:
  the model cannot run that hook while the core skill is user-invocable only.
- The option is stored with the integration's other options and reapplied by
  `specify integration upgrade vibe`. Passing `--integration-options` to
  `upgrade` replaces all stored options; `--integration-options=""` clears
  them. Re-running `specify init` likewise stores only the options passed to it.
- Core command skills that a preset overrides, or stops overriding, are reverted
  to the default by commands that re-register preset skills without reinstalling
  Mistral Vibe: commands that install, remove or update presets (including
  `specify bundle` commands that carry presets), `specify integration use vibe`,
  and `specify integration switch vibe` when Mistral Vibe is installed but not
  the default. To reapply the option, run `specify integration upgrade vibe`
  while Mistral Vibe is the default integration. Managed preset changes do not
  require `--force`; local edits to tracked files still block upgrade unless you
  explicitly use `--force` to overwrite them.

## Runtime Events

Native events use `.vibe/hooks.toml`. Vibe supports only `pre_tool_use`,
`post_tool_use`, and `stop`, mapped to `pre_tool`, `post_tool`, and `post_agent`.
Session-start, session-end, and prompt-submit events are not emitted for Vibe;
unsupported handlers are skipped with a warning.
`--integration-options="--events false"` disables Spec Kit event handlers.
See [runtime events](cli.md#runtime-events).

Spec Kit refreshes and removes only the `[[hooks]]` entries it wrote, which
carry `speckit_marker = true`. Each entry ends after its last TOML line and the
blank lines right after it, so a comment that follows a Spec Kit entry, such as
a note above your own hook, stays in the file. If removing Spec Kit's entries
leaves only comments and blank lines, Spec Kit deletes `.vibe/hooks.toml`, and
those comments are deleted with it. Spec Kit applies the same rule to Codex's
`.codex/config.toml`.

## Workflow Dispatch

Workflow steps use `vibe -p <prompt>` and request `--output json` for structured
output. The adapter ignores the workflow `model` setting. Select the model with
Vibe's `active_model` configuration or `VIBE_ACTIVE_MODEL` instead.
