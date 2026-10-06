# Spec Kit Integration Catalog

The integration catalog enables discovery, versioning, and distribution of AI agent integrations for Spec Kit.

## Catalog Files

### Built-In Catalog (`catalog.json`)

Contains integrations that ship with Spec Kit. These are maintained by the core team and always installable.

### Community Catalog (`catalog.community.json`)

Community-contributed integrations. The default community source is
discovery-only: listing an adapter is neither installation permission nor a
code audit. Review external code before using an install-enabled catalog.

## Catalog Configuration

The catalog stack is resolved in this order (first match wins):

1. **Environment variable** — `SPECKIT_INTEGRATION_CATALOG_URL` overrides all catalogs with a single URL
2. **Project config** — `.specify/integration-catalogs.yml` in the project root
3. **User config** — `~/.specify/integration-catalogs.yml` in the user home directory
4. **Built-in defaults** — `catalog.json` + `catalog.community.json`

Example `integration-catalogs.yml`:

```yaml
catalogs:
  - url: "https://example.com/my-catalog.json"
    name: "my-catalog"
    priority: 1
    install_allowed: true
```

## CLI Commands

```bash
# List built-in and trusted installed integrations
specify integration list

# Browse full catalog (built-in + community)
specify integration list --catalog

# Install an integration
specify integration install copilot

# Register a reviewed private catalog and install its external adapter
specify integration catalog add https://example.com/catalog.json --name samples
specify integration install sample-agent

# Non-interactive install, after reviewing and trusting the adapter
specify integration install sample-agent --trust-integration

# Make an installed adapter the default
specify integration use sample-agent

# Upgrade the current integration (diff-aware)
specify integration upgrade

# Upgrade with force (overwrite modified files)
specify integration upgrade --force
```

## Integration Descriptor (`integration.yml`)

Each external integration package includes an adapter-only `integration.yml`
descriptor and a root `__init__.py` exporting an `IntegrationBase` subclass.
No command inventory or copied core templates are needed:

```yaml
schema_version: "1.0"
integration:
  id: "sample-agent"
  name: "Sample Agent"
  version: "1.0.0"
  description: "Adapter for Sample Agent"
  license: "MIT"
requires:
  speckit_version: ">=1.1.2.dev0"
  tools:
    - name: "sample-agent"
      required: true
```

`requires.tools` is optional; omit it for adapters with no required executable.
Optional legacy `provides` metadata remains valid but does not supply host
commands. See [integration design](../design/integration.md#external-adapter-package-contract)
for class metadata, runtime methods, tools, and storage requirements.

## Catalog Schema

Both catalog files follow the same JSON schema:

```json
{
  "schema_version": "1.0",
  "updated_at": "2026-04-08T00:00:00Z",
  "catalog_url": "https://...",
  "integrations": {
    "sample-agent": {
      "id": "sample-agent",
      "name": "Sample Agent",
      "version": "1.0.0",
      "description": "Adapter for Sample Agent",
      "download_url": "https://example.com/sample-agent/1.0.0/sample-agent.zip",
      "tags": ["cli"]
    }
  }
}
```

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `schema_version` | string | Must be `"1.0"` |
| `updated_at` | string | Optional ISO 8601 timestamp |
| `integrations` | object | Map of integration ID → metadata |

### Integration Entry Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | No | Optional explicit ID; must match the map key |
| `name` | string | Yes | Human-readable display name |
| `version` | string | Yes | PEP 440 version (e.g., `1.0.0`, `1.0.0a1`) |
| `description` | string | Yes | One-line description |
| `author` | string | No | Author name or organization |
| `repository` | string | No | Source repository URL |
| `license` | string | No | License identifier matching the descriptor |
| `tags` | array | No | Searchable tags (e.g., `["cli", "ide"]`) |
| `download_url` | string | External installs | Pinned ZIP, tar.gz, or tgz archive URL; HTTPS or loopback HTTP |
| `sha256` | string | No | 64-character hexadecimal SHA-256 of the archive |
| `requires` | object | No | Must match descriptor requirements when supplied |

The map key and any declared `id` must match `integration.id`. Name, version,
description, and optional author/repository/license metadata must match the
descriptor. Built-in entries need no download fields because their
implementations ship with the CLI.

Registering a catalog with `integration catalog add` creates an install-enabled
project source. Set `install_allowed: false` in its configuration to permit
discovery only. This policy cannot be overridden with `--trust-integration` or
`--force`. Each external install/update prompts before downloading/importing
Python unless explicitly pre-authorized with `--trust-integration`.
Authenticated GitHub assets use the existing Spec Kit authentication providers.

Installed code is stored in `.specify/integrations/packages/<id>/` with trust,
provenance, and hashes in `packages.json`. Generated files have a separate
hash-tracked `<id>.manifest.json`; new CLI processes load the trusted package
without fetching the catalog. An upgrade fetches the catalog's current version
and checks its descriptor again. Do not edit installed package code in place:
publish a new archive/version and upgrade instead.
Catalog management/discovery and `integration info` remain metadata-only and do
not import adapters. Forced upgrade/uninstall can recover damaged installed code
using validated ownership metadata, without bypassing source policy or trust.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to add integrations to the community catalog.
