# Contributing to the Integration Catalog

This guide covers adding integrations to both the **built-in** and **community** catalogs.

## Adding a Built-In Integration

Built-in integrations are maintained by the Spec Kit core team and ship with the CLI.

### Checklist

1. **Create the integration subpackage** under `src/specify_cli/integrations/<name>/`
2. **Implement the integration class** extending `MarkdownIntegration`, `TomlIntegration`, or `SkillsIntegration`
3. **Register the integration** in `src/specify_cli/integrations/__init__.py`
4. **Add tests** under `tests/integrations/test_integration_<name>.py`
5. **Add a catalog entry** in `integrations/catalog.json`
6. **Update documentation** in `AGENTS.md` and `README.md`

### Catalog Entry Format

Add your integration to `integrations/catalog.json`:

```json
{
  "my-agent": {
    "id": "my-agent",
    "name": "My Agent",
    "version": "1.0.0",
    "description": "Integration for My Agent",
    "author": "spec-kit-core",
    "repository": "https://github.com/github/spec-kit",
    "tags": ["cli"]
  }
}
```

## Adding a Community Integration

Community integrations are contributed by external developers and listed in `integrations/catalog.community.json` for discovery.

### Prerequisites

1. **Working integration** — tested with `specify integration install`
2. **Public repository** — hosted on GitHub or similar
3. **`integration.yml` descriptor** — valid descriptor file (see below)
4. **Documentation** — README with usage instructions
5. **License** — open source license file

### `integration.yml` Descriptor

Every community integration must include an `integration.yml`:

```yaml
schema_version: "1.0"
integration:
  id: "my-agent"
  name: "My Agent"
  version: "1.0.0"
  description: "Integration for My Agent"
  author: "your-name"
  repository: "https://github.com/your-name/speckit-my-agent"
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
  scripts:
    - update-context.sh
```

### Descriptor Validation Rules

| Field | Rule |
|-------|------|
| `schema_version` | Must be `"1.0"` |
| `integration.id` | Lowercase alphanumeric + hyphens (`^[a-z0-9-]+$`) |
| `integration.version` | Valid semantic version |
| `requires.speckit_version` | Required field; current validation checks presence only |
| `provides` | Must include at least one command or script |
| `provides.commands[].name` | String identifier |
| `provides.commands[].file` | Relative path to template file |

### Submitting to the Community Catalog

1. **Fork** the [spec-kit repository](https://github.com/github/spec-kit)
2. **Add your entry** to `integrations/catalog.community.json`:

```json
{
  "my-agent": {
    "id": "my-agent",
    "name": "My Agent",
    "version": "1.0.0",
    "description": "Integration for My Agent",
    "author": "your-name",
    "repository": "https://github.com/your-name/speckit-my-agent",
    "tags": ["cli"]
  }
}
```

3. **Open a pull request** with:
   - Your catalog entry
   - Link to your integration repository
   - Confirmation that `integration.yml` is valid

### Version Updates

To update your integration version in the catalog:

1. Release a new version of your integration
2. Open a PR updating the `version` field in `catalog.community.json`
3. Ensure backward compatibility or document breaking changes

## Upgrade Workflow

The `specify integration upgrade` command supports diff-aware upgrades:

1. **Hash comparison** — the manifest records SHA-256 hashes of all installed files
2. **Modified file detection** — files changed since installation are flagged
3. **Safe default** — the upgrade blocks if any installed files were modified since installation
4. **Forced reinstall** — passing `--force` overwrites modified files with the latest version

```bash
# Upgrade current integration (blocks if files are modified)
specify integration upgrade

# Force upgrade (overwrites modified files)
specify integration upgrade --force
```
