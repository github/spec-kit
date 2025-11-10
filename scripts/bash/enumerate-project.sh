#!/usr/bin/env bash
#
# enumerate-project.sh - Enumerate all files in a project for AI analysis
#
# Usage:
#   ./enumerate-project.sh --project PATH [--output FILE] [--max-size BYTES]
#
# This script performs a full recursive scan of a project directory and outputs
# a JSON manifest of all files with metadata. AI will use this to decide what
# to include/exclude and how to read each file.
#

set -euo pipefail

# Default values
PROJECT_PATH=""
OUTPUT_FILE=""
MAX_FILE_SIZE=$((10 * 1024 * 1024))  # 10MB default
SCAN_START=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Colors for output (if not outputting JSON to stdout)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script metadata
SCRIPT_VERSION="1.0.0"
SCRIPT_NAME="enumerate-project.sh"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --project)
            PROJECT_PATH="$2"
            shift 2
            ;;
        --output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        --max-size)
            MAX_FILE_SIZE="$2"
            shift 2
            ;;
        -h|--help)
            cat <<EOF
Usage: $0 --project PATH [OPTIONS]

Enumerate all files in a project directory for AI analysis.

Required Arguments:
  --project PATH       Path to project root directory

Optional Arguments:
  --output FILE        Output JSON file (default: stdout)
  --max-size BYTES     Maximum file size to include (default: 10485760 = 10MB)
  -h, --help          Show this help message

Output Format:
  JSON object with project structure, file metadata, and statistics

Examples:
  # Scan current directory, output to stdout
  $0 --project .

  # Scan project, save to file
  $0 --project /path/to/legacy --output manifest.json

  # Scan with custom size limit (50MB)
  $0 --project . --output manifest.json --max-size 52428800

EOF
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            echo "Use --help for usage information" >&2
            exit 1
            ;;
    esac
done

# Validate required arguments
if [[ -z "$PROJECT_PATH" ]]; then
    echo "ERROR: --project is required" >&2
    echo "Use --help for usage information" >&2
    exit 1
fi

# Validate project path
if [[ ! -d "$PROJECT_PATH" ]]; then
    echo "ERROR: Project path does not exist or is not a directory: $PROJECT_PATH" >&2
    exit 1
fi

# Convert to absolute path
PROJECT_PATH=$(cd "$PROJECT_PATH" && pwd)

# Determine if we should show progress (only if output goes to file)
SHOW_PROGRESS=false
if [[ -n "$OUTPUT_FILE" ]]; then
    SHOW_PROGRESS=true
fi

# Progress function
log_progress() {
    if [[ "$SHOW_PROGRESS" == "true" ]]; then
        echo -e "${BLUE}ℹ${NC} $1" >&2
    fi
}

log_success() {
    if [[ "$SHOW_PROGRESS" == "true" ]]; then
        echo -e "${GREEN}✓${NC} $1" >&2
    fi
}

log_warning() {
    if [[ "$SHOW_PROGRESS" == "true" ]]; then
        echo -e "${YELLOW}⚠${NC} $1" >&2
    fi
}

log_error() {
    echo -e "${RED}✗${NC} $1" >&2
}

# Detect if a file is binary
is_binary() {
    local file="$1"

    # Check using file command if available
    if command -v file &> /dev/null; then
        if file --mime-type "$file" 2>/dev/null | grep -q 'text/'; then
            echo "false"
            return
        fi
    fi

    # Fallback: check for null bytes in first 8KB
    if head -c 8192 "$file" 2>/dev/null | grep -qI .; then
        echo "false"
    else
        echo "true"
    fi
}

# Get file category based on extension
get_category() {
    local file="$1"
    local ext="${file##*.}"

    case "$ext" in
        # Code files
        js|ts|jsx|tsx|mjs|cjs) echo "code" ;;
        cs|fs|vb) echo "code" ;;
        java|kt|scala|groovy) echo "code" ;;
        py|pyw|pyx) echo "code" ;;
        rb|rake|gemspec) echo "code" ;;
        go) echo "code" ;;
        rs) echo "code" ;;
        php|phtml) echo "code" ;;
        c|cpp|cc|cxx|h|hpp) echo "code" ;;
        swift|m|mm) echo "code" ;;

        # Markup and styles
        html|htm|xhtml) echo "markup" ;;
        css|scss|sass|less) echo "style" ;;
        vue|svelte) echo "component" ;;

        # Configuration
        json|yaml|yml|toml|ini|conf|config) echo "config" ;;
        xml|plist) echo "config" ;;
        env|properties) echo "config" ;;

        # Build and project files
        csproj|sln|fsproj|vbproj) echo "project" ;;
        gradle|pom) echo "project" ;;
        gemfile|rakefile) echo "project" ;;
        lock) echo "lockfile" ;;

        # Database
        sql|psql|mysql) echo "database" ;;

        # Scripts
        sh|bash|zsh|fish) echo "script" ;;
        ps1|psm1|psd1) echo "script" ;;
        bat|cmd) echo "script" ;;

        # Documentation
        md|markdown|txt|rst|adoc) echo "documentation" ;;

        # Data
        csv|tsv|dat) echo "data" ;;

        # Binary/compiled
        dll|exe|so|dylib|a|o|obj|pdb) echo "binary" ;;
        class|jar|war|ear) echo "binary" ;;
        pyc|pyo) echo "binary" ;;

        # Images
        jpg|jpeg|png|gif|svg|ico|webp) echo "image" ;;

        # Archives
        zip|tar|gz|bz2|xz|7z|rar) echo "archive" ;;

        # Default
        *)
            if [[ ! "$file" =~ \. ]]; then
                echo "no_extension"
            else
                echo "other"
            fi
            ;;
    esac
}

# Main enumeration function
enumerate_files() {
    log_progress "Starting full recursive scan of: $PROJECT_PATH"

    local file_count=0
    local total_size=0
    local binary_count=0
    local oversized_count=0
    local error_count=0

    # Arrays to collect data
    declare -a files_json
    declare -a errors_json
    declare -A category_counts
    declare -A extension_counts

    # Use find to enumerate all files
    while IFS= read -r -d '' filepath; do
        ((file_count++))

        # Show progress every 100 files
        if [[ $((file_count % 100)) -eq 0 ]]; then
            log_progress "Scanned $file_count files..."
        fi

        # Get relative path
        local rel_path="${filepath#$PROJECT_PATH/}"

        # Get file size
        local size
        if [[ -f "$filepath" ]]; then
            size=$(stat -f %z "$filepath" 2>/dev/null || stat -c %s "$filepath" 2>/dev/null || echo 0)
        else
            size=0
        fi

        ((total_size += size))

        # Get file extension
        local ext="${filepath##*.}"
        if [[ "$filepath" =~ \. ]]; then
            ext=".$ext"
        else
            ext=""
        fi

        # Get category
        local category=$(get_category "$filepath")

        # Update counters
        ((category_counts[$category]=${category_counts[$category]:-0} + 1))
        if [[ -n "$ext" ]]; then
            ((extension_counts[$ext]=${extension_counts[$ext]:-0} + 1))
        fi

        # Check if file is readable
        local readable="true"
        local is_binary_file="false"
        local size_category="normal"
        local skip_reason=""

        if [[ ! -r "$filepath" ]]; then
            readable="false"
            skip_reason="permission_denied"
            ((error_count++))
        elif [[ $size -gt $MAX_FILE_SIZE ]]; then
            size_category="oversized"
            skip_reason="exceeds_max_size"
            ((oversized_count++))
        elif [[ "$category" == "binary" ]] || [[ "$category" == "image" ]] || [[ "$category" == "archive" ]]; then
            is_binary_file="true"
            ((binary_count++))
        elif [[ -f "$filepath" ]]; then
            # Check if actually binary
            is_binary_file=$(is_binary "$filepath")
            if [[ "$is_binary_file" == "true" ]]; then
                ((binary_count++))
            fi
        fi

        # Determine size category for readable files
        if [[ "$size_category" != "oversized" ]] && [[ "$readable" == "true" ]]; then
            if [[ $size -lt 10240 ]]; then
                size_category="tiny"      # < 10KB
            elif [[ $size -lt 102400 ]]; then
                size_category="small"     # < 100KB
            elif [[ $size -lt 1048576 ]]; then
                size_category="medium"    # < 1MB
            else
                size_category="large"     # 1MB - 10MB
            fi
        fi

        # Build JSON object for this file
        local file_json=$(cat <<EOF
{
  "path": "$rel_path",
  "absolute_path": "$filepath",
  "size_bytes": $size,
  "extension": "$ext",
  "category": "$category",
  "size_category": "$size_category",
  "is_binary": $is_binary_file,
  "readable": $readable,
  "skip_reason": "$skip_reason"
}
EOF
)

        files_json+=("$file_json")

        # Log errors
        if [[ "$readable" == "false" ]]; then
            local error_json=$(cat <<EOF
{
  "path": "$rel_path",
  "reason": "$skip_reason"
}
EOF
)
            errors_json+=("$error_json")
        fi

    done < <(find "$PROJECT_PATH" -type f -print0 2>/dev/null)

    log_success "Scanned $file_count files"

    # Build category statistics JSON
    local categories_json=""
    for category in "${!category_counts[@]}"; do
        if [[ -n "$categories_json" ]]; then
            categories_json+=","
        fi
        categories_json+="\"$category\": ${category_counts[$category]}"
    done

    # Build extension statistics JSON
    local extensions_json=""
    for ext in "${!extension_counts[@]}"; do
        if [[ -n "$extensions_json" ]]; then
            extensions_json+=","
        fi
        extensions_json+="\"$ext\": ${extension_counts[$ext]}"
    done

    # Get top 10 largest files
    local largest_files=$(find "$PROJECT_PATH" -type f -exec stat -f '%z %N' {} \; 2>/dev/null | \
                          sort -rn | head -10 | \
                          awk -v project="$PROJECT_PATH/" '{size=$1; $1=""; path=$0; sub(/^[ \t]+/, "", path); sub(project, "", path); printf "{\"path\": \"%s\", \"size_bytes\": %d}", path, size}' | \
                          paste -sd ',' -)

    # Build final JSON output
    local scan_end=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    # Join files array
    local files_array=$(printf "%s," "${files_json[@]}" | sed 's/,$//')

    # Join errors array
    local errors_array=""
    if [[ ${#errors_json[@]} -gt 0 ]]; then
        errors_array=$(printf "%s," "${errors_json[@]}" | sed 's/,$//')
    fi

    # Output JSON
    cat <<EOF
{
  "scan_info": {
    "project_path": "$PROJECT_PATH",
    "scanner": "bash-${BASH_VERSION}",
    "script_version": "$SCRIPT_VERSION",
    "scan_start": "$SCAN_START",
    "scan_end": "$scan_end",
    "max_file_size_bytes": $MAX_FILE_SIZE
  },
  "statistics": {
    "total_files": $file_count,
    "total_size_bytes": $total_size,
    "binary_files": $binary_count,
    "oversized_files": $oversized_count,
    "unreadable_files": $error_count,
    "by_category": {$categories_json},
    "by_extension": {$extensions_json},
    "largest_files": [$largest_files]
  },
  "files": [$files_array],
  "errors": [$errors_array]
}
EOF
}

# Main execution
log_progress "enumerate-project.sh v$SCRIPT_VERSION"
log_progress "Project: $PROJECT_PATH"

if [[ -n "$OUTPUT_FILE" ]]; then
    log_progress "Output: $OUTPUT_FILE"
    enumerate_files > "$OUTPUT_FILE"
    log_success "Enumeration complete: $OUTPUT_FILE"
else
    enumerate_files
fi
