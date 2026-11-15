# Bundles

Bundles compose existing Spec Kit extensions, presets, workflows, and workflow
step types into one versioned, installable setup for a role or team. A bundle
declares the components to install in `bundle.yml`; it does not add runtime
behavior of its own. Each component is installed through its own machinery.

Use an extension to add capabilities, a preset to customize existing
capabilities, and a workflow to automate a sequence. Use a bundle when those
pieces should be distributed and installed together.

> [!IMPORTANT]
> Vet third-party bundles and the components they install before using them.
> Community catalogs are discovery channels, not security endorsements.
> Maintainers check submission metadata for completeness and format; they do
> not review, audit, endorse, or support community bundle code or its components.

## Quick start

Discover bundles and inspect the components a catalog bundle declares:

```bash
specify bundle search
specify bundle info bugfix
```

Install a first-party bundle, inspect the installed record, and remove it:

```bash
specify bundle install bugfix
specify bundle list
specify bundle remove bugfix
```

`add` is an alias for `install`. Installation initializes a Spec Kit project
if needed; use `--integration copilot`, for example, to select the integration
for a new project. It does not switch an existing project's active integration.

For a bundle you have authored or vetted, pass a local directory, manifest, or
built artifact:

```bash
specify bundle install ./team-setup/bundle.yml
specify bundle install ./team-setup-1.0.0.zip
```

The local source supplies the manifest, not an embedded component repository.
Its components still need to resolve from packaged assets, compatible installed
components, or their own catalogs. A community search result does not itself
permit installation by ID.

## First-party bundles

Spec Kit maintains the first-party catalog in `bundles/catalog.json`, exposed
through the install-allowed `builtin://default` source. Its entries are marked
`verified: true`.

| Bundle | Components | Use case |
| --- | --- | --- |
| `bugfix` | `bug` extension and `bugfix` workflow | Guided assess, assessment gate, fix, and test |
| `assess` | `assess` extension and `assess` workflow | Idea triage before Spec-Driven Development |

```bash
specify bundle add assess
```

Installing a workflow does not run it. Follow the
[bug-fixing guide](../guides/bugfix.md) or
[idea assessment guide](../guides/assessment.md) to use the installed setup.

Built-in catalogs are fetched online and use packaged snapshots offline.
Catalog-discovered bundle manifests still require a network download, even for
first-party entries. A local manifest can install packaged components with
`--offline`; see the CLI reference for the exact limits.

## Lifecycle and ownership

Bundles record both required components and the components they contributed.
A compatible component installed independently can satisfy a requirement
without becoming bundle-owned. Removing the bundle leaves it in place.
Components shared with other bundles remain installed while still needed.

Repeating an unchanged install preserves existing components and local edits.
Use `bundle update <id>` for a catalog release, or
`bundle install <path> --refresh` for a revised local source, to reapply owned
components. Updates are not a global transaction: changes to components that
were already installed are not rolled back after a later failure.

## See also

- [CLI reference](cli.md)
- [Developing bundles](developing.md)
- [Manifest and composition API](api.md)
- [Catalogs](catalogs.md)
- [Publishing bundles](publishing.md)
- [Community bundles](../community/bundles.md)
- [Community walkthroughs](../community/walkthroughs.md)
- [Choosing customization building blocks](../how-to/customization.md)
