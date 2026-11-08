# Nexora Code

Install the [Nexora Code](https://marketplace.visualstudio.com/items?itemName=nexora-intelligence.nexora-code)
extension for VS Code, Antigravity, or Cursor before setup (it is also published
on [Open VSX](https://open-vsx.org/extension/nexora-intelligence/nexora-code)).
The integration key is `nexora`; no separate CLI is required. The optional
companion terminal CLI (`npm i -g @nexoracode/cli`, binary `nexora`) reads the
same skills.

## Multi-Install Safety

This integration is declared multi-install safe. See the
[shared multi-install rules](cli.md#can-i-install-multiple-integrations-in-the-same-project).

## Setup

```bash
specify init my-project --integration nexora
```

For an existing Spec Kit project, use `specify integration install nexora`.
See [integration management](cli.md) for activation, upgrades, and removal.

## Installed Skills

Skills are installed as `.nexora/skills/speckit-<command>/SKILL.md`.
Invoke them in Nexora Code's chat (or the `nexora` CLI), for example
`/speckit-specify` or `/speckit-bug-assess` for the installed bug extension.

Supported core skills receive inline argument hints. Nexora Code also reads the
shared `.agents/skills/` root, so a project set up for another skills-based
agent that writes there works in Nexora Code unchanged.

## Workflow Limitation

This integration does not support CLI dispatch for workflow command or prompt
steps. It installs editor skills only and has no integration-specific setup
options; a `--skills` flag is not needed or declared. There are no other known
limitations.
