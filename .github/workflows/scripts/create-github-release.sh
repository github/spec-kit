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
  .genreleases/spec-kit-template-copilot-sh-"$VERSION".zip \
  .genreleases/spec-kit-template-copilot-ps-"$VERSION".zip \
  .genreleases/spec-kit-template-claude-sh-"$VERSION".zip \
  .genreleases/spec-kit-template-claude-ps-"$VERSION".zip \
  .genreleases/spec-kit-template-gemini-sh-"$VERSION".zip \
  .genreleases/spec-kit-template-gemini-ps-"$VERSION".zip \
  .genreleases/spec-kit-template-cursor-sh-"$VERSION".zip \
  .genreleases/spec-kit-template-cursor-ps-"$VERSION".zip \
  .genreleases/spec-kit-template-opencode-sh-"$VERSION".zip \
  .genreleases/spec-kit-template-opencode-ps-"$VERSION".zip \
  .genreleases/spec-kit-template-qwen-sh-"$VERSION".zip \
  .genreleases/spec-kit-template-qwen-ps-"$VERSION".zip \
  .genreleases/spec-kit-template-windsurf-sh-"$VERSION".zip \
  .genreleases/spec-kit-template-windsurf-ps-"$VERSION".zip \
  .genreleases/spec-kit-template-codex-sh-"$VERSION".zip \
  .genreleases/spec-kit-template-codex-ps-"$VERSION".zip \
  .genreleases/spec-kit-template-kilocode-sh-"$VERSION".zip \
  .genreleases/spec-kit-template-kilocode-ps-"$VERSION".zip \
  .genreleases/spec-kit-template-auggie-sh-"$VERSION".zip \
  .genreleases/spec-kit-template-auggie-ps-"$VERSION".zip \
  --title "Spec Kit Templates - $VERSION_NO_V" \
  --notes-file release_notes.md