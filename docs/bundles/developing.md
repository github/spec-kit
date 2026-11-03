# Developing bundles

A bundle distributes an existing component stack through a manifest and usage
documentation. Start with the role or team outcome, select components that
provide it, and test their combined installation. A bundle does not replace
extension, preset, workflow, or step authoring.

## Create a bundle directory

Keep the manifest and README at the directory root:

```text
team-setup/
  bundle.yml
  README.md
  LICENSE
```

This minimal example uses the packaged bug extension and workflow:

```yaml
schema_version: "1.0"
bundle:
  id: team-setup
  name: Team setup
  version: 1.0.0
  role: developer
  description: A bug-fixing setup for the team
  author: Example team
  license: MIT
requires:
  speckit_version: ">=0.9.0"
provides:
  extensions:
    - id: bug
      version: 1.0.2
  workflows:
    - id: bugfix
      version: 1.0.0
tags: [developer, bugfix]
```

Choose pins from releases you have tested. Compatible newer stable packaged
patches may satisfy these pins with warnings; explicit component catalog
sources retain exact-pin enforcement.

The README should explain the intended role, installed components, integration
requirements, catalogs users need to register, installation commands, and how
to use the installed setup. For community publication, include a license file.

## Select components and their sources

Extension, preset, and workflow references require exact versions. Steps may
omit a version, in which case installation selects the current step catalog
release. Pin steps too when reproducibility matters.

Presets must declare an integer priority of at least `1` and a composition
strategy. Extensions can also declare priority; their default is `10`.
Use the API reference for the complete field contract.

An optional component `source` names the expected winning component catalog.
It is not a URL, a directory, or a mechanism to change catalog precedence.
Before selecting sources, inspect the effective catalogs:

```bash
specify extension catalog list
specify preset catalog list
specify workflow catalog list
specify workflow step catalog list
```

Document every non-default catalog needed by the bundle, with its appropriate
`catalog add` command. Catalogs remain separate: adding a bundle catalog does
not add component catalogs. Users must vet them before granting installation.
Use unique component catalog names; an explicit source that matches multiple
active catalogs is ambiguous and rejected.

Local bundle assets are packaged for distribution but are not automatically
installed as component payloads. In particular, copying a custom step under
`steps/<id>/` does not make it resolvable. Publish it through an accessible step
catalog and document that dependency.

## Compose existing bundles

Use schema `1.1` and `provides.bundles` to reference exact releases of other
bundles. For example, after checking the release is available in your catalog:

```yaml
schema_version: "1.1"
bundle:
  id: team-setup
  name: Team setup
  version: 1.0.0
  role: developer
  description: A composed team setup
  author: Example team
  license: MIT
requires:
  speckit_version: ">=0.9.0"
provides:
  bundles:
    - id: bugfix
      version: 1.0.2
      source: default
```

References resolve through the effective bundle catalog, including when the
parent is a local manifest. They are not local path references and are not
embedded by `build`. The parent's own component declarations can override
referenced declarations; incompatible sibling declarations need an explicit
parent resolution. The API reference defines ordering, deduplication, and
limits.

First-party bundle catalogs currently keep no historical releases. An exact
reference can stop resolving when the catalog advances to its next release.
For long-lived composition, use a catalog that preserves the required history.

## Validate and build

From the repository or directory containing your bundle:

```bash
specify bundle validate --path ./team-setup
specify bundle build --path ./team-setup --output ./dist
```

Read warnings as well as errors. Online validation checks component
resolution and expands references, but it does not enforce the running CLI's
Spec Kit version gate. Offline validation cannot confirm network-only
components or expand bundle references.

Build requires a regular `README.md` and `bundle.yml` and checks manifest
structure. It does not confirm that references resolve or that installation
succeeds. The resulting ZIP contains root-level files and local assets, not
downloaded component payloads or referenced bundles.

Build output is reproducible for identical inputs: files are sorted by their
POSIX archive paths, timestamps are fixed, and permissions normalize to
executable or non-executable modes. Symlinks, `.git`, `__pycache__`, `.DS_Store`,
previous versioned build artifacts for this bundle, and a nested output
directory are excluded.

## Test installation and changes

Use a clean project with the intended integration. Register any vetted
dependency catalogs, then install the exact artifact users will receive:

```bash
specify init --here --integration copilot
specify bundle install /path/to/dist/team-setup-1.0.0.zip
specify bundle list --json
```

Inspect delivered commands and run the installed workflows or other intended
capabilities. Repeat the installation to confirm that unchanged components
and local edits are preserved. Test removal while independent or other-bundle
components remain installed.

For local development, ordinary reinstall is not an update operation. Apply
revised versions, changed owned-component settings, or removed components with:

```bash
specify bundle install /path/to/team-setup/bundle.yml --refresh
```

Refresh can overwrite owned components through their update paths and is not
fully rolled back on failure. Use a disposable project for this test.
Test both valid installs and relevant rejected cases, such as unavailable pins,
integration mismatches, and conflicts with another bundle's requirements.

If distributing through a catalog, test ID installation from that
install-allowed catalog too. A successful direct-artifact install does not
verify catalog precedence, download metadata, or historical release selection.

## See also

- [Bundle overview](overview.md)
- [Manifest and bundle-reference API](api.md)
- [CLI reference](cli.md)
- [Catalog configuration](catalogs.md)
- [Publishing bundles](publishing.md)
