# Auggie CLI

Install [Auggie CLI](https://docs.augmentcode.com/cli/overview) before setup.
The integration key is `auggie`.

## Multi-Install Safety

This integration is declared multi-install safe. See the
[shared multi-install rules](cli.md#can-i-install-multiple-integrations-in-the-same-project).

## Setup

```bash
specify init my-project --integration auggie
```

For an existing Spec Kit project, use `specify integration install auggie`.
See [integration management](cli.md) for activation, upgrades, and removal.

## Installed Commands

Markdown commands are installed under `.augment/commands/`.
Invoke them in the agent's chat using dotted notation, for example
`/speckit.specify` or `/speckit.bug.assess` for the installed bug extension.

## Workflow Dispatch

Workflow steps use `auggie -p <prompt>`, with `--model` when configured and
`--output-format json` when structured output is requested.
There are no integration-specific setup options.
