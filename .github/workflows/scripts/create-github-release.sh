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
  .genreleases/ce-kit-template-copilot-sh-"$VERSION".zip \
  .genreleases/ce-kit-template-copilot-ps-"$VERSION".zip \
  .genreleases/ce-kit-template-claude-sh-"$VERSION".zip \
  .genreleases/ce-kit-template-claude-ps-"$VERSION".zip \
  .genreleases/ce-kit-template-gemini-sh-"$VERSION".zip \
  .genreleases/ce-kit-template-gemini-ps-"$VERSION".zip \
  .genreleases/ce-kit-template-cursor-sh-"$VERSION".zip \
  .genreleases/ce-kit-template-cursor-ps-"$VERSION".zip \
  .genreleases/ce-kit-template-opencode-sh-"$VERSION".zip \
  .genreleases/ce-kit-template-opencode-ps-"$VERSION".zip \
  .genreleases/ce-kit-template-qwen-sh-"$VERSION".zip \
  .genreleases/ce-kit-template-qwen-ps-"$VERSION".zip \
  .genreleases/ce-kit-template-windsurf-sh-"$VERSION".zip \
  .genreleases/ce-kit-template-windsurf-ps-"$VERSION".zip \
  .genreleases/ce-kit-template-codex-sh-"$VERSION".zip \
  .genreleases/ce-kit-template-codex-ps-"$VERSION".zip \
  .genreleases/ce-kit-template-kilocode-sh-"$VERSION".zip \
  .genreleases/ce-kit-template-kilocode-ps-"$VERSION".zip \
  .genreleases/ce-kit-template-auggie-sh-"$VERSION".zip \
  .genreleases/ce-kit-template-auggie-ps-"$VERSION".zip \
  .genreleases/ce-kit-template-roo-sh-"$VERSION".zip \
  .genreleases/ce-kit-template-roo-ps-"$VERSION".zip \
  --title "Context Engineering Kit Templates - $VERSION_NO_V" \
  --notes-file release_notes.md