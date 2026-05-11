# Releasing InfraKit

This document covers how InfraKit ships releases to PyPI and GitHub, and what to do when a release misbehaves.

## TL;DR

> **Every push to `main` that touches `src/**`, `templates/**`, `pyproject.toml`, or `.github/workflows/**` ships a new patch release to PyPI and GitHub.**

No manual steps. No release branches. No "let's wait for a freeze." The contract is: if your change is worth merging, it's worth shipping.

## The release pipeline

The full pipeline lives in [`.github/workflows/release.yml`](./.github/workflows/release.yml). Each release does, in order:

1. **Resolve next version.** Reads the latest git tag (e.g. `v0.1.13`), bumps the patch component (`v0.1.14`).
2. **Skip if the release already exists.** Lets the workflow re-run safely (idempotent).
3. **Stamp `pyproject.toml`.** Writes the new version into the package metadata.
4. **Build wheel + sdist** with `uv build`. Templates are force-included into the wheel via `[tool.hatch.build.targets.wheel.force-include]`.
5. **`twine check --strict`** against the built artifacts. Catches malformed README, broken `long_description_content_type`, missing license, etc. before they reach PyPI.
6. **Generate release notes** from the commits since the last tag.
7. **Publish to PyPI** via [Trusted Publishing](https://docs.pypi.org/trusted-publishers/) (PEP 740 / OIDC). No API token in the repo.
8. **Create GitHub Release** with the wheel + sdist attached.
9. **Commit the version bump** back to `main` with `[skip ci]` so the next push picks up from the new version.

If any step fails, subsequent steps are skipped — **including** the version bump — so the next CI run retries from the same version number.

## One-time setup (already done)

These steps were performed once when the project was first published. They're documented here for reference and disaster recovery.

### 1. Reserve the project name on PyPI

```bash
# Local
uv build
uvx twine upload dist/*
```

This is the only time a maintainer uploads from a laptop. Once the project exists on PyPI, switch to Trusted Publishing for all subsequent releases.

### 2. Configure Trusted Publishing on PyPI

1. Go to <https://pypi.org/manage/project/infrakit-cli/settings/publishing/>.
2. Click **Add a new pending publisher** (or **Add a new publisher** if `0.1.0` is already uploaded).
3. Fill in:
   - **PyPI Project Name:** `infrakit-cli`
   - **Owner:** `neelneelpurk`
   - **Repository name:** `infrakit`
   - **Workflow name:** `release.yml`
   - **Environment name:** `pypi`
4. Save.

### 3. Configure the `pypi` environment in GitHub

1. Go to <https://github.com/neelneelpurk/infrakit/settings/environments>.
2. Create environment named `pypi`.
3. (Optional but recommended) Add a required reviewer for the environment — a small friction that prevents accidental releases from rebase-merges that touched the wrong paths.

After these three steps, the workflow's `pypa/gh-action-pypi-publish` step authenticates against PyPI via OIDC. No tokens stored anywhere.

## What triggers a release

Path filters in [`release.yml`](./.github/workflows/release.yml):

```yaml
paths:
  - 'src/**'
  - 'templates/**'
  - 'pyproject.toml'
  - '.github/workflows/release.yml'
  - '.github/workflows/scripts/**'
```

Changes that affect what users install ship a release. Changes that don't (README polish, examples, docs/, CHANGELOG entry for an already-released version) don't.

### Should `examples/**` trigger a release?

No. The examples are static reference material; they don't end up in the wheel beyond the sdist. Releasing for an example tweak would burn version numbers for no behavioural reason.

### Should `README.md` trigger a release?

No. PyPI keeps the long-description from the version that was uploaded; later README edits don't backfill. If you want the PyPI long-description updated, make a change that *also* touches `src/**` (or bump the version manually via a tagged release).

### Manual releases

If you really need to release without a path-triggered commit, run the workflow with `workflow_dispatch`:

```bash
gh workflow run release.yml --ref main
```

This goes through the exact same steps. The version still bumps off the latest tag.

## Versioning

InfraKit follows **semver-ish patch-bumping**. Each release is a patch bump (`v0.1.13` → `v0.1.14`). The minor and major numbers stay where they are until a maintainer manually tags a higher version:

```bash
# Cut a minor release manually
git tag v0.2.0
git push origin v0.2.0
# Then push a change that triggers release.yml — it picks up v0.2.0 and
# the next auto-bumped version will be v0.2.1.
```

Breaking changes are flagged with `!` in the commit subject (e.g. `feat(packaging)!:`) and a minor bump is cut manually before the next release.

## Local sanity checks before pushing

```bash
# Build + render check
uv build
uvx twine check --strict dist/*

# Confirm templates are inside the wheel
unzip -l dist/infrakit_cli-*.whl | grep templates | head

# Run the full test suite + ruff (CI parity)
uv run pytest
uvx ruff check src/

# Offline e2e: install the wheel into a fresh venv and run infrakit init
uv venv /tmp/release-check
uv pip install --python /tmp/release-check/bin/python dist/infrakit_cli-*.whl
mkdir -p /tmp/release-check-project && cd /tmp/release-check-project
/tmp/release-check/bin/infrakit init demo --ai claude --iac terraform \
    --script sh --no-git --ignore-agent-tools
test -f demo/.claude/commands/infrakit:setup.md
```

If all of those pass, your change is safe to merge — the CI will rerun the same checks under `twine check --strict` before publishing.

## Disaster recovery

### Released a broken version to PyPI

PyPI does **not** allow re-uploading the same version. Options:

1. **Yank the broken release** at <https://pypi.org/manage/project/infrakit-cli/release/X.Y.Z/>. Yanked versions remain installable by exact `==X.Y.Z` but no longer satisfy version ranges.
2. **Cut a new patch version** with the fix. This is the normal path — yanking + bumping is much easier than trying to recover the broken version.

### PyPI publish step failed mid-way

The version-bump commit is the **last** step in the workflow. If publish failed, the version is not yet committed to `main` — the next CI run will pick up the same version number and retry.

### GitHub Release was created but PyPI publish failed

Unusual ordering, but possible if you re-run a partially-completed workflow. Delete the GitHub release manually:

```bash
gh release delete vX.Y.Z --yes
git tag -d vX.Y.Z
git push origin :refs/tags/vX.Y.Z
```

Then re-trigger the workflow.

## Manual emergency release from a laptop

Only do this if Trusted Publishing is broken or PyPI's OIDC verification is down. Requires a PyPI API token with upload permission for `infrakit-cli`.

```bash
git checkout main && git pull
uv build
uvx twine check --strict dist/*
uvx twine upload dist/* --username __token__ --password "$PYPI_API_TOKEN"
```

Then create the corresponding tag + GitHub release manually so the workflow doesn't try to re-release the same version.
