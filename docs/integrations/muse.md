# Muse Code

Install [Muse Code](https://dev.meta.ai/docs/muse-code) before setup.
The integration key is `muse`.

## Multi-Install Safety

This integration is not declared multi-install safe. See the
[shared multi-install rules](cli.md#can-i-install-multiple-integrations-in-the-same-project).

## Setup

```bash
specify init my-project --integration muse
```

For an existing Spec Kit project, use `specify integration install muse`.
See [integration management](cli.md) for activation, upgrades, and removal.

## Installed Skills

Skills are installed as `.agents/skills/speckit-<command>/SKILL.md`.
Invoke them in the agent's chat, for example `/speckit-specify` or
`/speckit-bug-assess` for the installed bug extension.
This directory is shared with other integrations, so do not assume their
generated skills can coexist without overlap.

The optional `--integration-options="--skills"` flag restates the default;
this integration always scaffolds skills.

## Workflow Dispatch

Workflow steps use `muse exec <prompt>`, with `--model` when configured and
`--json` when structured output is requested.
