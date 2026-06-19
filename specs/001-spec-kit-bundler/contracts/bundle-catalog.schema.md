# Contract: Bundle Catalog (entry + source stack)

**Feature**: Spec Kit Bundler | **Date**: 2026-06-19

Bundles are distributed through the same catalog model as the other Spec Kit primitives: a **priority-ordered stack of catalog sources**, each carrying **install-policy metadata**, with a built-in default stack as fallback (FR-024..FR-027, research R3/R10).

## Catalog source stack (config file)

Project-scoped config (mirrors `.specify/extension-catalogs.yml`, e.g. `.specify/bundle-catalogs.yml`), with a user-scoped fallback and the built-in default beneath it. Precedence: **project > user > built-in**.

```yaml
# .specify/bundle-catalogs.yml (project scope)
catalogs:
  - id: "acme-org"
    url: "https://raw.githubusercontent.com/acme/spec-kit-bundles/main/catalog.json"
    priority: 1                       # lower number = higher precedence
    install_policy: "install-allowed" # install-allowed | discovery-only
  - id: "community"
    url: "https://raw.githubusercontent.com/acme/spec-kit-bundles/main/catalog.community.json"
    priority: 2
    install_policy: "discovery-only"
```

Built-in default stack (used when no project/user config overrides it):

| id | priority | install_policy |
|----|----------|----------------|
| `default` | 1 | install-allowed |
| `community` | 2 | discovery-only |

**Source rules**:
- `install` is permitted **only** from `install-allowed` sources. Bundles resolvable only from `discovery-only` sources appear in `search`/`info` but installing them is refused with a clear "discovery-only" message.
- A misconfigured/unreachable source causes discovery/install to fail **naming that source** (never a silent empty result).
- `specify bundle catalog add/remove` edits the project-scoped config; built-in defaults cannot be deleted, only overridden.

## Catalog file shape (entry)

Same `schema_version`/entry shape as the other primitive catalogs.

```json
{
  "schema_version": "1.0",
  "updated_at": "2026-06-12T00:00:00Z",
  "catalog_url": "https://raw.githubusercontent.com/acme/spec-kit-bundles/main/catalog.json",
  "bundles": {
    "security-researcher": {
      "id": "security-researcher",
      "name": "Security Researcher",
      "version": "1.0.0",
      "role": "security-researcher",
      "description": "One-stop SDD setup for security researchers.",
      "author": "acme-platform-team",
      "license": "MIT",
      "download_url": "https://github.com/acme/spec-kit-bundles/releases/download/security-researcher-v1.0.0/security-researcher.zip",
      "repository": "https://github.com/acme/spec-kit-bundles",
      "requires": { "speckit_version": ">=0.9.0" },
      "provides": { "extensions": 2, "presets": 2, "steps": 0, "workflows": 1, "integration": 1 },
      "tags": ["security", "compliance"],
      "verified": true
    }
  }
}
```

## Entry field rules

| Field | Required | Notes |
|-------|----------|-------|
| `id`, `name`, `version`, `role`, `description`, `author`, `license` | yes | Discovery/governance metadata (FR-027); `version` semver |
| `download_url` | yes | Points at the hosted artifact (out-of-band distribution, FR-030) |
| `repository` | no | Provenance |
| `requires.speckit_version` | yes | Pre-install compatibility check (FR-016) |
| `provides` | yes | Summary counts per component type |
| `tags` | no | Discovery filters |
| `verified` | yes | Trust indicator distinguishing org-curated vs community (FR-010) |

## Discovery/inspection guarantees

- `search` and `info` MUST expose each entry's **source catalog** and **install policy** alongside its metadata (FR-027).
- `info` MUST additionally expand the bundle to its concrete component set with versions/priorities — equal to what `install` will add (transparency, SC-002). The expanded set is resolved by fetching the referenced manifest/artifact, not stored in the catalog entry (which carries only summary counts).
- `verified: false` / community-policy sources let users judge trust level before installing (FR-010).
