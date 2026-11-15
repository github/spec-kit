# opencode

Install [opencode](https://opencode.ai/) before setup.
The integration key is `opencode`.

## Multi-Install Safety

This integration is declared multi-install safe. See the
[shared multi-install rules](cli.md#can-i-install-multiple-integrations-in-the-same-project).

## Setup

```bash
specify init my-project --integration opencode
```

For an existing Spec Kit project, use `specify integration install opencode`.
See [integration management](cli.md) for activation, upgrades, and removal.

## Installed Commands

Markdown commands are installed under `.opencode/commands/`.
Invoke them in the agent's chat using dotted notation, for example
`/speckit.specify` or `/speckit.bug.assess` for the installed bug extension.

Legacy `.opencode/command/` installations remain a registration fallback when
the canonical directory does not exist.

## Runtime Events and Workflow Dispatch

Native events use `.opencode/plugin/speckit-events.ts` rather than a JSON hook
map; Spec Kit merges its plugin reference into `opencode.json`.
`--integration-options="--events false"` disables Spec Kit event handlers.
See [runtime events](cli.md#runtime-events).

Workflow steps use `opencode run`. Slash-prefixed prompts become
`--command <name>` with the remaining text as the message; other prompts are
passed as message text. The adapter forwards a configured model with `-m` and
requests `--format json` for structured output.
