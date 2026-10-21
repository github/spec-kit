# Contributing Integrations

This guide covers built-in integrations, external adapter development, and
community catalog submissions.

Start with the [agent integration design](https://github.com/github/spec-kit/blob/main/design/integration.md)
for implementation contracts, ownership, and delivery requirements.

## Adding a Built-In Integration

Built-in integrations are maintained by the Spec Kit core team and ship with the CLI.

For checkout setup, see [local development](../local-development.md). Follow the
[contributor testing guidance](https://github.com/github/spec-kit/blob/main/CONTRIBUTING.md#testing-deterministic-behavior)
and [validation flow](https://github.com/github/spec-kit/blob/main/CONTRIBUTING.md#recommended-validation-flow),
then the [integration PR requirements](https://github.com/github/spec-kit/blob/main/CONTRIBUTING.md#integration-pull-requests).

### Checklist

1. **Create the integration subpackage** under `src/specify_cli/integrations/<package_dir>/`
   using the integration key with hyphens replaced by underscores for `<package_dir>`.
2. **Implement the integration class** following [Adding an agent](https://github.com/github/spec-kit/blob/main/design/integration.md#adding-an-agent).
3. **Register the integration** in `src/specify_cli/integrations/__init__.py`.
4. **Add tests** under `tests/integrations/test_integration_<package_dir>.py`.
5. **Add a catalog entry** in `integrations/catalog.json`.
6. **Update documentation:** add `docs/integrations/<key>.md` and link it from
   the [integration index](index.md) and [navigation](../toc.yml).
   Update the [catalog reference](catalog.md) if needed and
   [integration design](https://github.com/github/spec-kit/blob/main/design/integration.md)
   if the contract changes.

Use the [catalog schema](catalog.md#catalog-schema) for the built-in entry format.

## Developing an External Adapter

Implement and package your adapter using the
[external adapter contract](https://github.com/github/spec-kit/blob/main/design/integration.md#external-adapter-package-contract).
The [descriptor reference](catalog.md#integration-descriptor-integrationyml)
documents package metadata; the [catalog schema](catalog.md#catalog-schema)
documents published entries.

For local installation and trust decisions, follow
[catalog-installed external adapters](cli.md#catalog-installed-external-adapters).
See [upgrading an integration](cli.md#upgrade-an-integration) for update behavior.

### Validate Your Adapter

Test your package through the public path: register a local loopback test
catalog, install its neutral adapter, start a fresh CLI process, register
extension/preset contributions, and exercise command/prompt workflow dispatch
with a harmless process double.

Cover the [lifecycle contract](https://github.com/github/spec-kit/blob/main/design/integration.md#storage-loading-and-lifecycle),
including:

- Invalid metadata/classes, trust denial, unsafe archives, setup errors, and
  upgrade/uninstall failures.
- Package code kept separate from generated-file manifests; rollback and
  cleanup that preserve modified files, unrelated user files, independent
  workflow progress, and concurrent edits.
- Metadata-only commands without import side effects; forced recovery of
  damaged packages using local ownership proof, and manual-cleanup warnings
  when that proof is absent.
- Symlinked write destinations, reserved roots, unsafe legacy paths, and
  case-insensitive overlap between primary and legacy output paths.
- Overlapping project dispatch and lazy relative imports that retain the
  correct adapter without serializing independent agent processes.
- For event-capable adapters, event-only extension add/remove and enable/disable
  in fresh CLI processes, including explicit errors when installed code cannot load.

## Submitting to the Community Catalog

External developers can list integrations in `integrations/catalog.community.json`
for discovery. Catalog maintainers review listing metadata, not adapter
implementations; users must vet the code. A listing does not grant installation
permission.

### Prerequisites

1. **Working external adapter** — packaged and validated as described above.
2. **Public repository** — hosted on GitHub or similar.
3. **Documentation** — README with usage instructions.
4. **License** — open source license file.

Prepare your entry using the [catalog schema](catalog.md#catalog-schema).
Metadata must match the packaged descriptor. Publish a pinned archive URL;
an archive SHA-256 digest is recommended.

### Submission

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
