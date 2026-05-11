# Releasing InfraKit

This document covers how InfraKit ships releases to PyPI and GitHub, and what to do when a release misbehaves.

## TL;DR

> **Every merge to `main` ships a new patch release: PyPI upload, GitHub Release, and tag — all in one workflow run.**

No path filters. No manual steps. No release branches. No "let's wait for a freeze." The contract is: if your change is worth merging, it's worth shipping.

## The release pipeline

The full pipeline lives in a single workflow — [`.github/workflows/release.yml`](./.github/workflows/release.yml). Every push to `main` runs it. Each run does, in order:

1. **Resolve next version.** Reads the latest git tag (e.g. `v0.1.13`), bumps the patch component (`v0.1.14`).
2. **Skip if the release already exists.** Lets the workflow re-run safely (idempotent). Every subsequent step is gated on this check.
3. **Stamp `pyproject.toml`.** Writes the new version into the package metadata.
4. **Build wheel + sdist** with `uv build`. Templates are force-included into the wheel via `[tool.hatch.build.targets.wheel.force-include]`.
5. **`twine check --strict`** against the built artifacts. Catches malformed README, broken `long_description_content_type`, missing license, etc. before they reach PyPI.
6. **Generate release notes** from the commits since the last tag.
7. **Publish to PyPI** via [Trusted Publishing](https://docs.pypi.org/trusted-publishers/) (PEP 740 / OIDC). No API token in the repo.
8. **Create GitHub Release** with the wheel + sdist attached. `gh release create --target main` creates the tag server-side against the merge commit at the same time.
9. **Commit the version bump** back to `main` with `[skip ci]` so future pushes pick up from the new version. The `[skip ci]` marker is honoured natively by GitHub Actions — the bump commit does **not** re-trigger this workflow.

If any step fails, subsequent steps are skipped — **including** the version bump — so the next CI run retries from the same version number. PyPI publish + GitHub Release + tag therefore ship atomically: either all three or none.

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

**Any merge to `main`.** No path filter. Every commit that lands on main runs the workflow and ships a release. README typos, doc tweaks, example refreshes — they all bump a patch version and upload a new wheel.

This is a deliberate choice. The alternative (path filters) requires constant maintenance ("does this dir count? what about that one?") and tends to drift out of sync with reality. Bumping a patch number for a README edit is essentially free; the cost of *missing* a release because the trigger filter didn't fire is much higher.

If you want to land changes without a release — for instance, in-progress doc cleanup that doesn't justify a version bump — squash them into your next substantive PR.

### Manual releases

Outside of a normal merge, you can fire the workflow on demand:

```bash
gh workflow run release.yml --ref main
```

Same workflow, same outcome: PyPI upload, GitHub Release, tag, version-bump commit.

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
