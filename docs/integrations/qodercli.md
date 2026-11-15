# Qoder CLI

Install [Qoder CLI](https://qoder.com/cli) before setup.
The integration key is `qodercli`.

## Multi-Install Safety

This integration is declared multi-install safe. See the
[shared multi-install rules](cli.md#can-i-install-multiple-integrations-in-the-same-project).

## Setup

```bash
specify init my-project --integration qodercli
```

For an existing Spec Kit project, use `specify integration install qodercli`.
See [integration management](cli.md) for activation, upgrades, and removal.

## Installed Skills

Skills are installed as `.qoder/skills/speckit-<command>/SKILL.md`.
Invoke them in the agent's chat, for example `/speckit-specify` or
`/speckit-bug-assess` for the installed bug extension.

The skills layout replaces legacy `.qoder/commands/` scanning. When enabled
extensions are re-registered, old flat extension command files are retired
only after their replacement skill files exist. Back up edits to those legacy
extension commands before re-registration: that retirement does not compare
their content hashes.

## Workflow Dispatch

Workflow steps use `qodercli -p <prompt>`, with `--model` when configured and
`--output-format json` when structured output is requested.
There are no integration-specific setup options; skills mode is unconditional.
