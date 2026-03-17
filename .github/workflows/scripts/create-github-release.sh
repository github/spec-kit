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

# Find the built wheel dynamically to avoid version mismatch between
# pyproject.toml and the git tag.
shopt -s nullglob
wheel_files=(.genreleases/specify_cli-*-py3-none-any.whl)

if (( ${#wheel_files[@]} == 0 )); then
  echo "Error: No specify_cli wheel found in .genreleases/" >&2
  exit 1
fi

if (( ${#wheel_files[@]} > 1 )); then
  echo "Error: Multiple specify_cli wheels found in .genreleases/; expected exactly one:" >&2
  printf '  %s\n' "${wheel_files[@]}" >&2
  exit 1
fi

WHEEL_FILE="${wheel_files[0]}"

gh release create "$VERSION" \
  "$WHEEL_FILE" \
  .genreleases/spec-kit-template-copilot-sh-"$VERSION".zip \
  .genreleases/spec-kit-template-copilot-ps-"$VERSION".zip \
  .genreleases/spec-kit-template-claude-sh-"$VERSION".zip \
  .genreleases/spec-kit-template-claude-ps-"$VERSION".zip \
  .genreleases/spec-kit-template-gemini-sh-"$VERSION".zip \
  .genreleases/spec-kit-template-gemini-ps-"$VERSION".zip \
  .genreleases/spec-kit-template-cursor-agent-sh-"$VERSION".zip \
  .genreleases/spec-kit-template-cursor-agent-ps-"$VERSION".zip \
  .genreleases/spec-kit-template-opencode-sh-"$VERSION".zip \
  .genreleases/spec-kit-template-opencode-ps-"$VERSION".zip \
  .genreleases/spec-kit-template-qwen-sh-"$VERSION".zip \
  .genreleases/spec-kit-template-qwen-ps-"$VERSION".zip \
  .genreleases/spec-kit-template-windsurf-sh-"$VERSION".zip \
  .genreleases/spec-kit-template-windsurf-ps-"$VERSION".zip \
  .genreleases/spec-kit-template-junie-sh-"$VERSION".zip \
  .genreleases/spec-kit-template-junie-ps-"$VERSION".zip \
  .genreleases/spec-kit-template-codex-sh-"$VERSION".zip \
  .genreleases/spec-kit-template-codex-ps-"$VERSION".zip \
  .genreleases/spec-kit-template-kilocode-sh-"$VERSION".zip \
  .genreleases/spec-kit-template-kilocode-ps-"$VERSION".zip \
  .genreleases/spec-kit-template-auggie-sh-"$VERSION".zip \
  .genreleases/spec-kit-template-auggie-ps-"$VERSION".zip \
  .genreleases/spec-kit-template-roo-sh-"$VERSION".zip \
  .genreleases/spec-kit-template-roo-ps-"$VERSION".zip \
  .genreleases/spec-kit-template-codebuddy-sh-"$VERSION".zip \
  .genreleases/spec-kit-template-codebuddy-ps-"$VERSION".zip \
  .genreleases/spec-kit-template-qodercli-sh-"$VERSION".zip \
  .genreleases/spec-kit-template-qodercli-ps-"$VERSION".zip \
  .genreleases/spec-kit-template-amp-sh-"$VERSION".zip \
  .genreleases/spec-kit-template-amp-ps-"$VERSION".zip \
  .genreleases/spec-kit-template-shai-sh-"$VERSION".zip \
  .genreleases/spec-kit-template-shai-ps-"$VERSION".zip \
  .genreleases/spec-kit-template-tabnine-sh-"$VERSION".zip \
  .genreleases/spec-kit-template-tabnine-ps-"$VERSION".zip \
  .genreleases/spec-kit-template-kiro-cli-sh-"$VERSION".zip \
  .genreleases/spec-kit-template-kiro-cli-ps-"$VERSION".zip \
  .genreleases/spec-kit-template-agy-sh-"$VERSION".zip \
  .genreleases/spec-kit-template-agy-ps-"$VERSION".zip \
  .genreleases/spec-kit-template-bob-sh-"$VERSION".zip \
  .genreleases/spec-kit-template-bob-ps-"$VERSION".zip \
  .genreleases/spec-kit-template-vibe-sh-"$VERSION".zip \
  .genreleases/spec-kit-template-vibe-ps-"$VERSION".zip \
  .genreleases/spec-kit-template-kimi-sh-"$VERSION".zip \
  .genreleases/spec-kit-template-kimi-ps-"$VERSION".zip \
  .genreleases/spec-kit-template-trae-sh-"$VERSION".zip \
  .genreleases/spec-kit-template-trae-ps-"$VERSION".zip \
  .genreleases/spec-kit-template-pi-sh-"$VERSION".zip \
  .genreleases/spec-kit-template-pi-ps-"$VERSION".zip \
  .genreleases/spec-kit-template-iflow-sh-"$VERSION".zip \
  .genreleases/spec-kit-template-iflow-ps-"$VERSION".zip \
  .genreleases/spec-kit-template-generic-sh-"$VERSION".zip \
  .genreleases/spec-kit-template-generic-ps-"$VERSION".zip \
  --title "Spec Kit Templates - $VERSION_NO_V" \
  --notes-file release_notes.md
