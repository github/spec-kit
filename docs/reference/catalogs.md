# Catalogs

Catalogs are indexes that let Specify discover integrations, extensions,
presets, workflows, workflow step types, and bundles. Spec Kit includes
built-in catalogs, including community catalogs where available, and lets a
project or user add private catalog sources.

A catalog is not one shared registry for every component type. Each component
type has its own catalog schema, command group, configuration, and resolution
stack. An organization that curates several component types normally publishes
one catalog file for each type.

## Discover components

Search uses all active catalogs for that component type:

```bash
specify integration search <query>
specify extension search <query>
specify preset search <query>
specify workflow search <query>
specify workflow step search <query>
specify bundle search <query>
```

Use the corresponding version view to inspect advertised releases:

```bash
specify integration info <id> --versions
specify extension info <id> --versions
specify preset info <id> --versions
specify workflow info <id> --versions
specify workflow step info <id> --versions
specify bundle info <id> --versions
```

Plain `info` output and the details shown by `--versions` vary by component
type. The version view lists current and historical catalog releases and, where
supported, labels the winning source as installable or discovery-only. A
discovery-only release remains non-installable by ID even when it appears in
the version list. Use the component's `catalog list` command to confirm the
active source and install policy instead of relying on plain `info` output.

You can also browse the maintained community lists for
[extensions](../community/extensions.md),
[presets](../community/presets.md), [bundles](../community/bundles.md), and
[workflow step types](../community/workflow-steps.md).

## Inspect and manage catalog sources

List the active catalog stack before installing components from an unfamiliar
project:

| Component type | List active catalogs | Detailed reference |
| --- | --- | --- |
| Integrations | `specify integration catalog list` | [Integrations](../integrations/cli.md#catalog-management) |
| Extensions | `specify extension catalog list` | [Extensions](extensions.md#catalog-management) |
| Presets | `specify preset catalog list` | [Presets](presets.md#catalog-management) |
| Workflows | `specify workflow catalog list` | [Workflows](workflows.md#catalog-management) |
| Workflow steps | `specify workflow step catalog list` | [Workflows](workflows.md#catalog-management) |
| Bundles | `specify bundle catalog list` | [Bundles](bundles.md#manage-catalog-sources) |

Each command group also provides `catalog add` and `catalog remove`. Options,
identifiers, install policies, and configuration filenames differ by component
type, so use the linked reference before changing a catalog stack.

Catalog scope and precedence use two models:

- **Integrations, extensions, presets, workflows, and workflow steps** select
  one configuration layer. An environment-variable override replaces
  everything; otherwise a project catalog file replaces the user and built-in
  layers, a user file replaces the built-in layer, and built-in catalogs are
  used only when no higher layer is configured. Within the selected layer,
  entries are ordered by numeric priority. Adding the first project catalog
  therefore removes the built-in sources from the active stack unless you also
  list those sources in the project file.
- **Bundles** merge built-in, user, and project sources by source ID. A
  higher-scope definition replaces a lower-scope source with the same ID, then
  all remaining sources are sorted by numeric priority. A project source does
  not automatically outrank a differently named built-in source.

Among catalogs that load successfully, the higher-priority entry providing an
identifier wins. Some component readers skip ordinary fetch failures and
continue with the remaining sources, so an unreachable higher-priority source
can allow a lower-priority source to resolve the same identifier. Do not treat
source priority as a fail-closed security control.

## Discovery and trust

A catalog listing is not an audit or endorsement. Catalogs can be:

- **Install-allowed**: a source you trust for installation by component ID.
- **Discovery-only**: searchable for evaluation, but blocked from installation
  by ID through that catalog.

Discovery-only policy does not block a separately requested direct-source
installation such as a supported `--from` URL or `--dev` path. Review that
source independently before using the direct-install route.

Community catalogs are discovery surfaces and should remain discovery-only.
Review a component's source and release artifact before using it. To make
reviewed components reusable across a team, copy their vetted entries into a
catalog your organization controls rather than changing an unvetted public
catalog to install-allowed.

Project catalog configuration is also untrusted input. A repository can add or
prioritize catalog sources under `.specify/`, but the presence of that
configuration does not mean its sources or components were approved. Run the
relevant `catalog list` command and inspect every install-allowed source before
installing or running components from an unfamiliar project.

## Host a private catalog

1. Review and approve the entries and release artifacts before registering an
   install-allowed source.
2. Choose the component type and follow its catalog schema or publishing guide.
3. Publish the catalog JSON at an HTTPS URL reachable by the intended users.
4. Add that URL with the component's `catalog add` command.
5. Confirm the resulting source, precedence, and install policy with
   `catalog list`.

The `catalog add` trust default differs by component type:

| Component type | Default when added |
| --- | --- |
| Integrations | Install-allowed |
| Extensions | Discovery-only; requires `--install-allowed` to enable installation |
| Presets | Discovery-only; requires `--install-allowed` to enable installation |
| Workflows | Install-allowed |
| Workflow steps | Install-allowed |
| Bundles | Install-allowed; use `--policy discovery-only` to restrict it |

Because integration, workflow, workflow-step, and bundle additions can permit
installation immediately, do not register an unreviewed source and plan to
approve it later.

Use the component-specific publishing guidance when authoring catalog entries:

| Component type | Publishing guidance |
| --- | --- |
| Integrations | [Integration catalog contributions](../integrations/contributing.md) |
| Extensions | [Extension Publishing Guide](https://github.com/github/spec-kit/blob/main/extensions/EXTENSION-PUBLISHING-GUIDE.md) |
| Presets | [Preset Publishing Guide](https://github.com/github/spec-kit/blob/main/presets/PUBLISHING.md) |
| Workflows | [Workflow Publishing Guide](https://github.com/github/spec-kit/blob/main/workflows/PUBLISHING.md) |
| Workflow steps | [Community workflow step types](../community/workflow-steps.md) |
| Bundles | [Community bundles](../community/bundles.md) |

For example, a reviewed extension catalog can be registered with:

```bash
specify extension catalog add https://catalog.example.com/extensions.json \
  --name approved-extensions \
  --priority 5 \
  --install-allowed
```

Use separate catalog files and commands for presets, integrations, workflows,
workflow steps, and bundles. Their detailed references document the supported
options and expected entry formats.

## Private and offline environments

If a catalog or its component downloads require credentials, configure
[catalog and download authentication](authentication.md). Authentication is
opt-in and scoped to explicitly configured hosts.

Behind a firewall, host catalogs and artifacts on approved internal HTTPS
endpoints and add those endpoints to the appropriate catalog stacks. In a
fully disconnected environment, transfer the CLI and reviewed component
artifacts through your approved process; built-in assets remain available
without network access. See [Enterprise / Air-Gapped Installation](../install/air-gapped.md)
for installing the CLI offline.

External integration adapters have no direct or local installation route.
Installing one requires both an install-allowed integration catalog and its
referenced archive to remain reachable. See
[Catalog-installed external adapters](../integrations/cli.md#catalog-installed-external-adapters).

Catalog metadata alone is not enough for offline installation: every selected
release artifact and any bundle-provided dependency must also be reachable or
transferred into the environment.
