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
