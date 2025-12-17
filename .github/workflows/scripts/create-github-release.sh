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

gh release create "$VERSION" \
  .genreleases/speclite-template-copilot-sh-"$VERSION_NO_V".zip \
  .genreleases/speclite-template-copilot-ps-"$VERSION_NO_V".zip \
  .genreleases/speclite-template-claude-sh-"$VERSION_NO_V".zip \
  .genreleases/speclite-template-claude-ps-"$VERSION_NO_V".zip \
  .genreleases/speclite-template-gemini-sh-"$VERSION_NO_V".zip \
  .genreleases/speclite-template-gemini-ps-"$VERSION_NO_V".zip \
  .genreleases/speclite-template-cursor-agent-sh-"$VERSION_NO_V".zip \
  .genreleases/speclite-template-cursor-agent-ps-"$VERSION_NO_V".zip \
  .genreleases/speclite-template-codex-sh-"$VERSION_NO_V".zip \
  .genreleases/speclite-template-codex-ps-"$VERSION_NO_V".zip \
  --title "SpecLite Templates - $VERSION_NO_V" \
  --notes-file release_notes.md
