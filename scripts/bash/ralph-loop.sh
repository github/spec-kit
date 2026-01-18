#!/usr/bin/env bash
#
# ralph-loop.sh - Ralph loop orchestrator for autonomous implementation
#
# Executes GitHub Copilot CLI in a controlled loop, processing tasks from tasks.md.
# Each iteration spawns a fresh agent context with the speckit.implement profile.
#
# The loop terminates when:
# - Agent outputs <promise>COMPLETE</promise>
# - Max iterations reached
# - All tasks in tasks.md are complete
# - User interrupts with Ctrl+C
#
# Usage:
#   ./ralph-loop.sh --feature-name "001-feature" --tasks-path "specs/001-feature/tasks.md" \
#                   --spec-dir "specs/001-feature" --max-iterations 10 --model "claude-sonnet-4.5"

set -euo pipefail

#region Configuration

FEATURE_NAME=""
TASKS_PATH=""
SPEC_DIR=""
MAX_ITERATIONS=10
MODEL="claude-sonnet-4.5"
VERBOSE=false
WORKING_DIRECTORY=""

#endregion

#region Parse Arguments

while [[ $# -gt 0 ]]; do
    case $1 in
        --feature-name)
            FEATURE_NAME="$2"
            shift 2
            ;;
        --tasks-path)
            TASKS_PATH="$2"
            shift 2
            ;;
        --spec-dir)
            SPEC_DIR="$2"
            shift 2
            ;;
        --max-iterations)
            MAX_ITERATIONS="$2"
            shift 2
            ;;
        --model)
            MODEL="$2"
            shift 2
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --working-directory)
            WORKING_DIRECTORY="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1" >&2
            exit 1
            ;;
    esac
done

# Validate required arguments
if [[ -z "$FEATURE_NAME" || -z "$TASKS_PATH" || -z "$SPEC_DIR" ]]; then
    echo "Error: Missing required arguments" >&2
    echo "Usage: $0 --feature-name NAME --tasks-path PATH --spec-dir DIR [--max-iterations N] [--model MODEL] [--verbose]" >&2
    exit 1
fi

#endregion

#region Resolve Paths

REPO_ROOT="$(pwd)"
TASKS_PATH="$(realpath "$TASKS_PATH")"
SPEC_DIR="$(realpath "$SPEC_DIR")"
PROGRESS_PATH="$SPEC_DIR/progress.md"

# Paths for spec files
SPEC_PATH="$SPEC_DIR/spec.md"
PLAN_PATH="$SPEC_DIR/plan.md"

# Use working directory if not specified
if [[ -z "$WORKING_DIRECTORY" ]]; then
    WORKING_DIRECTORY="$REPO_ROOT"
fi

#endregion

#region Helper Functions

print_header() {
    local iteration=$1
    local max=$2
    local border
    border=$(printf '=%.0s' {1..60})
    
    echo ""
    echo -e "\033[36m$border\033[0m"
    echo -e "\033[36m  Ralph Loop - $FEATURE_NAME\033[0m"
    echo -e "\033[37m  Iteration $iteration of $max\033[0m"
    echo -e "\033[36m$border\033[0m"
    echo ""
}

print_status() {
    local iteration=$1
    local status=$2
    local message=$3
    local timestamp
    timestamp=$(date +"%H:%M:%S")
    
    local icon color
    case "$status" in
        running)  icon="o"; color="\033[36m" ;;
        success)  icon="*"; color="\033[32m" ;;
        failure)  icon="x"; color="\033[31m" ;;
        skipped)  icon="-"; color="\033[33m" ;;
        *)        icon="o"; color="\033[37m" ;;
    esac
    
    echo -ne "\033[90m[$timestamp] \033[0m"
    echo -ne "${color}${icon}\033[0m"
    echo -ne " \033[37mIteration $iteration\033[0m"
    if [[ -n "$message" ]]; then
        echo -e " \033[90m- $message\033[0m"
    else
        echo ""
    fi
}

get_incomplete_task_count() {
    local path=$1
    if [[ ! -f "$path" ]]; then
        echo 0
        return
    fi
    grep -c '\- \[ \]' "$path" 2>/dev/null || echo 0
}

initialize_progress_file() {
    local path=$1
    local feature=$2
    
    if [[ ! -f "$path" ]]; then
        local timestamp
        timestamp=$(date +"%Y-%m-%d %H:%M:%S")
        cat > "$path" << EOF
# Ralph Progress Log

Feature: $feature
Started: $timestamp

## Codebase Patterns

[Patterns discovered during implementation - updated by agent]

---

EOF
        echo -e "\033[90mCreated progress log: $path\033[0m"
    fi
}

invoke_copilot_iteration() {
    local model=$1
    local iteration=$2
    local work_dir=$3
    
    # Simple prompt - the speckit.ralph agent already knows to complete one work unit
    local prompt="Iteration $iteration - Complete one work unit from tasks.md"
    
    # Only show debug info when verbose
    if [[ "$VERBOSE" == "true" ]]; then
        echo -e "\033[35mDEBUG: Prompt = $prompt\033[0m" >&2
        echo -e "\033[35mDEBUG: WorkDir = $work_dir\033[0m" >&2
    fi
    
    # Change to working directory if specified
    local original_dir
    original_dir=$(pwd)
    if [[ -n "$work_dir" && -d "$work_dir" ]]; then
        cd "$work_dir"
        if [[ "$VERBOSE" == "true" ]]; then
            echo -e "\033[35mDEBUG: Changed to $work_dir\033[0m" >&2
        fi
    fi
    
    # Always stream copilot output in real-time so user can see what the agent is doing
    echo "" >&2
    echo -e "\033[36m--- Copilot Agent Output ---\033[0m" >&2
    
    local exit_code=0
    local output_lines=()
    
    # Stream output line by line - use speckit.ralph agent (it already knows to complete one work unit)
    while IFS= read -r line; do
        echo "$line" >&2
        output_lines+=("$line")
    done < <(copilot --agent speckit.ralph -p "$prompt" --model "$model" --allow-all-tools -s 2>&1) || exit_code=$?
    
    echo -e "\033[36m--- End Agent Output ---\033[0m" >&2
    echo "" >&2
    
    # Restore original directory
    if [[ -n "$work_dir" && -d "$work_dir" ]]; then
        cd "$original_dir"
    fi
    
    if [[ "$VERBOSE" == "true" ]]; then
        echo -e "\033[35mDEBUG: copilot exit code = $exit_code\033[0m" >&2
    fi
    
    # Join output lines for return
    local output
    output=$(printf '%s\n' "${output_lines[@]}")
    
    # Return output via stdout, exit code via return
    echo "$output"
    return $exit_code
}

test_completion_signal() {
    local output=$1
    echo "$output" | grep -q '<promise>COMPLETE</promise>'
}
#endregion

#region Signal Handling

INTERRUPTED=false

cleanup() {
    INTERRUPTED=true
    echo ""
    echo -e "\033[33mInterrupted by user\033[0m"
}

trap cleanup SIGINT SIGTERM

#endregion

#region Main Loop

# Initialize progress file
initialize_progress_file "$PROGRESS_PATH" "$FEATURE_NAME"

# Check initial task count
INITIAL_TASKS=$(get_incomplete_task_count "$TASKS_PATH")
if [[ "$INITIAL_TASKS" -eq 0 ]]; then
    echo -e "\033[32mAll tasks are already complete!\033[0m"
    echo "<promise>COMPLETE</promise>"
    exit 0
fi

echo -e "\033[37mFound $INITIAL_TASKS incomplete task(s)\033[0m"

# Iteration tracking
iteration=1
consecutive_failures=0
max_consecutive_failures=3
completed=false

while [[ $iteration -le $MAX_ITERATIONS && "$completed" == "false" && "$INTERRUPTED" == "false" ]]; do
    print_header "$iteration" "$MAX_ITERATIONS"
    print_status "$iteration" "running" "Starting iteration"
    
    # Invoke Copilot CLI with speckit.ralph agent (agent already knows to complete one work unit)
    set +e
    output=$(invoke_copilot_iteration \
        "$MODEL" \
        "$iteration" \
        "$WORKING_DIRECTORY")
    exit_code=$?
    set -e
    
    # Check for completion signal
    if test_completion_signal "$output"; then
        print_status "$iteration" "success" "COMPLETE signal received"
        completed=true
        break
    fi
    
    # Check exit code
    if [[ $exit_code -ne 0 ]]; then
        ((consecutive_failures++))
        print_status "$iteration" "failure" "Exit code $exit_code (failure $consecutive_failures/$max_consecutive_failures)"
        
        if [[ $consecutive_failures -ge $max_consecutive_failures ]]; then
            echo -e "\033[31mToo many consecutive failures. Stopping loop.\033[0m"
            exit 1
        fi
    else
        consecutive_failures=0
        print_status "$iteration" "success" "Iteration completed"
    fi
    
    # Check remaining tasks
    remaining_tasks=$(get_incomplete_task_count "$TASKS_PATH")
    if [[ "$remaining_tasks" -eq 0 ]]; then
        echo -e "\033[32mAll tasks complete!\033[0m"
        completed=true
        break
    fi
    
    echo -e "\033[90m$remaining_tasks task(s) remaining\033[0m"
    
    ((iteration++))
done

#endregion

#region Summary

border=$(printf '=%.0s' {1..60})
echo ""
echo -e "\033[36m$border\033[0m"
echo -e "\033[36m  Ralph Loop Summary\033[0m"
echo -e "\033[36m$border\033[0m"

final_tasks=$(get_incomplete_task_count "$TASKS_PATH")
tasks_completed=$((INITIAL_TASKS - final_tasks))

echo -e "  \033[37mIterations run: $((iteration - 1))\033[0m"
echo -e "  \033[37mTasks completed: $tasks_completed\033[0m"
echo -e "  \033[37mTasks remaining: $final_tasks\033[0m"

if [[ "$completed" == "true" ]]; then
    echo -ne "  \033[37mStatus: \033[0m"
    echo -e "\033[32mCOMPLETED\033[0m"
    exit 0
elif [[ "$INTERRUPTED" == "true" ]]; then
    echo -ne "  \033[37mStatus: \033[0m"
    echo -e "\033[33mINTERRUPTED\033[0m"
    exit 130
else
    echo -ne "  \033[37mStatus: \033[0m"
    echo -e "\033[33mITERATION LIMIT REACHED\033[0m"
    exit 1
fi

#endregion
