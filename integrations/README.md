# Spec Kit Integration Catalog

The integration catalog enables discovery, versioning, and distribution of AI agent integrations for Spec Kit.

## Catalog Files

### Built-In Catalog (`catalog.json`)

Contains integrations that ship with Spec Kit. These are maintained by the core team and always installable.

### Community Catalog (`catalog.community.json`)

Community-contributed integrations. Listed for discovery only — users install from the source repositories.

## CLI Commands

```bash
# List built-in integrations (default)
specify integration list

# Browse full catalog (built-in + community)
specify integration list --catalog

# Install an integration
specify integration install copilot

# Upgrade the current integration (diff-aware)
specify integration upgrade

# Upgrade with force (overwrite modified files)
specify integration upgrade --force
```

## Integration Descriptor (`integration.yml`)

Each integration can include an `integration.yml` descriptor that documents its metadata, requirements, and provided commands/scripts:

```yaml
schema_version: "1.0"
integration:
  id: "my-agent"
  name: "My Agent"
  version: "1.0.0"
  description: "Integration for My Agent"
  author: "my-org"
  repository: "https://github.com/my-org/speckit-my-agent"
  license: "MIT"
requires:
  speckit_version: ">=0.6.0"
  tools:
    - name: "my-agent"
      version: ">=1.0.0"
      required: true
provides:
  commands:
    - name: "speckit.specify"
      file: "templates/speckit.specify.md"
    - name: "speckit.plan"
      file: "templates/speckit.plan.md"
  scripts:
    - update-context.sh
    - update-context.ps1
```

## Catalog Schema

Both catalog files follow the same JSON schema:

```json
{
  "schema_version": "1.0",
  "updated_at": "2026-04-08T00:00:00Z",
  "catalog_url": "https://...",
  "integrations": {
    "my-agent": {
      "id": "my-agent",
      "name": "My Agent",
      "version": "1.0.0",
      "description": "Integration for My Agent",
      "author": "my-org",
      "repository": "https://github.com/my-org/speckit-my-agent",
      "tags": ["cli"]
    }
  }
}
```

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `schema_version` | string | Must be `"1.0"` |
| `updated_at` | string | ISO 8601 timestamp |
| `integrations` | object | Map of integration ID → metadata |

### Integration Entry Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique ID (lowercase alphanumeric + hyphens) |
| `name` | string | Yes | Human-readable display name |
| `version` | string | Yes | Semantic version |
| `description` | string | Yes | One-line description |
| `author` | string | No | Author name or organization |
| `repository` | string | No | Source repository URL |
| `tags` | array | No | Searchable tags (e.g., `["cli", "ide"]`) |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to add integrations to the community catalog.
