#!/usr/bin/env bash

set -e

# Source common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

JSON_MODE=false
VALIDATE_MODE="current"  # current, spec, plan, tasks, all, constitution

# Parse arguments
while [ $# -gt 0 ]; do
    case "$1" in
        --json)
            JSON_MODE=true
            shift
            ;;
        --current)
            VALIDATE_MODE="current"
            shift
            ;;
        --spec)
            VALIDATE_MODE="spec"
            shift
            ;;
        --plan)
            VALIDATE_MODE="plan"
            shift
            ;;
        --tasks)
            VALIDATE_MODE="tasks"
            shift
            ;;
        --all)
            VALIDATE_MODE="all"
            shift
            ;;
        --constitution)
            VALIDATE_MODE="constitution"
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [--json] [mode]"
            echo ""
            echo "Modes:"
            echo "  --current        Validate current feature (default)"
            echo "  --spec           Validate only spec.md"
            echo "  --plan           Validate only plan.md"
            echo "  --tasks          Validate only tasks.md"
            echo "  --all            Validate all features"
            echo "  --constitution   Validate constitution.md"
            echo ""
            echo "Options:"
            echo "  --json           Output in JSON format"
            exit 0
            ;;
        *)
            shift
            ;;
    esac
done

# Get repository root
REPO_ROOT=$(get_repo_root)
SPECS_DIR="$REPO_ROOT/specs"
CONSTITUTION_FILE="$REPO_ROOT/memory/constitution.md"

# Validate a single file
validate_file() {
    local file_path="$1"
    local file_type="$2"
    local issues=()

    if [ ! -f "$file_path" ]; then
        echo '{"exists": false, "complete": false, "issues": ["File not found"]}'
        return
    fi

    # Check file size
    local size=$(wc -c < "$file_path" 2>/dev/null || echo "0")
    local min_size=100

    case "$file_type" in
        spec)
            min_size=500
            # Check for required sections
            grep -q "## User Scenarios" "$file_path" || issues+=("Missing User Scenarios section")
            grep -q "## Functional Requirements" "$file_path" || issues+=("Missing Functional Requirements section")
            # Check for placeholders
            grep -qi "TODO\|TBD\|FIXME\|XXX" "$file_path" && issues+=("Contains TODO/TBD placeholders")
            ;;
        plan)
            min_size=300
            grep -q "## Technology Stack\|## Tech Stack" "$file_path" || issues+=("Missing Technology Stack section")
            grep -q "## Project Structure" "$file_path" || issues+=("Missing Project Structure section")
            ;;
        tasks)
            min_size=200
            local task_count=$(grep -c "^-\|^[0-9]" "$file_path" 2>/dev/null || echo "0")
            [ "$task_count" -lt 5 ] && issues+=("Only $task_count tasks found (minimum 5 recommended)")
            ;;
        constitution)
            min_size=300
            grep -q "## Principles\|# Principles" "$file_path" || issues+=("Missing Principles section")
            ;;
    esac

    if [ "$size" -lt "$min_size" ]; then
        issues+=("File too short ($size bytes, minimum $min_size)")
    fi

    local complete="true"
    [ ${#issues[@]} -gt 0 ] && complete="false"

    # Format issues for JSON
    local issues_json="[]"
    if [ ${#issues[@]} -gt 0 ]; then
        issues_json="["
        for i in "${!issues[@]}"; do
            issues_json+="\"${issues[$i]}\""
            [ $i -lt $((${#issues[@]} - 1)) ] && issues_json+=","
        done
        issues_json+="]"
    fi

    echo "{\"exists\": true, \"complete\": $complete, \"issues\": $issues_json}"
}

# Validate single feature
validate_feature() {
    local feature_dir="$1"
    local feature_name=$(basename "$feature_dir")

    local spec_result=$(validate_file "$feature_dir/spec.md" "spec")
    local plan_result=$(validate_file "$feature_dir/plan.md" "plan")
    local tasks_result=$(validate_file "$feature_dir/tasks.md" "tasks")

    # Determine overall status
    local status="success"
    echo "$spec_result" | grep -q '"complete": false' && status="error"
    echo "$plan_result" | grep -q '"complete": false' && status="warning"
    echo "$tasks_result" | grep -q '"complete": false' && status="warning"

    echo "{\"feature\": \"$feature_name\", \"validations\": {\"spec\": $spec_result, \"plan\": $plan_result, \"tasks\": $tasks_result}, \"status\": \"$status\"}"
}

# Main validation logic
if [ "$VALIDATE_MODE" = "constitution" ]; then
    # Validate constitution only
    result=$(validate_file "$CONSTITUTION_FILE" "constitution")
    if [ "$JSON_MODE" = true ]; then
        echo "{\"constitution\": $result}"
    else
        exists=$(echo "$result" | grep -o '"exists": [^,}]*' | cut -d' ' -f2)
        complete=$(echo "$result" | grep -o '"complete": [^,}]*' | cut -d' ' -f2)
        if [ "$exists" = "false" ]; then
            echo "✗ Constitution: Not found"
            echo "  Run: /speckit.constitution"
        elif [ "$complete" = "false" ]; then
            echo "⚠ Constitution: Incomplete"
            issues=$(echo "$result" | grep -o '"issues": \[[^]]*\]' | sed 's/"issues": //')
            echo "  Issues: $issues"
        else
            echo "✓ Constitution: Complete"
        fi
    fi
    exit 0
fi

if [ "$VALIDATE_MODE" = "all" ]; then
    # Validate all features
    if [ ! -d "$SPECS_DIR" ]; then
        echo "ERROR: Specs directory not found" >&2
        exit 1
    fi

    feature_results=()
    while IFS= read -r feature_dir; do
        result=$(validate_feature "$feature_dir")
        feature_results+=("$result")
    done < <(find "$SPECS_DIR" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | sort)

    if [ "$JSON_MODE" = true ]; then
        echo -n '{"features": ['
        for i in "${!feature_results[@]}"; do
            echo -n "${feature_results[$i]}"
            [ $i -lt $((${#feature_results[@]} - 1)) ] && echo -n ","
        done
        echo ']}'
    else
        echo "Project Validation Summary"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "Total features: ${#feature_results[@]}"
        echo ""
        for result in "${feature_results[@]}"; do
            feature=$(echo "$result" | grep -o '"feature": "[^"]*"' | cut -d'"' -f4)
            status=$(echo "$result" | grep -o '"status": "[^"]*"' | cut -d'"' -f4)
            case "$status" in
                success) echo "✓ $feature: Complete" ;;
                warning) echo "⚠ $feature: Warnings" ;;
                error) echo "✗ $feature: Errors" ;;
            esac
        done
    fi
    exit 0
fi

# Validate current feature
CURRENT_BRANCH=$(get_current_branch)
FEATURE_DIR=$(find_feature_dir_by_prefix "$REPO_ROOT" "$CURRENT_BRANCH")

if [ ! -d "$FEATURE_DIR" ]; then
    echo "ERROR: Not in a feature branch or feature directory not found" >&2
    exit 1
fi

result=$(validate_feature "$FEATURE_DIR")

if [ "$JSON_MODE" = true ]; then
    echo "$result"
else
    feature=$(echo "$result" | grep -o '"feature": "[^"]*"' | cut -d'"' -f4)
    echo "Validation: $feature"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    # Parse and display results
    spec_complete=$(echo "$result" | grep -o '"spec": {[^}]*}' | grep -o '"complete": [^,}]*' | cut -d' ' -f2)
    plan_complete=$(echo "$result" | grep -o '"plan": {[^}]*}' | grep -o '"complete": [^,}]*' | cut -d' ' -f2)
    tasks_complete=$(echo "$result" | grep -o '"tasks": {[^}]*}' | grep -o '"complete": [^,}]*' | cut -d' ' -f2)

    [ "$spec_complete" = "true" ] && echo "✓ spec.md: Complete" || echo "✗ spec.md: Issues found"
    [ "$plan_complete" = "true" ] && echo "✓ plan.md: Complete" || echo "⚠ plan.md: Issues found"
    [ "$tasks_complete" = "true" ] && echo "✓ tasks.md: Complete" || echo "⚠ tasks.md: Issues found"

    echo ""
    status=$(echo "$result" | grep -o '"status": "[^"]*"' | cut -d'"' -f4)
    case "$status" in
        success) echo "Status: ✓ Excellent" ;;
        warning) echo "Status: ⚠️  Warning" ;;
        error) echo "Status: ✗ Errors found" ;;
    esac
fi
