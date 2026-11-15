# Community Integrations

Community integrations connect Spec Kit to additional coding agents through
independently maintained external adapters.

> [!NOTE]
> Maintainers check catalog entry metadata, not adapter implementations.
> A listing is not a code audit, endorsement, support commitment, or installation
> permission. Review the adapter's source and release before installation and
> use.

## Available integrations

The [community integration catalog](https://github.com/github/spec-kit/blob/main/integrations/catalog.community.json)
currently contains no entries. Built-in integrations ship with the CLI and are
listed separately in the integration directory.

Inspect the sources active in your project and search their metadata:

```bash
specify integration catalog list
specify integration search
specify integration info <id> --versions
```

Search uses your active catalog configuration, not exclusively the community
source. The default community source is discovery-only. Installing an external
adapter requires an explicitly install-allowed catalog and a reachable package
archive; there is no direct-URL or local installation route.

## Contribute an integration

Develop and test an external adapter, publish its descriptor and pinned release
archive, then submit a catalog PR editing `integrations/catalog.community.json`.
Follow the integration contribution guide for the package contract, required
metadata, validation evidence, and version updates. Built-in integration
contributions follow a separate path in that guide.

## See also

- [Integration directory](../integrations/index.md)
- [External adapter installation](../integrations/cli.md#catalog-installed-external-adapters)
- [Catalog schema and configuration](../integrations/catalog.md)
- [Developing and submitting integrations](../integrations/contributing.md)
- [Catalog discovery and trust](../overview/catalogs.md)
