# Generic: Bring Your Own Agent

Use the `generic` integration for an AI coding agent not covered by a built-in
integration. Supply a project-local output directory with `--commands-dir`.
Spec Kit does not require a particular agent CLI for this integration.

## Multi-Install Safety

This integration is not declared multi-install safe because it uses dynamic
output paths. See the
[shared multi-install rules](cli.md#can-i-install-multiple-integrations-in-the-same-project).

## Setup

```bash
specify init my-project --integration generic --integration-options="--commands-dir .myagent/cmds"
```

For an existing Spec Kit project:

```bash
specify integration install generic --integration-options="--commands-dir .myagent/cmds"
```

See [integration management](cli.md) for activation, upgrades, and removal.

## Output Options and Invocation

| Option | Description |
| --- | --- |
| `--commands-dir <path>` | Required. Project-local output directory for commands or skills. |
| `--skills` | Write `speckit-<command>/SKILL.md` directories instead of flat `speckit.<command>.md` files. |

Default command references use `/speckit.specify` and `/speckit.bug.assess`.
Skills mode changes command references and next-step guidance to
`/speckit-specify` and `/speckit-bug-assess`:

```bash
specify integration install generic --integration-options="--commands-dir .myagent/skills --skills"
```

Your agent must support the selected file layout and invocation style; Spec Kit
does not add native command discovery to the agent.

## Extensions

Once `generic` is the active integration, `specify extension add` registers
extension commands in its configured `--commands-dir`, as command files or
skills according to `--skills`. `specify extension remove` removes unchanged
extension-owned artifacts while leaving core commands, user files, and edited
extension files intact.

## Workflow Limitation

The generic integration does not support CLI dispatch for workflow command or
prompt steps. Selecting an output directory does not configure an executable
or teach Spec Kit how to invoke an arbitrary agent CLI.
