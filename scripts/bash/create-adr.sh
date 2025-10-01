#!/usr/bin/env bash
set -euo pipefail

# create-adr.sh - Create a new Architecture Decision Record deterministically
# Usage:
#   scripts/bash/create-adr.sh \
#     --title "Use WebSockets for Real-time Chat" \
#     [--feature 003-chat-system] \
#     [--spec specs/003-chat-system/spec.md] \
#     [--plan specs/003-chat-system/plan.md] \
#     [--context "Need bidirectional low-latency messaging"] \
#     [--decision "Adopt WebSockets"] \
#     [--positive "+ Low latency; + Bidirectional"] \
#     [--negative "- Connection mgmt complexity"] \
#     [--alternatives "SSE; Polling; GraphQL Subscriptions"] \
#     [--json]
#
# Behavior:
#   - Ensures docs/adr exists
#   - Computes next ADR ID (0001, 0002, ...)
#   - Slugifies title for filename
#   - Copies templates/adr-template.md if present, otherwise writes a minimal template
#   - Replaces placeholders and prints absolute path (and JSON if --json)

JSON=false
TITLE=""
FEATURE=""
SPEC_LINK=""
PLAN_LINK=""
CTX=""
DECISION=""
POS=""
NEG=""
ALTS=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --json) JSON=true; shift ;;
    --title) TITLE=${2:-}; shift 2 ;;
    --feature) FEATURE=${2:-}; shift 2 ;;
    --spec) SPEC_LINK=${2:-}; shift 2 ;;
    --plan) PLAN_LINK=${2:-}; shift 2 ;;
    --context) CTX=${2:-}; shift 2 ;;
    --decision) DECISION=${2:-}; shift 2 ;;
    --positive) POS=${2:-}; shift 2 ;;
    --negative) NEG=${2:-}; shift 2 ;;
    --alternatives) ALTS=${2:-}; shift 2 ;;
    --help|-h)
      cat <<EOF
Usage: $0 --title <title> [options]
Options:
  --feature <slug>         Feature slug or branch (e.g., 003-chat-system)
  --spec <path>            Path to feature spec file
  --plan <path>            Path to feature plan file
  --context <text>         ADR context
  --decision <text>        ADR decision summary
  --positive <text>        Positive consequences (semicolon separated)
  --negative <text>        Negative consequences (semicolon separated)
  --alternatives <text>    Alternatives considered (semicolon separated)
  --json                   Output JSON with id and path
  --help                   Show help
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
ADR_DIR="$REPO_ROOT/docs/adr"
TPL="$REPO_ROOT/templates/adr-template.md"
mkdir -p "$ADR_DIR"

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
DATE_ISO=$(date -u +%Y-%m-%d)
OUTFILE="$ADR_DIR/${ID}-${SLUG}.md"

if [[ -f "$TPL" ]]; then
  cp "$TPL" "$OUTFILE"
  sed -i '' \
    -e "s/{{ID}}/$ID/g" \
    -e "s/{{TITLE}}/$(printf '%s' "$TITLE" | sed 's,/,\\/,g')/g" \
    -e "s/{{DATE_ISO}}/$DATE_ISO/g" \
    -e "s/{{FEATURE_NAME}}/$(printf '%s' "$FEATURE" | sed 's,/,\\/,g')/g" \
    -e "s/{{CONTEXT}}/$(printf '%s' "$CTX" | sed 's,/,\\/,g')/g" \
    -e "s/{{DECISION}}/$(printf '%s' "$DECISION" | sed 's,/,\\/,g')/g" \
    -e "s/{{POSITIVE_CONSEQUENCES}}/$(printf '%s' "$POS" | sed 's,/,\\/,g')/g" \
    -e "s/{{NEGATIVE_CONSEQUENCES}}/$(printf '%s' "$NEG" | sed 's,/,\\/,g')/g" \
    -e "s/{{ALTERNATIVES}}/$(printf '%s' "$ALTS" | sed 's,/,\\/,g')/g" \
    -e "s,{{SPEC_LINK}},$SPEC_LINK,g" \
    -e "s,{{PLAN_LINK}},$PLAN_LINK,g" \
    -e "s/{{RELATED_ADRS}}/none/g" \
    "$OUTFILE"
else
  cat > "$OUTFILE" <<EOF
# ADR-$ID: $TITLE

- **Status:** Proposed
- **Date:** $DATE_ISO
- **Feature:** ${FEATURE:-}
- **Context:** ${CTX:-}
- **Decision:** ${DECISION:-}
- **Consequences:**
  - **Positive:** ${POS:-}
  - **Negative:** ${NEG:-}
- **Alternatives Considered:** ${ALTS:-}
- **References:**
  - Feature Spec: ${SPEC_LINK:-}
  - Implementation Plan: ${PLAN_LINK:-}
  - Related ADRs: none
EOF
fi

ABS=$(cd "$(dirname "$OUTFILE")" && pwd)/$(basename "$OUTFILE")
if $JSON; then
  printf '{"id":"%s","path":"%s"}\n' "$ID" "$ABS"
else
  echo "$ABS"
fi
