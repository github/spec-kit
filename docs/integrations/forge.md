# Forge

Install [Forge](https://forgecode.dev/) before setup.
The integration key is `forge`.

## Multi-Install Safety

This integration is not declared multi-install safe. See the
[shared multi-install rules](cli.md#can-i-install-multiple-integrations-in-the-same-project).

## Setup

```bash
specify init my-project --integration forge
```

For an existing Spec Kit project, use `specify integration install forge`.
See [integration management](cli.md) for activation, upgrades, and removal.

## Installed Commands

Markdown commands are installed under `.forge/commands/`, using dotted
filenames such as `speckit.specify.md`. Their frontmatter command names are
hyphenated, such as `speckit-specify`; filenames and invocation names differ.
Invoke them in the agent's chat as `/speckit-specify` or
`/speckit-bug-assess` for the installed bug extension, not dotted commands.

Forge templates use `{{parameters}}` for arguments. Spec Kit strips incompatible
`handoffs` frontmatter during core setup.

## Workflow Dispatch

Workflow steps use `forge -p <prompt>`. The adapter does not forward a configured
`model` or add a structured-output flag. Select the model in Forge's own
configuration, for example with `forge config set model`.
There are no integration-specific setup options.
