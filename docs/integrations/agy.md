# Antigravity

Install [Antigravity](https://antigravity.google/) before setup.
The integration key is `agy`. The skills layout requires Antigravity CLI
v1.0.0 or newer, or Antigravity IDE v2.0.0 or newer.

## Multi-Install Safety

This integration is not declared multi-install safe. See the
[shared multi-install rules](cli.md#can-i-install-multiple-integrations-in-the-same-project).

## Setup

```bash
specify init my-project --integration agy
```

For an existing Spec Kit project, use `specify integration install agy`.
See [integration management](cli.md) for activation, upgrades, and removal.

## Installed Skills

Skills are installed as `.agents/skills/speckit-<command>/SKILL.md`.
Invoke them in the agent's chat, for example `/speckit-specify` or
`/speckit-bug-assess` for the installed bug extension.
This directory is shared with other integrations, so do not assume their
generated skills can coexist without overlap.

## Headless Permissions

Automatic tool approval is disabled by default. In headless non-interactive
runs, explicitly enable `--dangerously-skip-permissions` by setting
`SPECKIT_AGY_ALLOW_ALL_TOOLS=1` or
`SPECKIT_INTEGRATION_AGY_ALLOW_ALL_TOOLS=1` only if you intend to authorize
tool actions without interactive approval.

## Workflow Dispatch

Workflow steps use `agy --print <prompt>`. Spec Kit supplies `--add-dir`
with the project root so skills remain discoverable, forwards a configured
`--model`, and requests `--output-format json` for structured output.
There are no integration-specific setup options.
