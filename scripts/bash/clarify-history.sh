#!/usr/bin/env bash

set -e

# Source common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

JSON_MODE=false
SEARCH_QUERY=""
VERIFY_MODE=false
FEATURE_NAME=""

# Parse arguments
while [ $# -gt 0 ]; do
    case "$1" in
        --json)
            JSON_MODE=true
            shift
            ;;
        search)
            SEARCH_QUERY="$2"
            shift 2
            ;;
        verify)
            VERIFY_MODE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [--json] [search QUERY] [verify] [FEATURE]"
            echo ""
            echo "View clarification history for a feature specification."
            echo ""
            echo "Options:"
            echo "  --json       Output in JSON format"
            echo "  search QUERY Search for specific keywords in Q&A"
            echo "  verify       Check that all clarifications are integrated"
            echo "  FEATURE      Feature name or number (default: current)"
            echo ""
            echo "Examples:"
            echo "  $0                          # Current feature history"
            echo "  $0 001-task-management      # Specific feature"
            echo "  $0 search \"authentication\"  # Search Q&A"
            echo "  $0 verify                   # Verify integration"
            exit 0
            ;;
        *)
            FEATURE_NAME="$1"
            shift
            ;;
    esac
done

# Get repository root
REPO_ROOT=$(get_repo_root)

# Determine feature
if [ -z "$FEATURE_NAME" ]; then
    # Use current branch
    CURRENT_BRANCH=$(get_current_branch 2>/dev/null || echo "")
    FEATURE_DIR=$(find_feature_dir_by_prefix "$REPO_ROOT" "$CURRENT_BRANCH" 2>/dev/null || echo "")

    if [ -z "$FEATURE_DIR" ]; then
        echo "Error: Could not determine current feature. Provide feature name as argument." >&2
        exit 1
    fi

    FEATURE_NAME=$(basename "$FEATURE_DIR")
else
    # Find feature by name/number
    FEATURE_DIR=$(find_feature_dir "$REPO_ROOT" "$FEATURE_NAME" 2>/dev/null || echo "")

    if [ -z "$FEATURE_DIR" ]; then
        echo "Error: Feature not found: $FEATURE_NAME" >&2
        exit 1
    fi

    FEATURE_NAME=$(basename "$FEATURE_DIR")
fi

SPEC_FILE="$FEATURE_DIR/spec.md"

if [ ! -f "$SPEC_FILE" ]; then
    echo "Error: Spec file not found: $SPEC_FILE" >&2
    exit 1
fi

# Parse clarifications from spec
parse_clarifications() {
    local spec_file="$1"
    local in_clarifications=false
    local current_session=""
    local session_count=0
    local total_questions=0

    declare -A sessions
    declare -A session_questions

    while IFS= read -r line; do
        # Detect clarifications section start
        if echo "$line" | grep -q "^## Clarifications"; then
            in_clarifications=true
            continue
        fi

        # Exit clarifications section on next ## heading
        if [ "$in_clarifications" = true ] && echo "$line" | grep -q "^## [^#]"; then
            in_clarifications=false
            break
        fi

        # Parse session date
        if [ "$in_clarifications" = true ] && echo "$line" | grep -qE "^### Session [0-9]{4}-[0-9]{2}-[0-9]{2}"; then
            current_session=$(echo "$line" | grep -oE "[0-9]{4}-[0-9]{2}-[0-9]{2}")
            session_count=$((session_count + 1))
            sessions["$current_session"]=""
            session_questions["$current_session"]=0
            continue
        fi

        # Parse Q&A pairs
        if [ "$in_clarifications" = true ] && [ -n "$current_session" ]; then
            if echo "$line" | grep -qE "^[[:space:]]*-[[:space:]]*Q:"; then
                # Extract question and answer
                local qa=$(echo "$line" | sed 's/^[[:space:]]*-[[:space:]]*//')
                local question=$(echo "$qa" | sed 's/ → A:.*//' | sed 's/^Q: //')
                local answer=$(echo "$qa" | sed 's/.*→ A: //')

                # Filter by search query if provided
                if [ -n "$SEARCH_QUERY" ]; then
                    if ! echo "$qa" | grep -qi "$SEARCH_QUERY"; then
                        continue
                    fi
                fi

                # Append to session data
                if [ -z "${sessions[$current_session]}" ]; then
                    sessions["$current_session"]="$question|$answer"
                else
                    sessions["$current_session"]="${sessions[$current_session]}:SEP:$question|$answer"
                fi

                local count=${session_questions[$current_session]}
                session_questions["$current_session"]=$((count + 1))
                total_questions=$((total_questions + 1))
            fi
        fi
    done < "$spec_file"

    # Output results
    if [ "$JSON_MODE" = true ]; then
        echo "{"
        echo "  \"feature\": \"$FEATURE_NAME\","
        echo "  \"spec_file\": \"$SPEC_FILE\","
        echo "  \"total_sessions\": $session_count,"
        echo "  \"total_questions\": $total_questions,"
        echo "  \"sessions\": ["

        local first_session=true
        for session in $(echo "${!sessions[@]}" | tr ' ' '\n' | sort); do
            if [ "$first_session" = false ]; then
                echo ","
            fi
            first_session=false

            local qa_data="${sessions[$session]}"
            local question_count=${session_questions[$session]}

            echo "    {"
            echo "      \"date\": \"$session\","
            echo "      \"questions\": $question_count,"
            echo "      \"qa_pairs\": ["

            if [ -n "$qa_data" ]; then
                local first_qa=true
                IFS=':SEP:' read -ra QA_ARRAY <<< "$qa_data"
                for qa in "${QA_ARRAY[@]}"; do
                    if [ "$first_qa" = false ]; then
                        echo ","
                    fi
                    first_qa=false

                    IFS='|' read -r q a <<< "$qa"
                    # Escape quotes for JSON
                    q=$(echo "$q" | sed 's/"/\\"/g')
                    a=$(echo "$a" | sed 's/"/\\"/g')

                    echo "        {"
                    echo "          \"question\": \"$q\","
                    echo "          \"answer\": \"$a\""
                    echo -n "        }"
                done
            fi

            echo ""
            echo "      ]"
            echo -n "    }"
        done

        echo ""
        echo "  ]"
        echo "}"
    else
        # Text mode output
        echo "Clarification History: $FEATURE_NAME"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""

        if [ $session_count -eq 0 ]; then
            echo "No clarification sessions found."
            echo ""
            echo "The spec.md file does not contain a ## Clarifications section."
            echo ""
            echo "Recommendation: Run /speckit.clarify to identify ambiguities"
            return
        fi

        echo "📊 Summary:"
        echo "  Total Sessions: $session_count"
        echo "  Total Questions: $total_questions"
        echo "  Spec File: $SPEC_FILE"
        echo ""

        if [ -n "$SEARCH_QUERY" ]; then
            echo "🔍 Search Results for: \"$SEARCH_QUERY\""
            echo ""
        fi

        # Display each session
        for session in $(echo "${!sessions[@]}" | tr ' ' '\n' | sort); do
            local qa_data="${sessions[$session]}"
            local question_count=${session_questions[$session]}

            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo ""
            echo "Session $session ($question_count questions)"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo ""

            if [ -n "$qa_data" ]; then
                local qa_index=1
                IFS=':SEP:' read -ra QA_ARRAY <<< "$qa_data"
                for qa in "${QA_ARRAY[@]}"; do
                    IFS='|' read -r q a <<< "$qa"
                    echo "Q$qa_index: $q"
                    echo "→  $a"
                    echo ""
                    qa_index=$((qa_index + 1))
                done
            fi
        done

        if [ -z "$SEARCH_QUERY" ] && [ $total_questions -gt 0 ]; then
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo ""
            echo "✓ All clarifications recorded"
            echo ""
            echo "Next steps:"
            echo "  • Review history: /speckit.clarify-history search \"keyword\""
            echo "  • Continue to planning: /speckit.plan"
        fi
    fi
}

# Verify integration (if requested)
if [ "$VERIFY_MODE" = true ]; then
    echo "Verification not yet implemented" >&2
    exit 1
fi

# Main execution
parse_clarifications "$SPEC_FILE"
