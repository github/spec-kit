# SHAI (OVHcloud)

Install [SHAI](https://github.com/ovh/shai) before setup.
The integration key is `shai`.

## Multi-Install Safety

This integration is declared multi-install safe. See the
[shared multi-install rules](cli.md#can-i-install-multiple-integrations-in-the-same-project).

## Setup

```bash
specify init my-project --integration shai
```

For an existing Spec Kit project, use `specify integration install shai`.
See [integration management](cli.md) for activation, upgrades, and removal.

## Installed Commands

Markdown commands are installed under `.shai/commands/`, using dotted names
such as `speckit.specify.md`.

## Workflow Limitation

Workflow `command` and `prompt` steps cannot run through SHAI. Its CLI accepts
prompt text as arguments, on stdin, or through `shai agent`, but hands it to
its auto-fix agent and never loads `.shai/commands/`, so those steps fail.

The adapter explicitly declines CLI dispatch rather than reporting success
without running the installed command. There are no integration-specific
setup options.
