# Workflow catalogs

Workflow catalogs control where `search` and `add` look for workflows. Catalogs are checked in priority order.

Workflow catalogs cache fetched JSON and freshness metadata for one hour in
`.specify/workflows/.cache/`. Cache I/O does not follow symlinked directory components or
cache files. Writes atomically replace cache files rather than truncate their
referents, so a pre-existing cache-file symlink can be replaced without changing
its target. If a cache cannot be safely written, a warning is logged and
discovery continues using the fetched catalog.

> **A project's `.specify/workflow-catalogs.yml` can point `add` and `search` at a catalog you didn't choose.** Before running a workflow from an unfamiliar project, run `specify workflow catalog list` (and `specify workflow step catalog list` for the step catalogs its steps can pull in) — a project supplying that config is not evidence its workflows or steps were vetted. Maintainers do not audit workflow code; review both `run` and `env` in its shell steps yourself, including strict steps (see [Reviewing shell execution](../workflow-steps/types.md#reviewing-shell-execution) and [Who maintains workflows?](overview.md#who-maintains-workflows)).

## Discovery and trust

Workflow catalogs advertise `workflow.yml` files or complete packages. Built-in sources include `default` (installation allowed) and `community` (discovery-only). Users must vet sources before installation and use; maintainers do not audit or endorse component code.

An explicit direct-URL install chooses a source without catalog lookup. It does not make unreviewed content safe.

## Catalog configuration

| Level | Workflows |
| --- | --- |
| Environment override | `SPECKIT_WORKFLOW_CATALOG_URL` |
| Project | `.specify/workflow-catalogs.yml` |
| User | `~/.specify/workflow-catalogs.yml` |
| Default | Official and community workflow catalogs |

The first usable level supplies the whole stack, not an additive layer. An environment override selects one install-allowed source. Empty configurations fall through; malformed YAML and invalid configured URLs/priorities report errors.

```yaml
catalogs:
  - name: my-org
    url: https://catalog.example.com/workflows.json
    priority: 5
    install_allowed: true
    description: Our vetted workflows
```

`url` requires HTTPS (loopback HTTP is allowed for development). Lower numeric priorities win; the first source wins ties. `install_allowed` defaults to false in hand-authored configuration.

`specify workflow catalog add` creates project entries with installation allowed and a priority after existing entries. It does not expose preset-style `--install-allowed` or `--priority` flags. Add only vetted sources; edit the configuration when a discovery-only source is intended. Adding a project stack replaces implicit defaults unless you include them explicitly.

## Workflow entry schema

Catalog JSON contains `schema_version` and a `workflows` mapping keyed by workflow ID. Entries carry `id`, `name`, `description`, `author`, `version`, `url`, and optional `sha256`, `requires`, `repository`, `license`, `tags`, and timestamps. A download can be raw YAML or a complete workflow archive. First-party entries marked `bundled: true` use packaged definitions rather than a network download.

## Workflow releases

Catalog entries keep the current release's `version`, `url`, optional `sha256`,
and optional `requires` at the top level. An optional `releases` mapping
advertises historical versions without changing what unqualified `add`,
`search`, `info`, or `update` select:

```json
{
  "id": "example",
  "version": "2.0.0",
  "url": "https://example.com/example-2.0.0.zip",
  "releases": {
    "1.0.0": {
      "url": "https://example.com/example-1.0.0.zip",
      "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "requires": {"speckit_version": ">=1.0.0"}
    }
  }
}
```

Each historical release needs its own URL and SHA-256 digest; `requires` is
optional and, when present, must match the downloaded workflow definition.
Advertised versions use the workflow definition's `X.Y.Z` version format;
`--version` also accepts equivalent spellings such as `v1.0` when selecting an
advertised `1.0.0` release.
The requested version must exist in the highest-priority catalog that provides
the workflow. A missing version does not fall back to another source, and
discovery-only catalogs cannot be installed from. The downloaded workflow ID,
version, and declared digest are verified before installation. `--version` does
not apply to local paths, direct URLs, or `--from` installations.

## Resolution and failures

Workflow lookups merge all active catalogs, including for an exact ID.
They do not stop after finding an ID. Sources are processed in reverse priority
order so higher-precedence entries overwrite lower-precedence entries; each
source may be fetched or read from cache even when another provides the ID.
Vet every active source, not just the source expected to win.

The winning entry supplies its metadata, releases, and installation policy
together. A lower-priority entry cannot supply a missing version or override a
winning discovery-only decision. However, a source that fails to fetch
contributes no entries, so a lower-priority source can supply the ID when the
preferred source is unavailable. Fetch failures remaining after cache fallback
are skipped when another source succeeds; if every configured catalog fails,
lookup reports an error.

A fetched catalog must be a JSON object. Its `workflows` collection
accepts mapping or list forms; unsupported collection shapes and
non-mapping entries are skipped. These ignored contents do not count as fetch
failures, so a successfully fetched object can contribute no entries and lookup
can return no results rather than a structure-validation error. Release
metadata is validated separately and can still produce errors.

## Cache and private sources

Workflow catalog caches live under `.specify/workflows/.cache/`, with a one-hour lifetime. Payload and freshness files are keyed by URL hash. Unusable cache entries trigger a fetch; unsafe cache writes log warnings without discarding the fetched discovery result.

Private catalog and package downloads use shared opt-in authentication from `~/.specify/auth.json`. A token environment variable alone does not enable it. Configure only authorized destination hosts; never embed credentials in catalog JSON or URLs.

## See also

- [Catalog CLI commands](cli.md#catalog-management)
- [Publishing workflows](publishing.md)
- [Community workflows](../community/workflows.md)
- [Step catalogs](../workflow-steps/catalogs.md)
- [Cross-component catalogs](../overview/catalogs.md)
- [Download authentication](../reference/authentication.md)
- [Shell source review](../workflow-steps/types.md#reviewing-shell-execution)
