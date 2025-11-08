#!/usr/bin/env bash
set -euo pipefail

# get-next-version.sh
# Calculate the next version based on the latest GitHub release or git tag
# Usage: get-next-version.sh

# Try to get latest version from GitHub releases first, fallback to git tags
if command -v gh >/dev/null 2>&1 && [[ -n "${GITHUB_TOKEN:-}" ]]; then
  # Get the latest release from GitHub (sorted by semver)
  LATEST_TAG=$(gh release list --limit 100 --json tagName --jq '.[].tagName' 2>/dev/null |
    grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$' |
    sort -V |
    tail -1 || echo "v0.0.0")
  echo "Latest version from GitHub releases: $LATEST_TAG"
else
  # Fallback to git tags if gh CLI not available
  LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")
  echo "Latest version from git tags: $LATEST_TAG"
fi

echo "latest_tag=$LATEST_TAG" >> $GITHUB_OUTPUT

# Extract version number and increment
VERSION=$(echo $LATEST_TAG | sed 's/v//')
IFS='.' read -ra VERSION_PARTS <<< "$VERSION"
MAJOR=${VERSION_PARTS[0]:-0}
MINOR=${VERSION_PARTS[1]:-0}
PATCH=${VERSION_PARTS[2]:-0}

# Increment patch version
PATCH=$((PATCH + 1))
NEW_VERSION="v$MAJOR.$MINOR.$PATCH"

echo "new_version=$NEW_VERSION" >> $GITHUB_OUTPUT
echo "New version will be: $NEW_VERSION (incrementing from $LATEST_TAG)"
