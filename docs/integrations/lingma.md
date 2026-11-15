# Lingma

Install [Lingma](https://lingma.aliyun.com/) in your IDE before setup.
The integration key is `lingma`; no separate CLI is required.

## Multi-Install Safety

This integration is declared multi-install safe. See the
[shared multi-install rules](cli.md#can-i-install-multiple-integrations-in-the-same-project).

## Setup

```bash
specify init my-project --integration lingma
```

For an existing Spec Kit project, use `specify integration install lingma`.
See [integration management](cli.md) for activation, upgrades, and removal.

## Installed Skills

Skills are installed automatically as `.lingma/skills/speckit-<command>/SKILL.md`.
Invoke them in the agent's chat, for example `/speckit-specify` or
`/speckit-bug-assess` for the installed bug extension.

The optional `--integration-options="--skills"` flag restates the default;
this integration always scaffolds skills.

## Workflow Limitation

This integration does not support CLI dispatch for workflow command or prompt
steps; its supported path is the IDE skills interface.
