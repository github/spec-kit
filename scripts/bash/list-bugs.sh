#!/usr/bin/env bash

# List unresolved bugs from validation
#
# This script scans validation/bugs/ directory and returns bugs that haven't been resolved.
# Used by the fix command to automatically load bugs to fix.
#
# Usage: ./list-bugs.sh [OPTIONS]
#
# OPTIONS:
#   --json              Output in JSON format
#   --all               Include resolved bugs (default: unresolved only)
#   --summary           Show summary counts only
#   --help, -h          Show help message
#
# OUTPUTS:
#   JSON mode: {"FEATURE_DIR":"...", "BUGS":[{"id":"...", "status":"...", ...}], "SUMMARY":{...}}
#   Text mode: List of bug files with status

set -e

# Parse command line arguments
JSON_MODE=false
INCLUDE_RESOLVED=false
SUMMARY_ONLY=false

for arg in "$@"; do
    case "$arg" in
        --json)
            JSON_MODE=true
            ;;
        --all)
            INCLUDE_RESOLVED=true
            ;;
        --summary)
            SUMMARY_ONLY=true
            ;;
        --help|-h)
            cat << 'EOF'
Usage: list-bugs.sh [OPTIONS]

List unresolved bugs from validation/bugs/ directory.

OPTIONS:
  --json              Output in JSON format
  --all               Include resolved bugs (default: unresolved only)
  --summary           Show summary counts only
  --help, -h          Show this help message

BUG FILE FORMAT:
  Each bug file in validation/bugs/ should be named: BUG-{number}-{short-desc}.md
  The file must contain YAML frontmatter with at least:
    - status: open | in_progress | resolved | wont_fix
    - severity: critical | high | medium | low
    - user_story: US identifier (e.g., US1, US2)

EXAMPLES:
  # List unresolved bugs in JSON (for fix command)
  ./list-bugs.sh --json

  # Show all bugs including resolved
  ./list-bugs.sh --all

  # Get summary counts only
  ./list-bugs.sh --summary

EOF
            exit 0
            ;;
        *)
            echo "ERROR: Unknown option '$arg'. Use --help for usage information." >&2
            exit 1
            ;;
    esac
done

# Source common functions
SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Get feature paths
eval $(get_feature_paths)

BUGS_DIR="$FEATURE_DIR/validation/bugs"

# Initialize counters
total=0
open=0
in_progress=0
resolved=0
wont_fix=0
critical=0
high=0
medium=0
low=0

# Initialize bug list for JSON
bugs_json=""

# Check if bugs directory exists
if [[ ! -d "$BUGS_DIR" ]]; then
    if $JSON_MODE; then
        printf '{"FEATURE_DIR":"%s","BUGS":[],"SUMMARY":{"total":0,"open":0,"in_progress":0,"resolved":0,"critical":0,"high":0,"medium":0,"low":0}}\n' "$FEATURE_DIR"
    else
        echo "No bugs directory found at: $BUGS_DIR"
        echo "This feature has no recorded validation bugs."
    fi
    exit 0
fi

# Process each bug file
for bug_file in "$BUGS_DIR"/BUG-*.md; do
    # Check if any files exist (glob might return literal if no matches)
    [[ -e "$bug_file" ]] || continue

    ((total++))

    # Extract metadata from YAML frontmatter
    bug_id=$(basename "$bug_file" .md)

    # Parse frontmatter (between first --- and second ---)
    status=""
    severity=""
    user_story=""
    title=""
    scenario=""

    in_frontmatter=false
    while IFS= read -r line; do
        if [[ "$line" == "---" ]]; then
            if $in_frontmatter; then
                break  # End of frontmatter
            else
                in_frontmatter=true
                continue
            fi
        fi

        if $in_frontmatter; then
            # Parse YAML key: value
            if [[ "$line" =~ ^status:\ *(.+)$ ]]; then
                status="${BASH_REMATCH[1]}"
            elif [[ "$line" =~ ^severity:\ *(.+)$ ]]; then
                severity="${BASH_REMATCH[1]}"
            elif [[ "$line" =~ ^user_story:\ *(.+)$ ]]; then
                user_story="${BASH_REMATCH[1]}"
            elif [[ "$line" =~ ^title:\ *(.+)$ ]]; then
                title="${BASH_REMATCH[1]}"
            elif [[ "$line" =~ ^scenario:\ *(.+)$ ]]; then
                scenario="${BASH_REMATCH[1]}"
            fi
        fi
    done < "$bug_file"

    # Update counters
    case "$status" in
        open) ((open++)) ;;
        in_progress) ((in_progress++)) ;;
        resolved) ((resolved++)) ;;
        wont_fix) ((wont_fix++)) ;;
    esac

    case "$severity" in
        critical) ((critical++)) ;;
        high) ((high++)) ;;
        medium) ((medium++)) ;;
        low) ((low++)) ;;
    esac

    # Skip resolved bugs unless --all
    if ! $INCLUDE_RESOLVED && [[ "$status" == "resolved" || "$status" == "wont_fix" ]]; then
        continue
    fi

    # Add to output
    if $JSON_MODE && ! $SUMMARY_ONLY; then
        # Escape quotes in title
        escaped_title="${title//\"/\\\"}"
        escaped_scenario="${scenario//\"/\\\"}"

        if [[ -n "$bugs_json" ]]; then
            bugs_json+=","
        fi
        bugs_json+="{\"id\":\"$bug_id\",\"status\":\"$status\",\"severity\":\"$severity\",\"user_story\":\"$user_story\",\"title\":\"$escaped_title\",\"scenario\":\"$escaped_scenario\",\"file\":\"$bug_file\"}"
    elif ! $SUMMARY_ONLY; then
        # Text output
        status_icon="?"
        case "$status" in
            open) status_icon="🔴" ;;
            in_progress) status_icon="🟡" ;;
            resolved) status_icon="🟢" ;;
            wont_fix) status_icon="⚪" ;;
        esac

        severity_badge=""
        case "$severity" in
            critical) severity_badge="[CRITICAL]" ;;
            high) severity_badge="[HIGH]" ;;
            medium) severity_badge="[MEDIUM]" ;;
            low) severity_badge="[LOW]" ;;
        esac

        echo "$status_icon $bug_id $severity_badge - $title ($user_story)"
    fi
done

# Calculate unresolved count
unresolved=$((open + in_progress))

# Output results
if $JSON_MODE; then
    printf '{"FEATURE_DIR":"%s","BUGS":[%s],"SUMMARY":{"total":%d,"unresolved":%d,"open":%d,"in_progress":%d,"resolved":%d,"wont_fix":%d,"critical":%d,"high":%d,"medium":%d,"low":%d}}\n' \
        "$FEATURE_DIR" "$bugs_json" "$total" "$unresolved" "$open" "$in_progress" "$resolved" "$wont_fix" "$critical" "$high" "$medium" "$low"
else
    if $SUMMARY_ONLY || [[ $total -gt 0 ]]; then
        echo ""
        echo "=== Bug Summary ==="
        echo "Total: $total"
        echo "  Open: $open"
        echo "  In Progress: $in_progress"
        echo "  Resolved: $resolved"
        echo "  Won't Fix: $wont_fix"
        echo ""
        echo "By Severity:"
        echo "  Critical: $critical"
        echo "  High: $high"
        echo "  Medium: $medium"
        echo "  Low: $low"
        echo ""
        if [[ $unresolved -gt 0 ]]; then
            echo "⚠️  $unresolved bug(s) need attention"
        else
            echo "✅ All bugs resolved"
        fi
    fi
fi
