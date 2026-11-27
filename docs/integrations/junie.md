# Junie

Install [Junie](https://junie.jetbrains.com/) before setup.
The integration key is `junie`; Specify checks for its CLI.

## Multi-Install Safety

This integration is declared multi-install safe. See the
[shared multi-install rules](cli.md#can-i-install-multiple-integrations-in-the-same-project).

## Setup

```bash
specify init my-project --integration junie
```

For an existing Spec Kit project, use `specify integration install junie`.
See [integration management](cli.md) for activation, upgrades, and removal.

## Installed Commands

Markdown commands are installed under `.junie/commands/`, using hyphenated
filenames such as `speckit-specify.md`.
Invoke them in Junie's chat as `/speckit-specify` or
`/speckit-bug-assess` for the installed bug extension, not dotted commands.

Handoff references and extension/preset command content are also normalized
to hyphenated command names, so `/speckit.git.commit` in an extension command
becomes `/speckit-git-commit`. Path-qualified names, quoted paths, and
bracketed or dotted directory segments—such as
`.specify/extensions/git/commands/speckit.git.commit.md`,
`scripts/speckit.git.commit.sh`, `scripts/run-speckit.git.commit.sh`,
`scripts/C++/speckit.git.commit.sh`, `"scripts/my speckit.git.commit.sh"`,
`commands/[old]speckit.git.commit.md`,
`speckit.demo[old]/commands/speckit.git.commit.md`,
`/tmp/speckit.demo/commands/speckit.git.commit.md`, `C:\speckit.foo.md`,
`C:\Program Files (x86)\speckit.foo.md`,
`C:\Program Files (old versions)\speckit.foo.md`, `%TEMP%\speckit.foo.md`,
`./commands[old]/speckit.foo.md`, and
`./commands[old files]/speckit.foo.md`—keep their dots.
A bare or slash-prefixed token such as `/speckit.foo.md` is treated as a
command reference and hyphenated. Core command content is not rewritten this
way.

## Workflow Dispatch

Workflow steps use `junie --task <prompt>`, with `--model` when configured and
`--output-format json` when structured output is requested.
There are no integration-specific setup options.
