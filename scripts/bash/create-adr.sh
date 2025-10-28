#!/usr/bin/env bash
set -euo pipefail

# create-adr.sh - Create a new Architecture Decision Record deterministically
#
# This script ONLY:
#   1. Creates the correct directory structure (history/adr/)
#   2. Copies the template with {{PLACEHOLDERS}} intact
#   3. Returns metadata (id, path) for AI to fill in
#
# The calling AI agent is responsible for filling {{PLACEHOLDERS}}
#
# Usage:
#   scripts/bash/create-adr.sh \
#     --title "Use WebSockets for Real-time Chat" \
#     [--json]

JSON=false
TITLE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --json) JSON=true; shift ;;
    --title) TITLE=${2:-}; shift 2 ;;
    --help|-h)
      cat <<EOF
Usage: $0 --title <title> [options]

Required:
  --title <text>       Title for the ADR (used for filename)

Optional:
  --json               Output JSON with id and path

Output:
  Creates ADR file with template placeholders ({{ID}}, {{TITLE}}, etc.)
  AI agent must fill these placeholders after creation

Examples:
  $0 --title "Use WebSockets for Real-time Chat" --json
  $0 --title "Adopt PostgreSQL for Primary Database"
EOF
      exit 0
      ;;
    *) shift ;;
  esac
done

if [[ -z "$TITLE" ]]; then
  echo "Error: --title is required" >&2
  exit 1
fi

REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
ADR_DIR="$REPO_ROOT/history/adr"
mkdir -p "$ADR_DIR"

# Check for template (try both locations)
TPL=""
if [[ -f "$REPO_ROOT/.specify/templates/adr-template.md" ]]; then
  TPL="$REPO_ROOT/.specify/templates/adr-template.md"
elif [[ -f "$REPO_ROOT/templates/adr-template.md" ]]; then
  TPL="$REPO_ROOT/templates/adr-template.md"
else
  echo "Error: ADR template not found at .specify/templates/ or templates/" >&2
  exit 1
fi

# next id
next_id() {
  local max=0 base num
  shopt -s nullglob
  for f in "$ADR_DIR"/[0-9][0-9][0-9][0-9]-*.md; do
    base=$(basename "$f")
    num=${base%%-*}
    if [[ $num =~ ^[0-9]{4}$ ]]; then
      local n=$((10#$num))
      (( n > max )) && max=$n
    fi
  done
  printf "%04d" $((max+1))
}

slugify() {
  echo "$1" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g; s/-\{2,\}/-/g; s/^-//; s/-$//'
}

ID=$(next_id)
SLUG=$(slugify "$TITLE")
OUTFILE="$ADR_DIR/${ID}-${SLUG}.md"

# Simply copy the template (AI will fill placeholders)
cp "$TPL" "$OUTFILE"

ABS=$(cd "$(dirname "$OUTFILE")" && pwd)/$(basename "$OUTFILE")
if $JSON; then
  printf '{"id":"%s","path":"%s","template":"%s"}\n' "$ID" "$ABS" "$(basename "$TPL")"
else
  echo "✅ ADR template copied → $ABS"
  echo "Note: AI agent should now fill in {{PLACEHOLDERS}}"
fi
