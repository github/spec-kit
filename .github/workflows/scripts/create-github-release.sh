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

AGENTS=(
  claude
  gemini
  copilot
  cursor-agent
  qwen
  opencode
  windsurf
  codex
  kilocode
  auggie
  roo
  codebuddy
  amp
  q
)

FILES=()
for agent in "${AGENTS[@]}"; do
  artifact=".genreleases/spec-kit-template-${agent}-${VERSION}.zip"
  if [[ ! -f "$artifact" ]]; then
    echo "Error: missing release artifact '$artifact'" >&2
    exit 1
  fi
  FILES+=("$artifact")
done

gh release create "$VERSION" \
  "${FILES[@]}" \
  --title "Spec Kit Templates - $VERSION_NO_V" \
  --notes-file release_notes.md
