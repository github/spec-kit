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
  The exception is `uninstall --force` or `switch --force`, which deletes a
  generated file you edited as it does any other modified file. When the
  policy is added or removed, such a file is rewritten as plain YAML, so its
  comments and formatting are not kept. It is rewritten in place, so its
  owner, group and access-control list are kept; a read-only file, or one with
  other hard links, is refused instead, as is one that changes while Spec Kit
  is updating it. On Windows an existing file is never rewritten, because its
  backup (below) could not be kept as private as the file: setup stops with an
  error naming it, and uninstall leaves the policy in it with a warning. Add
  `policy.allow_implicit_invocation: false` to such a file yourself, or move it
  aside, and run the command again.
  Its values are read and written by the YAML 1.2 rules Codex uses, so
  unquoted values such as `On` or `no` stay strings and numbers such as `007`
  keep their text. One that already sets it to `false` is left untouched, and
  so is a tracked file that still holds it. If uninstall cannot remove the
  policy from your own file, it logs a warning naming the file so you can
  remove it by hand. If an existing file cannot be read, is not valid YAML, is
  not a mapping, repeats a key or has keys that would merge into one (such as
  `true` and `1`), or has a field Codex would reject (for example
  `interface` or `dependencies.tools` of the wrong type, which makes Codex
  ignore the whole file), setup stops with an error naming the file and leaves
  it unchanged; `specify integration install`, `switch` and `upgrade` check this before
  changing anything, so a refused switch keeps the current integration. Setup
  with the option also stops before writing anything if
  `.agents`, `.agents/skills` or a core `speckit-<command>` skill directory is a
  symlink, or if a path where a policy goes is a file rather than a directory.
  Once the policy has been removed from a file Spec Kit no longer tracks it, so
  a policy you set there yourself afterwards is never removed. If writing or
  removing policies fails part-way through setup, the policies it had already
  written are undone. If Spec Kit is stopped while rewriting a file, the
  previous content is left beside it as `openai.yaml.speckit-backup`. While
  that backup exists, setup stops with an error and policy cleanup, including
  uninstall, leaves both files alone, so neither is lost: compare the two, keep
  the right content in `openai.yaml`, delete the backup and run the command
  again. A file is never written through a symlinked directory, even one
  swapped in while the rewrite runs.
- Core command skills registered without running Codex's `setup()` get no
  `agents/openai.yaml`: those registered by commands that install, remove or
  update presets (including `specify bundle` commands that carry presets),
  `specify integration use codex`, and `specify integration switch codex` when
  Codex is installed but not the default. To add the policy, run `specify
  integration upgrade codex --force` while Codex is the default integration.
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

## Workflow Dispatch Settings

Command and prompt steps can set
[`reasoning_effort` and `context_size`](../workflow-steps/types.md#reasoning-effort-and-context-size).
Codex dispatch passes them as configuration overrides after `--model`:

| Step setting | Codex CLI argument | Values |
|---|---|---|
| `reasoning_effort` | `-c model_reasoning_effort="<value>"` | A level the selected model supports, such as `low`, `medium`, `high`, or `xhigh` |
| `context_size` | `-c model_context_window=<value>` | A token count: a positive whole number without leading zeros, at most `9223372036854775807` |

Spec Kit passes `reasoning_effort` through unchanged; Codex CLI 0.165.0
forwards it to the model without checking it. Codex displays the reasoning
effort it is given, so set it from a literal or a workflow input, not from
captured output. A `context_size` that is not a valid token count fails the
step before Codex starts.

`context_size` overrides the context window that Codex assumes for the model.
Codex clamps the value to the model's maximum, and a value below the model's
default shrinks the usable context.
