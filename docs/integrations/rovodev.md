# RovoDev

Install [RovoDev](https://www.atlassian.com/software/rovo-dev) before setup.
The integration key is `rovodev`; runtime dispatch uses `acli rovodev`.

## Multi-Install Safety

This integration is not declared multi-install safe. See the
[shared multi-install rules](cli.md#can-i-install-multiple-integrations-in-the-same-project).

## Setup

```bash
specify init my-project --integration rovodev
```

For an existing Spec Kit project, use `specify integration install rovodev`.
See [integration management](cli.md) for activation, upgrades, and removal.

## Installed Skills and Prompts

The integration generates `.rovodev/skills/`, prompt wrappers under
`.rovodev/prompts/`, and `.rovodev/prompts.yml`.
Skills use the `speckit-<command>/SKILL.md` layout. Invoke them in the agent's
chat as `/speckit-specify` or `/speckit-bug-assess` for the installed bug extension.

Prompt wrappers contain `use skill <name> $ARGUMENTS`. Setup merges manifest
entries by name: generated entries replace matching entries while unmatched
user entries retain their ordering. The merged `prompts.yml` is tracked as a
whole file: if unchanged since setup it is removed on uninstall, even when it
contains previously merged user entries. Back up that manifest if needed.

## Workflow Dispatch

Workflow steps use `acli rovodev run <prompt>`. The executable override
`SPECKIT_INTEGRATION_ROVODEV_EXECUTABLE` replaces `acli`, not the `rovodev`
subcommand. Structured-output requests add `--output-schema` with a result
object schema. The workflow `model` setting is not forwarded.
There are no integration-specific setup options; skills mode is unconditional.
