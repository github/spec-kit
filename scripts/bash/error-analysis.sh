#!/usr/bin/env bash

set -e

# Source common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

JSON_MODE=false
ERROR_MESSAGE=""
ERROR_FILE=""
ERROR_LINE=""

# Parse arguments
while [ $# -gt 0 ]; do
    case "$1" in
        --json)
            JSON_MODE=true
            shift
            ;;
        --file)
            ERROR_FILE="$2"
            shift 2
            ;;
        --line)
            ERROR_LINE="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [--json] [--file FILE] [--line LINE] ERROR_MESSAGE"
            echo ""
            echo "Analyze errors with specification context."
            echo ""
            echo "Options:"
            echo "  --json          Output in JSON format"
            echo "  --file FILE     File where error occurred"
            echo "  --line LINE     Line number where error occurred"
            echo ""
            echo "Examples:"
            echo "  $0 \"TypeError: Cannot read property 'status' of undefined\""
            echo "  $0 --file src/api/tasks.py --line 145 \"TypeError\""
            exit 0
            ;;
        *)
            ERROR_MESSAGE="$ERROR_MESSAGE $1"
            shift
            ;;
    esac
done

ERROR_MESSAGE=$(echo "$ERROR_MESSAGE" | sed 's/^ *//')

if [ -z "$ERROR_MESSAGE" ]; then
    echo "Error: No error message provided" >&2
    exit 1
fi

# Get repository root
REPO_ROOT=$(get_repo_root)

# Extract keywords from error message
extract_keywords() {
    local text="$1"
    # Convert to lowercase, remove common words, split on non-alphanumeric
    echo "$text" | \
        tr '[:upper:]' '[:lower:]' | \
        sed 's/\b\(the\|is\|are\|where\|what\|when\|how\|a\|an\|and\|or\|of\|to\|in\|for\|on\|at\|by\|with\|from\)\b//g' | \
        tr -cs '[:alnum:]' '\n' | \
        grep -v '^$' | \
        awk 'length($0) >= 3'
}

# Classify error type
classify_error() {
    local error="$1"

    if echo "$error" | grep -qiE "(TypeError|AttributeError|NullReferenceException|Cannot read property|undefined)"; then
        echo "type_error"
    elif echo "$error" | grep -qiE "(Test failed|Assertion|Expected .* but got)"; then
        echo "test_failure"
    elif echo "$error" | grep -qiE "(SyntaxError|ImportError|Module not found|cannot find module)"; then
        echo "build_error"
    elif echo "$error" | grep -qiE "(500|Database error|Connection refused|ECONNREFUSED)"; then
        echo "runtime_error"
    else
        echo "unknown"
    fi
}

# Search specs for related requirements
search_specs() {
    local keywords="$1"
    local specs_dir="$REPO_ROOT/specs"

    if [ ! -d "$specs_dir" ]; then
        echo "[]"
        return
    fi

    declare -A relevance_scores
    declare -A requirement_lines
    declare -A requirement_texts

    # Search through all spec files
    while IFS= read -r spec_file; do
        if [ ! -f "$spec_file" ]; then
            continue
        fi

        local feature_name=$(basename "$(dirname "$spec_file")")

        # Search for requirements with keywords
        while IFS= read -r keyword; do
            if [ -z "$keyword" ]; then
                continue
            fi

            # Search in spec.md
            if grep -qiE "\b$keyword\b" "$spec_file" 2>/dev/null; then
                # Find requirement sections containing keyword
                local line_num=0
                local current_req=""
                local current_req_text=""

                while IFS= read -r line; do
                    line_num=$((line_num + 1))

                    # Detect requirement ID
                    if echo "$line" | grep -qE "^(REQ-[0-9]+|#### REQ-[0-9]+)"; then
                        current_req=$(echo "$line" | grep -oE "REQ-[0-9]+")
                        current_req_text="$line"
                    fi

                    # If we have a current requirement and line matches keyword
                    if [ -n "$current_req" ] && echo "$line" | grep -qiE "\b$keyword\b"; then
                        local key="$feature_name:$current_req"

                        # Calculate relevance score
                        local score=${relevance_scores[$key]:-0}
                        score=$((score + 40))  # Keyword match

                        # File proximity bonus
                        if [ -n "$ERROR_FILE" ]; then
                            if echo "$current_req_text" | grep -qF "$(basename "$ERROR_FILE")"; then
                                score=$((score + 30))
                            fi
                        fi

                        relevance_scores[$key]=$score
                        requirement_lines[$key]="$spec_file:$line_num"

                        # Extract requirement text
                        if [ -z "${requirement_texts[$key]}" ]; then
                            local req_text=$(echo "$current_req_text" | sed 's/^#### //' | sed 's/^REQ-[0-9]*: *//')
                            requirement_texts[$key]="$req_text"
                        fi
                    fi
                done < "$spec_file"
            fi
        done <<< "$keywords"
    done < <(find "$specs_dir" -name "spec.md" -type f 2>/dev/null)

    # Build JSON array of results, sorted by relevance
    local results="["
    local first=true

    for key in "${!relevance_scores[@]}"; do
        local feature="${key%%:*}"
        local req="${key##*:}"
        local score="${relevance_scores[$key]}"
        local line="${requirement_lines[$key]}"
        local text="${requirement_texts[$key]}"

        if [ "$first" = true ]; then
            first=false
        else
            results="$results,"
        fi

        results="$results{\"feature\":\"$feature\",\"requirement\":\"$req\",\"text\":\"$text\",\"file\":\"$line\",\"relevance\":$score}"
    done

    results="$results]"

    # Sort by relevance (simple approach - just output unsorted for now)
    echo "$results"
}

# Generate possible causes based on error type
generate_causes() {
    local error_type="$1"
    local error_msg="$2"

    case "$error_type" in
        type_error)
            echo '["Object not initialized before property access","Async operation not awaited","Null/undefined returned from function or database","Missing null/undefined check"]'
            ;;
        test_failure)
            echo '["Expected behavior not matching specification","Missing edge case handling","Incorrect test assertion","Implementation incomplete"]'
            ;;
        build_error)
            echo '["Missing dependency in package.json/requirements.txt","Incorrect import path","Module not installed","Syntax error in recent changes"]'
            ;;
        runtime_error)
            echo '["External service not running","Incorrect configuration","Network connectivity issue","Database connection problem"]'
            ;;
        *)
            echo '["Unknown error type - manual analysis required"]'
            ;;
    esac
}

# Generate suggestions based on error analysis
generate_suggestions() {
    local error_type="$1"
    local related_specs="$2"

    local suggestions="["

    # Add spec-based suggestions
    local spec_count=$(echo "$related_specs" | jq '. | length' 2>/dev/null || echo "0")

    if [ "$spec_count" -gt 0 ]; then
        local top_spec=$(echo "$related_specs" | jq -r '.[0]' 2>/dev/null)
        if [ -n "$top_spec" ] && [ "$top_spec" != "null" ]; then
            local feature=$(echo "$top_spec" | jq -r '.feature' 2>/dev/null)
            local req=$(echo "$top_spec" | jq -r '.requirement' 2>/dev/null)
            local file=$(echo "$top_spec" | jq -r '.file' 2>/dev/null)

            suggestions="$suggestions\"Check requirement $req in specs/$feature/spec.md\""

            if [ "$error_type" = "type_error" ]; then
                suggestions="$suggestions,\"Verify null handling requirements in $req\""
            fi
        fi
    fi

    # Add generic suggestions based on error type
    case "$error_type" in
        type_error)
            suggestions="$suggestions,\"Add null/undefined checks before property access\""
            suggestions="$suggestions,\"Ensure objects are properly initialized\""
            ;;
        test_failure)
            suggestions="$suggestions,\"Review acceptance criteria in specification\""
            suggestions="$suggestions,\"Check edge cases documented in spec\""
            ;;
        build_error)
            suggestions="$suggestions,\"Check technology stack in plan.md\""
            suggestions="$suggestions,\"Verify dependencies are installed\""
            ;;
        runtime_error)
            suggestions="$suggestions,\"Check non-functional requirements for error handling\""
            suggestions="$suggestions,\"Verify external service configuration\""
            ;;
    esac

    suggestions="$suggestions]"
    echo "$suggestions"
}

# Main analysis
ERROR_TYPE=$(classify_error "$ERROR_MESSAGE")
KEYWORDS=$(extract_keywords "$ERROR_MESSAGE")

# Search for related specs
RELATED_SPECS=$(search_specs "$KEYWORDS")

# Generate possible causes and suggestions
POSSIBLE_CAUSES=$(generate_causes "$ERROR_TYPE" "$ERROR_MESSAGE")
SUGGESTIONS=$(generate_suggestions "$ERROR_TYPE" "$RELATED_SPECS")

# Find related files in codebase
RELATED_FILES="[]"
if [ -n "$KEYWORDS" ]; then
    # Search for files containing error keywords
    files_json="["
    first=true

    while IFS= read -r keyword; do
        if [ -z "$keyword" ]; then
            continue
        fi

        # Search source files (limit to first 3 matches per keyword)
        while IFS=: read -r file line context; do
            if [ -n "$file" ] && [ -f "$file" ]; then
                # Skip spec files
                if echo "$file" | grep -q "specs/"; then
                    continue
                fi

                if [ "$first" = true ]; then
                    first=false
                else
                    files_json="$files_json,"
                fi

                rel_path="${file#$REPO_ROOT/}"
                clean_context=$(echo "$context" | sed 's/"/\\"/g' | head -c 60)
                files_json="$files_json{\"file\":\"$rel_path\",\"line\":$line,\"context\":\"$clean_context\"}"

                break  # Only first match per keyword
            fi
        done < <(grep -rn --include="*.py" --include="*.js" --include="*.ts" --include="*.tsx" -i "\b$keyword\b" "$REPO_ROOT" 2>/dev/null | head -n 1)
    done <<< "$KEYWORDS"

    files_json="$files_json]"
    RELATED_FILES="$files_json"
fi

# Output results
if [ "$JSON_MODE" = true ]; then
    cat <<EOF
{
  "error": "$ERROR_MESSAGE",
  "error_type": "$ERROR_TYPE",
  "location": {
    "file": "$ERROR_FILE",
    "line": "$ERROR_LINE"
  },
  "related_specs": $RELATED_SPECS,
  "related_files": $RELATED_FILES,
  "possible_causes": $POSSIBLE_CAUSES,
  "suggestions": $SUGGESTIONS
}
EOF
else
    echo "Error Analysis"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "🔴 Error: $ERROR_MESSAGE"

    if [ -n "$ERROR_FILE" ]; then
        echo ""
        echo "📍 Location: $ERROR_FILE$([ -n "$ERROR_LINE" ] && echo ":$ERROR_LINE")"
    fi

    # Display related specs
    spec_count=$(echo "$RELATED_SPECS" | jq '. | length' 2>/dev/null || echo "0")

    if [ "$spec_count" -gt 0 ]; then
        echo ""
        echo "📋 Related Requirements ($spec_count found):"
        echo ""

        index=0
        while [ $index -lt $spec_count ] && [ $index -lt 3 ]; do
            spec=$(echo "$RELATED_SPECS" | jq -r ".[$index]" 2>/dev/null)
            feature=$(echo "$spec" | jq -r '.feature' 2>/dev/null)
            req=$(echo "$spec" | jq -r '.requirement' 2>/dev/null)
            text=$(echo "$spec" | jq -r '.text' 2>/dev/null)
            file=$(echo "$spec" | jq -r '.file' 2>/dev/null)
            relevance=$(echo "$spec" | jq -r '.relevance' 2>/dev/null)

            echo "  $((index + 1)). $req in $feature (relevance: $relevance%)"
            echo "     \"$text\""
            echo "     → $file"
            echo ""

            index=$((index + 1))
        done
    else
        echo ""
        echo "📋 Related Requirements: None found in specifications"
        echo ""
        echo "This may indicate:"
        echo "  • Infrastructure/environment issue (not spec-related)"
        echo "  • Missing specification coverage"
        echo "  • Error in external dependency"
    fi

    # Display possible causes
    echo ""
    echo "🔍 Possible Causes:"
    echo ""
    cause_count=$(echo "$POSSIBLE_CAUSES" | jq '. | length' 2>/dev/null || echo "0")
    cause_index=0
    while [ $cause_index -lt $cause_count ]; do
        cause=$(echo "$POSSIBLE_CAUSES" | jq -r ".[$cause_index]" 2>/dev/null)
        echo "  • $cause"
        cause_index=$((cause_index + 1))
    done

    # Display suggestions
    echo ""
    echo "💡 Suggestions:"
    echo ""
    sugg_count=$(echo "$SUGGESTIONS" | jq '. | length' 2>/dev/null || echo "0")
    sugg_index=0
    while [ $sugg_index -lt $sugg_count ] && [ $sugg_index -lt 5 ]; do
        suggestion=$(echo "$SUGGESTIONS" | jq -r ".[$sugg_index]" 2>/dev/null)
        echo "  $((sugg_index + 1)). $suggestion"
        sugg_index=$((sugg_index + 1))
    done

    echo ""
fi
