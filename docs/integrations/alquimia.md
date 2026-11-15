# Alquimia AI

Install the [Alquimia AI CLI](https://docs.alquimia.ai) before setup.
The integration key is `alquimia`.

## Multi-Install Safety

This integration is declared multi-install safe. See the
[shared multi-install rules](cli.md#can-i-install-multiple-integrations-in-the-same-project).

## Setup

```bash
specify init my-project --integration alquimia
```

For an existing Spec Kit project, use `specify integration install alquimia`.
See [integration management](cli.md) for activation, upgrades, and removal.

## Installed Skills

Skills are installed as `.alquimia/skills/speckit-<command>/SKILL.md`.
Invoke them in the agent's chat, for example `/speckit-specify` or
`/speckit-bug-assess` for the installed bug extension.

Generated skills are both user- and model-invocable; supported core skills also
receive inline argument hints.

## Workflow Dispatch

Workflow command and prompt steps use `alquimia -p <prompt>`, with `--model`
when configured and `--output-format json` when structured output is requested.
There are no integration-specific setup options.
