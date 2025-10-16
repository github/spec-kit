#!/usr/bin/env bash
set -euo pipefail

# create-github-release.sh
# Create a GitHub release with all template zip files
# Usage: create-github-release.sh <version>

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <version>" >&2
  exit 1
fi

VERSION="$1"

# Remove 'v' prefix from version for release title
VERSION_NO_V=${VERSION#v}

# Source centralized agent configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/agent-config.sh"

# Dynamically build release asset list
RELEASE_ASSETS=()
for agent in "${ALL_AGENTS[@]}"; do
  for script_type in sh ps; do
    RELEASE_ASSETS+=(".genreleases/spec-kit-template-${agent}-${script_type}-${VERSION}.zip")
  done
done

# Create GitHub release with all assets
gh release create "$VERSION" \
  "${RELEASE_ASSETS[@]}" \
  --title "Spec Kit Templates - $VERSION_NO_V" \
  --notes-file release_notes.md
