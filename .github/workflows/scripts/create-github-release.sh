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
  .genreleases/diagramly-kit-template-copilot-sh-"$VERSION".zip \
  .genreleases/diagramly-kit-template-copilot-ps-"$VERSION".zip \
  .genreleases/diagramly-kit-template-claude-sh-"$VERSION".zip \
  .genreleases/diagramly-kit-template-claude-ps-"$VERSION".zip \
  .genreleases/diagramly-kit-template-gemini-sh-"$VERSION".zip \
  .genreleases/diagramly-kit-template-gemini-ps-"$VERSION".zip \
  .genreleases/diagramly-kit-template-cursor-sh-"$VERSION".zip \
  .genreleases/diagramly-kit-template-cursor-ps-"$VERSION".zip \
  .genreleases/diagramly-kit-template-opencode-sh-"$VERSION".zip \
  .genreleases/diagramly-kit-template-opencode-ps-"$VERSION".zip \
  .genreleases/diagramly-kit-template-qwen-sh-"$VERSION".zip \
  .genreleases/diagramly-kit-template-qwen-ps-"$VERSION".zip \
  .genreleases/diagramly-kit-template-windsurf-sh-"$VERSION".zip \
  .genreleases/diagramly-kit-template-windsurf-ps-"$VERSION".zip \
  .genreleases/diagramly-kit-template-codex-sh-"$VERSION".zip \
  .genreleases/diagramly-kit-template-codex-ps-"$VERSION".zip \
  .genreleases/diagramly-kit-template-kilocode-sh-"$VERSION".zip \
  .genreleases/diagramly-kit-template-kilocode-ps-"$VERSION".zip \
  .genreleases/diagramly-kit-template-auggie-sh-"$VERSION".zip \
  .genreleases/diagramly-kit-template-auggie-ps-"$VERSION".zip \
  .genreleases/diagramly-kit-template-roo-sh-"$VERSION".zip \
  .genreleases/diagramly-kit-template-roo-ps-"$VERSION".zip \
  .genreleases/diagramly-kit-template-codebuddy-sh-"$VERSION".zip \
  .genreleases/diagramly-kit-template-codebuddy-ps-"$VERSION".zip \
  .genreleases/diagramly-kit-template-q-sh-"$VERSION".zip \
  .genreleases/diagramly-kit-template-q-ps-"$VERSION".zip \
  --title "Diagramly Kit Templates - $VERSION_NO_V" \
  --notes-file release_notes.md