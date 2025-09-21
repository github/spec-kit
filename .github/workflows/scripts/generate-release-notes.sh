#!/usr/bin/env bash
set -euo pipefail

# generate-release-notes.sh
# Generate release notes from git history
# Usage: generate-release-notes.sh <new_version> <last_tag>

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 <new_version> <last_tag>" >&2
  exit 1
fi

NEW_VERSION="$1"
LAST_TAG="$2"

# Get commits since last tag
if [ "$LAST_TAG" = "v0.0.0" ]; then
  # Check how many commits we have and use that as the limit
  COMMIT_COUNT=$(git rev-list --count HEAD)
  if [ "$COMMIT_COUNT" -gt 10 ]; then
    COMMITS=$(git log --oneline --pretty=format:"- %s" HEAD~10..HEAD)
  else
    COMMITS=$(git log --oneline --pretty=format:"- %s" HEAD~$COMMIT_COUNT..HEAD 2>/dev/null || git log --oneline --pretty=format:"- %s")
  fi
else
  COMMITS=$(git log --oneline --pretty=format:"- %s" $LAST_TAG..HEAD)
fi

# Create release notes
cat > release_notes.md << EOF
Template release $NEW_VERSION

Updated specification-driven development templates for GitHub Copilot, Claude Code, Gemini CLI, Cursor, Qwen, opencode, Windsurf, and Codex.

Now includes per-script variants for POSIX shell (sh) and PowerShell (ps).

Download the template for your preferred AI assistant + script type:
- spec-kit-template-copilot-sh-$NEW_VERSION.zip
- spec-kit-template-copilot-ps-$NEW_VERSION.zip
- spec-kit-template-claude-sh-$NEW_VERSION.zip
- spec-kit-template-claude-ps-$NEW_VERSION.zip
- spec-kit-template-gemini-sh-$NEW_VERSION.zip
- spec-kit-template-gemini-ps-$NEW_VERSION.zip
- spec-kit-template-cursor-sh-$NEW_VERSION.zip
- spec-kit-template-cursor-ps-$NEW_VERSION.zip
- spec-kit-template-opencode-sh-$NEW_VERSION.zip
- spec-kit-template-opencode-ps-$NEW_VERSION.zip
- spec-kit-template-qwen-sh-$NEW_VERSION.zip
- spec-kit-template-qwen-ps-$NEW_VERSION.zip
- spec-kit-template-windsurf-sh-$NEW_VERSION.zip
- spec-kit-template-windsurf-ps-$NEW_VERSION.zip
- spec-kit-template-codex-sh-$NEW_VERSION.zip
- spec-kit-template-codex-ps-$NEW_VERSION.zip
EOF

echo "Generated release notes:"
cat release_notes.md