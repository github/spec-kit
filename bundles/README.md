# Bundle catalogs (AI Team distribution)

This directory publishes the **AI Team bundle catalog** for Spec Kit's bundle
subsystem. It follows the upstream pattern: catalog JSON + per-bundle manifests.

## Layout

| Path | Purpose |
|------|---------|
| [`catalog.json`](catalog.json) | Bundle catalog entries (`ai-team`, …) |
| [`ai-team/bundle.yml`](ai-team/bundle.yml) | Manifest: pinned extensions, preset, workflows |
| [`ai-team/README.md`](ai-team/README.md) | Bundle-specific usage |

## Consumer flow (方案 A)

Users install the CLI from this fork, then **per coding repository**:

```bash
specify init . --integration cursor-agent
specify bundle catalog add https://raw.githubusercontent.com/EuphoriaYan/spec-kit/main/bundles/catalog.json \
  --id ai-team --policy install-allowed
specify bundle install ai-team
```

`catalog add` writes `.specify/bundle-catalogs.yml` in the **coding repo** — it
does not happen automatically because the catalog file lives in the **spec-kit
fork**, not in the user's project.

## Maintainer notes

- Update `catalog.json` when bumping bundle `version` or `download_url` (e.g.
  after `specify bundle build` and a GitHub release).
- `download_url` may point at `bundle.yml` on `main` or at a versioned `.zip`
  artifact from a release.
- Authoring: `specify bundle validate --path bundles/ai-team` and
  `specify bundle build --path bundles/ai-team --output dist/`.
