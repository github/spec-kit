# Workflow step catalogs

Step catalogs control where `specify workflow step search` and `add` look for
custom step packages. They are independent of workflow catalogs.

## Discovery and trust

Step catalogs advertise executable Python packages through individual file
URLs. Built-in sources include `default` (installation allowed) and `community`
(discovery-only). Users must vet sources before installation and use;
maintainers do not audit or endorse component code.

A project's `.specify/step-catalogs.yml` can select sources you did not choose.
Inspect them with `specify workflow step catalog list` before installing or
loading custom steps. A direct archive URL bypasses catalog lookup, not source
review; direct URL installation asks for trust confirmation before making a
network request.

## Catalog configuration

| Level | Step types |
| --- | --- |
| Environment override | `SPECKIT_STEP_CATALOG_URL` |
| Project | `.specify/step-catalogs.yml` |
| User | `~/.specify/step-catalogs.yml` |
| Default | Official and community step catalogs |

The first usable level supplies the whole stack, not an additive layer. An
environment override selects one install-allowed source. Empty configurations
fall through; malformed YAML and invalid configured URLs/priorities report
errors.

```yaml
catalogs:
  - name: my-org
    url: https://catalog.example.com/steps.json
    priority: 5
    install_allowed: true
    description: Our vetted workflow steps
```

`url` requires HTTPS, including for local development; plain HTTP is rejected
before network access. Lower numeric
priorities win; the first source wins ties. `install_allowed` defaults to false
in hand-authored configuration.

`specify workflow step catalog add` creates project entries with installation
allowed and a priority after existing entries. It does not expose preset-style
`--install-allowed` or `--priority` flags. Add only vetted sources; edit the
configuration when a discovery-only source is intended. Adding a project stack
replaces implicit defaults unless you include them explicitly.

### Migrating legacy HTTP sources

Older configurations may contain loopback HTTP URLs that are no longer accepted.
Remove a legacy project source with `specify workflow step catalog remove <index>`;
removal does not fetch or validate source URLs. Indexes follow ascending
priority, with YAML declaration order breaking ties; entries without a URL are
skipped. `step catalog list` still rejects invalid URLs, so inspect
`.specify/step-catalogs.yml` to determine the index when it cannot list them.
Other entries can also be removed while a legacy HTTP source remains.

Alternatively, edit `.specify/step-catalogs.yml` for project sources or
`~/.specify/step-catalogs.yml` for user sources. Replace the source's `url` with
a working HTTPS catalog URL, or remove its entire item from `catalogs`.
Local HTTPS servers need a certificate trusted by Python's TLS client; browser
or operating-system trust alone may not suffice. See
[TLS certificates](../reference/authentication.md#tls-certificates) for
`SSL_CERT_FILE` configuration. Changing the URL scheme alone does not enable HTTPS.

An empty or deleted configuration falls through to the next level. Built-in
defaults apply when no higher level supplies a stack. Also update or unset
`SPECKIT_STEP_CATALOG_URL` if it still selects an HTTP source.

## Step entry schema

Catalog JSON contains `schema_version` and a `steps` collection. Entries identify
the type and version, its `step_yml_url` (or `url`), `init_url`, optional
`extra_files`, and per-file `sha256` digests. Catalog installation downloads
individual package files rather than the archive used by `--from`.

The community submission guide defines the additional metadata and pinned-file
requirements for community entries.

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

Step lookups merge all active catalogs, including for an exact ID.
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

A fetched catalog must be a JSON object. Its `steps` collection accepts mapping
or list forms; unsupported collection shapes and non-mapping entries are
skipped. These ignored contents do not count as fetch failures, so a
successfully fetched object can contribute no entries and lookup can return no
results rather than a structure-validation error. Step catalogs additionally
reject duplicate JSON fields and duplicate step IDs in list form. Release
metadata is validated separately and can still produce errors.

## Cache and private sources

Step catalogs cache fetched JSON and freshness metadata for one hour in
`.specify/workflows/steps/.cache/`. Payload and freshness files are keyed by URL
hash. Unusable cache entries trigger a fetch. Cache I/O does not follow
symlinked directory components or cache files. Writes atomically replace cache
files rather than truncate their referents, so a pre-existing cache-file
symlink can be replaced without changing its target. Unsafe cache writes log
warnings without discarding the fetched discovery result.

Private catalog and package downloads use shared opt-in authentication from
`~/.specify/auth.json`. A token environment variable alone does not enable it.
Configure only authorized destination hosts; never embed credentials in catalog
JSON or URLs.

## See also

- [Catalog CLI commands](cli.md#catalog-management)
- [Publishing steps](publishing.md)
- [Community step submissions](../community/workflow-steps.md)
- [Workflow catalogs](../workflows/catalogs.md)
- [Cross-component catalogs](../overview/catalogs.md)
- [Download authentication](../reference/authentication.md)
