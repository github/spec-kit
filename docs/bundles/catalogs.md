# Bundle catalogs

Bundle catalogs locate bundle manifests and describe the setups available for
discovery. They do not supply the extension, preset, workflow, or step catalogs
needed by those manifests. Register and vet those component catalogs
separately.

## Trust and installation policy

> [!IMPORTANT]
> Vet both a bundle source and its component catalogs before installation.
> A project can supply bundle and install-allowed component catalogs under
> `.specify/`; their presence is not evidence that anyone reviewed them.

Inspect all applicable sources, including those you did not add yourself:

```bash
specify bundle catalog list
specify extension catalog list
specify preset catalog list
specify workflow catalog list
specify workflow step catalog list
```

Treat unfamiliar sources as unvetted until you have reviewed them. For workflow
components, inspect shell `run` and `env` fields and referenced code, including
active overlays. Even `strict: true` steps can change executable lookup or
runtime loading through environment bindings; see
[reviewing shell execution](../workflow-steps/types.md#reviewing-shell-execution).

| Policy | Effect |
| --- | --- |
| `install-allowed` | Permits installation/update from this source |
| `discovery-only` | Permits search and inspection, but refuses installation/update |

The `verified` flag is catalog metadata, not an installation policy or a
security guarantee. Community entries are unverified, and maintainers do not
review, audit, endorse, or support their code. Bundle installation does not
automatically register or trust companion catalogs.

## Built-in sources

| Source ID | URL | Priority | Policy |
| --- | --- | --- | --- |
| `default` | `builtin://default` | `1` | `install-allowed` |
| `community` | `builtin://community` | `20` | `discovery-only` |

The default catalog is `bundles/catalog.json`; community submissions appear
in `bundles/catalog.community.json`. Both are fetched from the repository
online. Offline discovery uses the packaged wheel snapshots. Transient
built-in catalog availability failures warn and fall back to those snapshots;
malformed content or security validation failures do not silently fall back.

The bundle manifest's `download_url` still requires network access. A packaged
catalog snapshot is not a local payload store.

## Configure sources

From an initialized project, after vetting the source:

```bash
specify bundle catalog add https://example.com/bundles.json \
  --id team --priority 10 --policy install-allowed
specify bundle catalog list
specify bundle catalog remove team
```

The CLI writes `.specify/bundle-catalogs.yml`:

```yaml
schema_version: "1.0"
catalogs:
  - id: team
    url: https://example.com/bundles.json
    priority: 10
    install_policy: install-allowed
```

User configuration uses the same shape at `~/.specify/bundle-catalogs.yml`.
CLI add/remove operations write project scope only. Both readers accept a
missing schema version for compatibility and reject an unsupported major
version.

Source URLs can be HTTPS, `file://`, local paths, or known
`builtin://` URLs. Plain HTTP is rejected before network access, including on
localhost. Added local paths are stored as absolute paths. This
flexibility applies to the catalog file, not its bundle download URLs.

### Precedence

Two steps determine the effective stack:

1. Merge sources by ID: a project-scoped source replaces the same ID in user
   scope, and user scope replaces the same ID in built-in scope.
2. Sort surviving sources by numeric priority, then source ID. Lower priority
   numbers win.

Scope does not outrank priority for distinct IDs. An added source defaults to
priority `10`, ahead of the community source at `20`, but behind the default
source at `1`. Override a built-in source by its ID or choose an appropriate
priority deliberately.

The first source containing a bundle ID wins. A missing historical release,
source mismatch, or discovery-only policy does not cause fallback to a
lower-priority catalog. `source` in a bundle reference asserts this winner; it
does not select a source.

Re-adding an existing URL with matching ID/settings is a no-op. Conflicting
URL/ID settings fail. Built-in sources cannot be removed, but a project
override of a built-in ID can be removed to restore the lower-scope source.

## Catalog payload

Catalog files are JSON objects with a `bundles` mapping keyed by bundle ID:

```json
{
  "schema_version": "1.0",
  "bundles": {
    "team-setup": {
      "id": "team-setup",
      "name": "Team setup",
      "version": "1.2.0",
      "role": "developer",
      "description": "A curated team setup",
      "author": "Example team",
      "license": "MIT",
      "repository": "https://github.com/example/team-setup",
      "download_url": "https://github.com/example/team-setup/releases/download/v1.2.0/team-setup-1.2.0.zip",
      "requires": {"speckit_version": ">=0.9.0"},
      "provides": {"extensions": 1, "presets": 0, "steps": 0, "workflows": 1},
      "tags": ["developer", "bugfix"],
      "verified": false
    }
  }
}
```

The entry's `id` must match its enclosing key. `requires` and `provides`, when
present and non-null, must be mappings; `tags` must be a list of strings;
`verified` must be a real boolean. `provides` describes component counts, not
the manifest's component lists. Catalog schema versions with an unsupported
major version and duplicate JSON keys are rejected.

Use a `sha256` digest to verify artifact bytes. Community submission automation
records the digest it computes from the actual archive; a submitted checksum
mismatch fails validation. The generic current-entry reader still accepts
entries without a digest. Historical releases require their own digest.

Catalog bundle download URLs must use HTTPS, or HTTP on localhost, and resolve
to a bundle manifest or ZIP containing root-level `bundle.yml`. The fetched
manifest's ID and version must match the selected catalog entry. Local paths
and `file://` are not accepted as bundle download URLs; pass local bundle
sources directly to `bundle install`.

Community submissions have a narrower publishing contract: a versioned,
tag-pinned GitHub release ZIP asset. See the publishing guide.

## Release history

An entry can add approved historical releases alongside its current release:

```json
{
  "id": "team-setup",
  "version": "1.2.0",
  "download_url": "https://example.com/team-setup-1.2.0.zip",
  "releases": {
    "1.1.0": {
      "download_url": "https://example.com/team-setup-1.1.0.zip",
      "sha256": "<64-character SHA-256 digest>"
    }
  }
}
```

This is an entry fragment, not a complete catalog. Replace the digest
placeholder before use. Each historical record needs its own HTTPS (or
localhost HTTP) `download_url` and 64-character hexadecimal SHA-256 digest.
A digest may have a case-insensitive `sha256:` prefix and surrounding
whitespace; other algorithm prefixes are rejected.

History keys must be strict SemVer values that are PEP 440-comparable. They
cannot duplicate the current version or each other, including equivalent
spellings such as `1.0.0-rc.1` and `1.0.0-rc1`. A historical record cannot
contain `id`, `version`, or `releases`.

Shared metadata such as name, description, and author is inherited unless
overridden. Release-specific `requires`, `provides`, and `verified` are not
inherited: supply them on each historical record, or that release has no
requirements, no provided counts, and `community` trust.

```bash
specify bundle info team-setup --versions
specify bundle install team-setup --version 1.1.0
```

Equivalent version spellings such as `v1.1.0` and `1.1.0` select the same
release; the catalog key spelling is display-only. Exact bundle release
selection never changes component pins in the fetched manifest.
`bundle update` always selects the current release.

History is validated when the catalog source loads. Malformed history fails
any operation that consults that source. An ID lookup can leave malformed
lower-precedence sources unobserved after finding a winner; search loads all
sources, so even shadowed malformed entries fail search.

Existing single-release catalogs remain valid. First-party and community
bundle catalogs currently advertise one release per bundle, not historical
retention.

## See also

- [Bundle CLI reference](cli.md)
- [Manifest and source assertions](api.md)
- [Publishing and community submission](publishing.md)
- [Community bundles](../community/bundles.md)
- [Shared catalog concepts](../overview/catalogs.md)
