# DeepSeek Harness

Install [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness) before setup.
The integration key is `dsh`.

## Multi-Install Safety

This integration is declared multi-install safe. See the
[shared multi-install rules](cli.md#can-i-install-multiple-integrations-in-the-same-project).

## Setup

```bash
specify init my-project --integration dsh
```

For an existing Spec Kit project, use `specify integration install dsh`.
See [integration management](cli.md) for activation, upgrades, and removal.

## Installed Skills

Skills are installed as `.dsh/skills/speckit-<command>/SKILL.md`.
Invoke them in the agent's chat, for example `/speckit-specify` or
`/speckit-bug-assess` for the installed bug extension.

## Workflow Dispatch

Workflow steps use `dsh --profile headless <prompt>`. The adapter ignores
the workflow `model` and structured-output requests: the headless profile
returns the last assistant message as plain text.
There are no integration-specific setup options.
