#!/usr/bin/env bash

set -e

# Source common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

JSON_MODE=false
LIMIT=10
QUERY=""
SEARCH_TYPE="all"  # all, code, docs, tests
FEATURE_FILTER=""

# Parse arguments
while [ $# -gt 0 ]; do
    case "$1" in
        --json)
            JSON_MODE=true
            shift
            ;;
        --limit)
            LIMIT="$2"
            shift 2
            ;;
        --type)
            SEARCH_TYPE="$2"
            shift 2
            ;;
        --feature)
            FEATURE_FILTER="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [--json] [options] \"query\""
            echo ""
            echo "Options:"
            echo "  --json              Output in JSON format"
            echo "  --limit N           Show top N results (default: 10)"
            echo "  --type TYPE         Filter by type: code, docs, tests, all (default: all)"
            echo "  --feature NAME      Search only in specific feature"
            echo ""
            echo "Examples:"
            echo "  $0 \"authentication handling\""
            echo "  $0 --type code \"validation logic\""
            echo "  $0 --feature 001-tasks \"status update\""
            exit 0
            ;;
        *)
            QUERY="$QUERY $1"
            shift
            ;;
    esac
done

# Trim query
QUERY=$(echo "$QUERY" | xargs)

if [ -z "$QUERY" ]; then
    echo "ERROR: No search query provided" >&2
    echo "Usage: $0 \"your search query\"" >&2
    exit 1
fi

# Get repository root
REPO_ROOT=$(get_repo_root)

# Extract keywords from query (remove common stop words)
extract_keywords() {
    local query="$1"
    # Convert to lowercase, remove stop words, split on spaces
    echo "$query" | tr '[:upper:]' '[:lower:]' | \
        sed 's/\b\(the\|is\|are\|where\|what\|how\|does\|do\|for\|to\|in\|on\|at\|from\|by\|with\)\b//g' | \
        tr -s ' ' '\n' | grep -v '^$' | sort -u
}

# Determine file type
get_file_type() {
    local file="$1"
    case "$file" in
        *.py|*.js|*.ts|*.tsx|*.jsx|*.go|*.rs|*.java|*.c|*.cpp|*.h)
            echo "code"
            ;;
        *test*.py|*test*.js|*test*.ts|*_test.go|*Test.java)
            echo "test"
            ;;
        *.md)
            if [[ "$file" == */specs/* ]]; then
                echo "docs"
            else
                echo "docs"
            fi
            ;;
        *)
            echo "other"
            ;;
    esac
}

# Calculate relevance score
calculate_score() {
    local matches=$1
    local proximity=$2
    local file_type=$3
    local is_quick_ref=$4

    local score=$((matches * 40))

    # Proximity bonus (terms close together)
    [ "$proximity" = "high" ] && score=$((score + 30))
    [ "$proximity" = "medium" ] && score=$((score + 15))

    # File type bonus
    case "$file_type" in
        docs)
            score=$((score + 20))
            [ "$is_quick_ref" = "true" ] && score=$((score + 10))
            ;;
        code)
            score=$((score + 15))
            ;;
        test)
            score=$((score + 10))
            ;;
    esac

    # Cap at 100
    [ $score -gt 100 ] && score=100

    echo $score
}

# Search function
KEYWORDS=$(extract_keywords "$QUERY")
RESULTS=()
RESULT_FILES=()
RESULT_LINES=()
RESULT_CONTEXTS=()
RESULT_TYPES=()
RESULT_SCORES=()

# Build search pattern
GREP_PATTERN=$(echo "$KEYWORDS" | tr '\n' '|' | sed 's/|$//')

# Determine search locations
SEARCH_DIRS=("$REPO_ROOT/specs")
if [ "$SEARCH_TYPE" = "all" ] || [ "$SEARCH_TYPE" = "code" ]; then
    [ -d "$REPO_ROOT/src" ] && SEARCH_DIRS+=("$REPO_ROOT/src")
    [ -d "$REPO_ROOT/lib" ] && SEARCH_DIRS+=("$REPO_ROOT/lib")
fi
if [ "$SEARCH_TYPE" = "all" ] || [ "$SEARCH_TYPE" = "tests" ]; then
    [ -d "$REPO_ROOT/tests" ] && SEARCH_DIRS+=("$REPO_ROOT/tests")
    [ -d "$REPO_ROOT/test" ] && SEARCH_DIRS+=("$REPO_ROOT/test")
fi

# Apply feature filter
if [ -n "$FEATURE_FILTER" ]; then
    SEARCH_DIRS=("$REPO_ROOT/specs/$FEATURE_FILTER")
fi

# Perform search
START_TIME=$(date +%s%3N)

for search_dir in "${SEARCH_DIRS[@]}"; do
    [ ! -d "$search_dir" ] && continue

    while IFS=: read -r file line context; do
        # Skip binary files
        file "$file" | grep -q "text" || continue

        # Count keyword matches
        matches=0
        for keyword in $KEYWORDS; do
            echo "$context" | grep -iq "$keyword" && matches=$((matches + 1))
        done

        [ $matches -eq 0 ] && continue

        # Determine proximity (simple heuristic: all keywords in one line = high)
        proximity="low"
        all_in_line=true
        for keyword in $KEYWORDS; do
            echo "$context" | grep -iq "$keyword" || all_in_line=false
        done
        $all_in_line && proximity="high"

        # Get file type
        file_type=$(get_file_type "$file")

        # Check if quick ref
        is_quick_ref="false"
        [[ "$file" == *"/quick-ref.md" ]] && is_quick_ref="true"

        # Calculate score
        score=$(calculate_score $matches $proximity $file_type $is_quick_ref)

        # Store result
        RESULT_FILES+=("$file")
        RESULT_LINES+=("$line")
        RESULT_CONTEXTS+=("$context")
        RESULT_TYPES+=("$file_type")
        RESULT_SCORES+=("$score")

    done < <(grep -rni "$GREP_PATTERN" "$search_dir" 2>/dev/null | head -100)
done

END_TIME=$(date +%s%3N)
SEARCH_TIME=$((END_TIME - START_TIME))

# Sort results by score (descending)
SORTED_INDICES=()
for i in "${!RESULT_SCORES[@]}"; do
    SORTED_INDICES+=("$i:${RESULT_SCORES[$i]}")
done

# Sort and extract indices
SORTED_INDICES=($(printf '%s\n' "${SORTED_INDICES[@]}" | sort -t: -k2 -rn | cut -d: -f1))

# Output results
TOTAL_RESULTS=${#RESULT_FILES[@]}

if [ "$JSON_MODE" = true ]; then
    echo -n '{"query": "'"$QUERY"'", "results": ['

    count=0
    for idx in "${SORTED_INDICES[@]}"; do
        [ $count -ge $LIMIT ] && break

        file="${RESULT_FILES[$idx]}"
        line="${RESULT_LINES[$idx]}"
        context="${RESULT_CONTEXTS[$idx]}"
        type="${RESULT_TYPES[$idx]}"
        score="${RESULT_SCORES[$idx]}"

        # Escape quotes in context
        context=$(echo "$context" | sed 's/"/\\"/g')

        [ $count -gt 0 ] && echo -n ","
        echo -n "{\"file\": \"$file\", \"line\": $line, \"type\": \"$type\", \"context\": \"$context\", \"relevance\": $score}"

        count=$((count + 1))
    done

    echo "], \"total_results\": $TOTAL_RESULTS, \"search_time_ms\": $SEARCH_TIME}"
else
    # Human-readable output
    echo "Search Results: \"$QUERY\""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    if [ $TOTAL_RESULTS -eq 0 ]; then
        echo "No matches found."
        echo ""
        echo "Try:"
        echo "  • Broader search terms"
        echo "  • Different keywords"
        echo "  • Check spelling"
    else
        echo "Found $TOTAL_RESULTS matches (showing top $LIMIT):"
        echo ""

        count=0
        for idx in "${SORTED_INDICES[@]}"; do
            [ $count -ge $LIMIT ] && break

            file="${RESULT_FILES[$idx]}"
            line="${RESULT_LINES[$idx]}"
            context="${RESULT_CONTEXTS[$idx]}"
            type="${RESULT_TYPES[$idx]}"
            score="${RESULT_SCORES[$idx]}"

            # Determine icon
            icon="📄"
            case "$type" in
                code) icon="🔧" ;;
                docs) icon="📝" ;;
                test) icon="🧪" ;;
            esac

            # Make file path relative
            rel_file="${file#$REPO_ROOT/}"

            echo "$((count + 1)). $rel_file:$line (relevance: $score%)"
            echo "   $icon $(echo "$context" | xargs | cut -c1-80)"
            echo ""

            count=$((count + 1))
        done

        # Quick ref suggestion
        for idx in "${SORTED_INDICES[@]}"; do
            file="${RESULT_FILES[$idx]}"
            if [[ "$file" == *"/quick-ref.md" ]]; then
                rel_file="${file#$REPO_ROOT/}"
                echo "💡 Quick Reference Available:"
                echo "  $rel_file (~200 tokens)"
                echo ""
                echo "Read this first for an overview!"
                break
            fi
        done
    fi

    echo "Search completed in ${SEARCH_TIME}ms"
fi
