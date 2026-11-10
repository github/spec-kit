# Remote Catalog Contracts

This document records the behavior-preserving contracts of Spec Kit's
remote/catalog-backed primitives:

- extensions
- presets
- integrations
- workflows
- workflow step types
- bundles

It defines the boundary for a future shared catalog layer. It does not require
the current implementations to move into that layer, and it does not change any
existing trust, installation, network, cache, or user-interface behavior.

[Shared Command Application Architecture](shared.md) remains the governing
application-layer design. A future catalog layer is a focused domain service
below CLI and MCP adapters, not a central command dispatcher or adapter-owned
abstraction.

## Out of scope

Two other uses of the word "catalog" are intentionally separate:

- `ArtifactCatalog` resolves locally installed artifact contributions and
  composition stacks. It is not a remote source catalog.
- `specify_cli.mcp_server.catalog` is the explicit inventory of MCP command
  exposure. It describes tools and adapter metadata, not downloadable content.

Neither belongs in the shared remote catalog layer described here.

## Current source models

The implementations use two source-stack models.

### Replacement-layer catalogs

Extensions, presets, integrations, workflows, and workflow step types resolve
exactly one source layer:

1. An environment override can replace every configured/default source.
2. A project config replaces the user and built-in layers when that project
   config contributes an active stack.
3. A user config replaces the built-in layer when it contributes an active
   stack.
4. Otherwise the built-in official and community sources are used.

Within the selected layer, lower numeric `priority` means higher precedence.
Equal priorities preserve source-file order because the current loaders use a
stable sort.

The built-in official source permits installation. The built-in community
source is discovery-only. Environment overrides are currently install-enabled.
Configured sources default to discovery-only when `install_allowed` is omitted.

Environment-value normalization is not uniform. Extensions and presets test the
raw variable for presence and then strip it, so a whitespace-only value selects
the override path and fails URL validation. Integrations, workflows, and
workflow steps strip first, so a whitespace-only value is ignored and
resolution continues to project, user, or built-in configuration.

| Primitive | Environment override | Project config | User config |
| --- | --- | --- | --- |
| Extensions | `SPECKIT_CATALOG_URL` | `.specify/extension-catalogs.yml` | `~/.specify/extension-catalogs.yml` |
| Presets | `SPECKIT_PRESET_CATALOG_URL` | `.specify/preset-catalogs.yml` | `~/.specify/preset-catalogs.yml` |
| Integrations | `SPECKIT_INTEGRATION_CATALOG_URL` | `.specify/integration-catalogs.yml` | `~/.specify/integration-catalogs.yml` |
| Workflows | `SPECKIT_WORKFLOW_CATALOG_URL` | `.specify/workflow-catalogs.yml` | `~/.specify/workflow-catalogs.yml` |
| Workflow steps | `SPECKIT_STEP_CATALOG_URL` | `.specify/step-catalogs.yml` | `~/.specify/step-catalogs.yml` |

The source entry shape is effectively:

```yaml
catalogs:
  - name: team
    url: https://example.com/catalog.json
    priority: 10
    install_allowed: false
    description: Optional text
```

`name` is display/provenance data, not the content identifier used for
shadowing.

### Scope-merging bundle catalogs

Bundles merge sources by source `id` across built-in, user, and project scopes:

1. Built-in sources establish the fallback.
2. User sources replace built-in sources with the same `id`.
3. Project sources replace user or built-in sources with the same `id`.
4. Sources with distinct IDs remain in the effective stack.

The final stack sorts by `(priority, id)`, so source ID is the deterministic
tie-breaker. Bundle source configuration is project-writable through
`.specify/bundle-catalogs.yml`; callers may also supply a user config directory
when loading the stack. There is no bundle environment override.

Bundle sources use an explicit policy enum rather than a boolean:

```yaml
schema_version: "1.0"
catalogs:
  - id: team
    url: https://example.com/bundles.json
    priority: 10
    install_policy: discovery-only
```

Supported bundle source schemes are `https`, localhost `http`, `file`,
`builtin`, and local filesystem paths. The other five catalog types accept
remote HTTPS URLs, with HTTP allowed only for localhost.

## Configuration semantics

The active-stack readers for all six primitives reject a non-mapping YAML root,
a non-list non-null `catalogs` value, and non-mapping source entries. Validation
phase and accepted values otherwise differ:

- Replacement-layer loaders validate remote URLs while reading the active
  stack. Bundle resolution validates source structure while materializing
  `CatalogSource` values, but the bundle catalog command reader's `_read()`
  only validates the outer configuration shape and schema version.
  `add_source()` materializes and validates existing entries before appending,
  while `remove_source()` intentionally filters raw mappings by ID or URL
  without validating their other fields. This lets users remove a hand-edited
  invalid source instead of being trapped by the invalid entry.
- All readers reject boolean priorities. Replacement-layer loaders otherwise
  call `int(value)`, so a fractional numeric value such as `1.9` is truncated
  to `1`. Bundle `CatalogSource` materialization rejects booleans and floats
  rather than coercing them, but `_read()` and `remove_source()` can carry or
  remove those raw values without materializing them.
- Replacement-layer loaders reject malformed remote URLs and non-localhost
  HTTP while resolving the active stack. Bundle source validation depends on
  the path: catalog commands validate supported schemes and remote security
  before writing, while a hand-edited stack is revalidated by the fetcher when
  used.
- Presets, workflows, workflow steps, and both bundle readers treat
  `catalogs: null` as contributing no entries. Extensions and integrations
  treat it as an empty selected config and fail closed.

The current empty-config behavior is intentionally not uniform:

| Primitive | Empty document / `null` | Missing or empty `catalogs` | Entries with no usable URL |
| --- | --- | --- | --- |
| Extensions | Error | Error | Error |
| Integrations | Error | Error | Error |
| Presets | Layer contributes nothing | Layer contributes nothing | Layer contributes nothing |
| Workflows | Layer contributes nothing | Layer contributes nothing | Error when a non-empty list has no usable URL |
| Workflow steps | Layer contributes nothing | Layer contributes nothing | Error when a non-empty list has no usable URL |
| Bundles, resolution reader | Empty document contributes nothing; explicit `null` is malformed | Contributes nothing | Source validation fails |
| Bundles, config command reader | Missing/empty document returns an empty project list; explicit `null` is malformed | Returns an empty project list | Source validation occurs when materializing entries |

These differences are historical contracts, not recommendations. A future
unification must make any semantic change explicit, separately reviewed, and
covered as a behavior change rather than silently normalizing the readers.

Bundle configuration accepts a missing schema version for backward
compatibility, accepts forward-compatible `1.x` versions, and rejects an
unsupported major version. The other source config files are currently
unversioned.

## Fetching, redirects, and cache behavior

Catalog payload fetches are bounded and use the repository's authenticated HTTP
helpers where supported. Remote source URLs must be validated before use and
after redirects.

Current behavior differs by primitive:

- Extensions and presets use one-hour per-URL caches, retain legacy cache names
  for the official source, validate every redirect hop, validate cached payload
  shape, and treat cache read/write failures as best-effort.
- Integrations use one-hour per-URL caches. The shared HTTP redirect handler
  applies its strict scheme, host, and remote-to-local policy on every hop;
  integrations do not add their catalog-specific URL validator per hop, but do
  apply it to a changed terminal URL. They validate cached payload shape,
  discard invalid cache entries when possible, and treat cache writes as
  best-effort.
- Workflows use one-hour per-URL caches, validate every redirect hop, fall back
  to any readable stale cache after errors while opening, redirecting, bounded
  reading, UTF-8 decoding, or JSON parsing, and currently require only a mapping
  at the payload root before merge. A freshly parsed non-object payload is
  rejected after that fallback boundary.
- Workflow steps follow the workflow cache/fallback model, validate every
  redirect hop, and disable cache use when the cache path contains a symlink.
  Duplicate JSON fields are re-raised as fatal validation errors before stale
  fallback; a freshly parsed non-object payload is also rejected after the
  fallback boundary.
- Bundle catalog fetchers do not maintain a general remote TTL cache. Built-in
  sources fetch repository catalogs when online and fall back to packaged
  snapshots only for catalog-unavailable failures; malformed or unsafe content
  is not masked by the snapshot. Bundle stacks memoize parsed payloads for the
  lifetime of one stack instance.

A future shared fetch boundary may share URL validation, redirect validation,
bounded reads, cache records, and error types. It must preserve each
primitive's fallback policy until a separate behavior change is approved.

## Payload validation ownership

The shared source layer should own source configuration, fetching, cache
mechanics, and source provenance. The primitive remains responsible for its
payload schema and entry semantics:

- extension catalogs validate the `extensions` mapping and extension metadata
- preset catalogs validate the `presets` mapping and preset metadata
- integration catalogs validate the `integrations` mapping and integration
  metadata
- workflow catalogs validate workflow records
- workflow-step catalogs validate step records, including duplicate identifiers
- bundle catalogs validate their schema version and strongly typed bundle
  entries

Domain validation must happen before installation side effects. The shared
layer must not turn malformed payloads into empty successful results.

## Source failures

Recoverable source-fetch errors can be skipped by extensions, presets,
integrations, workflows, and workflow steps so another selected source remains
usable. Validation errors are not uniformly recoverable:

- Extensions and integrations emit warnings for failed sources and raise when
  every source fails. Because integration release-history validation happens
  during `_fetch_single_catalog`, malformed release history is represented as
  an `IntegrationCatalogError`, so the merge warns, skips that source, and can
  expose a lower-precedence copy.
- Preset lookup preserves the first fetch error when no source is readable;
  preset search currently converts ordinary fetch failures to an empty result.
  `PresetCatalogValidationError` remains fatal: search can fail on invalid
  lower-precedence content even after reading a valid higher source, while a
  targeted lookup can return as soon as it finds the requested higher entry.
- Workflow and step merges count source failures and raise when every source
  fails. Workflow-step duplicate JSON fields and duplicate IDs are fatal
  validation errors rather than skippable source-fetch errors.
- Workflow and step fetches may use readable stale cache data after broad
  fetch-path failures, including rejected redirects, bounded-read failures,
  decoding failures, and malformed JSON. Fresh non-object payloads and step
  duplicate-field errors remain outside that fallback.

Bundle lookup is fail-fast in precedence order: loading a source error stops
the operation. Built-in fetch fallback is handled inside the bundle fetcher,
not by skipping the source in `CatalogStack`.

These are visible behavior differences. A shared layer needs a declared source
failure strategy per caller rather than one implicit global policy.

## Shadowing, provenance, search, and lookup

For well-formed entries from readable sources, the highest-precedence source
that defines a content ID wins. A lower-precedence copy is shadowed even when:

- the lower copy matches a search query that the winning copy does not
- the lower copy permits installation and the winning copy is discovery-only
- the lower copy contains a requested historical version absent from the
  winning copy

Search must describe the same winning entry that lookup/install would resolve;
it must not expose an unreachable shadowed entry.

Malformed entry handling is an established exception:

- Extensions, integrations, workflows, and workflow steps skip non-mapping
  entries during merge, so a well-formed lower-precedence copy can win.
- Preset search skips non-mapping entries and can show a lower-precedence copy,
  but targeted preset lookup/install treats a malformed matching entry as
  fatal and does not fall through.
- Bundle payload parsing rejects malformed entries rather than skipping them.
- Integration release-history validation occurs at fetch time; an invalid
  higher source is skipped as a failed source, allowing a lower copy and its
  installation policy to win.

Resolved/search results preserve source provenance:

- replacement-layer catalogs annotate records with `_catalog_name` and
  `_install_allowed`
- bundles return a `ResolvedBundle` carrying its `CatalogSource`, and the
  materialized entry records `source_id` and `source_policy`

Provenance is semantic data needed for installation policy checks and
diagnostics. It is not presentation-only metadata.

## Exact historical release selection

All six primitives support selecting the advertised current version or an
exact historical release from the winning well-formed entry. Selection:

- never falls through to a lower-precedence source
- accepts PEP 440-equivalent spellings where the current selector does
- preserves the release spelling advertised by the catalog
- materializes historical release fields without inheriting current-only
  download, checksum, compatibility, or similar metadata
- reports or returns "not found" when the winning entry does not advertise the
  requested release

Malformed release history is a validation failure, but its failure phase
matters. Extensions, presets, workflows, workflow steps, and bundles do not
consult a lower source after the winning entry fails release selection.
Integrations validate history while fetching a source, so the merge can skip
that source and select a lower copy instead.

## Intended shared-layer boundary

`src/specify_cli/catalogs.py` already provides a narrow shared starting point:
`CatalogEntry` and `CatalogStackBase` centralize source-entry fields, remote URL
validation, and YAML config loading. Extensions and integrations subclass that
base today. Presets, workflows, workflow steps, and bundles retain independent
source models and loaders, and fetching, cache, merge, failure, payload, and
release behavior remains primitive-owned for all six domains.

A broader shared catalog domain, whether evolved in `specify_cli.catalogs` or
split into focused adjacent modules, may own:

- typed source identity, scope, priority, trust/install policy, and provenance
- config parsing primitives with an explicit empty-config policy
- environment/project/user/built-in source resolution strategies
- stable source ordering and shadowing
- authenticated bounded fetches and per-hop redirect validation
- cache interfaces and explicitly selected stale/offline fallback strategies
- source-failure strategies
- generic "winning source first" search/lookup orchestration

Primitive modules continue to own:

- payload and entry schemas
- release metadata fields and domain-specific validation
- install/download planning and side effects
- CLI prompting, warnings, rendering, and exit codes
- MCP schemas, annotations, and protocol errors

The shared layer must accept explicit project and user paths. It must not read
mutable process working-directory state, prompt, print, infer trust from
machine-readable mode, or make a source installable merely because it is
reachable.

## Migration constraints

Refactoring into the shared layer must be incremental and behavior-preserving:

1. Keep the characterization matrix passing.
2. Move one independently testable concern at a time.
3. Preserve existing import and monkeypatch paths where tests or consumers rely
   on them, including `specify_cli.catalogs.CatalogEntry`,
   `specify_cli.catalogs.CatalogStackBase`, and the extension/integration
   package exports and subclass patch points built on those types.
4. Do not normalize empty configs, source failure handling, cache fallback, or
   trust defaults in a structural PR.
5. Treat any intended normalization as a separate behavior change with positive
   and negative evidence under
   [Testing deterministic behavior](../CONTRIBUTING.md#testing-deterministic-behavior).
