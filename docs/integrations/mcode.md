# MiniMax Code

Install [MiniMax Code](https://github.com/MiniMax-AI/minimax-code) before setup.
The integration key is `mcode`.

## Multi-Install Safety

This integration is declared multi-install safe. See the
[shared multi-install rules](cli.md#can-i-install-multiple-integrations-in-the-same-project).

## Setup

```bash
specify init my-project --integration mcode
```

For an existing Spec Kit project, use `specify integration install mcode`.
See [integration management](cli.md) for activation, upgrades, and removal.

## Installed Skills

Skills are installed as `.minimax/skills/speckit-<command>/SKILL.md`.
Invoke them in the agent's chat, for example `/speckit-specify` or
`/speckit-bug-assess` for the installed bug extension.

The optional `--integration-options="--skills"` flag restates the default;
this integration always scaffolds skills.

## Headless Permissions

Headless workflow dispatch uses `--permission full` so tool actions are not
blocked by headless permission gating. Set
`SPECKIT_INTEGRATION_MCODE_EXTRA_ARGS="--permission smart"` to use MiniMax
Code's stricter policy.

Dispatch uses `mcode exec <prompt>`. A configured `--model` and requested
`--output-format json` are forwarded.
