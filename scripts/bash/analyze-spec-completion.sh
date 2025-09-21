#!/usr/bin/env bash
# Spec Completion Analyzer - Detailed analysis of spec folder completeness
set -e

JSON_MODE=false
SPEC_PATH=""
ARGS=()

for arg in "$@"; do
    case "$arg" in
        --json) JSON_MODE=true ;;
        --help|-h) 
            echo "Usage: $0 [--json] [spec_path]"
            echo "Analyzes completion status of specs. If spec_path provided, analyzes single spec."
            echo "Otherwise analyzes all specs in specs/ directory."
            exit 0 ;;
        *) 
            if [ -z "$SPEC_PATH" ]; then
                SPEC_PATH="$arg"
            else
                ARGS+=("$arg")
            fi
            ;;
    esac
done

REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
if [ $? -ne 0 ]; then
    echo "ERROR: Not in a git repository. Run this script from within a git repository." >&2
    exit 1
fi

SPECS_DIR="$REPO_ROOT/specs"

# Define required artifacts for a complete spec
REQUIRED_ARTIFACTS=(
    "spec.md"
    "plan.md" 
    "tasks.md"
    "data-model.md"
    "research.md"
    "quickstart.md"
)

# Define optional artifacts
OPTIONAL_ARTIFACTS=(
    "contracts/"
)

# Function to analyze a single spec folder
analyze_spec() {
    local spec_path="$1"
    local spec_name=$(basename "$spec_path")
    
    # Check if directory exists
    if [ ! -d "$spec_path" ]; then
        echo "ERROR: Spec directory not found: $spec_path" >&2
        return 1
    fi
    
    local missing_artifacts=()
    local present_artifacts=()
    local completion_percentage=0
    local task_completion=""
    local total_tasks=0
    local completed_tasks=0
    
    # Check required artifacts
    for artifact in "${REQUIRED_ARTIFACTS[@]}"; do
        if [ -f "$spec_path/$artifact" ]; then
            present_artifacts+=("$artifact")
        else
            missing_artifacts+=("$artifact")
        fi
    done
    
    # Special analysis for tasks.md
    if [ -f "$spec_path/tasks.md" ]; then
        total_tasks=$(grep -E "^- \[\s*\]" "$spec_path/tasks.md" 2>/dev/null | wc -l || echo "0")
        completed_tasks=$(grep -E "^- \[x\]" "$spec_path/tasks.md" 2>/dev/null | wc -l || echo "0")
        
        # Trim whitespace and handle case where wc returns empty string
        total_tasks=$(echo "$total_tasks" | tr -d '[:space:]')
        completed_tasks=$(echo "$completed_tasks" | tr -d '[:space:]')
        
        if [ -z "$total_tasks" ] || [ "$total_tasks" = "" ]; then
            total_tasks=0
        fi
        if [ -z "$completed_tasks" ] || [ "$completed_tasks" = "" ]; then
            completed_tasks=0
        fi
        
        if [ "$total_tasks" -gt 0 ]; then
            task_completion="$completed_tasks/$total_tasks"
        else
            task_completion="0/0"
        fi
    fi
    
    # Calculate completion percentage
    local total_required=${#REQUIRED_ARTIFACTS[@]}
    local present_count=${#present_artifacts[@]}
    completion_percentage=$((present_count * 100 / total_required))
    
    # Determine completion status
    local status=""
    if [ "$completion_percentage" -eq 100 ]; then
        if [ "$total_tasks" -gt 0 ] && [ "$completed_tasks" -eq "$total_tasks" ]; then
            status="fully_complete"
        elif [ "$total_tasks" -gt 0 ] && [ "$completed_tasks" -gt 0 ]; then
            status="implementation_in_progress"
        else
            status="ready_for_implementation"
        fi
    elif [ "$completion_percentage" -ge 50 ]; then
        status="partially_complete"
    else
        status="incomplete"
    fi
    
    # Check for contracts directory
    local contracts_status="missing"
    if [ -d "$spec_path/contracts" ]; then
        local contract_files=$(find "$spec_path/contracts" -name "*.md" | wc -l)
        if [ "$contract_files" -gt 0 ]; then
            contracts_status="present"
        else
            contracts_status="empty"
        fi
    fi
    
    if $JSON_MODE; then
        printf '{"spec_name":"%s","status":"%s","completion_percentage":%d,"present_artifacts":%s,"missing_artifacts":%s,"task_completion":"%s","contracts_status":"%s","total_tasks":%d,"completed_tasks":%d}\n' \
            "$spec_name" \
            "$status" \
            "$completion_percentage" \
            "$(printf '%s\n' "${present_artifacts[@]}" | jq -R . | jq -s .)" \
            "$(printf '%s\n' "${missing_artifacts[@]}" | jq -R . | jq -s .)" \
            "$task_completion" \
            "$contracts_status" \
            "$total_tasks" \
            "$completed_tasks"
    else
        echo "=== Spec: $spec_name ==="
        echo "Status: $status"
        echo "Completion: $completion_percentage%"
        echo "Task Progress: $task_completion"
        echo "Contracts: $contracts_status"
        if [ ${#present_artifacts[@]} -gt 0 ]; then
            echo "Present: ${present_artifacts[*]}"
        fi
        if [ ${#missing_artifacts[@]} -gt 0 ]; then
            echo "Missing: ${missing_artifacts[*]}"
        fi
        echo ""
    fi
}

# Main execution
if [ -n "$SPEC_PATH" ]; then
    # Analyze single spec
    if [[ "$SPEC_PATH" != /* ]]; then
        # Relative path, make it absolute
        SPEC_PATH="$SPECS_DIR/$SPEC_PATH"
    fi
    analyze_spec "$SPEC_PATH"
else
    # Analyze all specs
    if [ ! -d "$SPECS_DIR" ]; then
        if $JSON_MODE; then
            echo '{"error":"No specs directory found","specs":[]}'
        else
            echo "No specs directory found at: $SPECS_DIR"
        fi
        exit 1
    fi
    
    SPECS_ANALYSIS=()
    
    if $JSON_MODE; then
        echo "{"
        echo '"specs":['
        first=true
        for spec_dir in "$SPECS_DIR"/*; do
            if [ -d "$spec_dir" ]; then
                if [ "$first" = true ]; then
                    first=false
                else
                    echo ","
                fi
                analyze_spec "$spec_dir"
            fi
        done
        echo "],"
        echo '"analysis_date":"'$(date -Iseconds)'"'
        echo "}"
    else
        echo "=== Spec Completion Analysis ==="
        echo "Date: $(date)"
        echo ""
        
        for spec_dir in "$SPECS_DIR"/*; do
            if [ -d "$spec_dir" ]; then
                analyze_spec "$spec_dir"
            fi
        done
    fi
fi