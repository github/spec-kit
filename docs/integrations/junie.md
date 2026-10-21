# Junie

Install [Junie](https://junie.jetbrains.com/) before setup.
The integration key is `junie`; Specify checks for its CLI.

## Multi-Install Safety

This integration is declared multi-install safe. See the
[shared multi-install rules](cli.md#can-i-install-multiple-integrations-in-the-same-project).

## Setup

```bash
specify init my-project --integration junie
```

For an existing Spec Kit project, use `specify integration install junie`.
See [integration management](cli.md) for activation, upgrades, and removal.

## Installed Commands

Markdown commands are installed under `.junie/commands/`, using hyphenated
filenames such as `speckit-specify.md`.
Invoke them in Junie's chat as `/speckit-specify` or
`/speckit-bug-assess` for the installed bug extension, not dotted commands.

Handoff references and extension/preset command content are also normalized to
hyphenated names.

## Workflow Dispatch

Workflow steps use `junie -p <prompt>`, with `--model` when configured and
`--output-format json` when structured output is requested.
There are no integration-specific setup options.
