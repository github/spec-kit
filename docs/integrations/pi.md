# Pi Coding Agent

Install [Pi Coding Agent](https://pi.dev) before setup.
The integration key is `pi`.

## Multi-Install Safety

This integration is declared multi-install safe. See the
[shared multi-install rules](cli.md#can-i-install-multiple-integrations-in-the-same-project).

## Setup

```bash
specify init my-project --integration pi
```

For an existing Spec Kit project, use `specify integration install pi`.
See [integration management](cli.md) for activation, upgrades, and removal.

## Installed Prompts

Markdown prompts are installed under `.pi/prompts/`.
Invoke them in the agent's chat using dotted notation, for example
`/speckit.specify` or `/speckit.bug.assess` for the installed bug extension.

## Workflow Dispatch and Tooling

Workflow steps use `pi -p <prompt>`, with `--model` when configured and
`--mode json` (JSONL events), not `--output-format`, when structured output is
requested.
There are no integration-specific setup options.

This integration scaffolds prompt files; it does not install or configure MCP
servers. Commands requiring GitHub tools need that tooling configured in Pi
separately. See
[Pi extensions](https://github.com/badlogic/pi-mono/tree/main/packages/coding-agent#extensions).
