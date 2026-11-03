# Workflow catalogs

Workflow catalogs control where `search` and `add` look for workflows. Catalogs are checked in priority order.

Workflow and step catalogs cache fetched JSON and freshness metadata for one
hour in `.specify/workflows/.cache/` and `.specify/workflows/steps/.cache/`,
respectively. Cache I/O does not follow symlinked directory components or
cache files. Writes atomically replace cache files rather than truncate their
referents, so a pre-existing cache-file symlink can be replaced without changing
its target. If a cache cannot be safely written, a warning is logged and
discovery continues using the fetched catalog.

> **A project's `.specify/workflow-catalogs.yml` can point `add` and `search` at a catalog you didn't choose.** Before running a workflow from an unfamiliar project, run `specify workflow catalog list` (and `specify workflow step catalog list` for the step catalogs its steps can pull in) — a project supplying that config is not evidence its workflows or steps were vetted. Maintainers do not audit workflow code; review both `run` and `env` in its shell steps yourself, including strict steps (see [Reviewing shell execution](steps.md#reviewing-shell-execution) and [Who maintains workflows?](overview.md#who-maintains-workflows)).

## Discovery and trust

Workflow catalogs advertise `workflow.yml` files or complete packages. Step catalogs advertise executable Python packages through individual file URLs. They are independent stacks with built-in `default` (installation allowed) and `community` (discovery-only) sources. Users must vet sources before installation and use; maintainers do not audit or endorse component code.

An explicit direct-URL install chooses a source without catalog lookup. It does not make unreviewed content safe. A direct custom-step archive install asks for trust confirmation before making a network request.

## Catalog configuration

| Level | Workflows | Step types |
| --- | --- | --- |
| Environment override | `SPECKIT_WORKFLOW_CATALOG_URL` | `SPECKIT_STEP_CATALOG_URL` |
| Project | `.specify/workflow-catalogs.yml` | `.specify/step-catalogs.yml` |
| User | `~/.specify/workflow-catalogs.yml` | `~/.specify/step-catalogs.yml` |
| Default | Official and community workflow catalogs | Official and community step catalogs |

The first usable level supplies the whole stack, not an additive layer. An environment override selects one install-allowed source. Empty configurations fall through; malformed YAML and invalid configured URLs/priorities report errors.

```yaml
catalogs:
  - name: my-org
    url: https://catalog.example.com/workflows.json
    priority: 5
    install_allowed: true
    description: Our vetted workflows
```

Use the same entry shape for a step catalog in its separate file. `url` requires HTTPS (loopback HTTP is allowed for development). Lower numeric priorities win; the first source wins ties. `install_allowed` defaults to false in hand-authored configuration.

`specify workflow catalog add` and `specify workflow step catalog add` create project entries with installation allowed and a priority after existing entries. They do not expose preset-style `--install-allowed` or `--priority` flags. Add only vetted sources; edit the configuration when a discovery-only source is intended. Adding a project stack replaces implicit defaults unless you include them explicitly.

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

## Step releases

`specify workflow step info <id> --versions` lists the current and historical
releases in the winning catalog. `specify workflow step add <id> --version <v>`
selects the exact catalog release; without `--version`, `add` installs the
advertised current release. The requested version never falls back to a
lower-priority catalog, and discovery-only sources remain non-installable.
`--version` cannot be combined with direct `--dev` or `--from` installs.

Existing single-version catalog entries continue to work. Keep the current
release's `version`, `step_yml_url` (or `url`), `init_url`, and optional files
at the top level. An optional `releases` mapping adds historical versions:

```json
{
  "steps": {
    "my-step": {
      "version": "2.0",
      "step_yml_url": "https://example.com/my-step/2.0/step.yml",
      "releases": {
        "1.0": {
          "step_yml_url": "https://example.com/my-step/1.0/step.yml",
          "init_url": "https://example.com/my-step/1.0/__init__.py",
          "extra_files": {"helper.py": "https://example.com/my-step/1.0/helper.py"},
          "sha256": {
            "step.yml": "<64 hex digits>",
            "__init__.py": "<64 hex digits>",
            "helper.py": "<64 hex digits>"
          }
        }
      }
    }
  }
}
```

Each historical release must supply its own step URL and SHA-256 digest for
every downloaded file. `init_url` can be omitted when derived from a
`step_yml_url` ending in `step.yml`. To select the current version explicitly,
its top-level entry must likewise supply the per-file `sha256` mapping.
Release-specific files and requirements are not inherited from the current
release. Repeated or malformed versions are rejected; equivalent PEP 440
spellings such as `v1.0` and `1.0` select the same advertised release. The
downloaded `step.yml` must declare the selected step ID and version. An
unqualified legacy catalog install does not require digests or a step version.
Only one version of each step ID can be installed at a time; use `--force` to
replace a previous installation after reviewing the selected package.

## Resolution and failures

Workflow and step lookups merge all active catalogs, including for an exact ID.
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

A fetched catalog must be a JSON object. Within that object, `workflows` and
`steps` accept mapping or list forms; unsupported collection shapes and
non-mapping entries are skipped. These ignored contents do not count as fetch
failures, so a successfully fetched object can contribute no entries and lookup
can return no results rather than a structure-validation error. Step catalogs
additionally reject duplicate JSON fields and duplicate step IDs in list form.
Release metadata is validated separately and can still produce errors.

## Cache and private sources

Workflow and step catalog caches live under `.specify/workflows/.cache/` and `.specify/workflows/steps/.cache/`, with a one-hour lifetime. Payload and freshness files are keyed by URL hash. Unusable cache entries trigger a fetch; unsafe cache writes log warnings without discarding the fetched discovery result.

Private catalog and package downloads use shared opt-in authentication from `~/.specify/auth.json`. A token environment variable alone does not enable it. Configure only authorized destination hosts; never embed credentials in catalog JSON or URLs.

## See also

- [Catalog CLI commands](cli.md#catalog-management)
- [Publishing workflows](publishing.md)
- [Community step submissions](../community/workflow-steps.md)
- [Cross-component catalogs](../reference/catalogs.md)
- [Download authentication](../reference/authentication.md)
- [Shell source review](steps.md#reviewing-shell-execution)
