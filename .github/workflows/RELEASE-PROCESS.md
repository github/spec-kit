# Release Process

This document describes the automated release process for Spec Kit.

## Overview

The release process is split into two workflows to ensure version consistency:

1. **Release Trigger Workflow** (`release-trigger.yml`) - Manages versioning and triggers release
2. **Release Workflow** (`release.yml`) - Builds and publishes artifacts

This separation ensures that git tags always point to commits with the correct version in `pyproject.toml`.

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
```
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
- Open a PR to merge the version bump into `main`
- Trigger the release workflow automatically via the tag push

## What Happens Next

Once the release trigger workflow completes:

1. A `chore/release-vX.Y.Z` branch is pushed with the version bump commit
2. The git tag is pushed, pointing to that commit
3. The **Release Workflow** is automatically triggered by the tag push
4. Release artifacts are built for all supported agents
5. A GitHub Release is created with all assets
6. A PR is opened to merge the version bump branch into `main`

> **Note**: Merge the auto-opened PR after the release is published to keep `main` in sync.

## Workflow Details

### Release Trigger Workflow

**File**: `.github/workflows/release-trigger.yml`

**Trigger**: Manual (`workflow_dispatch`)

**Permissions Required**: `contents: write`

**Steps**:
1. Checkout repository
2. Determine version (manual or auto-increment)
3. Check if tag already exists (prevents duplicates)
4. Create `chore/release-vX.Y.Z` branch
5. Update `pyproject.toml`
6. Update `CHANGELOG.md` from git commits
7. Commit changes
8. Push branch and tag
9. Open PR to merge version bump into `main`

### Release Workflow

**File**: `.github/workflows/release.yml`

**Trigger**: Tag push (`v*`)

**Permissions Required**: `contents: write`

**Steps**:
1. Checkout repository at tag
2. Extract version from tag name
3. Check if release already exists
4. Build release package variants (all agents × shell/powershell)
5. Generate release notes from commits
6. Create GitHub Release with all assets

## Version Constraints

- Tags must follow format: `v{MAJOR}.{MINOR}.{PATCH}`
- Example valid versions: `v0.1.11`, `v0.2.0`, `v1.0.0`
- Auto-increment only bumps patch version
- Cannot create duplicate tags (workflow will fail)

## Benefits of This Approach

✅ **Version Consistency**: Git tags point to commits with matching `pyproject.toml` version

✅ **Single Source of Truth**: Version set once, used everywhere

✅ **Prevents Drift**: No more manual version synchronization needed

✅ **Clean Separation**: Versioning logic separate from artifact building

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

If you see "Error: Tag vX.Y.Z already exists!", you need to:
- Choose a different version number, or
- Delete the existing tag if it was created in error

### Release Workflow Didn't Trigger

Check that:
- The release trigger workflow completed successfully
- The tag was pushed (check repository tags)
- The release workflow is enabled in Actions settings

### Version Mismatch

If `pyproject.toml` doesn't match the latest tag:
- Run the release trigger workflow to sync versions
- Or manually update `pyproject.toml` and push changes before running the release trigger

## Legacy Behavior (Pre-v0.1.10)

Before this change, the release workflow:
- Created tags automatically on main branch pushes
- Updated `pyproject.toml` AFTER creating the tag
- Resulted in tags pointing to commits with outdated versions

This has been fixed in v0.1.10+.
