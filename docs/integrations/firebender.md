# Firebender

Install [Firebender](https://firebender.com/) in Android Studio or IntelliJ
before setup. The integration key is `firebender`; no separate CLI is required.

## Multi-Install Safety

This integration is declared multi-install safe. See the
[shared multi-install rules](cli.md#can-i-install-multiple-integrations-in-the-same-project).

## Setup

```bash
specify init my-project --integration firebender
```

For an existing Spec Kit project, use `specify integration install firebender`.
See [integration management](cli.md) for activation, upgrades, and removal.

## Installed Commands

Commands are installed as `.firebender/commands/speckit.<command>.mdc`.
Invoke them in the agent's chat using dotted notation, for example
`/speckit.specify` or `/speckit.bug.assess` for the installed bug extension.

## Workflow Limitation

This integration does not support CLI dispatch for workflow command or prompt
steps. It installs IDE commands only and has no integration-specific setup
options.
