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

## Options and Workflow Dispatch

`--integration-options="--skills"` explicitly selects the skills layout, which
is already the only supported layout for this integration. Native events use
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
