#!/usr/bin/env bash
set -euo pipefail

# create-github-release.sh
# Create a GitHub release with all InfraKit template zip files
# Usage: create-github-release.sh <version>

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <version>" >&2
  exit 1
fi

VERSION="$1"

# Remove 'v' prefix from version for release title
VERSION_NO_V=${VERSION#v}

gh release create "$VERSION" \
  .genreleases/infrakit-template-copilot-crossplane-sh-"$VERSION".zip \
  .genreleases/infrakit-template-copilot-crossplane-ps-"$VERSION".zip \
  .genreleases/infrakit-template-claude-crossplane-sh-"$VERSION".zip \
  .genreleases/infrakit-template-claude-crossplane-ps-"$VERSION".zip \
  .genreleases/infrakit-template-gemini-crossplane-sh-"$VERSION".zip \
  .genreleases/infrakit-template-gemini-crossplane-ps-"$VERSION".zip \
  .genreleases/infrakit-template-cursor-agent-crossplane-sh-"$VERSION".zip \
  .genreleases/infrakit-template-cursor-agent-crossplane-ps-"$VERSION".zip \
  .genreleases/infrakit-template-opencode-crossplane-sh-"$VERSION".zip \
  .genreleases/infrakit-template-opencode-crossplane-ps-"$VERSION".zip \
  .genreleases/infrakit-template-qwen-crossplane-sh-"$VERSION".zip \
  .genreleases/infrakit-template-qwen-crossplane-ps-"$VERSION".zip \
  .genreleases/infrakit-template-windsurf-crossplane-sh-"$VERSION".zip \
  .genreleases/infrakit-template-windsurf-crossplane-ps-"$VERSION".zip \
  .genreleases/infrakit-template-codex-crossplane-sh-"$VERSION".zip \
  .genreleases/infrakit-template-codex-crossplane-ps-"$VERSION".zip \
  .genreleases/infrakit-template-kilocode-crossplane-sh-"$VERSION".zip \
  .genreleases/infrakit-template-kilocode-crossplane-ps-"$VERSION".zip \
  .genreleases/infrakit-template-auggie-crossplane-sh-"$VERSION".zip \
  .genreleases/infrakit-template-auggie-crossplane-ps-"$VERSION".zip \
  .genreleases/infrakit-template-roo-crossplane-sh-"$VERSION".zip \
  .genreleases/infrakit-template-roo-crossplane-ps-"$VERSION".zip \
  .genreleases/infrakit-template-codebuddy-crossplane-sh-"$VERSION".zip \
  .genreleases/infrakit-template-codebuddy-crossplane-ps-"$VERSION".zip \
  .genreleases/infrakit-template-qodercli-crossplane-sh-"$VERSION".zip \
  .genreleases/infrakit-template-qodercli-crossplane-ps-"$VERSION".zip \
  .genreleases/infrakit-template-amp-crossplane-sh-"$VERSION".zip \
  .genreleases/infrakit-template-amp-crossplane-ps-"$VERSION".zip \
  .genreleases/infrakit-template-shai-crossplane-sh-"$VERSION".zip \
  .genreleases/infrakit-template-shai-crossplane-ps-"$VERSION".zip \
  .genreleases/infrakit-template-q-crossplane-sh-"$VERSION".zip \
  .genreleases/infrakit-template-q-crossplane-ps-"$VERSION".zip \
  .genreleases/infrakit-template-agy-crossplane-sh-"$VERSION".zip \
  .genreleases/infrakit-template-agy-crossplane-ps-"$VERSION".zip \
  .genreleases/infrakit-template-bob-crossplane-sh-"$VERSION".zip \
  .genreleases/infrakit-template-bob-crossplane-ps-"$VERSION".zip \
  .genreleases/infrakit-template-generic-crossplane-sh-"$VERSION".zip \
  .genreleases/infrakit-template-generic-crossplane-ps-"$VERSION".zip \
  --title "InfraKit Templates - $VERSION_NO_V" \
  --notes-file release_notes.md
