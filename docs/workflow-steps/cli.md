# Workflow step CLI reference

The `specify workflow step` group manages custom step packages and their
catalogs in an initialized Spec Kit project. Built-in types ship with the CLI
and do not need separate installation.

## Step Management

Custom steps contain executable Python. Review their source before installation and use. See [Developing custom step packages](developing.md#custom-step-packages) for the package contract.

```bash
specify workflow step list
specify workflow step search [query]
specify workflow step info <step_id>
specify workflow step info <step_id> --versions
```

`list` shows installed custom step types; `search` searches active step catalogs; `info` shows installed or catalog metadata and source provenance. `--versions` lists releases from the winning catalog.

### Install from a local directory

```bash
specify workflow step add my-step --dev /path/to/my-step
```

`--dev` takes a **directory** (not an archive, not a bare `step.yml`) that is a
complete package. This needs no catalog, server, or network, which makes it the
supported local-authoring loop:

```bash
specify workflow step add my-step --dev ./my-step
specify workflow step list
specify workflow step info my-step
# edit ./my-step, then replace the installed copy:
specify workflow step add my-step --dev ./my-step --force
specify workflow step remove my-step
```

### Install from an archive URL

```bash
specify workflow step add my-step --from https://example.com/my-step.zip
```

`--from` accepts a `.zip`, `.tar.gz`, or `.tgz` archive (a bare `step.yml`
URL is **not** a package). The archive may place `step.yml` and `__init__.py`
at its root or under exactly one top-level directory; unrelated top-level
siblings are rejected. Because a step package contains executable Python, a
direct URL install shows a default-deny trust confirmation before any network
request; declining cancels with no request and no error. HTTPS is required
(HTTP is permitted only for loopback hosts), redirects must remain secure, and
downloads are size-bounded.

### Install from the catalog

```bash
specify workflow step add my-step
```

Catalog installs resolve individual file URLs from the active step catalogs and
then go through the same validation and commit path as `--dev` and `--from`.
Discovery-only catalogs cannot be installed from.

To submit a custom step type to the discovery-only community catalog, follow
[Community Workflow Steps](../community/workflow-steps.md). Submissions use
tag-pinned individual file URLs and per-file digests; maintainers validate
metadata and distribution evidence, not submitted code.

See [Step releases](catalogs.md#step-releases) for catalog history and exact-version selection.

### Replacement and force

```bash
specify workflow step add my-step --dev ./my-step --force
specify workflow step add my-step --from https://example.com/my-step.zip --force
```

`--force` first stages and validates the replacement before touching the
existing installation, and can replace both a registered install and a leftover
unregistered directory. Validation and staging failures leave the previous
package untouched. If removing the old directory fails, the replacement is not
published. If publishing the replacement or updating the registry fails after
the old directory has been removed, the installation may be left incomplete:
rerun the command with the original source and `--force` to reinstall. No
automatic rollback is attempted.

### Listing, running, and removing

Installed custom steps appear in `specify workflow step list` and are loaded
automatically by `workflow add`, `workflow run`, and `workflow resume`. Remove
one with:

```bash
specify workflow step remove my-step
```

## Catalog Management

Step catalogs are independent of workflow catalogs.

### List Catalogs

```bash
specify workflow step catalog list
```

Shows all active step catalog sources.

### Add a Catalog

```bash
specify workflow step catalog add <url> [--name <name>]
```

| Option | Description |
| --- | --- |
| `--name <name>` | Optional name for the catalog |

Adds a custom catalog URL to the project's `.specify/step-catalogs.yml`.
New entries allow installation and receive a priority after existing entries.
Only add vetted sources. Configure discovery-only sources by editing the
catalog configuration.

Re-adding the same step catalog URL with the same name succeeds without
changing the configuration; a different name is rejected.

### Remove a Catalog

```bash
specify workflow step catalog remove <index>
```

Removes a project catalog by its index in the priority-ordered `catalog list`.
Sources supplied by `SPECKIT_STEP_CATALOG_URL` cannot be removed this way;
unset the variable to manage project sources.

## See also

- [Step overview](overview.md)
- [Built-in step types](types.md)
- [Package development and validation](developing.md)
- [Python API and registry](api.md)
- [Catalog schemas and trust](catalogs.md)
- [Workflow execution CLI](../workflows/cli.md)
