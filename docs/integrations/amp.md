# Amp

Install the [Amp CLI](https://ampcode.com/) before setup.
The integration key is `amp`.

## Multi-Install Safety

This integration is not declared multi-install safe. See the
[shared multi-install rules](cli.md#can-i-install-multiple-integrations-in-the-same-project).

## Setup

```bash
specify init my-project --integration amp
```

For an existing Spec Kit project, use `specify integration install amp`.
See [integration management](cli.md) for activation, upgrades, and removal.

## Installed Commands

Markdown commands are installed under `.agents/commands/`.
Invoke them in the agent's chat using dotted notation, for example
`/speckit.specify` or `/speckit.bug.assess` for the installed bug extension.

## Workflow Dispatch

Workflow steps use `amp --execute <prompt>`, adding `--stream-json` when
structured output is requested. The integration does not forward the workflow
`model` setting: Amp's `--mode` selects an agent mode, not a model.
There are no integration-specific setup options.
