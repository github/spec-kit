# None: Shared Scaffolding Only

Use the `none` integration for an agent-neutral project. It installs shared
`.specify/` scaffolding without agent-specific commands, skills, settings, or
hooks. No coding agent is required.

## Multi-Install Safety

This integration is declared multi-install safe because it generates no
agent-specific files. Other installed integrations must also be declared safe
to coexist without `--force`. See the
[shared multi-install rules](cli.md#can-i-install-multiple-integrations-in-the-same-project).

## Setup

```bash
specify init my-project --integration none
```

To replace the current default integration in an existing project:

```bash
specify integration switch none
```

If `none` is already installed, `switch` only selects it as the default;
it does not remove other integrations. See
[integration management](cli.md) for installation, activation, and cleanup.

## Shared Files and Removal

Templates, scripts, constitution, bundled workflows, and project metadata remain
available under `.specify/`. The integration's generated-file manifest is empty;
uninstalling `none` does not remove shared scaffolding or unowned files.

For an optional mixed-agent team approach, see
[Working in a Team](index.md#working-in-a-team).

## Workflow Limitation

This integration cannot dispatch workflow command or prompt steps. Switch to
an agent integration that supports CLI dispatch to run those steps.
There are no integration-specific setup options.
