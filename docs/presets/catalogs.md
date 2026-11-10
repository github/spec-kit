# Preset catalogs

Catalogs discover presets and select releases for ID-based installation.
Their priorities order catalog sources, independently of the installed
preset priorities that determine artifact resolution.

## Discovery and trust

The built-in stack contains:

| Name | Source | Default permission |
| --- | --- | --- |
| `default` | [First-party preset catalog](https://github.com/github/spec-kit/blob/main/presets/catalog.json) | Installation allowed |
| `community` | [Community preset catalog](https://github.com/github/spec-kit/blob/main/presets/catalog.community.json) | Discovery only |

Community presets are independently maintained. Maintainers check catalog
entries for completeness and format, not the safety or quality of the
preset code. They do not review, audit, endorse, or support that code.
Users must vet a preset's source before installation and use.

> [!IMPORTANT]
> A project's `.specify/preset-catalogs.yml` can point `add` and `search` at a
> catalog you did not choose. Run `specify preset catalog list` in unfamiliar
> projects and inspect install-allowed sources. Project configuration and
> `install_allowed: true` are not evidence of code review. Only permit
> installation from catalogs you own or have vetted; leave unfamiliar and
> community sources discovery-only.

After vetting a community release, an explicit `specify preset add --from
<archive-url>` installs that archive without catalog lookup. This is a
source choice, not a bypass that makes unreviewed content safe.

## Catalog configuration

The first usable configuration level supplies the whole stack; project and
user entries do not automatically augment the defaults:

| Order | Source |
| --- | --- |
| First | `SPECKIT_PRESET_CATALOG_URL` environment variable |
| Next | Project `.specify/preset-catalogs.yml` |
| Next | User `~/.specify/preset-catalogs.yml` |
| Last | Built-in `default` and `community` catalogs |

The environment variable selects one catalog named `custom` with
installation allowed. Use it only with a vetted source. A config file with
no valid catalog entries falls through to the next level; malformed YAML
or invalid configured URLs/priorities raise validation errors rather than
silently selecting another source.

Example project configuration:

```yaml
catalogs:
  - name: "my-org-presets"
    url: "https://catalog.example.com/presets.json"
    priority: 5
    install_allowed: true
    description: "Our vetted presets"
```

| Entry field | Meaning |
| --- | --- |
| `url` | HTTPS catalog URL, including for local development; plain HTTP is rejected |
| `name` | Source name displayed by the CLI and used for provenance |
| `priority` | Lower numbers are checked first |
| `install_allowed` | Whether ID-based installation is permitted; default `false` |
| `description` | Optional source description |

Use the CLI to manage project entries:

```bash
specify preset catalog list
specify preset catalog add https://catalog.example.com/presets.json \
  --name my-org-presets --priority 5 --install-allowed
specify preset catalog remove my-org-presets
```

Only use `--install-allowed` after vetting the source. Omitting it adds a
discovery-only catalog. Adding the first project entry replaces the implicit
built-in stack; explicitly include other sources if you still need them.
The user-level file is configured separately, not by `catalog add`.

## Entry schema

Catalog JSON has a `schema_version` field and a `presets` object keyed by
preset ID. The following illustrates a downloadable current release for a
private catalog; replace the example URLs and digest before use:

```json
{
  "schema_version": "1.0",
  "updated_at": "2026-11-03T00:00:00Z",
  "presets": {
    "team-traceability": {
      "id": "team-traceability",
      "name": "Team Traceability",
      "description": "Adds team traceability requirements to specifications",
      "author": "Example Team",
      "version": "2.0.0",
      "download_url": "https://github.com/example/team-traceability/archive/refs/tags/v2.0.0.zip",
      "sha256": "<64 hexadecimal digits for this archive>",
      "repository": "https://github.com/example/team-traceability",
      "documentation": "https://github.com/example/team-traceability/blob/main/README.md",
      "license": "MIT",
      "requires": {
        "speckit_version": ">=0.9.0"
      },
      "provides": {
        "templates": 1,
        "commands": 0,
        "scripts": 0
      },
      "tags": ["traceability", "governance"],
      "created_at": "2026-11-03",
      "updated_at": "2026-11-03"
    }
  }
}
```

Catalog `provides` holds contribution counts, unlike the manifest's
`provides.templates` list. Keep metadata consistent with the published
manifest. `bundled: true` can describe a first-party preset shipped inside
Spec Kit; such an entry may have no download URL and requires the matching
packaged files rather than a network download.

Single-version legacy entries remain valid. Current releases may omit
`sha256`; when present, the digest is checked before installation.
Community submission automation computes and records the downloaded
archive's digest even when the submitter did not provide one.

## Historical releases

To advertise older releases, add a `releases` mapping keyed by version:

```json
{
  "version": "2.0.0",
  "download_url": "https://example.com/team-traceability-2.0.0.zip",
  "sha256": "<64 hexadecimal digits for the current archive>",
  "releases": {
    "1.5.0": {
      "download_url": "https://example.com/team-traceability-1.5.0.zip",
      "sha256": "<64 hexadecimal digits for the older archive>",
      "requires": {"speckit_version": ">=0.8.0"},
      "provides": {"templates": 1, "commands": 0, "scripts": 0}
    }
  }
}
```

This is the release-related portion of one entry, not a complete catalog.
Each historical record needs its own HTTPS archive URL (or loopback HTTP
for development) and a 64-digit SHA-256 digest. Digests may have a
case-insensitive `sha256:` prefix and surrounding whitespace; other
algorithm prefixes are rejected.

Optional historical `requires` and `provides` describe that release; they
do not inherit the current release's values when absent. Shared metadata
such as name, description, and catalog permissions is inherited.
Historical `requires.extensions` uses the manifest's string-or-mapping
dependency format. Do not put `id`, `version`, nested `releases`, or internal
`_catalog_name` / `_install_allowed` fields inside a historical record.

Version keys must be distinct, including PEP 440-equivalent spellings, and
cannot repeat the current version. Duplicate JSON keys are rejected before
parsing can discard a release record.

```bash
specify preset info team-traceability --versions
specify preset add team-traceability --version 1.5.0
```

Available versions list the current release first, then historical versions
in descending order. Exact release selection checks the downloaded
manifest's ID and version before modifying installed presets.

The community catalog remains discovery-only and need not publish release
histories. Bundle pin resolution is a separate capability; adding preset
release records alone does not make bundle pins installable.

## Lookup and failure behavior

Catalogs are checked in ascending priority order. The highest-precedence
entry for an ID supplies both its release metadata and install permission.
A lower-priority source cannot provide a missing historical version or
override a discovery-only decision.

For exact ID lookup, malformed or oversized catalogs encountered before a
winning entry fail resolution. A malformed lower-priority source cannot
block an already found higher-priority entry. A non-object entry fails an
exact lookup for its own ID, but all-catalog searches skip that entry and
retain other valid ones.

Searches across all sources still fail on malformed catalogs. Historical
release validation applies to winning entries; invalid history from a
shadowed entry does not block a valid higher-priority replacement.
Unreachable sources can be skipped when another source is readable. If
every source fails, lookup, including `info --versions`, reports the fetch
error rather than claiming no versions exist.

## Cache and private sources

Catalogs are cached for one hour in `.specify/presets/.cache/`. The default
catalog retains legacy `catalog.json` and `catalog-metadata.json` filenames;
other sources use URL-hashed cache filenames. Cache payloads undergo the
same shape validation as network responses; unreadable or invalid cached
content triggers a fetch.

Private catalog and archive requests use the shared opt-in authentication
configuration in `~/.specify/auth.json`. A token environment variable by
itself does not enable authentication. Configure only the hosts authorized
to receive credentials; the authentication reference covers GitHub CLI,
token, enterprise, and other supported providers. Do not put credentials in
catalog JSON or source URLs.

## See also

- [Preset overview](overview.md)
- [Catalog CLI commands](cli.md#catalog-management)
- [Manifest API](api.md)
- [Publishing and community submission](publishing.md)
- [Cross-component catalog guidance](../overview/catalogs.md)
- [Catalog and download authentication](../reference/authentication.md)
- [Community presets](../community/presets.md)
