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

Use the corresponding `info` command to inspect a result, its source, available
versions, and whether it can be installed. You can also browse the maintained
community lists for [extensions](../community/extensions.md),
[presets](../community/presets.md), [bundles](../community/bundles.md), and
[workflow step types](../community/workflow-steps.md).

## Inspect and manage catalog sources

List the active catalog stack before installing components from an unfamiliar
project:

| Component type | List active catalogs | Detailed reference |
| --- | --- | --- |
| Integrations | `specify integration catalog list` | [Integrations](integrations.md#catalog-management) |
| Extensions | `specify extension catalog list` | [Extensions](extensions.md#catalog-management) |
| Presets | `specify preset catalog list` | [Presets](presets.md#catalog-management) |
| Workflows | `specify workflow catalog list` | [Workflows](workflows.md#catalog-management) |
| Workflow steps | `specify workflow step catalog list` | [Workflows](workflows.md#catalog-management) |
| Bundles | `specify bundle catalog list` | [Bundles](bundles.md#manage-catalog-sources) |

Each command group also provides `catalog add` and `catalog remove`. Options,
identifiers, install policies, and configuration filenames differ by component
type, so use the linked reference before changing a catalog stack.

Catalogs are resolved by precedence. Project sources generally take precedence
over user and built-in sources, and environment-variable overrides are checked
first where supported. Within a stack, the higher-precedence source that
provides an identifier wins; Specify does not silently bypass that source to
install a same-named component from a lower-precedence catalog.

## Discovery and trust

A catalog listing is not an audit or endorsement. Catalogs can be:

- **Install-allowed**: a source you trust as an installation source.
- **Discovery-only**: searchable for evaluation, but blocked from direct
  installation.

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

1. Choose the component type and follow its catalog schema or publishing guide.
2. Publish the catalog JSON at an HTTPS URL reachable by the intended users.
3. Add that URL with the component's `catalog add` command.
4. Mark the source install-allowed only after your organization has reviewed
   and approved its entries and release artifacts.
5. Confirm the resulting source, precedence, and install policy with
   `catalog list`.

Use the component-specific publishing guidance when authoring catalog entries:

| Component type | Publishing guidance |
| --- | --- |
| Integrations | [Integration catalog contributions](https://github.com/github/spec-kit/blob/main/integrations/CONTRIBUTING.md) |
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

Catalog metadata alone is not enough for offline installation: every selected
release artifact and any bundle-provided dependency must also be reachable or
transferred into the environment.
