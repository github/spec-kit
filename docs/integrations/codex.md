# Codex CLI

Install [Codex CLI](https://github.com/openai/codex) before setup.
The integration key is `codex`.

## Multi-Install Safety

This integration is declared multi-install safe. See the
[shared multi-install rules](cli.md#can-i-install-multiple-integrations-in-the-same-project).

## Setup

```bash
specify init my-project --integration codex
```

For an existing Spec Kit project, use `specify integration install codex`.
See [integration management](cli.md) for activation, upgrades, and removal.

## Installed Skills

Skills are installed as `.agents/skills/speckit-<command>/SKILL.md`.
Invoke them in Codex's chat with a dollar prefix, for example `$speckit-specify`
or `$speckit-bug-assess` for the installed bug extension.
Other integrations also target `.agents/skills/`; review
[shared multi-install rules](cli.md#can-i-install-multiple-integrations-in-the-same-project)
before installing another agent that shares this directory.

## User-Invocable-Only Skills

To stop Codex invoking the core Spec Kit command skills implicitly:

```bash
specify init my-project --integration codex --integration-options="--no-model-invocation"
```

This writes `agents/openai.yaml` with `policy.allow_implicit_invocation: false`
next to each core command skill. OpenAI's
[skills documentation](https://learn.chatgpt.com/docs/build-skills) says Codex
then does not invoke the skill implicitly from the prompt, and explicit `$skill`
invocation still works. It does not say whether such a skill keeps its name and
description in Codex's context.

- Extension skills stay model-invocable, because mandatory extension hooks rely
  on the model invoking them. If an extension's mandatory hook runs a core
  command (its `command:` is a core `speckit.<command>`), leave this option off:
  the model cannot run that hook while the core skill is user-invocable only.
- The option is stored with the integration's other options and reapplied by
  `specify integration upgrade codex`. Passing `--integration-options` to
  `upgrade` replaces all stored options (to keep both, pass
  `--integration-options="--events false --no-model-invocation"`);
  `--integration-options=""` clears them and undoes the policy. Re-running
  `specify init` likewise stores only the options passed to it, and re-running
  it without the option undoes the policy too.
- Undoing the policy (clearing the option or `specify integration uninstall
  codex`) deletes the `agents/openai.yaml` files Spec Kit generated. An
  `agents/openai.yaml` that already existed, or that you edited, keeps its other
  keys: only `policy.allow_implicit_invocation` is set, and later removed again.
  Such a file is rewritten as plain YAML, so its comments and formatting are
  not kept. One that already sets it to `false` is left untouched. If an existing file
  cannot be read, is not valid YAML, or is not a mapping, setup stops with an
  error naming the file and leaves it unchanged. Skills that commands other than
  `init`, `install` and `upgrade` register (for example presets that add core
  skills) get no `agents/openai.yaml` until `specify integration upgrade codex
  --force` is run.
- Preset overrides rewrite only `SKILL.md`, so the sibling `agents/openai.yaml`
  of an overridden core skill is left in place.

## Options and Workflow Dispatch

`--integration-options="--skills"` explicitly selects the skills layout, which
is already the only supported layout for this integration, and
`--no-model-invocation` is described above. Native events use
`.codex/config.toml`; `--events false` disables Spec Kit event handlers.
See [runtime events](cli.md#runtime-events).

Workflow steps use `codex exec <prompt>`, with `--model` when configured and
`--json` when structured output is requested. Codex dev-mode registration writes
skill files rather than symlinking them.
