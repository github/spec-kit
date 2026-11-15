# IBM Bob

Install [IBM Bob](https://www.ibm.com/products/bob) before setup.
The integration key is `bob`; no separate CLI is required.

## Multi-Install Safety

This integration is not declared multi-install safe. See the
[shared multi-install rules](cli.md#can-i-install-multiple-integrations-in-the-same-project).

## Setup

```bash
specify init my-project --integration bob
```

For an existing Spec Kit project, use `specify integration install bob`.
See [integration management](cli.md) for activation, upgrades, and removal.

## Default Skills Layout

Skills are installed as `.bob/skills/speckit-<command>/SKILL.md`.
Bob's skills are intent-activated: ask Bob to use the `speckit-specify` skill,
or `speckit-bug-assess` for the installed bug extension. Spec Kit renders
`/speckit-<command>` references for skills-mode command dispatch, but that does
not mean each skill is a separately registered IDE slash command.

## Legacy Commands and Migration

Pass `--integration-options="--legacy-commands"` to scaffold the deprecated Bob
1.x layout (`.bob/commands/*.md`) instead. This flag will be removed in a future
release.

Existing legacy installations can migrate with:

```bash
specify integration upgrade bob --integration-options="--skills"
```

This converts the installation to the skills layout and removes the old
command files. If preset overrides are installed, migration is rejected because
preset artifacts cannot yet be reconciled across a layout change. Remove the
presets, migrate, then reinstall them.

`--skills` and `--legacy-commands` are mutually exclusive. Without an explicit
selector, managed legacy command files keep an existing installation in legacy
mode unless managed Spec Kit skills are present. Merely creating an unrelated
`.bob/skills/` directory does not migrate it. Legacy command references retain
the dotted `/speckit.<command>` form.

## Workflow Permissions

Workflow dispatch additionally requires the `bob` CLI, even though IDE setup
does not. It uses `bob run --trust --accept-license` with a positional prompt,
selecting `-f pretty` for streamed output or `-f json` for captured output.
The trust and license flags apply to this non-interactive invocation.

The adapter does not forward the workflow `model` setting; Bob selects its
model through `session.model` in its own settings.
