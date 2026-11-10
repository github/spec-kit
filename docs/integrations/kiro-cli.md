# Kiro CLI

Install [Kiro CLI](https://kiro.dev/docs/cli/) before setup.
The integration key is `kiro-cli`. The executable compatibility check also
accepts `kiro`, but `kiro` is not a registered integration key.

## Multi-Install Safety

This integration is declared multi-install safe. See the
[shared multi-install rules](cli.md#can-i-install-multiple-integrations-in-the-same-project).

## Setup

```bash
specify init my-project --integration kiro-cli
```

For an existing Spec Kit project, use `specify integration install kiro-cli`.
See [integration management](cli.md) for activation, upgrades, and removal.

## Installed Prompts

Markdown prompts are installed under `.kiro/prompts/`.
Spec Kit uses dotted names such as `speckit.specify`; use Kiro's
[prompt interface](https://kiro.dev/docs/cli/chat/manage-prompts/) to select them.

Kiro CLI does not substitute `$ARGUMENTS` in file-based prompts. Spec Kit
therefore renders a prose fallback instructing the model to take the argument
from the conversation. See
[github/spec-kit#1926](https://github.com/github/spec-kit/issues/1926).

## Workflow Dispatch

Workflow steps use the `kiro-cli` executable with `-p <prompt>`, forwarding
`--model` and requesting `--output-format json` when appropriate.
Tool detection also recognizes the `kiro` executable, but the adapter's default
dispatch executable remains `kiro-cli`. If only `kiro` is available, set
`SPECKIT_INTEGRATION_KIRO_CLI_EXECUTABLE` to its path for workflow dispatch.
There are no integration-specific setup options.
