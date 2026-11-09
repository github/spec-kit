# Oh My Pi

Install [Oh My Pi](https://www.npmjs.com/package/@oh-my-pi/pi-coding-agent) before setup.
The integration key is `omp`.

## Multi-Install Safety

This integration is declared multi-install safe. See the
[shared multi-install rules](cli.md#can-i-install-multiple-integrations-in-the-same-project).

## Setup

```bash
specify init my-project --integration omp
```

For an existing Spec Kit project, use `specify integration install omp`.
See [integration management](cli.md) for activation, upgrades, and removal.

## Installed Commands

Markdown slash commands are installed under `.omp/commands/`.
Invoke them in the agent's chat using dotted notation, for example
`/speckit.specify` or `/speckit.bug.assess` for the installed bug extension.

## Workflow Dispatch

Workflow steps use `omp --print <prompt>`; `--print` enables one-shot mode
and the prompt is positional. The adapter forwards a configured `--model` and
uses `--mode json`, not `--output-format`, for structured output.
There are no integration-specific setup options.
