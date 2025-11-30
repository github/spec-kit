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
  .genreleases/spectrena-template-copilot-sh-"$VERSION".zip \
  .genreleases/spectrena-template-copilot-ps-"$VERSION".zip \
  .genreleases/spectrena-template-claude-sh-"$VERSION".zip \
  .genreleases/spectrena-template-claude-ps-"$VERSION".zip \
  .genreleases/spectrena-template-gemini-sh-"$VERSION".zip \
  .genreleases/spectrena-template-gemini-ps-"$VERSION".zip \
  .genreleases/spectrena-template-cursor-agent-sh-"$VERSION".zip \
  .genreleases/spectrena-template-cursor-agent-ps-"$VERSION".zip \
  .genreleases/spectrena-template-opencode-sh-"$VERSION".zip \
  .genreleases/spectrena-template-opencode-ps-"$VERSION".zip \
  .genreleases/spectrena-template-qwen-sh-"$VERSION".zip \
  .genreleases/spectrena-template-qwen-ps-"$VERSION".zip \
  .genreleases/spectrena-template-windsurf-sh-"$VERSION".zip \
  .genreleases/spectrena-template-windsurf-ps-"$VERSION".zip \
  .genreleases/spectrena-template-codex-sh-"$VERSION".zip \
  .genreleases/spectrena-template-codex-ps-"$VERSION".zip \
  .genreleases/spectrena-template-kilocode-sh-"$VERSION".zip \
  .genreleases/spectrena-template-kilocode-ps-"$VERSION".zip \
  .genreleases/spectrena-template-auggie-sh-"$VERSION".zip \
  .genreleases/spectrena-template-auggie-ps-"$VERSION".zip \
  .genreleases/spectrena-template-roo-sh-"$VERSION".zip \
  .genreleases/spectrena-template-roo-ps-"$VERSION".zip \
  .genreleases/spectrena-template-codebuddy-sh-"$VERSION".zip \
  .genreleases/spectrena-template-codebuddy-ps-"$VERSION".zip \
  .genreleases/spectrena-template-amp-sh-"$VERSION".zip \
  .genreleases/spectrena-template-amp-ps-"$VERSION".zip \
  .genreleases/spectrena-template-shai-sh-"$VERSION".zip \
  .genreleases/spectrena-template-shai-ps-"$VERSION".zip \
  .genreleases/spectrena-template-q-sh-"$VERSION".zip \
  .genreleases/spectrena-template-q-ps-"$VERSION".zip \
  .genreleases/spectrena-template-bob-sh-"$VERSION".zip \
  .genreleases/spectrena-template-bob-ps-"$VERSION".zip \
  --title "Spectrena Templates - $VERSION_NO_V" \
  --notes-file release_notes.md
