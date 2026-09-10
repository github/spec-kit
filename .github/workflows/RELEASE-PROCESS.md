# Release Process

This document describes the automated release process for Spec Kit.

## Overview

The release process is split into three workflows:

1. **Release Trigger Workflow** (`release-trigger.yml`) - Manages versioning, creates the tag, and opens the release PR
2. **Release Workflow** (`release.yml`) - Creates the GitHub Release and release notes
3. **Publish to PyPI Workflow** (`publish-pypi.yml`) - Builds and publishes the Python package from an exact tag

This separation ensures that git tags point to commits with the correct version in `pyproject.toml` and lets maintainers recover the GitHub and PyPI publishing steps independently.

## Before Creating a Release

**Important**: Write clear, descriptive commit messages!

### How CHANGELOG.md Works

The CHANGELOG is **automatically generated** from your git commit messages:

1. **During Development**: Write clear, descriptive commit messages:

   ```bash
   git commit -m "feat: Add new authentication feature"
   git commit -m "fix: Resolve timeout issue in API client (#123)"
   git commit -m "docs: Update installation instructions"
   ```

2. **When Releasing**: The release trigger workflow automatically:
   - Finds all commits since the last release tag
   - Formats them as changelog entries
   - Inserts them into CHANGELOG.md
   - Commits the updated changelog before creating the new tag

### Commit Message Best Practices

Good commit messages make good changelogs:

- **Be descriptive**: "Add user authentication" not "Update files"
- **Reference issues/PRs**: Include `(#123)` for automated linking
- **Use conventional commits** (optional): `feat:`, `fix:`, `docs:`, `chore:`
- **Keep it concise**: One line is ideal, details go in commit body

**Example commits that become good changelog entries:**

```text
fix: prepend YAML frontmatter to Cursor .mdc files (#1699)
feat: add generic agent support with customizable command directories (#1639)
docs: document dual-catalog system for extensions (#1689)
```

## Creating a Release

### Option 1: Auto-Increment (Recommended for patches)

1. Go to **Actions** → **Release Trigger**
2. Click **Run workflow**
3. Leave the version field **empty**
4. Click **Run workflow**

The workflow will:

- Auto-increment the patch version (e.g., `0.1.10` → `0.1.11`)
- Update `pyproject.toml`
- Update `CHANGELOG.md` by adding a new section for the release based on commits since the last tag
- Commit changes to a `chore/release-vX.Y.Z` branch
- Create and push the git tag from that branch
- Bump the release branch to the next patch development version (for example, `1.2.3` → `1.2.4.dev0`)
- Open a PR to merge the version bump into `main`
- Trigger the release workflow automatically via the tag push

### Option 2: Manual Version (For major/minor bumps)

1. Go to **Actions** → **Release Trigger**
2. Click **Run workflow**
3. Enter the desired version (e.g., `0.2.0` or `v0.2.0`)
4. Click **Run workflow**

The workflow will:

- Use your specified version
- Update `pyproject.toml`
- Update `CHANGELOG.md` by adding a new section for the release based on commits since the last tag
- Commit changes to a `chore/release-vX.Y.Z` branch
- Create and push the git tag from that branch
- Bump the release branch to the next patch development version (for example, `1.2.3` → `1.2.4.dev0`)
- Open a PR to merge the version bump into `main`
- Trigger the release workflow automatically via the tag push

## What Happens Next

Once the release trigger workflow completes:

1. A `chore/release-vX.Y.Z` branch is pushed with the version bump commit
2. The git tag is pushed, pointing to that release commit
3. The **Release Workflow** is automatically triggered by the tag push
4. A GitHub Release is created with generated release notes. No per-agent ZIP assets are built or uploaded; GitHub still provides its standard source archives
5. The release branch is bumped to the next patch development version
6. A PR is opened to merge both version commits into `main`
7. Run the **Publish to PyPI Workflow** manually with the same tag to build and publish the wheel and source distribution

> **Note**: The GitHub Release and PyPI workflows do not depend on each other. Waiting for the GitHub Release to complete before publishing to PyPI makes the release state easier to verify. Merge the auto-opened PR after publishing to keep `main` on the next development version.

## Workflow Details

### Release Trigger Workflow

**File**: `.github/workflows/release-trigger.yml`

**Trigger**: Manual (`workflow_dispatch`)

**Permissions Required**: `contents: write`, `pull-requests: write`

**Steps**:

1. Checkout repository
2. Determine version (manual or auto-increment)
3. Check if tag already exists (prevents duplicates)
4. Create `chore/release-vX.Y.Z` branch
5. Update `pyproject.toml`
6. Update `CHANGELOG.md` from git commits
7. Commit changes
8. Push branch and tag
9. Bump `pyproject.toml` to the next patch development version and push the branch
10. Open PR to merge the release and development version commits into `main`

### Release Workflow

**File**: `.github/workflows/release.yml`

**Trigger**: Tag push (`v*`)

**Permissions Required**: `contents: write`

**Steps**:

1. Checkout repository at tag
2. Extract version from tag name
3. Check if release already exists
4. Generate release notes from commits
5. Create the GitHub Release without additional uploaded assets

### Publish to PyPI Workflow

**File**: `.github/workflows/publish-pypi.yml`

**Trigger**: Manual (`workflow_dispatch`) with the exact release tag

**Permissions Required**: `contents: read`, `actions: write` for the build job; `actions: read`, `id-token: write` for the publish job

**Steps**:

1. Validate that the input uses the strict `vX.Y.Z` tag format
2. Checkout `refs/tags/vX.Y.Z`
3. Verify that the tag version exactly matches the version in `pyproject.toml`
4. Build the wheel and source distribution with `uv build`
5. Transfer the distributions between jobs as a GitHub Actions artifact
6. Publish them to PyPI with `uv publish` and Trusted Publishing

## Version Constraints

- Tags must follow format: `v{MAJOR}.{MINOR}.{PATCH}`
- Example valid versions: `v0.1.11`, `v0.2.0`, `v1.0.0`
- Auto-increment only bumps patch version
- Cannot create duplicate tags (workflow will fail)

## Benefits of This Approach

✅ **Version Consistency**: Git tags point to commits with matching `pyproject.toml` version

✅ **Single Source of Truth**: Version set once, used everywhere

✅ **Prevents Drift**: No more manual version synchronization needed

✅ **Independent Publishing**: GitHub Release creation and PyPI publishing can be verified and recovered separately

✅ **Flexibility**: Supports both auto-increment and manual versioning

## Troubleshooting

### No Commits Since Last Release

If you run the release trigger workflow when there are no new commits since the last tag:

- The workflow will still succeed
- The CHANGELOG will show "- Initial release" if it's the first release
- Or it will be empty if there are no commits
- Consider adding meaningful commits before releasing

**Best Practice**: Use descriptive commit messages - they become your changelog!

### Tag Already Exists

If you see "Error: Tag vX.Y.Z already exists!", inspect the existing tag, GitHub Release, and PyPI version before taking action. Do not move or delete a tag for a version that has already been published to PyPI. PyPI does not allow an uploaded distribution filename to be reused, even after deletion.

Choose a new version if the existing tag or PyPI publication is valid. Only consider removing an erroneous tag when you have confirmed that the version was not published to PyPI and that no consumers rely on it.

### Recovering an Incomplete Release

Verify the release branch/tag, GitHub Release, wheel (`.whl`), and source distribution (`.tar.gz`) separately. A PyPI version page alone does not confirm that both distributions were uploaded.

| State | Recovery |
|---|---|
| Tag exists, release branch development bump or PR is incomplete | Keep the tag unchanged. Inspect `chore/release-vX.Y.Z` and any existing PR; restore the branch from the release commit if missing, apply the next patch development bump if needed, and open or reuse the PR into `main`. Merge after publication is complete. Do not rerun Release Trigger for the existing tag. |
| Tag exists, GitHub Release is missing | Confirm that the tag points to the intended release commit, then create the GitHub Release from that existing tag with the same notes format used by `release.yml`. |
| Valid tag exists, neither wheel nor sdist is published to PyPI | Run **Publish to PyPI** manually with the exact release tag, independently of GitHub Release creation. |
| PyPI version exists, GitHub Release is missing | Keep the existing tag unchanged and create the GitHub Release from it. |
| Wheel is published, sdist is missing | Verify the published wheel and recover the matching sdist from the original run's `dist` artifact. Use an authorized publishing path to upload only the missing sdist; do not replace the wheel. |
| Sdist is published, wheel is missing | Verify the published sdist and recover the matching wheel from the original run's `dist` artifact. Use an authorized publishing path to upload only the missing wheel; do not replace the sdist. |

For partial PyPI uploads, inspect the original run and published files before retrying. The current workflow rebuilds and publishes all of `dist/`; it is not a missing-file-only recovery command. If the original artifact is unavailable, investigate how to reproduce the matching distribution before publishing. Previously used filenames cannot be replaced or reused.

### Release Workflow Didn't Trigger

Check that:

- The release trigger workflow completed successfully
- The tag was pushed (check repository tags)
- The release workflow is enabled in Actions settings

### Version Mismatch

After a release PR is merged, `pyproject.toml` on `main` is expected to differ from the latest release tag. The tag `vX.Y.Z` points to a commit whose package version is exactly `X.Y.Z`; the release branch is subsequently bumped to the next patch development version (for example, `1.2.3` → `1.2.4.dev0`). Do not sync `main` back to the released version.

The **Publish to PyPI** workflow checks out the release tag and verifies that its version, without the `v` prefix, exactly matches `pyproject.toml` at that commit. A mismatch at the tagged commit is an error; the next development version on `main` is expected.

If that check fails, inspect the tag, GitHub Release, and PyPI publication state before choosing a recovery path (see **Tag Already Exists** and **Recovering an Incomplete Release** above). Do not move or recreate a published tag.

## Legacy Behavior (Pre-v0.1.10)

Before this change, the release workflow:

- Created tags automatically on main branch pushes
- Updated `pyproject.toml` AFTER creating the tag
- Resulted in tags pointing to commits with outdated versions

This has been fixed in v0.1.10+.
