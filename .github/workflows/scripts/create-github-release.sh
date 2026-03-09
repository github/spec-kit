#!/usr/bin/env bash

# Create GitHub Release with all agent template packages
#
# This script creates a GitHub release and uploads all generated zip archives
# as release assets.

set -euo pipefail

#==============================================================================
# Configuration
#==============================================================================

# Version from git tag or environment
VERSION="${VERSION:-$(git describe --tags --always 2>/dev/null || echo 'dev')}"

# Release directory
RELEASE_DIR=".genreleases"

#==============================================================================
# Main
#==============================================================================

echo "Creating GitHub release for version: $VERSION"
echo ""

# Create the release with all agent packages
gh release create "$VERSION" \
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
  .genreleases/spec-kit-template-generic-sh-"$VERSION".zip \
  .genreleases/spec-kit-template-generic-ps-"$VERSION".zip \
  --title "Spec Kit Templates - $VERSION_NO_V" \
  --notes-file release_notes.md
