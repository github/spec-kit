#!/usr/bin/env bash
set -euo pipefail

# get-next-version.sh
# Calculate the next version based on the latest git tag and output GitHub Actions variables
# Usage: get-next-version.sh

# Get the latest fork-specific tag, or use fork-v0.0.0 if no tags exist
LATEST_TAG=$(git describe --tags --match "fork-v*" --abbrev=0 2>/dev/null || echo "fork-v0.0.0")
echo "latest_tag=$LATEST_TAG" >> $GITHUB_OUTPUT

# Extract version number and increment (remove fork-v prefix)
VERSION=$(echo $LATEST_TAG | sed 's/fork-v//')
IFS='.' read -ra VERSION_PARTS <<< "$VERSION"
MAJOR=${VERSION_PARTS[0]:-0}
MINOR=${VERSION_PARTS[1]:-0}
PATCH=${VERSION_PARTS[2]:-0}

# Increment patch version
PATCH=$((PATCH + 1))
NEW_VERSION="fork-v$MAJOR.$MINOR.$PATCH"

echo "new_version=$NEW_VERSION" >> $GITHUB_OUTPUT
echo "New version will be: $NEW_VERSION"
