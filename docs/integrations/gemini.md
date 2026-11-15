# Gemini CLI

Install [Gemini CLI](https://github.com/google-gemini/gemini-cli) before setup.
The integration key is `gemini`.

## Multi-Install Safety

This integration is declared multi-install safe. See the
[shared multi-install rules](cli.md#can-i-install-multiple-integrations-in-the-same-project).

## Setup

```bash
specify init my-project --integration gemini
```

For an existing Spec Kit project, use `specify integration install gemini`.
See [integration management](cli.md) for activation, upgrades, and removal.

## Installed Commands

TOML commands are installed as `.gemini/commands/speckit.<command>.toml`.
Invoke them in the agent's chat using dotted notation, for example
`/speckit.specify` or `/speckit.bug.assess` for the installed bug extension.

## Runtime Events and Workflow Dispatch

Native events use `.gemini/settings.json`. The integration maps prompt-submit
and stop events to `BeforeAgent` and `AfterAgent`, and converts hook timeouts
to milliseconds. `--integration-options="--events false"` disables Spec Kit
event handlers. See [runtime events](cli.md#runtime-events).

Workflow steps use `gemini -p <prompt>`, with `-m` when a model is configured
and `--output-format json` when structured output is requested.
