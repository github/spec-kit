# Tabnine CLI

Install [Tabnine CLI](https://docs.tabnine.com/main/getting-started/tabnine-cli) before setup.
The integration key is `tabnine`.

## Multi-Install Safety

This integration is declared multi-install safe. See the
[shared multi-install rules](cli.md#can-i-install-multiple-integrations-in-the-same-project).

## Setup

```bash
specify init my-project --integration tabnine
```

For an existing Spec Kit project, use `specify integration install tabnine`.
See [integration management](cli.md) for activation, upgrades, and removal.

## Installed Commands

TOML commands are installed as `.tabnine/agent/commands/speckit.<command>.toml`.
Invoke them in the agent's chat using dotted notation, for example
`/speckit.specify` or `/speckit.bug.assess` for the installed bug extension.

## Runtime Events and Workflow Dispatch

Native events use `.tabnine/agent/settings.json`, mapping prompt-submit and stop
events to `BeforeAgent` and `AfterAgent`. Hook timeouts are converted to
milliseconds. `--integration-options="--events false"` disables Spec Kit event
handlers. See [runtime events](cli.md#runtime-events).

Workflow steps use `tabnine -p <prompt>`, with `-m` when a model is configured
and `--output-format json` when structured output is requested.
