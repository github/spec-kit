# ZCode

Install [ZCode](https://zcode.z.ai/) before setup.
The integration key is `zcode`.

## Multi-Install Safety

This integration is declared multi-install safe. See the
[shared multi-install rules](cli.md#can-i-install-multiple-integrations-in-the-same-project).

## Setup

```bash
specify init my-project --integration zcode
```

For an existing Spec Kit project, use `specify integration install zcode`.
See [integration management](cli.md) for activation, upgrades, and removal.

## Installed Skills

Skills are installed as `.zcode/skills/speckit-<command>/SKILL.md`.
Invoke them in the agent's chat with a dollar prefix, for example
`$speckit-specify` or `$speckit-bug-assess` for the installed bug extension.

The optional `--integration-options="--skills"` flag restates the default;
this integration always scaffolds skills.

## Workflow Dispatch

Workflow steps use `zcode -p <prompt>` and request `--output-format json` for
structured output. The adapter ignores the workflow `model` setting because
ZCode has no per-invocation model flag; select the model in-session with `/model`.
