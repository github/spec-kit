# Customize Spec Kit

The three first-party processes are starting points, not limits. Keep the
built-in SDD process, add bug fixing or assessment, adapt a process to your
organization, or bring a different process entirely.

## Choose the right building block

| Goal | Use |
| --- | --- |
| Add a new command, capability, or process | Extension |
| Integrate an external tool or service | Extension |
| Change the format or terminology of specs, plans, or tasks | Preset |
| Enforce organizational or regulatory standards in existing templates | Preset |
| Ship reusable domain-specific templates | Presets for overrides; extensions for templates accompanying new commands |
| Make a one-off template adjustment in a single project | Project-local override |
| Automate a multi-step process | Workflow |
| Provision a complete role-based setup in one operation | Bundle |

## Extensions: add capabilities

Extensions expand **what Spec Kit can do** through commands, templates, scripts,
and hooks. They can add domain-specific processes, external integrations, or
development phases beyond the core.

```bash
specify extension search
specify extension add <extension-name>
```

Examples include Jira integration, post-implementation code review, V-Model test
traceability, and project health diagnostics. The bundled
[bug](bugfix.md) and [assess](assessment.md) extensions are first-party examples.
Browse [community extensions](../community/extensions.md), or use the
[extension reference](../reference/extensions.md) for management and configuration.

## Presets: change how a process works

Presets override templates and commands supplied by the core **and by installed
extensions**. They customize the artifacts and instructions produced without
requiring new tooling.

```bash
specify preset search
specify preset add <preset-name>
```

Use a preset to require regulatory traceability, enforce test-first task ordering,
add security review gates to plans, or localize a workflow. Presets can also adapt
the methodology to Agile, Kanban, Waterfall, jobs-to-be-done, or domain-driven
design. The
[pirate-speak demo](https://github.com/mnriem/spec-kit-pirate-speak-preset-demo)
illustrates how extensively the terminology can change.

Multiple presets can be stacked with priorities. See
[community presets](../community/presets.md) for examples and the
[preset reference](../reference/presets.md) for installation, composition
strategies, and precedence.

## Project-local overrides and resolution

For a one-off project customization, place a template override in
`.specify/templates/overrides/` rather than creating a reusable preset.
The default replacement order is:

1. Project-local overrides.
2. Installed presets, in priority order.
3. Installed extensions, in priority order.
4. Spec Kit core templates in `.specify/templates/`.

Templates are resolved when needed, using the first match by default.
Commands are different: installing extensions or presets materializes command
files into the active integration's directory. Agents do not re-resolve that
stack every time they invoke a command. Removing an overriding component
restores the surviving command layer through reconciliation.

With no customizations, the core defaults apply. The
[file resolution reference](../reference/presets.md#file-resolution) is the
authoritative guide to paths, priorities, and prepend/append/wrap composition.

## Bundles: role-based setups

A bundle packages a curated set of extensions, presets, workflows, and workflow
steps as one versioned setup for a role or team. Its `bundle.yml` manifest pins
components and may target an integration; an integration-agnostic bundle inherits
the project's active integration.

```bash
specify bundle search
specify bundle info <bundle-id>
specify bundle install <bundle-id>
```

Inspect `info` before installing to see the resolved component set. See the
[bundle reference](../reference/bundles.md) for updates, removal, catalog policies,
offline limitations, validation, and publishing, and the
[example manifests](https://github.com/github/spec-kit/tree/main/examples/bundles)
for product manager, business analyst, security researcher, and developer setups.

## Share your customizations

Community components are independently maintained. Review source code before
installation and use it at your own discretion. Visit the
[community guide](../community/overview.md) to discover components or publish your
own, and the [workflow reference](../reference/workflows.md) to automate a process.
