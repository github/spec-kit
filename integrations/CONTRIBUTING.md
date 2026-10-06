# Contributing to the Integration Catalog

This guide covers adding integrations to both the **built-in** and **community** catalogs.

## Adding a Built-In Integration

Built-in integrations are maintained by the Spec Kit core team and ship with the CLI.

### Checklist

1. **Create the integration subpackage** under `src/specify_cli/integrations/<package_dir>/`
   — `<package_dir>` matches the integration key when it contains no hyphens (e.g., `gemini`), or replaces hyphens with underscores when it does (e.g., key `cursor-agent` → directory `cursor_agent/`, key `kiro-cli` → directory `kiro_cli/`). Python package names cannot use hyphens.
2. **Implement the integration class** using the appropriate base class from [integration design](../design/integration.md)
3. **Register the integration** in `src/specify_cli/integrations/__init__.py`
4. **Add tests** under `tests/integrations/test_integration_<package_dir>.py`
5. **Add a catalog entry** in `integrations/catalog.json`
6. **Update documentation** in [integration design](../design/integration.md), [supported integrations](../docs/reference/integrations.md), and this catalog's README as needed

### Catalog Entry Format

Add your integration under the top-level `integrations` key in `integrations/catalog.json`:

```json
{
  "schema_version": "1.0",
  "integrations": {
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
}
```

## Adding a Community Integration

Community integrations are contributed by external developers and listed in `integrations/catalog.community.json` for discovery.

### Prerequisites

1. **Working external integration** — distribute a standalone ZIP or tar.gz
   with root `integration.yml` and `__init__.py`; a discovery-only community
   listing does not grant installation permission
2. **Public repository** — hosted on GitHub or similar
3. **`integration.yml` descriptor** — valid descriptor file (see below)
4. **Documentation** — README with usage instructions
5. **License** — open source license file

### `integration.yml` Descriptor

Every community integration must include an `integration.yml`:

```yaml
schema_version: "1.0"
integration:
  id: "sample-agent"
  name: "Sample Agent"
  version: "1.0.0"
  description: "Adapter for Sample Agent"
  author: "your-name"
  repository: "https://github.com/your-name/speckit-sample-agent"
  license: "MIT"
requires:
  speckit_version: ">=1.1.2.dev0"
  tools:
    - name: "sample-agent"
      required: true
```

The root module exports exactly one adapter subclass, whose `key` and
`config.name` match the descriptor. Prefer `SkillsIntegration`,
`MarkdownIntegration`, `TomlIntegration`, or `YamlIntegration` to render the
host templates. Do not duplicate or enumerate Spec Kit's core commands.
Additional relative-import helper modules are allowed; external packages using
only the host API and standard library require neither pip installation nor
changes to the source registry. See the complete
[external adapter contract](../design/integration.md#external-adapter-package-contract).

### Descriptor Validation Rules

| Field | Rule |
|-------|------|
| `schema_version` | Must be `"1.0"` |
| `integration.id` | External package IDs start with a lowercase letter/digit, then lowercase alphanumeric + hyphens (`^[a-z0-9][a-z0-9-]*$`); built-in and Windows device names are reserved |
| `integration.version` | Valid PEP 440 version (parsed with `packaging.version.Version()`) |
| `requires.speckit_version` | Required valid PEP 440 constraint, enforced during install and load |
| `requires.tools` | Optional list; required executables are checked on PATH; version detection belongs to the adapter |
| `provides` | Optional legacy metadata; an adapter need not provide commands or scripts |
| `provides.commands[].name` | String identifier |
| `provides.commands[].file` | Relative path to template file |

Publish a pinned archive `download_url`, preferably with a hexadecimal archive
`sha256` digest. The catalog's ID/name/version/description and any optional
descriptor metadata or requirements must match `integration.yml`.
Never rely on importing a catalog to register your class: discovery does not
execute code. Installation from an install-enabled source requires an explicit
trust decision before import. Catalog maintainers review listing metadata, not
adapter implementations; users must vet the code.
Consent is user-local in `~/.specify/integration-trust.json`, bound to the
canonical project root, adapter ID, and verified package digest. Do not ship a
trust registry or rely on project metadata to authorize execution. A copied
project must reauthorize through a reviewed, install-enabled catalog using
`specify integration upgrade sample-agent --force --trust-integration`.

### Submitting to the Community Catalog

1. **Fork** the [spec-kit repository](https://github.com/github/spec-kit)
2. **Add your entry** under the `integrations` key in `integrations/catalog.community.json`:

   ```json
   {
     "schema_version": "1.0",
     "integrations": {
       "sample-agent": {
         "id": "sample-agent",
         "name": "Sample Agent",
         "version": "1.0.0",
         "description": "Adapter for Sample Agent",
         "author": "your-name",
         "repository": "https://github.com/your-name/speckit-sample-agent",
         "download_url": "https://github.com/your-name/speckit-sample-agent/releases/download/v1.0.0/sample-agent.zip",
         "tags": ["cli"]
       }
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
2. Open a PR updating the version, pinned archive URL, and digest (if provided)
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

# Upgrade a reviewed external adapter without a trust prompt
specify integration upgrade sample-agent --trust-integration
```

Test your package through the public path: register a local loopback test
catalog, install its neutral adapter, start a fresh CLI process, register
extension/preset contributions, and exercise command/prompt workflow dispatch
with a harmless process double. Include failures for invalid metadata/classes,
trust denial, unsafe archives, setup errors, and upgrades/uninstall. Keep
package code separate from generated-file manifests and verify rollback and
modified-file preservation.

Use manifest/base-class write helpers so failed lifecycle operations can restore
only the files your adapter changed. Legacy `record_existing()` writes are
covered within the adapter's declared output root; writes elsewhere must use
`record_file()` or host write helpers. Do not claim unrelated user files. Test
metadata-only commands without import side effects, forced recovery of damaged
installed packages, and rollback that preserves independent workflow progress
and concurrent user edits.
Host helpers reject symlinked write destinations; owned leaf links may be
unlinked without following them. Exercise overlapping project dispatch and lazy
relative imports: the host pins the correct adapter for each dispatch without
serializing independent agent processes. Forced recovery uses user-local
registrar/path ownership, not editable project metadata. Without that proof,
old-only artifacts are preserved with an explicit manual-cleanup warning.
