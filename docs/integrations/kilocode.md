# Kilo Code

Install [Kilo Code](https://github.com/Kilo-Org/kilocode) in your IDE before setup.
The integration key is `kilocode`; no separate CLI is required.

## Multi-Install Safety

This integration is declared multi-install safe. See the
[shared multi-install rules](cli.md#can-i-install-multiple-integrations-in-the-same-project).

## Setup

```bash
specify init my-project --integration kilocode
```

For an existing Spec Kit project, use `specify integration install kilocode`.
See [integration management](cli.md) for activation, upgrades, and removal.

## Installed Commands

Markdown commands are installed under `.kilo/commands/`.
Invoke them in the agent's chat using dotted notation, for example
`/speckit.specify` or `/speckit.bug.assess` for the installed bug extension.

Legacy `.kilocode/workflows/` installations remain supported as a registration
fallback.

Upgrade migrates manifest-tracked core commands to `.kilo/commands/`. If preset
command overrides affect the legacy directory, the upgrade is refused before
changing files; remove the presets, upgrade, then reinstall them. An unreadable
preset registry also blocks that migration.

## Workflow Limitation

This integration does not support CLI dispatch for workflow command or prompt
steps. It installs IDE commands only and has no integration-specific setup
options.
