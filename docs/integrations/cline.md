# Cline

Install [Cline](https://github.com/cline/cline) in your IDE before setup.
The integration key is `cline`; no separate CLI is required.

## Multi-Install Safety

This integration is declared multi-install safe. See the
[shared multi-install rules](cli.md#can-i-install-multiple-integrations-in-the-same-project).

## Setup

```bash
specify init my-project --integration cline
```

For an existing Spec Kit project, use `specify integration install cline`.
See [integration management](cli.md) for activation, upgrades, and removal.

## Installed Commands

Markdown workflows are installed under `.clinerules/workflows/`, using
hyphenated filenames such as `speckit-specify.md`.
Invoke them in Cline's chat as `/speckit-specify` or
`/speckit-bug-assess` for the installed bug extension, not dotted commands.

Handoff references and extension/preset command content are also normalized
to hyphenated command names, so `/speckit.git.commit` in an extension command
becomes `/speckit-git-commit`. A `speckit.*.md` file name inside a path, such
as `.specify/extensions/git/commands/speckit.git.commit.md`,
`C:\speckit.foo.md`, `C:\Program Files (x86)\speckit.foo.md`,
`%TEMP%\speckit.foo.md`, or `./commands[old]/speckit.foo.md`, keeps its dots
and `.md` extension. A bare or
slash-prefixed token such as `/speckit.foo.md` is treated as a command
reference and hyphenated. Core command content is not rewritten this way.

## Workflow Limitation

This integration does not support CLI dispatch for workflow command or prompt
steps. It installs IDE workflows only and has no integration-specific setup
options.
