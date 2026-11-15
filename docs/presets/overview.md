# Presets

Presets are stackable, priority-ordered customizations of Spec Kit templates,
commands, and scripts. Use them to enforce organizational standards, adapt a
Spec Kit process to your methodology, or change terminology without forking
core files. Extensions add capabilities; presets change how existing
capabilities work.

> [!IMPORTANT]
> Vet a third-party preset's source before installing it. Community catalogs
> are discovery channels, not security endorsements. Maintainers check catalog
> entries for completeness and format; they do not review, audit, endorse, or
> support community preset code.

## Quick start

Run preset commands inside a project initialized with `specify init`:

```bash
# Discover presets without installing them
specify preset search
specify preset info lean

# Install a bundled preset
specify preset add lean

# Inspect installed presets and template resolution
specify preset list
specify preset resolve spec-template

# Remove it and restore the surviving layers
specify preset remove lean
```

For a preset you have authored or vetted, install a local copy with
`specify preset add --dev ./my-preset`, or a pinned release archive with
`specify preset add --from <archive-url>`. Local installs copy the source;
they are not live links to the development directory. A community search
result does not itself permit installation by ID.

## How presets take effect

Templates define what gets produced, such as a specification or plan.
Commands contain the instructions your coding agent follows to produce it.
Scripts provide executable behavior and require the same scrutiny as other
code you install.

Each logical file name is resolved independently through these layers:

| Precedence | Layer |
| --- | --- |
| Highest | Project-local overrides in `.specify/templates/overrides/` |
| Next | Enabled presets, ordered by priority, then preset ID |
| Next | Enabled extension contributions, ordered by priority, then extension ID |
| Lowest | Spec Kit core defaults |

Lower priority numbers take precedence. Preset and extension priorities order
entries within their own layer; an extension cannot outrank the preset layer
by choosing a smaller number.

Templates and scripts are resolved when needed. Commands are materialized as
command files or skills for the active integration during installation and
reconciliation; agents do not resolve the stack on each invocation. Switching
the default integration rescaffolds enabled presets for that integration.
The generic integration does not register preset command or skill overrides.

With no preset installed, the remaining project overrides, extension
contributions, and core defaults continue to apply.

## Stacking and composition

Install multiple vetted presets with different priorities:

```bash
specify preset add --dev ./team-base --priority 10
specify preset add --dev ./compliance --priority 5
specify preset set-priority compliance 3
```

If both presets provide `spec-template` with the default `replace` strategy,
`compliance` wins entirely. Files provided only by `team-base` still use that
preset. Equal priorities are resolved alphabetically by preset ID.

Presets can augment lower layers instead of replacing them:

| Strategy | Effect |
| --- | --- |
| `replace` | Use this layer entirely; ignore lower layers |
| `prepend` | Put this layer before the lower-priority content |
| `append` | Put this layer after the lower-priority content |
| `wrap` | Insert lower-priority content at a placeholder in this layer |

Templates and commands support all four strategies. Scripts support only
`replace` and `wrap`. Composition needs a lower `replace` base; a wrapper
must contain the appropriate placeholder. The API reference defines the
exact rules.

## Constitution lifecycle

Initialization seeds `.specify/memory/constitution.md` once from the resolved
`constitution-template`, preserving an existing constitution. Later
`/speckit.constitution` runs resolve the current composed template and use the
live constitution for project-specific values and amendments.

By default, installing, removing, enabling, disabling, or reprioritizing
presets does not rewrite the live constitution. The bundled
`constitution-sync` preset opts into guarded install-time materialization and
command-time propagation. While it is enabled, stack changes may refresh an
unchanged generated constitution, but authored or hand-edited constitutions
are protected. Installing the preset can also seed a missing constitution.

## FAQ

### How do I see which file is being used?

Use `specify preset resolve spec-template` for a template or
`specify preset resolve speckit.specify` for a command. Composed output can
have several contributing files rather than one final source path.
Use `specify artifact info <name> --json` for the full artifact stack,
including hidden layers.

### Is disabling the same as removing?

No. Disabling excludes the preset from subsequent resolution but leaves
previously registered commands and skills in place. Use removal when you need
those delivered overrides cleaned up and the surviving layers restored.

### Who supports a preset?

Contact the preset's author through its repository. Community catalog
inclusion does not transfer maintenance or support responsibility to the
Spec Kit maintainers.

## See also

- [CLI reference](cli.md)
- [Developing presets](developing.md)
- [API reference](api.md)
- [Catalogs](catalogs.md)
- [Publishing presets](publishing.md)
- [Community presets](../community/presets.md)
- [Choosing customization building blocks](../how-to/customization.md)
