#!/usr/bin/env bash

# Common utility functions for Spec-Kit Bash scripts
# Provides cross-platform compatibility for Linux/macOS

set -euo pipefail

# ============================================================================
# Color Constants
# ============================================================================

readonly COLOR_RESET='\033[0m'
readonly COLOR_RED='\033[0;31m'
readonly COLOR_GREEN='\033[0;32m'
readonly COLOR_YELLOW='\033[0;33m'
readonly COLOR_BLUE='\033[0;34m'
readonly COLOR_CYAN='\033[0;36m'
readonly COLOR_GRAY='\033[0;90m'
readonly COLOR_WHITE='\033[1;37m'

# ============================================================================
# Output Functions
# ============================================================================

write_header() {
    local message="$1"
    echo -e "${COLOR_CYAN}${message}${COLOR_RESET}"
}

write_step_header() {
    local message="$1"
    echo ""
    echo -e "${COLOR_CYAN}${message}${COLOR_RESET}"
}

write_success() {
    local message="$1"
    echo -e "${COLOR_GREEN}  ✓ ${message}${COLOR_RESET}"
}

write_info() {
    local message="$1"
    echo -e "${COLOR_GRAY}  ${message}${COLOR_RESET}"
}

write_warning() {
    local message="$1"
    echo -e "${COLOR_YELLOW}  ⚠ ${message}${COLOR_RESET}"
}

write_error() {
    local message="$1"
    echo -e "${COLOR_RED}  ✗ ${message}${COLOR_RESET}"
}

write_progress() {
    local message="$1"
    echo -e "${COLOR_WHITE}${message}${COLOR_RESET}"
}

# ============================================================================
# JSON Functions
# ============================================================================

check_jq() {
    if ! command -v jq &> /dev/null; then
        write_error "jq is required but not installed."
        echo "Install jq:"
        echo "  - macOS: brew install jq"
        echo "  - Ubuntu/Debian: sudo apt-get install jq"
        echo "  - RHEL/CentOS: sudo yum install jq"
        exit 1
    fi
}

json_escape() {
    local string="$1"
    # Escape quotes and backslashes for JSON
    echo "$string" | sed 's/\\/\\\\/g; s/"/\\"/g'
}

# ============================================================================
# File System Functions
# ============================================================================

ensure_dir() {
    local dir="$1"
    if [[ ! -d "$dir" ]]; then
        mkdir -p "$dir"
    fi
}

file_exists() {
    local file="$1"
    [[ -f "$file" ]]
}

dir_exists() {
    local dir="$1"
    [[ -d "$dir" ]]
}

get_file_size() {
    local file="$1"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        stat -f%z "$file" 2>/dev/null || echo "0"
    else
        # Linux
        stat -c%s "$file" 2>/dev/null || echo "0"
    fi
}

get_file_mtime() {
    local file="$1"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        stat -f%m "$file" 2>/dev/null || echo "0"
    else
        # Linux
        stat -c%Y "$file" 2>/dev/null || echo "0"
    fi
}

get_file_hash() {
    local file="$1"
    if command -v md5sum &> /dev/null; then
        md5sum "$file" | awk '{print $1}'
    elif command -v md5 &> /dev/null; then
        # macOS
        md5 -q "$file"
    else
        # Fallback: use file size and mtime
        echo "$(get_file_size "$file")-$(get_file_mtime "$file")"
    fi
}

count_files() {
    local dir="$1"
    find "$dir" -type f 2>/dev/null | wc -l | tr -d ' '
}

get_dir_size() {
    local dir="$1"
    du -sb "$dir" 2>/dev/null | cut -f1 || echo "0"
}

# ============================================================================
# String Functions
# ============================================================================

trim() {
    local string="$1"
    # Remove leading/trailing whitespace
    echo "$string" | sed 's/^[[:space:]]*//; s/[[:space:]]*$//'
}

to_lowercase() {
    local string="$1"
    echo "$string" | tr '[:upper:]' '[:lower:]'
}

to_uppercase() {
    local string="$1"
    echo "$string" | tr '[:lower:]' '[:upper:]'
}

# ============================================================================
# Date/Time Functions
# ============================================================================

get_iso_timestamp() {
    date -u +"%Y-%m-%dT%H:%M:%SZ"
}

get_timestamp() {
    date +"%Y-%m-%d %H:%M:%S"
}

# ============================================================================
# Validation Functions
# ============================================================================

is_git_repo() {
    local dir="${1:-.}"
    git -C "$dir" rev-parse --is-inside-work-tree &>/dev/null
}

get_repo_root() {
    local dir="${1:-.}"
    git -C "$dir" rev-parse --show-toplevel 2>/dev/null || echo ""
}

validate_json_file() {
    local file="$1"
    if ! file_exists "$file"; then
        return 1
    fi
    jq empty "$file" 2>/dev/null
}

# ============================================================================
# Path Functions
# ============================================================================

get_absolute_path() {
    local path="$1"
    if [[ "$path" = /* ]]; then
        echo "$path"
    else
        echo "$(pwd)/$path"
    fi
}

get_relative_path() {
    local from="$1"
    local to="$2"
    python3 -c "import os; print(os.path.relpath('$to', '$from'))" 2>/dev/null || echo "$to"
}

# ============================================================================
# Array Functions (Bash 4+ compatible)
# ============================================================================

array_contains() {
    local search="$1"
    shift
    local item
    for item in "$@"; do
        if [[ "$item" == "$search" ]]; then
            return 0
        fi
    done
    return 1
}

array_join() {
    local delimiter="$1"
    shift
    local first="$1"
    shift
    printf "%s" "$first" "${@/#/$delimiter}"
}

# ============================================================================
# JSON Builder Functions
# ============================================================================

json_object_start() {
    echo "{"
}

json_object_end() {
    local last="${1:-false}"
    if [[ "$last" == "true" ]]; then
        echo "}"
    else
        echo "},"
    fi
}

json_array_start() {
    echo "["
}

json_array_end() {
    local last="${1:-false}"
    if [[ "$last" == "true" ]]; then
        echo "]"
    else
        echo "],"
    fi
}

json_field() {
    local key="$1"
    local value="$2"
    local last="${3:-false}"

    local comma=","
    if [[ "$last" == "true" ]]; then
        comma=""
    fi

    # Check if value is already JSON (starts with { or [)
    if [[ "$value" =~ ^[\[\{] ]]; then
        echo "  \"$key\": $value$comma"
    else
        # Escape value for JSON
        local escaped_value
        escaped_value=$(json_escape "$value")
        echo "  \"$key\": \"$escaped_value\"$comma"
    fi
}

json_field_number() {
    local key="$1"
    local value="$2"
    local last="${3:-false}"

    local comma=","
    if [[ "$last" == "true" ]]; then
        comma=""
    fi

    echo "  \"$key\": $value$comma"
}

json_field_bool() {
    local key="$1"
    local value="$2"
    local last="${3:-false}"

    local comma=","
    if [[ "$last" == "true" ]]; then
        comma=""
    fi

    echo "  \"$key\": $value$comma"
}

# ============================================================================
# Cache Functions
# ============================================================================

is_cache_valid() {
    local cache_file="$1"
    local max_age="${2:-3600}"  # Default: 1 hour

    if ! file_exists "$cache_file"; then
        return 1
    fi

    local mtime
    mtime=$(get_file_mtime "$cache_file")
    local now
    now=$(date +%s)
    local age=$((now - mtime))

    if [[ $age -gt $max_age ]]; then
        return 1
    fi

    return 0
}

# ============================================================================
# Error Handling
# ============================================================================

die() {
    local message="$1"
    local code="${2:-1}"
    local error_type="${3:-}"

    # Check if enhanced error messages are available and an error type is specified
    if [[ -n "$error_type" ]] && declare -f "error_${error_type}" > /dev/null 2>&1; then
        # Call specialized error handler
        # Pass all remaining arguments after the first 3
        shift 3
        "error_${error_type}" "$@"
        exit "$code"
    else
        # Fallback to simple error
        write_error "$message"
        exit "$code"
    fi
}

require_command() {
    local cmd="$1"
    local install_hint="${2:-}"

    if ! command -v "$cmd" &> /dev/null; then
        write_error "$cmd is required but not installed."
        if [[ -n "$install_hint" ]]; then
            echo "$install_hint"
        fi
        exit 1
    fi
}

# ============================================================================
# Version Functions
# ============================================================================

compare_versions() {
    # Returns: 0 if equal, 1 if $1 > $2, 2 if $1 < $2
    local ver1="$1"
    local ver2="$2"

    if [[ "$ver1" == "$ver2" ]]; then
        return 0
    fi

    local IFS=.
    local i ver1_arr=($ver1) ver2_arr=($ver2)

    # Fill empty positions with zeros
    for ((i=${#ver1_arr[@]}; i<${#ver2_arr[@]}; i++)); do
        ver1_arr[i]=0
    done
    for ((i=${#ver2_arr[@]}; i<${#ver1_arr[@]}; i++)); do
        ver2_arr[i]=0
    done

    for ((i=0; i<${#ver1_arr[@]}; i++)); do
        if ((10#${ver1_arr[i]} > 10#${ver2_arr[i]})); then
            return 1
        fi
        if ((10#${ver1_arr[i]} < 10#${ver2_arr[i]})); then
            return 2
        fi
    done

    return 0
}

# ============================================================================
# Initialization
# ============================================================================

# Check Bash version (require 4.0+)
if ((BASH_VERSINFO[0] < 4)); then
    write_error "Bash 4.0+ is required. Current version: $BASH_VERSION"
    exit 1
fi

# Check required commands
check_jq

# Export functions for use in other scripts
export -f write_header write_step_header write_success write_info write_warning write_error write_progress
export -f check_jq json_escape
export -f ensure_dir file_exists dir_exists get_file_size get_file_mtime get_file_hash count_files get_dir_size
export -f trim to_lowercase to_uppercase
export -f get_iso_timestamp get_timestamp
export -f is_git_repo get_repo_root validate_json_file
export -f get_absolute_path get_relative_path
export -f array_contains array_join
export -f json_object_start json_object_end json_array_start json_array_end
export -f json_field json_field_number json_field_bool
export -f is_cache_valid
export -f die require_command
export -f compare_versions
