# Extension Catalogs

Extension catalogs control where `specify extension search` and `add` look for
extensions. A catalog stack is an ordered list of sources searched together.
Lower catalog priority numbers take precedence when the same extension ID
appears in more than one source.

## Trust model: discovery-only vs. install sources

Catalogs come in two kinds, and the distinction is a **security boundary**:

- **Install sources** (`install_allowed: true`) are catalogs you trust as a place
  to install from. The built-in `default` catalog is one, as is a catalog you
  author and vet yourself.
- **Discovery-only** catalogs (`install_allowed: false`) are searchable surfaces
  for finding extensions, but are not installable. The built-in `community`
  catalog is already active for search; you do not need to add it.

| Priority | Built-in catalog | Install allowed | Purpose |
| --- | --- | --- | --- |
| 1 | `catalog.json` (`default`) | Yes | Installable extensions |
| 2 | `catalog.community.json` (`community`) | No | Discover community extensions |

Community entries are unvetted third-party code. Maintainers check catalog
metadata, not extension code. You must vet an extension before installing it.

> [!WARNING]
> Do not flip an unvetted discovery-only catalog to `install_allowed`. That
> defeats the separation between discovery and installation.

There are two ways to install something found through the community catalog:

1. **Install a single vetted release directly.** Get the candidate archive URL
   from `specify extension info <name>`, which prints a "Candidate archive" URL
   for uninstalled discovery-only entries. Treat the URL as untrusted until you have reviewed
   that release archive, then install it:

   ```bash
   specify extension info <name>
   specify extension add <name> --from <archive-url>
   ```

2. **Curate your own catalog.** For a governed, reusable organization source,
   review the releases yourself and mark only that controlled catalog
   `install_allowed: true`.

## Catalog resolution order

The active stack is selected in this order:

1. **Environment variable:** `SPECKIT_CATALOG_URL` overrides the entire stack.
2. **Project config:** `.specify/extension-catalogs.yml`.
3. **User config:** `~/.specify/extension-catalogs.yml`.
4. **Built-in defaults:** `default` and `community`.

An existing project configuration takes precedence over user configuration and
built-in defaults. Empty or malformed files, including `catalogs: []`, fail
closed with a validation error rather than falling back to another source.
Remove the configuration file to use the next source in the resolution order,
or populate it with valid catalog entries.
Within the selected stack, catalogs are checked by priority; the first matching
extension ID wins. Exact-version lookup does not fall back to another catalog
when the winning entry lacks the requested version.

## Managing catalogs

```bash
specify extension catalog list
specify extension catalog --help

# Add an internal source you own and vet
specify extension catalog add \
  --name "internal" \
  --priority 2 \
  --install-allowed \
  --description "Our approved extensions" \
  https://internal.company.com/spec-kit/catalog.json

# Add a discovery-only source (the default permission)
specify extension catalog add \
  --name "partner" \
  --priority 5 \
  https://partner.example.com/spec-kit/catalog.json

specify extension catalog remove internal
```

These commands edit the project's `.specify/extension-catalogs.yml`.
Re-adding the same named catalog with identical settings succeeds without
changing configuration; different settings are rejected. The complete option
reference is in [Catalog management](cli.md#catalog-management).

You can also edit the configuration directly:

```yaml
catalogs:
  - name: "default"
    url: "https://raw.githubusercontent.com/github/spec-kit/main/extensions/catalog.json"
    priority: 1
    install_allowed: true
    description: "Built-in catalog of installable extensions"

  - name: "internal"
    url: "https://internal.company.com/spec-kit/catalog.json"
    priority: 2
    install_allowed: true
    description: "Our approved extensions"

  - name: "community"
    url: "https://raw.githubusercontent.com/github/spec-kit/main/extensions/catalog.community.json"
    priority: 3
    install_allowed: false
    description: "Community-contributed extensions (discovery only)"
```

## Organization catalog customization

Organizations use private catalogs to control available releases, integrate
internal tools, meet compliance requirements, or support air-gapped networks.

### Create a catalog

Create a `catalog.json` file containing the releases your team has vetted:

```json
{
  "schema_version": "1.0",
  "updated_at": "2026-02-03T00:00:00Z",
  "catalog_url": "https://your-org.com/spec-kit/catalog.json",
  "extensions": {
    "jira": {
      "name": "Jira Integration",
      "id": "jira",
      "description": "Create Jira issues from spec-kit artifacts",
      "author": "Your Organization",
      "version": "2.1.0",
      "download_url": "https://github.com/your-org/spec-kit-jira/archive/refs/tags/v2.1.0.zip",
      "repository": "https://github.com/your-org/spec-kit-jira",
      "license": "MIT",
      "requires": {
        "speckit_version": ">=0.1.0",
        "tools": [
          {"name": "atlassian-mcp-server", "required": true}
        ]
      },
      "provides": {
        "commands": 3,
        "hooks": 1
      },
      "tags": ["jira", "atlassian", "issue-tracking"],
      "verified": true
    },
    "internal-tool": {
      "name": "Internal Tool Integration",
      "id": "internal-tool",
      "description": "Connect to internal company systems",
      "author": "Your Organization",
      "version": "1.0.0",
      "download_url": "https://internal.your-org.com/extensions/internal-tool-1.0.0.zip",
      "repository": "https://github.internal.your-org.com/spec-kit-internal",
      "license": "Proprietary",
      "requires": {
        "speckit_version": ">=0.1.0"
      },
      "provides": {
        "commands": 2
      },
      "tags": ["internal", "proprietary"],
      "verified": true
    }
  }
}
```

### Host and configure the catalog

| Method | URL example | Use case |
| --- | --- | --- |
| GitHub Pages | `https://your-org.github.io/spec-kit-catalog/catalog.json` | Public or org-visible |
| Internal web server | `https://internal.company.com/spec-kit/catalog.json` | Corporate network |
| S3/cloud storage | `https://s3.amazonaws.com/your-bucket/catalog.json` | Cloud-hosted teams |
| Local file server | `http://localhost:8000/catalog.json` | Development/testing |

URLs must use HTTPS, except localhost for testing.
Add your catalog with `specify extension catalog add`, or use:

```yaml
# .specify/extension-catalogs.yml
catalogs:
  - name: "my-org"
    url: "https://your-org.com/spec-kit/catalog.json"
    priority: 1
    install_allowed: true
    description: "Our approved extensions"
```

For CI/CD or a single-catalog environment, replace the whole stack:

```bash
export SPECKIT_CATALOG_URL="https://your-org.com/spec-kit/catalog.json"
```

Check the result:

```bash
specify extension catalog list
specify extension search
specify extension add jira
```

### Private GitHub-hosted catalogs

`GH_TOKEN` or `GITHUB_TOKEN` authenticates requests to GitHub-hosted URLs
(`raw.githubusercontent.com`, `github.com`, `api.github.com`, and
`codeload.github.com`). Private catalog JSON and extension ZIPs require access
to the relevant repositories. Non-GitHub catalog URLs are fetched without
these credentials.

```bash
export GITHUB_TOKEN=$(gh auth token)
specify extension search jira
specify extension add jira-sync
```

### Curated and air-gapped environments

A catalog can list only the approved extensions, such as `jira` and `github`.
Configure it as the sole catalog if only those entries should appear in search.
Private/proprietary extensions can point to internal archive hosts; public
catalog submission is optional.

For air-gapped networks, download vetted extension ZIPs to an internal file
server, create a catalog pointing to those internal URLs, and host the catalog
inside the network. For example, an entry can use
`"download_url": "https://files.internal/spec-kit/jira-2.1.0.zip"`.

### Development and testing

```bash
python -m http.server 8000 --directory ./my-catalog/
```

In another terminal:

```bash
export SPECKIT_CATALOG_URL="http://localhost:8000/catalog.json"
specify extension add my-new-extension
```

Catalog configuration does not prevent direct installation:

```bash
specify extension add jira
specify extension add <extension-name> --from https://github.com/someone/spec-kit-ext/archive/refs/tags/v1.0.0.zip
specify extension add --dev /path/to/extension
```

Direct URL installation shows a security warning because the archive is not
being selected through your configured catalog. Vet it before installing.

## Catalog entry schema

The following describes the catalog fields; community submission requirements
also require complete descriptive metadata.

The catalog root must contain `schema_version` and an `extensions` mapping.
Each mapping key is the authoritative extension ID; a repeated `id` field
inside the entry is optional.

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `name` | string | Yes | Human-readable name |
| `id` | string | No | Optional repetition of the authoritative mapping key |
| `version` | string | Yes | Current extension version |
| `download_url` | string | For archive releases | URL to the release archive; bundled entries can omit it |
| `bundled` | boolean | No | Marks an extension shipped with Spec Kit, resolved from the running distribution |
| `repository` | string | No | Source code URL (required for community submission) |
| `description` | string | Yes | Brief description; community submissions require under 200 characters |
| `author` | string | No | Author/organization (required for submission) |
| `license` | string | No | SPDX license identifier (required for submission) |
| `homepage`, `documentation`, `changelog` | string | No | Related URLs |
| `sha256` | string | No | Archive SHA-256 digest; verified before install when supplied |
| `requires.speckit_version` | string | No | Version constraint (required for submission) |
| `requires.tools` | array | No | Objects with required `name`, optional `version`, and `required` (default `false`) |
| `provides.commands`, `provides.hooks` | number | No | Capability counts |
| `tags` | array | No | Search tags (2-10 recommended) |
| `verified` | boolean | No | Metadata flag set by maintainers, default `false`; not a code-audit guarantee |
| `created_at`, `updated_at` | string | No | ISO 8601 timestamps |
| `releases` | object | No | Historical releases keyed by version |

### Historical releases

Catalogs may keep the current release in the top-level fields and add older
releases in a `releases` mapping. Older single-version catalogs continue to
work unchanged. Each historical release needs its own download URL and SHA-256
digest; release-specific requirements or provided capabilities must be placed
in that release's record rather than inherited from the current one. As with
current releases, a digest may use a case-insensitive `sha256:` prefix and
surrounding whitespace.

```json
{
  "extensions": {
    "my-extension": {
      "name": "My Extension",
      "version": "0.5.1",
      "download_url": "https://example.com/my-extension-0.5.1.zip",
      "sha256": "<64-character SHA-256 for 0.5.1>",
      "releases": {
        "0.4.12": {
          "download_url": "https://example.com/my-extension-0.4.12.zip",
          "sha256": "<64-character SHA-256 for 0.4.12>"
        }
      }
    }
  }
}
```

The example omits other metadata for brevity. The current version must not be
repeated in `releases`; malformed or duplicate release records are rejected.
Equivalent PEP 440 spellings, such as `v1.0` and `1.0`, select the same release;
the catalog's advertised spelling remains visible.

Catalog-backed bundle extension pins also select historical releases from the
winning source, using that release's own archive and digest and checking the
downloaded manifest's ID and version. Bundled extensions follow the packaged
version policy: a newer compatible packaged patch can be used with a warning.
See the [bundle reference](../reference/bundles.md) for bundle installation.

## See also

- [Extension user guide](overview.md)
- [Extension CLI reference](cli.md)
- [Publishing extensions](publishing.md)
- [Community extensions](../community/extensions.md)
- [Shared catalog reference](../reference/catalogs.md)
