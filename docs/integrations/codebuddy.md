# CodeBuddy CLI

Install [CodeBuddy CLI](https://www.codebuddy.cn/docs/cli/installation) before setup.
The integration key is `codebuddy`.

## Multi-Install Safety

This integration is declared multi-install safe. See the
[shared multi-install rules](cli.md#can-i-install-multiple-integrations-in-the-same-project).

## Setup

```bash
specify init my-project --integration codebuddy
```

For an existing Spec Kit project, use `specify integration install codebuddy`.
See [integration management](cli.md) for activation, upgrades, and removal.

## Installed Commands

Markdown commands are installed under `.codebuddy/commands/`.
Invoke them in the agent's chat using dotted notation, for example
`/speckit.specify` or `/speckit.bug.assess` for the installed bug extension.

## Workflow Dispatch

Workflow steps use `codebuddy -p <prompt>`, with `--model` when configured and
`--output-format json` when structured output is requested.
There are no integration-specific setup options.
