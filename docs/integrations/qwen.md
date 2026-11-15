# Qwen Code

Install [Qwen Code](https://github.com/QwenLM/qwen-code) before setup.
The integration key is `qwen`.

## Multi-Install Safety

This integration is declared multi-install safe. See the
[shared multi-install rules](cli.md#can-i-install-multiple-integrations-in-the-same-project).

## Setup

```bash
specify init my-project --integration qwen
```

For an existing Spec Kit project, use `specify integration install qwen`.
See [integration management](cli.md) for activation, upgrades, and removal.

## Installed Commands

Markdown commands are installed under `.qwen/commands/`.
Invoke them in the agent's chat using dotted notation, for example
`/speckit.specify` or `/speckit.bug.assess` for the installed bug extension.

## Runtime Events and Workflow Dispatch

Native events use `.qwen/settings.json`, with hook timeouts converted to
milliseconds. `--integration-options="--events false"` disables Spec Kit event
handlers. See [runtime events](cli.md#runtime-events).

Workflow steps use `qwen -p <prompt>`, with `--model` when configured and
`--output-format json` when structured output is requested.
