# Hermes

Install [Hermes Agent](https://github.com/NousResearch/hermes-agent) before setup.
The integration key is `hermes`.

## Multi-Install Safety

This integration is not declared multi-install safe. Its skills are shared across
projects in the same user's home directory. See the
[shared multi-install rules](cli.md#can-i-install-multiple-integrations-in-the-same-project).

## Setup

```bash
specify init my-project --integration hermes
```

For an existing Spec Kit project, use `specify integration install hermes`.
See [integration management](cli.md) for activation, upgrades, and removal.

## Installed Skills

Unlike project-local skills integrations, Hermes installs skills globally as
`~/.hermes/skills/speckit-<command>/SKILL.md`.
Invoke them in Hermes's chat, for example `/speckit-specify` or
`/speckit-bug-assess` for the installed bug extension.

An empty project-local `.hermes/skills/` marker enables integration detection;
the generated core skill files themselves are not copied into the project.
The optional `--integration-options="--skills"` flag restates the default.

## Global Ownership and Removal

Setup can replace another project's global Spec Kit skill files.

**Uninstall removes every global `speckit-*` skill directory, even if edited
and even without `--force`.** These global files are not protected by the
project-local manifest's modified-file checks. Back up customizations before
uninstalling or switching away from Hermes. An empty project-local marker is
also removed; non-Spec-Kit global skills remain.

## Workflow Dispatch

Workflow steps use `hermes chat -Q`. Slash-prefixed prompts select a skill with
`-s`; remaining text is passed with `-q`. Other prompts use `-q` directly.
The adapter forwards a configured model with `-m` and requests `--json` for
structured output.
